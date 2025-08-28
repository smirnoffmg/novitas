"""Agent memory management for the Novitas AI system."""

import asyncio
from collections.abc import Callable
from datetime import UTC
from datetime import datetime
from typing import Any
from uuid import UUID

from langchain.memory import ConversationBufferMemory

from ..config.logging import get_logger
from ..core.exceptions import AgentError
from ..core.models import MemoryItem
from ..core.models import MemoryType
from ..core.protocols import Agent
from ..core.protocols import DatabaseManager


class MemoryFilter:
    """Filter for querying memory items."""

    def __init__(
        self,
        memory_types: list[MemoryType] | None = None,
        tags: list[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
    ) -> None:
        """Initialize the memory filter.

        Args:
            memory_types: Filter by memory types
            tags: Filter by tags
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of items to return
        """
        self.memory_types = memory_types
        self.tags = tags
        self.start_time = start_time
        self.end_time = end_time
        self.limit = limit

    def matches(self, item: MemoryItem) -> bool:
        """Check if a memory item matches this filter.

        Args:
            item: Memory item to check

        Returns:
            True if item matches the filter
        """
        # Check memory type
        if self.memory_types and item.memory_type not in self.memory_types:
            return False

        # Check tags
        if self.tags and not any(tag in item.tags for tag in self.tags):
            return False

        # Check time range
        if self.start_time and item.timestamp < self.start_time:
            return False

        if self.end_time and item.timestamp > self.end_time:
            return False

        return True


class AgentMemoryManager:
    """Manages memory for agents in the system."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initialize the memory manager.

        Args:
            database_manager: Database manager for memory persistence
        """
        self.database_manager = database_manager
        self.logger = get_logger("agent.memory")
        self._agents: dict[UUID, Agent] = {}
        self._memory_cache: dict[UUID, list[MemoryItem]] = {}
        self._memory_handlers: dict[UUID, list[Callable[[MemoryItem], None]]] = {}
        self._cleanup_tasks: dict[UUID, asyncio.Task[None]] = {}

    async def register_agent(self, agent: Agent) -> None:
        """Register an agent for memory management.

        Args:
            agent: Agent to register

        Raises:
            AgentError: If agent is already registered
        """
        if agent.id in self._agents:
            raise AgentError(f"Agent {agent.id} is already registered")

        self._agents[agent.id] = agent
        self._memory_cache[agent.id] = []
        self._memory_handlers[agent.id] = []

        # Load existing memory
        await self._load_agent_memory(agent.id)

        # Start memory cleanup task
        self._cleanup_tasks[agent.id] = asyncio.create_task(
            self._cleanup_agent_memory(agent.id)
        )

        self.logger.info("Agent registered for memory management", agent_id=agent.id)

    async def unregister_agent(self, agent_id: UUID) -> None:
        """Unregister an agent from memory management.

        Args:
            agent_id: ID of the agent to unregister

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        # Stop cleanup task
        if agent_id in self._cleanup_tasks:
            self._cleanup_tasks[agent_id].cancel()
            try:
                await self._cleanup_tasks[agent_id]
            except asyncio.CancelledError:
                pass
            del self._cleanup_tasks[agent_id]

        # Save memory before unregistering
        await self._save_agent_memory(agent_id)

        # Clear memory cache
        if agent_id in self._memory_cache:
            del self._memory_cache[agent_id]

        # Remove handlers
        if agent_id in self._memory_handlers:
            del self._memory_handlers[agent_id]

        # Remove agent
        del self._agents[agent_id]

        self.logger.info("Agent unregistered from memory management", agent_id=agent_id)

    async def add_memory(
        self,
        agent_id: UUID,
        memory_type: MemoryType,
        content: dict[str, Any],
        tags: list[str] | None = None,
        importance: float = 1.0,
        ttl: float | None = None,
    ) -> UUID:
        """Add a memory item for an agent.

        Args:
            agent_id: ID of the agent
            memory_type: Type of memory
            content: Memory content
            tags: Tags for the memory
            importance: Importance score (0.0 to 1.0)
            ttl: Time to live in seconds (None for permanent)

        Returns:
            Memory item ID

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_item = MemoryItem(
            memory_type=memory_type,
            content=content,
            tags=tags or [],
            importance=importance,
            timestamp=datetime.now(UTC),
            ttl=ttl,
        )

        # Add to cache
        self._memory_cache[agent_id].append(memory_item)

        # Notify handlers
        for handler in self._memory_handlers[agent_id]:
            try:
                handler(memory_item)
            except Exception as e:
                self.logger.error(
                    "Memory handler failed",
                    agent_id=agent_id,
                    memory_id=memory_item.id,
                    error=str(e),
                )

        self.logger.info(
            "Memory added",
            agent_id=agent_id,
            memory_id=memory_item.id,
            memory_type=memory_type.value,
            importance=importance,
        )

        return memory_item.id

    async def get_memory(
        self,
        agent_id: UUID,
        memory_filter: MemoryFilter | None = None,
    ) -> list[MemoryItem]:
        """Get memory items for an agent.

        Args:
            agent_id: ID of the agent
            memory_filter: Filter to apply to memory items

        Returns:
            List of memory items

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        if memory_filter:
            memory_items = [
                item for item in memory_items if memory_filter.matches(item)
            ]

            if memory_filter.limit:
                memory_items = memory_items[: memory_filter.limit]

        return memory_items

    async def search_memory(
        self,
        agent_id: UUID,
        query: str,
        memory_types: list[MemoryType] | None = None,
        limit: int | None = None,
    ) -> list[MemoryItem]:
        """Search memory items for an agent.

        Args:
            agent_id: ID of the agent
            query: Search query
            memory_types: Filter by memory types
            limit: Maximum number of results

        Returns:
            List of matching memory items

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        # Filter by memory type
        if memory_types:
            memory_items = [
                item for item in memory_items if item.memory_type in memory_types
            ]

        # Simple text search (can be enhanced with vector search)
        matching_items = []
        query_lower = query.lower()

        for item in memory_items:
            # Search in content
            content_str = str(item.content).lower()
            if query_lower in content_str:
                matching_items.append(item)
                continue

            # Search in tags
            for tag in item.tags:
                if query_lower in tag.lower():
                    matching_items.append(item)
                    break

        # Sort by importance and recency
        matching_items.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)

        if limit:
            matching_items = matching_items[:limit]

        return matching_items

    async def update_memory(
        self,
        agent_id: UUID,
        memory_id: UUID,
        updates: dict[str, Any],
    ) -> None:
        """Update a memory item.

        Args:
            agent_id: ID of the agent
            memory_id: ID of the memory item
            updates: Updates to apply

        Raises:
            AgentError: If agent is not registered or memory not found
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        for item in memory_items:
            if item.id == memory_id:
                # Apply updates
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)

                self.logger.info(
                    "Memory updated",
                    agent_id=agent_id,
                    memory_id=memory_id,
                    updates=list(updates.keys()),
                )
                return

        raise AgentError(f"Memory item {memory_id} not found for agent {agent_id}")

    async def delete_memory(self, agent_id: UUID, memory_id: UUID) -> None:
        """Delete a memory item.

        Args:
            agent_id: ID of the agent
            memory_id: ID of the memory item

        Raises:
            AgentError: If agent is not registered or memory not found
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        for i, item in enumerate(memory_items):
            if item.id == memory_id:
                del memory_items[i]

                self.logger.info(
                    "Memory deleted",
                    agent_id=agent_id,
                    memory_id=memory_id,
                )
                return

        raise AgentError(f"Memory item {memory_id} not found for agent {agent_id}")

    async def clear_memory(
        self,
        agent_id: UUID,
        memory_filter: MemoryFilter | None = None,
    ) -> int:
        """Clear memory items for an agent.

        Args:
            agent_id: ID of the agent
            memory_filter: Filter for items to clear

        Returns:
            Number of items cleared

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        if memory_filter:
            items_to_remove = [
                item for item in memory_items if memory_filter.matches(item)
            ]
        else:
            items_to_remove = memory_items.copy()

        # Remove items
        for item in items_to_remove:
            memory_items.remove(item)

        self.logger.info(
            "Memory cleared",
            agent_id=agent_id,
            items_cleared=len(items_to_remove),
        )

        return len(items_to_remove)

    async def add_memory_handler(
        self,
        agent_id: UUID,
        handler: Callable[[MemoryItem], None],
    ) -> None:
        """Add a memory handler for an agent.

        Args:
            agent_id: ID of the agent
            handler: Handler function to call when memory is added

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        self._memory_handlers[agent_id].append(handler)

        self.logger.info("Memory handler added", agent_id=agent_id)

    async def remove_memory_handler(
        self,
        agent_id: UUID,
        handler: Callable[[MemoryItem], None],
    ) -> None:
        """Remove a memory handler from an agent.

        Args:
            agent_id: ID of the agent
            handler: Handler function to remove

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        if handler in self._memory_handlers[agent_id]:
            self._memory_handlers[agent_id].remove(handler)

        self.logger.info("Memory handler removed", agent_id=agent_id)

    async def _load_agent_memory(self, agent_id: UUID) -> None:
        """Load memory for an agent from the database.

        Args:
            agent_id: ID of the agent
        """
        try:
            memory_data = await self.database_manager.load_agent_memory(agent_id)
            if memory_data:
                # Convert to MemoryItem objects
                memory_items = []
                for item_data in memory_data.get("items", []):
                    memory_item = MemoryItem(**item_data)
                    memory_items.append(memory_item)

                self._memory_cache[agent_id] = memory_items

                self.logger.info(
                    "Agent memory loaded",
                    agent_id=agent_id,
                    items_loaded=len(memory_items),
                )

        except Exception as e:
            self.logger.error(
                "Failed to load agent memory",
                agent_id=agent_id,
                error=str(e),
            )

    async def _save_agent_memory(self, agent_id: UUID) -> None:
        """Save memory for an agent to the database.

        Args:
            agent_id: ID of the agent
        """
        try:
            memory_items = self._memory_cache[agent_id]

            # Convert to serializable format
            memory_data = {
                "agent_id": agent_id,
                "items": [item.model_dump() for item in memory_items],
                "last_updated": datetime.now(UTC).isoformat(),
            }

            await self.database_manager.save_agent_memory(agent_id, memory_data)

            self.logger.info(
                "Agent memory saved",
                agent_id=agent_id,
                items_saved=len(memory_items),
            )

        except Exception as e:
            self.logger.error(
                "Failed to save agent memory",
                agent_id=agent_id,
                error=str(e),
            )

    async def _cleanup_agent_memory(self, agent_id: UUID) -> None:
        """Clean up expired memory items for an agent.

        Args:
            agent_id: ID of the agent
        """
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                memory_items = self._memory_cache[agent_id]
                current_time = datetime.now(UTC)
                expired_items = []

                for item in memory_items:
                    if (
                        item.ttl
                        and (current_time - item.timestamp).total_seconds() > item.ttl
                    ):
                        expired_items.append(item)

                # Remove expired items
                for item in expired_items:
                    memory_items.remove(item)

                if expired_items:
                    self.logger.info(
                        "Expired memory items cleaned up",
                        agent_id=agent_id,
                        items_removed=len(expired_items),
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "Memory cleanup failed",
                    agent_id=agent_id,
                    error=str(e),
                )

    def get_memory_stats(self, agent_id: UUID) -> dict[str, Any]:
        """Get memory statistics for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Memory statistics

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        # Count by memory type
        type_counts: dict[str, int] = {}
        for item in memory_items:
            type_counts[item.memory_type.value] = (
                type_counts.get(item.memory_type.value, 0) + 1
            )

        # Calculate average importance
        total_importance = sum(item.importance for item in memory_items)
        avg_importance = total_importance / len(memory_items) if memory_items else 0

        return {
            "total_items": len(memory_items),
            "type_counts": type_counts,
            "average_importance": avg_importance,
            "oldest_item": (
                min(item.timestamp for item in memory_items) if memory_items else None
            ),
            "newest_item": (
                max(item.timestamp for item in memory_items) if memory_items else None
            ),
        }


class LangChainMemoryManager:
    """LangChain-based memory manager for agents."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initialize the LangChain memory manager.

        Args:
            database_manager: Database manager for memory persistence
        """
        self.database_manager = database_manager
        self.logger = get_logger("agent.langchain_memory")
        self._agents: dict[UUID, Agent] = {}
        self._memory_cache: dict[UUID, list[MemoryItem]] = {}
        self._langchain_memories: dict[UUID, ConversationBufferMemory] = {}
        self._memory_handlers: dict[UUID, list[Callable[[MemoryItem], None]]] = {}
        self._cleanup_tasks: dict[UUID, asyncio.Task[None]] = {}

    async def register_agent(self, agent: Agent) -> None:
        """Register an agent for memory management.

        Args:
            agent: Agent to register

        Raises:
            AgentError: If agent is already registered
        """
        if agent.id in self._agents:
            raise AgentError(f"Agent {agent.id} is already registered")

        self._agents[agent.id] = agent
        self._memory_cache[agent.id] = []
        self._langchain_memories[agent.id] = ConversationBufferMemory()
        self._memory_handlers[agent.id] = []

        # Load existing memory
        await self._load_agent_memory(agent.id)

        # Start memory cleanup task
        self._cleanup_tasks[agent.id] = asyncio.create_task(
            self._cleanup_agent_memory(agent.id)
        )

        self.logger.info(
            "Agent registered for LangChain memory management", agent_id=agent.id
        )

    async def unregister_agent(self, agent_id: UUID) -> None:
        """Unregister an agent from memory management.

        Args:
            agent_id: ID of the agent to unregister

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        # Stop cleanup task
        if agent_id in self._cleanup_tasks:
            self._cleanup_tasks[agent_id].cancel()
            try:
                await self._cleanup_tasks[agent_id]
            except asyncio.CancelledError:
                pass
            del self._cleanup_tasks[agent_id]

        # Save memory before unregistering
        await self._save_agent_memory(agent_id)

        # Clear memory cache
        if agent_id in self._memory_cache:
            del self._memory_cache[agent_id]

        # Clear LangChain memory
        if agent_id in self._langchain_memories:
            del self._langchain_memories[agent_id]

        # Remove handlers
        if agent_id in self._memory_handlers:
            del self._memory_handlers[agent_id]

        # Remove agent
        del self._agents[agent_id]

        self.logger.info(
            "Agent unregistered from LangChain memory management", agent_id=agent_id
        )

    async def add_memory(
        self,
        agent_id: UUID,
        memory_type: MemoryType,
        content: dict[str, Any],
        tags: list[str] | None = None,
        importance: float = 1.0,
        ttl: float | None = None,
    ) -> UUID:
        """Add a memory item for an agent.

        Args:
            agent_id: ID of the agent
            memory_type: Type of memory
            content: Memory content
            tags: Tags for the memory
            importance: Importance score (0.0 to 1.0)
            ttl: Time to live in seconds (None for permanent)

        Returns:
            Memory item ID

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_item = MemoryItem(
            memory_type=memory_type,
            content=content,
            tags=tags or [],
            importance=importance,
            timestamp=datetime.now(UTC),
            ttl=ttl,
        )

        # Add to cache
        self._memory_cache[agent_id].append(memory_item)

        # Add to LangChain memory if it's a conversation
        if memory_type == MemoryType.CONVERSATION:
            await self._add_to_langchain_memory(agent_id, memory_item)

        # Notify handlers
        for handler in self._memory_handlers[agent_id]:
            try:
                handler(memory_item)
            except Exception as e:
                self.logger.error(
                    "Memory handler failed",
                    agent_id=agent_id,
                    memory_id=memory_item.id,
                    error=str(e),
                )

        self.logger.info(
            "Memory added to LangChain manager",
            agent_id=agent_id,
            memory_id=memory_item.id,
            memory_type=memory_type.value,
            importance=importance,
        )

        return memory_item.id

    async def get_memory(
        self,
        agent_id: UUID,
        memory_filter: "MemoryFilter | None" = None,
    ) -> list[MemoryItem]:
        """Get memory items for an agent.

        Args:
            agent_id: ID of the agent
            memory_filter: Filter to apply to memory items

        Returns:
            List of memory items

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        if memory_filter:
            memory_items = [
                item for item in memory_items if memory_filter.matches(item)
            ]

            if memory_filter.limit:
                memory_items = memory_items[: memory_filter.limit]

        return memory_items

    async def search_memory(
        self,
        agent_id: UUID,
        query: str,
        memory_types: list[MemoryType] | None = None,
        limit: int | None = None,
    ) -> list[MemoryItem]:
        """Search memory items for an agent.

        Args:
            agent_id: ID of the agent
            query: Search query
            memory_types: Filter by memory types
            limit: Maximum number of results

        Returns:
            List of matching memory items

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        # Filter by memory type
        if memory_types:
            memory_items = [
                item for item in memory_items if item.memory_type in memory_types
            ]

        # Simple text search (can be enhanced with vector search)
        matching_items = []
        query_lower = query.lower()

        for item in memory_items:
            # Search in content
            content_str = str(item.content).lower()
            if query_lower in content_str:
                matching_items.append(item)
                continue

            # Search in tags
            for tag in item.tags:
                if query_lower in tag.lower():
                    matching_items.append(item)
                    break

        # Sort by importance and recency
        matching_items.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)

        if limit:
            matching_items = matching_items[:limit]

        return matching_items

    async def update_memory(
        self,
        agent_id: UUID,
        memory_id: UUID,
        updates: dict[str, Any],
    ) -> None:
        """Update a memory item.

        Args:
            agent_id: ID of the agent
            memory_id: ID of the memory item
            updates: Updates to apply

        Raises:
            AgentError: If agent is not registered or memory not found
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        for item in memory_items:
            if item.id == memory_id:
                # Apply updates
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)

                self.logger.info(
                    "Memory updated in LangChain manager",
                    agent_id=agent_id,
                    memory_id=memory_id,
                    updates=list(updates.keys()),
                )
                return

        raise AgentError(f"Memory item {memory_id} not found for agent {agent_id}")

    async def delete_memory(self, agent_id: UUID, memory_id: UUID) -> None:
        """Delete a memory item.

        Args:
            agent_id: ID of the agent
            memory_id: ID of the memory item

        Raises:
            AgentError: If agent is not registered or memory not found
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        for i, item in enumerate(memory_items):
            if item.id == memory_id:
                del memory_items[i]

                self.logger.info(
                    "Memory deleted from LangChain manager",
                    agent_id=agent_id,
                    memory_id=memory_id,
                )
                return

        raise AgentError(f"Memory item {memory_id} not found for agent {agent_id}")

    async def clear_memory(
        self,
        agent_id: UUID,
        memory_filter: "MemoryFilter | None" = None,
    ) -> int:
        """Clear memory items for an agent.

        Args:
            agent_id: ID of the agent
            memory_filter: Filter for items to clear

        Returns:
            Number of items cleared

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        if memory_filter:
            items_to_remove = [
                item for item in memory_items if memory_filter.matches(item)
            ]
        else:
            items_to_remove = memory_items.copy()

        # Remove items
        for item in items_to_remove:
            memory_items.remove(item)

        # Clear LangChain memory if clearing all
        if not memory_filter:
            self._langchain_memories[agent_id].clear()

        self.logger.info(
            "Memory cleared from LangChain manager",
            agent_id=agent_id,
            items_cleared=len(items_to_remove),
        )

        return len(items_to_remove)

    async def add_memory_handler(
        self,
        agent_id: UUID,
        handler: Callable[[MemoryItem], None],
    ) -> None:
        """Add a memory handler for an agent.

        Args:
            agent_id: ID of the agent
            handler: Handler function to call when memory is added

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        self._memory_handlers[agent_id].append(handler)

        self.logger.info("Memory handler added to LangChain manager", agent_id=agent_id)

    async def remove_memory_handler(
        self,
        agent_id: UUID,
        handler: Callable[[MemoryItem], None],
    ) -> None:
        """Remove a memory handler from an agent.

        Args:
            agent_id: ID of the agent
            handler: Handler function to remove

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        if handler in self._memory_handlers[agent_id]:
            self._memory_handlers[agent_id].remove(handler)

        self.logger.info(
            "Memory handler removed from LangChain manager", agent_id=agent_id
        )

    def get_langchain_memory(self, agent_id: UUID) -> ConversationBufferMemory | None:
        """Get the LangChain memory for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            LangChain memory instance or None if agent not registered
        """
        return self._langchain_memories.get(agent_id)

    async def _add_to_langchain_memory(
        self, agent_id: UUID, memory_item: MemoryItem
    ) -> None:
        """Add memory item to LangChain memory.

        Args:
            agent_id: ID of the agent
            memory_item: Memory item to add
        """
        if memory_item.memory_type != MemoryType.CONVERSATION:
            return

        content = memory_item.content
        langchain_memory = self._langchain_memories[agent_id]

        # Try to extract input/output from content
        if "input" in content and "output" in content:
            langchain_memory.save_context(
                {"input": content["input"]}, {"output": content["output"]}
            )
        elif "message" in content:
            # Single message format
            langchain_memory.save_context(
                {"input": content["message"]}, {"output": "Message received"}
            )

    async def _load_agent_memory(self, agent_id: UUID) -> None:
        """Load memory for an agent from the database.

        Args:
            agent_id: ID of the agent
        """
        try:
            memory_data = await self.database_manager.load_agent_memory(agent_id)
            if memory_data:
                # Convert to MemoryItem objects
                memory_items = []
                for item_data in memory_data.get("items", []):
                    memory_item = MemoryItem(**item_data)
                    memory_items.append(memory_item)

                self._memory_cache[agent_id] = memory_items

                # Load into LangChain memory
                for item in memory_items:
                    await self._add_to_langchain_memory(agent_id, item)

                self.logger.info(
                    "Agent memory loaded into LangChain manager",
                    agent_id=agent_id,
                    items_loaded=len(memory_items),
                )

        except Exception as e:
            self.logger.error(
                "Failed to load agent memory into LangChain manager",
                agent_id=agent_id,
                error=str(e),
            )

    async def _save_agent_memory(self, agent_id: UUID) -> None:
        """Save memory for an agent to the database.

        Args:
            agent_id: ID of the agent
        """
        try:
            memory_items = self._memory_cache[agent_id]

            # Convert to serializable format
            memory_data = {
                "agent_id": agent_id,
                "items": [item.model_dump() for item in memory_items],
                "last_updated": datetime.now(UTC).isoformat(),
            }

            await self.database_manager.save_agent_memory(agent_id, memory_data)

            self.logger.info(
                "Agent memory saved from LangChain manager",
                agent_id=agent_id,
                items_saved=len(memory_items),
            )

        except Exception as e:
            self.logger.error(
                "Failed to save agent memory from LangChain manager",
                agent_id=agent_id,
                error=str(e),
            )

    async def _cleanup_agent_memory(self, agent_id: UUID) -> None:
        """Clean up expired memory items for an agent.

        Args:
            agent_id: ID of the agent
        """
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                memory_items = self._memory_cache[agent_id]
                current_time = datetime.now(UTC)
                expired_items = []

                for item in memory_items:
                    if (
                        item.ttl
                        and (current_time - item.timestamp).total_seconds() > item.ttl
                    ):
                        expired_items.append(item)

                # Remove expired items
                for item in expired_items:
                    memory_items.remove(item)

                if expired_items:
                    self.logger.info(
                        "Expired memory items cleaned up from LangChain manager",
                        agent_id=agent_id,
                        items_removed=len(expired_items),
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "Memory cleanup failed in LangChain manager",
                    agent_id=agent_id,
                    error=str(e),
                )

    def get_memory_stats(self, agent_id: UUID) -> dict[str, Any]:
        """Get memory statistics for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Memory statistics

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        memory_items = self._memory_cache[agent_id]

        # Count by memory type
        type_counts: dict[str, int] = {}
        for item in memory_items:
            type_counts[item.memory_type.value] = (
                type_counts.get(item.memory_type.value, 0) + 1
            )

        # Calculate average importance
        total_importance = sum(item.importance for item in memory_items)
        avg_importance = total_importance / len(memory_items) if memory_items else 0

        return {
            "total_items": len(memory_items),
            "type_counts": type_counts,
            "average_importance": avg_importance,
            "oldest_item": (
                min(item.timestamp for item in memory_items) if memory_items else None
            ),
            "newest_item": (
                max(item.timestamp for item in memory_items) if memory_items else None
            ),
        }
