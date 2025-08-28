"""Redis-based message broker implementation for Novitas."""

import asyncio
from collections.abc import Callable
from collections.abc import Coroutine
from contextlib import suppress
from datetime import UTC
from datetime import datetime
from typing import Any
from uuid import UUID
from uuid import uuid4

import redis.asyncio as redis

from ..config.logging import get_logger
from ..config.settings import settings
from ..core.exceptions import MessageBrokerError
from ..core.models import AgentMessage
from ..core.models import MessageType
from ..core.protocols import MessageBroker

logger = get_logger(__name__)


class RedisMessageBroker(MessageBroker):
    """Redis-based message broker implementation."""

    def __init__(self, redis_url: str | None = None) -> None:
        """Initialize the Redis message broker.

        Args:
            redis_url: Redis connection URL (defaults to settings)
        """
        self.redis_url = redis_url or settings.redis_url
        self._redis: redis.Redis | None = None
        self._subscribers: dict[
            UUID, list[Callable[[AgentMessage], Coroutine[Any, Any, None]]]
        ] = {}
        self._pubsub: redis.client.PubSub | None = None
        self._listening_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()

            # Initialize pub/sub
            self._pubsub = self._redis.pubsub()

            # Start listening for messages
            self._listening_task = asyncio.create_task(self._listen_for_messages())

            logger.info("Redis message broker connected successfully")

        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise MessageBrokerError(f"Failed to connect to Redis: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        try:
            self._shutdown_event.set()

            if self._listening_task:
                self._listening_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._listening_task

            if self._pubsub:
                await self._pubsub.close()

            if self._redis:
                await self._redis.close()

            logger.info("Redis message broker disconnected successfully")

        except Exception as e:
            logger.error("Failed to disconnect from Redis", error=str(e))
            raise MessageBrokerError(f"Failed to disconnect from Redis: {e}") from e

    async def send_message(self, to_agent: UUID, message: dict[str, Any]) -> None:
        """Send a message to an agent.

        Args:
            to_agent: ID of the recipient agent
            message: Message content
        """
        if not self._redis:
            raise MessageBrokerError("Message broker not connected")

        try:
            # Create message record
            message_record = AgentMessage(
                id=uuid4(),
                sender_id=message.get("sender_id"),
                recipient_id=to_agent,
                message_type=MessageType(message.get("type", "general")),
                content=message.get("content", {}),
                timestamp=message.get("timestamp") or datetime.now(UTC),
            )

            # Serialize message
            message_data = message_record.model_dump_json()

            # Send to Redis pub/sub
            channel = f"agent:{to_agent}"
            await self._redis.publish(channel, message_data)

            # Also store in agent's message queue for persistence
            queue_key = f"agent_queue:{to_agent}"
            await self._redis.lpush(queue_key, message_data)

            # Keep only last 100 messages per agent
            await self._redis.ltrim(queue_key, 0, 99)

            logger.info(
                "Message sent",
                message_id=message_record.id,
                to_agent=to_agent,
                message_type=message_record.message_type.value,
            )

        except Exception as e:
            logger.error(
                "Failed to send message",
                to_agent=to_agent,
                error=str(e),
            )
            raise MessageBrokerError(f"Failed to send message: {e}") from e

    async def receive_message(self, agent_id: UUID) -> dict[str, Any] | None:
        """Receive a message for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Message content or None if no message available
        """
        if not self._redis:
            raise MessageBrokerError("Message broker not connected")

        try:
            # Get message from agent's queue
            queue_key = f"agent_queue:{agent_id}"
            message_data = await self._redis.rpop(queue_key)

            if message_data:
                message = AgentMessage.model_validate_json(message_data)
                return message.model_dump()

            return None

        except Exception as e:
            logger.error(
                "Failed to receive message",
                agent_id=agent_id,
                error=str(e),
            )
            raise MessageBrokerError(f"Failed to receive message: {e}") from e

    async def broadcast_message(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all agents.

        Args:
            message: Message content
        """
        if not self._redis:
            raise MessageBrokerError("Message broker not connected")

        try:
            # Create message record
            message_record = AgentMessage(
                id=uuid4(),
                sender_id=message.get("sender_id"),
                recipient_id=None,  # Broadcast
                message_type=MessageType(message.get("type", "broadcast")),
                content=message.get("content", {}),
                timestamp=message.get("timestamp") or datetime.now(UTC),
            )

            # Serialize message
            message_data = message_record.model_dump_json()

            # Broadcast to all agents
            await self._redis.publish("broadcast", message_data)

            logger.info(
                "Broadcast message sent",
                message_id=message_record.id,
                message_type=message_record.message_type.value,
            )

        except Exception as e:
            logger.error(
                "Failed to broadcast message",
                error=str(e),
            )
            raise MessageBrokerError(f"Failed to broadcast message: {e}") from e

    def subscribe(
        self,
        agent_id: UUID,
        callback: Callable[[AgentMessage], Coroutine[Any, Any, None]],
    ) -> None:
        """Subscribe to messages for an agent.

        Args:
            agent_id: ID of the agent
            callback: Callback function to handle messages
        """
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []

        self._subscribers[agent_id].append(callback)

        # Subscribe to agent's channel
        if self._pubsub:
            # Store task reference to avoid RUF006 warning
            task = asyncio.create_task(self._pubsub.subscribe(f"agent:{agent_id}"))
            # We don't need to await this task, so we ignore it
            _ = task

        logger.info(f"Agent {agent_id} subscribed to messages")

    def unsubscribe(
        self,
        agent_id: UUID,
        callback: Callable[[AgentMessage], Coroutine[Any, Any, None]],
    ) -> None:
        """Unsubscribe from messages for an agent.

        Args:
            agent_id: ID of the agent
            callback: Callback function to remove
        """
        if agent_id in self._subscribers:
            if callback in self._subscribers[agent_id]:
                self._subscribers[agent_id].remove(callback)

            if not self._subscribers[agent_id]:
                del self._subscribers[agent_id]

                # Unsubscribe from agent's channel
                if self._pubsub:
                    # Store task reference to avoid RUF006 warning
                    task = asyncio.create_task(
                        self._pubsub.unsubscribe(f"agent:{agent_id}")
                    )
                    # We don't need to await this task, so we ignore it
                    _ = task

        logger.info(f"Agent {agent_id} unsubscribed from messages")

    async def _listen_for_messages(self) -> None:
        """Listen for incoming messages and route to subscribers."""
        if not self._pubsub:
            return

        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        # Parse message
                        message_data = message["data"]
                        agent_message = AgentMessage.model_validate_json(message_data)

                        # Route to subscribers
                        if agent_message.to_agent_id in self._subscribers:
                            for callback in self._subscribers[
                                agent_message.to_agent_id
                            ]:
                                try:
                                    await callback(agent_message)
                                except Exception as e:
                                    logger.error(
                                        "Error in message callback",
                                        agent_id=agent_message.to_agent_id,
                                        error=str(e),
                                    )

                        # Handle broadcast messages
                        if agent_message.to_agent_id is None:
                            for agent_id, callbacks in self._subscribers.items():
                                for callback in callbacks:
                                    try:
                                        await callback(agent_message)
                                    except Exception as e:
                                        logger.error(
                                            "Error in broadcast callback",
                                            agent_id=agent_id,
                                            error=str(e),
                                        )

                    except Exception as e:
                        logger.error(
                            "Error processing message",
                            error=str(e),
                        )

        except asyncio.CancelledError:
            logger.info("Message listening task cancelled")
        except Exception as e:
            logger.error("Error in message listening task", error=str(e))

    async def get_message_count(self, agent_id: UUID) -> int:
        """Get the number of messages in an agent's queue.

        Args:
            agent_id: ID of the agent

        Returns:
            Number of messages in queue
        """
        if not self._redis:
            return 0

        try:
            queue_key = f"agent_queue:{agent_id}"
            return await self._redis.llen(queue_key)
        except Exception as e:
            logger.error(
                "Failed to get message count",
                agent_id=agent_id,
                error=str(e),
            )
            return 0

    async def clear_agent_messages(self, agent_id: UUID) -> None:
        """Clear all messages for an agent.

        Args:
            agent_id: ID of the agent
        """
        if not self._redis:
            return

        try:
            queue_key = f"agent_queue:{agent_id}"
            await self._redis.delete(queue_key)
            logger.info(f"Cleared messages for agent {agent_id}")
        except Exception as e:
            logger.error(
                "Failed to clear agent messages",
                agent_id=agent_id,
                error=str(e),
            )


def get_message_broker(redis_url: str | None = None) -> MessageBroker:
    """Get a message broker instance.

    Args:
        redis_url: Redis connection URL (defaults to settings)

    Returns:
        Message broker instance
    """
    return RedisMessageBroker(redis_url)
