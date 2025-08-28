"""Tests for memory models."""

from datetime import UTC
from datetime import datetime
from uuid import uuid4

import pytest

from novitas.core.models import MemoryItem
from novitas.core.models import MemoryType


class TestMemoryType:
    """Test MemoryType enum."""

    def test_memory_type_values(self) -> None:
        """Test that all memory types have expected values."""
        assert MemoryType.CONVERSATION == "conversation"
        assert MemoryType.KNOWLEDGE == "knowledge"
        assert MemoryType.EXPERIENCE == "experience"
        assert MemoryType.TASK_RESULT == "task_result"
        assert MemoryType.ERROR == "error"
        assert MemoryType.METADATA == "metadata"

    def test_memory_type_enumeration(self) -> None:
        """Test that all memory types can be enumerated."""
        memory_types = list(MemoryType)
        expected_types = [
            "conversation",
            "knowledge",
            "experience",
            "task_result",
            "error",
            "metadata",
        ]
        assert [mt.value for mt in memory_types] == expected_types


class TestMemoryItem:
    """Test MemoryItem model."""

    def test_memory_item_creation(self) -> None:
        """Test basic memory item creation."""
        content = {"message": "test message", "sender": "agent1"}
        memory_item = MemoryItem(
            memory_type=MemoryType.CONVERSATION,
            content=content,
            tags=["test", "conversation"],
            importance=0.8,
        )

        assert memory_item.memory_type == MemoryType.CONVERSATION
        assert memory_item.content == content
        assert memory_item.tags == ["test", "conversation"]
        assert memory_item.importance == 0.8
        assert memory_item.ttl is None
        assert memory_item.metadata == {}
        assert isinstance(memory_item.id, uuid4().__class__)
        assert isinstance(memory_item.timestamp, datetime)

    def test_memory_item_defaults(self) -> None:
        """Test memory item with default values."""
        memory_item = MemoryItem(
            memory_type=MemoryType.KNOWLEDGE,
            content={"fact": "test fact"},
        )

        assert memory_item.memory_type == MemoryType.KNOWLEDGE
        assert memory_item.content == {"fact": "test fact"}
        assert memory_item.tags == []
        assert memory_item.importance == 1.0
        assert memory_item.ttl is None
        assert memory_item.metadata == {}

    def test_memory_item_with_ttl(self) -> None:
        """Test memory item with TTL."""
        memory_item = MemoryItem(
            memory_type=MemoryType.EXPERIENCE,
            content={"experience": "test"},
            ttl=3600.0,  # 1 hour
        )

        assert memory_item.ttl == 3600.0

    def test_memory_item_with_metadata(self) -> None:
        """Test memory item with metadata."""
        metadata = {"source": "test", "version": "1.0"}
        memory_item = MemoryItem(
            memory_type=MemoryType.TASK_RESULT,
            content={"result": "success"},
            metadata=metadata,
        )

        assert memory_item.metadata == metadata

    def test_memory_item_importance_validation(self) -> None:
        """Test importance validation."""
        # Valid importance values
        MemoryItem(
            memory_type=MemoryType.CONVERSATION,
            content={"test": "data"},
            importance=0.0,
        )
        MemoryItem(
            memory_type=MemoryType.CONVERSATION,
            content={"test": "data"},
            importance=0.5,
        )
        MemoryItem(
            memory_type=MemoryType.CONVERSATION,
            content={"test": "data"},
            importance=1.0,
        )

        # Invalid importance values - Pydantic handles validation automatically
        with pytest.raises(ValueError):
            MemoryItem(
                memory_type=MemoryType.CONVERSATION,
                content={"test": "data"},
                importance=-0.1,
            )

        with pytest.raises(ValueError):
            MemoryItem(
                memory_type=MemoryType.CONVERSATION,
                content={"test": "data"},
                importance=1.1,
            )

    def test_memory_item_serialization(self) -> None:
        """Test memory item serialization."""
        memory_item = MemoryItem(
            memory_type=MemoryType.ERROR,
            content={"error": "test error", "stack_trace": "trace"},
            tags=["error", "test"],
            importance=0.9,
            ttl=1800.0,
            metadata={"component": "test"},
        )

        # Test model_dump
        data = memory_item.model_dump()
        assert data["memory_type"] == "error"
        assert data["content"] == {"error": "test error", "stack_trace": "trace"}
        assert data["tags"] == ["error", "test"]
        assert data["importance"] == 0.9
        assert data["ttl"] == 1800.0
        assert data["metadata"] == {"component": "test"}
        assert "id" in data
        assert "timestamp" in data

    def test_memory_item_from_dict(self) -> None:
        """Test creating memory item from dictionary."""
        data = {
            "memory_type": "metadata",
            "content": {"key": "value"},
            "tags": ["tag1", "tag2"],
            "importance": 0.7,
            "ttl": 7200.0,
            "metadata": {"source": "test"},
        }

        memory_item = MemoryItem(**data)
        assert memory_item.memory_type == MemoryType.METADATA
        assert memory_item.content == {"key": "value"}
        assert memory_item.tags == ["tag1", "tag2"]
        assert memory_item.importance == 0.7
        assert memory_item.ttl == 7200.0
        assert memory_item.metadata == {"source": "test"}

    def test_memory_item_timestamp_utc(self) -> None:
        """Test that timestamp is in UTC."""
        memory_item = MemoryItem(
            memory_type=MemoryType.CONVERSATION,
            content={"test": "data"},
        )

        assert memory_item.timestamp.tzinfo == UTC

    def test_memory_item_unique_ids(self) -> None:
        """Test that memory items have unique IDs."""
        item1 = MemoryItem(
            memory_type=MemoryType.CONVERSATION,
            content={"test": "data1"},
        )
        item2 = MemoryItem(
            memory_type=MemoryType.CONVERSATION,
            content={"test": "data2"},
        )

        assert item1.id != item2.id
