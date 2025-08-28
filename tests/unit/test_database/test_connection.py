"""Tests for database connection manager."""

from uuid import uuid4

import pytest

from novitas.core.models import AgentState
from novitas.core.models import AgentStatus
from novitas.core.models import AgentType
from novitas.database.connection import DatabaseManagerImpl


class TestDatabaseManager:
    """Test DatabaseManager implementation."""

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, clean_database) -> None:
        """Test database connection and disconnection."""
        # Arrange
        manager = clean_database

        # Act & Assert
        assert manager.get_status() == "Connected"

        await manager.disconnect()
        assert manager.get_status() == "Disconnected"

    @pytest.mark.asyncio
    async def test_save_and_load_agent_state(
        self, clean_database, sample_agent_state
    ) -> None:
        """Test saving and loading agent state."""
        # Arrange
        manager = clean_database
        agent_state = sample_agent_state

        # Act
        await manager.save_agent_state(agent_state)
        loaded_agent = await manager.load_agent_state(agent_state.id)

        # Assert
        assert loaded_agent is not None
        assert loaded_agent.id == agent_state.id
        assert loaded_agent.name == agent_state.name
        assert loaded_agent.agent_type == agent_state.agent_type
        assert loaded_agent.status == agent_state.status

    @pytest.mark.asyncio
    async def test_load_nonexistent_agent_state(self, clean_database) -> None:
        """Test loading a non-existent agent state."""
        # Arrange
        manager = clean_database
        nonexistent_id = uuid4()

        # Act
        loaded_agent = await manager.load_agent_state(nonexistent_id)

        # Assert
        assert loaded_agent is None

    @pytest.mark.asyncio
    async def test_update_agent_state(self, clean_database, sample_agent_state) -> None:
        """Test updating an existing agent state."""
        # Arrange
        manager = clean_database
        agent_state = sample_agent_state

        # Act - Save initial state
        await manager.save_agent_state(agent_state)

        # Update the agent state
        agent_state.name = "Updated Agent Name"
        agent_state.status = AgentStatus.INACTIVE
        await manager.save_agent_state(agent_state)

        # Load and verify
        loaded_agent = await manager.load_agent_state(agent_state.id)

        # Assert
        assert loaded_agent is not None
        assert loaded_agent.name == "Updated Agent Name"
        assert loaded_agent.status == AgentStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_save_and_get_change_proposal(
        self, clean_database, sample_change_proposal
    ) -> None:
        """Test saving and retrieving change proposals."""
        # Arrange
        manager = clean_database
        proposal = sample_change_proposal

        # Act
        await manager.save_change_proposal(proposal)
        proposals = await manager.get_change_proposals(
            uuid4()
        )  # cycle_id not implemented yet

        # Assert
        assert len(proposals) >= 1
        # Note: get_change_proposals currently returns all proposals since cycle_id filtering isn't implemented

    @pytest.mark.asyncio
    async def test_save_and_get_improvement_cycle(
        self, clean_database, sample_improvement_cycle
    ) -> None:
        """Test saving and retrieving improvement cycles."""
        # Arrange
        manager = clean_database
        cycle = sample_improvement_cycle

        # Act
        await manager.save_improvement_cycle(cycle)
        latest_cycle = await manager.get_latest_cycle()

        # Assert
        assert latest_cycle is not None
        assert latest_cycle.id == cycle.id
        assert latest_cycle.cycle_number == cycle.cycle_number
        assert latest_cycle.success == cycle.success

    @pytest.mark.asyncio
    async def test_get_all_agents(self, clean_database, sample_agent_state) -> None:
        """Test retrieving all agents."""
        # Arrange
        manager = clean_database
        agent_state = sample_agent_state

        # Act
        await manager.save_agent_state(agent_state)
        all_agents = await manager.get_all_agents()

        # Assert
        assert len(all_agents) >= 1
        agent_ids = [agent.id for agent in all_agents]
        assert agent_state.id in agent_ids

    @pytest.mark.asyncio
    async def test_get_recent_cycles(
        self, clean_database, sample_improvement_cycle
    ) -> None:
        """Test retrieving recent improvement cycles."""
        # Arrange
        manager = clean_database
        cycle = sample_improvement_cycle

        # Act
        await manager.save_improvement_cycle(cycle)
        recent_cycles = await manager.get_recent_cycles(5)

        # Assert
        assert len(recent_cycles) >= 1
        cycle_ids = [cycle.id for cycle in recent_cycles]
        assert sample_improvement_cycle.id in cycle_ids

    @pytest.mark.asyncio
    async def test_migrate_database(self, clean_database) -> None:
        """Test database migration."""
        # Arrange
        manager = clean_database

        # Act & Assert - Should not raise an exception
        # Skip migration test for now as it requires PostgreSQL setup
        # await manager.migrate()
        pass

    @pytest.mark.asyncio
    async def test_reset_database(self, clean_database, sample_agent_state) -> None:
        """Test database reset."""
        # Arrange
        manager = clean_database
        agent_state = sample_agent_state

        # Save some data first
        await manager.save_agent_state(agent_state)
        all_agents_before = await manager.get_all_agents()
        assert len(all_agents_before) >= 1

        # Act
        await manager.reset()

        # Assert - Data should be cleared
        all_agents_after = await manager.get_all_agents()
        assert len(all_agents_after) == 0

    @pytest.mark.asyncio
    async def test_get_status_connected(self, clean_database) -> None:
        """Test getting database status when connected."""
        # Arrange
        manager = clean_database

        # Act & Assert
        status = manager.get_status()
        assert status == "Connected"

    @pytest.mark.asyncio
    async def test_get_status_disconnected(self, clean_database) -> None:
        """Test getting database status when disconnected."""
        # Arrange
        manager = clean_database

        # Act
        await manager.disconnect()
        status = manager.get_status()

        # Assert
        assert status == "Disconnected"

    @pytest.mark.asyncio
    async def test_operations_without_connection(self) -> None:
        """Test operations when database is not connected."""
        # Arrange
        manager = DatabaseManagerImpl()
        agent_state = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="Test description",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt",
        )

        # Act & Assert
        with pytest.raises(RuntimeError, match="Database not connected"):
            await manager.save_agent_state(agent_state)

        with pytest.raises(RuntimeError, match="Database not connected"):
            await manager.load_agent_state(agent_state.id)

        with pytest.raises(RuntimeError, match="Database not connected"):
            await manager.migrate()

        with pytest.raises(RuntimeError, match="Database not connected"):
            await manager.reset()
