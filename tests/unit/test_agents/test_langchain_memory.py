"""Tests for LangChain-based memory manager."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from langchain.memory import ConversationBufferMemory

from novitas.agents.memory import LangChainMemoryManager
from novitas.core.models import MemoryItem
from novitas.core.models import MemoryType


class TestLangChainMemoryManager:
    """Test LangChain-based memory manager."""

    @pytest.fixture
    def mock_database_manager(self):
        """Create a mock database manager."""
        return AsyncMock()

    @pytest.fixture
    def memory_manager(self, mock_database_manager):
        """Create a LangChain memory manager instance."""
        return LangChainMemoryManager(database_manager=mock_database_manager)

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = MagicMock()
        agent.id = uuid4()
        agent.name = "Test Agent"
        return agent

    @pytest.mark.asyncio
    async def test_register_agent(self, memory_manager, mock_agent):
        """Test agent registration."""
        await memory_manager.register_agent(mock_agent)

        assert mock_agent.id in memory_manager._agents
        assert mock_agent.id in memory_manager._langchain_memories
        assert isinstance(
            memory_manager._langchain_memories[mock_agent.id], ConversationBufferMemory
        )

    @pytest.mark.asyncio
    async def test_register_agent_already_registered(self, memory_manager, mock_agent):
        """Test registering an already registered agent."""
        await memory_manager.register_agent(mock_agent)

        with pytest.raises(Exception, match="Agent .* is already registered"):
            await memory_manager.register_agent(mock_agent)

    @pytest.mark.asyncio
    async def test_unregister_agent(self, memory_manager, mock_agent):
        """Test agent unregistration."""
        await memory_manager.register_agent(mock_agent)
        await memory_manager.unregister_agent(mock_agent.id)

        assert mock_agent.id not in memory_manager._agents
        assert mock_agent.id not in memory_manager._langchain_memories

    @pytest.mark.asyncio
    async def test_unregister_agent_not_registered(self, memory_manager):
        """Test unregistering a non-registered agent."""
        with pytest.raises(Exception, match="Agent .* is not registered"):
            await memory_manager.unregister_agent(uuid4())

    @pytest.mark.asyncio
    async def test_add_memory(self, memory_manager, mock_agent):
        """Test adding memory."""
        await memory_manager.register_agent(mock_agent)

        memory_id = await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"message": "Hello", "sender": "user"},
            tags=["greeting"],
            importance=0.8,
        )

        assert isinstance(memory_id, uuid4().__class__)

        # Check that memory was added to both systems
        memories = await memory_manager.get_memory(mock_agent.id)
        assert len(memories) == 1
        assert memories[0].memory_type == MemoryType.CONVERSATION
        assert memories[0].content == {"message": "Hello", "sender": "user"}

        # Check LangChain memory
        langchain_memory = memory_manager._langchain_memories[mock_agent.id]
        variables = langchain_memory.load_memory_variables({})
        assert "history" in variables

    @pytest.mark.asyncio
    async def test_add_memory_with_ttl(self, memory_manager, mock_agent):
        """Test adding memory with TTL."""
        await memory_manager.register_agent(mock_agent)

        memory_id = await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.EXPERIENCE,
            content={"experience": "test"},
            ttl=3600.0,
        )

        memories = await memory_manager.get_memory(mock_agent.id)
        assert len(memories) == 1
        assert memories[0].ttl == 3600.0

    @pytest.mark.asyncio
    async def test_get_memory_with_filter(self, memory_manager, mock_agent):
        """Test getting memory with filter."""
        await memory_manager.register_agent(mock_agent)

        # Add different types of memory
        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"message": "Hello"},
            tags=["greeting"],
        )

        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.KNOWLEDGE,
            content={"fact": "test fact"},
            tags=["fact"],
        )

        # Filter by memory type
        from novitas.agents.memory import MemoryFilter

        filter_obj = MemoryFilter(memory_types=[MemoryType.CONVERSATION])
        memories = await memory_manager.get_memory(mock_agent.id, filter_obj)

        assert len(memories) == 1
        assert memories[0].memory_type == MemoryType.CONVERSATION

    @pytest.mark.asyncio
    async def test_search_memory(self, memory_manager, mock_agent):
        """Test searching memory."""
        await memory_manager.register_agent(mock_agent)

        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"message": "Hello world"},
            tags=["greeting"],
        )

        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.KNOWLEDGE,
            content={"fact": "Python is a programming language"},
            tags=["programming"],
        )

        # Search for "Hello"
        results = await memory_manager.search_memory(
            agent_id=mock_agent.id, query="Hello"
        )
        assert len(results) == 1
        assert "Hello" in str(results[0].content)

        # Search for "Python"
        results = await memory_manager.search_memory(
            agent_id=mock_agent.id, query="Python"
        )
        assert len(results) == 1
        assert "Python" in str(results[0].content)

    @pytest.mark.asyncio
    async def test_update_memory(self, memory_manager, mock_agent):
        """Test updating memory."""
        await memory_manager.register_agent(mock_agent)

        memory_id = await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"message": "Hello"},
            importance=0.5,
        )

        # Update the memory
        await memory_manager.update_memory(
            agent_id=mock_agent.id,
            memory_id=memory_id,
            updates={"importance": 0.9, "tags": ["updated"]},
        )

        memories = await memory_manager.get_memory(mock_agent.id)
        assert len(memories) == 1
        assert memories[0].importance == 0.9
        assert "updated" in memories[0].tags

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_manager, mock_agent):
        """Test deleting memory."""
        await memory_manager.register_agent(mock_agent)

        memory_id = await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"message": "Hello"},
        )

        # Delete the memory
        await memory_manager.delete_memory(mock_agent.id, memory_id)

        memories = await memory_manager.get_memory(mock_agent.id)
        assert len(memories) == 0

    @pytest.mark.asyncio
    async def test_clear_memory(self, memory_manager, mock_agent):
        """Test clearing memory."""
        await memory_manager.register_agent(mock_agent)

        # Add multiple memories
        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"message": "Hello"},
        )

        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.KNOWLEDGE,
            content={"fact": "test"},
        )

        # Clear all memory
        cleared_count = await memory_manager.clear_memory(mock_agent.id)
        assert cleared_count == 2

        memories = await memory_manager.get_memory(mock_agent.id)
        assert len(memories) == 0

    @pytest.mark.asyncio
    async def test_get_memory_stats(self, memory_manager, mock_agent):
        """Test getting memory statistics."""
        await memory_manager.register_agent(mock_agent)

        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"message": "Hello"},
            importance=0.8,
        )

        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.KNOWLEDGE,
            content={"fact": "test"},
            importance=0.6,
        )

        stats = memory_manager.get_memory_stats(mock_agent.id)

        assert stats["total_items"] == 2
        assert stats["type_counts"]["conversation"] == 1
        assert stats["type_counts"]["knowledge"] == 1
        assert stats["average_importance"] == 0.7
        assert stats["oldest_item"] is not None
        assert stats["newest_item"] is not None

    @pytest.mark.asyncio
    async def test_langchain_integration(self, memory_manager, mock_agent):
        """Test LangChain memory integration."""
        await memory_manager.register_agent(mock_agent)

        # Add conversation memory
        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"input": "Hello", "output": "Hi there!"},
        )

        # Get LangChain memory
        langchain_memory = memory_manager._langchain_memories[mock_agent.id]
        variables = langchain_memory.load_memory_variables({})

        # The LangChain memory should contain the conversation
        assert "history" in variables

    @pytest.mark.asyncio
    async def test_memory_handlers(self, memory_manager, mock_agent):
        """Test memory handlers."""
        await memory_manager.register_agent(mock_agent)

        handler_called = False
        handler_memory = None

        def test_handler(memory_item: MemoryItem):
            nonlocal handler_called, handler_memory
            handler_called = True
            handler_memory = memory_item

        await memory_manager.add_memory_handler(mock_agent.id, test_handler)

        # Add memory to trigger handler
        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"message": "Hello"},
        )

        assert handler_called
        assert handler_memory is not None
        assert handler_memory.memory_type == MemoryType.CONVERSATION

    @pytest.mark.asyncio
    async def test_memory_persistence(
        self, memory_manager, mock_agent, mock_database_manager
    ):
        """Test memory persistence to database."""
        await memory_manager.register_agent(mock_agent)

        await memory_manager.add_memory(
            agent_id=mock_agent.id,
            memory_type=MemoryType.CONVERSATION,
            content={"message": "Hello"},
        )

        # Unregister agent to trigger save
        await memory_manager.unregister_agent(mock_agent.id)

        # Verify save was called
        mock_database_manager.save_agent_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_loading(
        self, memory_manager, mock_agent, mock_database_manager
    ):
        """Test memory loading from database."""
        # Mock database to return existing memory
        mock_database_manager.load_agent_memory.return_value = {
            "agent_id": str(mock_agent.id),
            "items": [
                {
                    "id": str(uuid4()),
                    "memory_type": "conversation",
                    "content": {"message": "Hello"},
                    "tags": ["greeting"],
                    "importance": 0.8,
                    "timestamp": "2024-01-01T00:00:00+00:00",
                    "ttl": None,
                    "metadata": {},
                }
            ],
            "last_updated": "2024-01-01T00:00:00+00:00",
        }

        await memory_manager.register_agent(mock_agent)

        # Verify memory was loaded
        memories = await memory_manager.get_memory(mock_agent.id)
        assert len(memories) == 1
        assert memories[0].memory_type == MemoryType.CONVERSATION
        assert memories[0].content == {"message": "Hello"}
