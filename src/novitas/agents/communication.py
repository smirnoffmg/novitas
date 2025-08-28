"""Agent communication system for the Novitas AI system."""

import asyncio
import contextlib
from collections.abc import Callable
from collections.abc import Coroutine
from datetime import UTC
from datetime import datetime
from typing import Any
from uuid import UUID
from uuid import uuid4

from ..config.logging import get_logger
from ..core.exceptions import AgentCommunicationError
from ..core.exceptions import AgentError
from ..core.models import AgentMessage
from ..core.models import MessageType
from ..core.protocols import Agent
from ..core.protocols import MessageBroker


class MessageHandler:
    """Handler for processing incoming messages."""

    def __init__(
        self,
        handler_func: Callable[[AgentMessage], Coroutine[Any, Any, None]],
        message_types: list[MessageType] | None = None,
    ) -> None:
        """Initialize the message handler.

        Args:
            handler_func: Function to handle the message
            message_types: Types of messages this handler can process (None for all)
        """
        self.handler_func = handler_func
        self.message_types = message_types or list(MessageType)

    async def can_handle(self, message: AgentMessage) -> bool:
        """Check if this handler can process the given message.

        Args:
            message: Message to check

        Returns:
            True if handler can process the message
        """
        return message.message_type in self.message_types

    async def handle(self, message: AgentMessage) -> None:
        """Handle the message.

        Args:
            message: Message to handle
        """
        await self.handler_func(message)


class AgentCommunicationManager:
    """Manages communication between agents."""

    def __init__(self, message_broker: MessageBroker) -> None:
        """Initialize the communication manager.

        Args:
            message_broker: Message broker for sending/receiving messages
        """
        self.message_broker = message_broker
        self.logger = get_logger("agent.communication")
        self._agents: dict[UUID, Agent] = {}
        self._message_handlers: dict[UUID, list[MessageHandler]] = {}
        self._message_queues: dict[UUID, asyncio.Queue[AgentMessage]] = {}
        self._processing_tasks: dict[UUID, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()

    async def register_agent(self, agent: Agent) -> None:
        """Register an agent for communication.

        Args:
            agent: Agent to register

        Raises:
            AgentError: If agent is already registered
        """
        if agent.id in self._agents:
            raise AgentError(f"Agent {agent.id} is already registered")

        self._agents[agent.id] = agent
        self._message_handlers[agent.id] = []
        self._message_queues[agent.id] = asyncio.Queue()

        # Start message processing task
        self._processing_tasks[agent.id] = asyncio.create_task(
            self._process_messages_for_agent(agent.id)
        )

        self.logger.info("Agent registered for communication", agent_id=agent.id)

    async def unregister_agent(self, agent_id: UUID) -> None:
        """Unregister an agent from communication.

        Args:
            agent_id: ID of the agent to unregister

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        # Stop message processing
        if agent_id in self._processing_tasks:
            self._processing_tasks[agent_id].cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._processing_tasks[agent_id]
            del self._processing_tasks[agent_id]

        # Clear message queue
        if agent_id in self._message_queues:
            del self._message_queues[agent_id]

        # Remove handlers
        if agent_id in self._message_handlers:
            del self._message_handlers[agent_id]

        # Remove agent
        del self._agents[agent_id]

        self.logger.info("Agent unregistered from communication", agent_id=agent_id)

    async def add_message_handler(
        self,
        agent_id: UUID,
        handler: MessageHandler,
    ) -> None:
        """Add a message handler for an agent.

        Args:
            agent_id: ID of the agent
            handler: Message handler to add

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        self._message_handlers[agent_id].append(handler)

        self.logger.info(
            "Message handler added",
            agent_id=agent_id,
            message_types=handler.message_types,
        )

    async def remove_message_handler(
        self,
        agent_id: UUID,
        handler: MessageHandler,
    ) -> None:
        """Remove a message handler from an agent.

        Args:
            agent_id: ID of the agent
            handler: Message handler to remove

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        if handler in self._message_handlers[agent_id]:
            self._message_handlers[agent_id].remove(handler)

        self.logger.info("Message handler removed", agent_id=agent_id)

    async def send_message(
        self,
        from_agent_id: UUID,
        to_agent_id: UUID,
        message_type: MessageType,
        content: dict[str, Any],
        priority: int = 0,
        timeout: float | None = None,
    ) -> UUID:
        """Send a message from one agent to another.

        Args:
            from_agent_id: ID of the sending agent
            to_agent_id: ID of the receiving agent
            message_type: Type of message
            content: Message content
            priority: Message priority (higher = more important)
            timeout: Message timeout in seconds

        Returns:
            Message ID

        Raises:
            AgentError: If agents are not registered
            CommunicationError: If message sending fails
        """
        if from_agent_id not in self._agents:
            raise AgentError(f"Source agent {from_agent_id} is not registered")

        if to_agent_id not in self._agents:
            raise AgentError(f"Target agent {to_agent_id} is not registered")

        message_id = uuid4()
        message = AgentMessage(
            id=message_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=message_type,
            content=content,
            priority=priority,
            timestamp=datetime.now(UTC),
            timeout=timeout,
        )

        try:
            # Send via message broker
            await self.message_broker.send_message(to_agent_id, message.model_dump())

            # Add to local queue for immediate processing
            await self._message_queues[to_agent_id].put(message)

            self.logger.info(
                "Message sent",
                message_id=message_id,
                from_agent=from_agent_id,
                to_agent=to_agent_id,
                message_type=message_type.value,
            )

            return message_id

        except Exception as e:
            self.logger.error(
                "Failed to send message",
                message_id=message_id,
                from_agent=from_agent_id,
                to_agent=to_agent_id,
                error=str(e),
            )
            raise AgentCommunicationError(f"Failed to send message: {e}") from e

    async def broadcast_message(
        self,
        from_agent_id: UUID,
        message_type: MessageType,
        content: dict[str, Any],
        exclude_agents: list[UUID] | None = None,
        priority: int = 0,
    ) -> list[UUID]:
        """Broadcast a message to all registered agents.

        Args:
            from_agent_id: ID of the sending agent
            message_type: Type of message
            content: Message content
            exclude_agents: List of agent IDs to exclude from broadcast
            priority: Message priority

        Returns:
            List of message IDs for sent messages

        Raises:
            AgentError: If source agent is not registered
        """
        if from_agent_id not in self._agents:
            raise AgentError(f"Source agent {from_agent_id} is not registered")

        exclude_agents = exclude_agents or []
        message_ids = []

        for agent_id in self._agents:
            if agent_id != from_agent_id and agent_id not in exclude_agents:
                try:
                    message_id = await self.send_message(
                        from_agent_id, agent_id, message_type, content, priority
                    )
                    message_ids.append(message_id)
                except Exception as e:
                    self.logger.error(
                        "Failed to broadcast message to agent",
                        agent_id=agent_id,
                        error=str(e),
                    )

        self.logger.info(
            "Message broadcasted",
            from_agent=from_agent_id,
            message_type=message_type.value,
            recipients=len(message_ids),
        )

        return message_ids

    async def get_messages(
        self,
        agent_id: UUID,
        message_types: list[MessageType] | None = None,
        limit: int | None = None,
    ) -> list[AgentMessage]:
        """Get messages for an agent.

        Args:
            agent_id: ID of the agent
            message_types: Filter by message types (None for all)
            limit: Maximum number of messages to return

        Returns:
            List of messages

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        messages = []
        queue = self._message_queues[agent_id]

        # Get messages from queue
        while not queue.empty() and (limit is None or len(messages) < limit):
            try:
                message = queue.get_nowait()

                # Filter by message type if specified
                if message_types is None or message.message_type in message_types:
                    messages.append(message)

            except asyncio.QueueEmpty:
                break

        return messages

    async def _process_messages_for_agent(self, agent_id: UUID) -> None:
        """Process messages for a specific agent.

        Args:
            agent_id: ID of the agent to process messages for
        """
        queue = self._message_queues[agent_id]

        while not self._shutdown_event.is_set():
            try:
                # Wait for message with timeout
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                except TimeoutError:
                    continue

                # Check message timeout
                if (
                    message.timeout
                    and (datetime.now(UTC) - message.timestamp).total_seconds()
                    > message.timeout
                ):
                    self.logger.warning(
                        "Message timed out",
                        message_id=message.id,
                        agent_id=agent_id,
                    )
                    continue

                # Find appropriate handler
                handled = False
                for handler in self._message_handlers[agent_id]:
                    if await handler.can_handle(message):
                        try:
                            await handler.handle(message)
                            handled = True
                            break
                        except Exception as e:
                            self.logger.error(
                                "Message handler failed",
                                message_id=message.id,
                                agent_id=agent_id,
                                error=str(e),
                            )

                if not handled:
                    self.logger.warning(
                        "No handler found for message",
                        message_id=message.id,
                        agent_id=agent_id,
                        message_type=message.message_type.value,
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "Error processing messages for agent",
                    agent_id=agent_id,
                    error=str(e),
                )

    async def shutdown(self) -> None:
        """Shutdown the communication manager."""
        self._shutdown_event.set()

        # Cancel all processing tasks
        for task in self._processing_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self._processing_tasks:
            await asyncio.gather(
                *self._processing_tasks.values(), return_exceptions=True
            )

        self.logger.info("Communication manager shutdown complete")

    def get_agent_message_count(self, agent_id: UUID) -> int:
        """Get the number of pending messages for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Number of pending messages

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        return self._message_queues[agent_id].qsize()

    def get_all_message_counts(self) -> dict[UUID, int]:
        """Get message counts for all agents.

        Returns:
            Dictionary of agent ID to message count
        """
        return {
            agent_id: self.get_agent_message_count(agent_id)
            for agent_id in self._agents
        }
