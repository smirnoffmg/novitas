"""Extended tests for database connection manager."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import uuid4

import pytest

from novitas.core.models import AgentState
from novitas.core.models import AgentStatus
from novitas.core.models import AgentType
from novitas.core.models import ChangeProposal
from novitas.core.models import ImprovementCycle
from novitas.core.models import ImprovementType
from novitas.database.connection import DatabaseManagerImpl
from novitas.database.connection import get_database_manager


class TestDatabaseManagerExtended:
    """Extended tests for DatabaseManager implementation."""

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, clean_database) -> None:
        """Test connecting when already connected."""
        manager = clean_database

        # Should not raise an exception
        await manager.connect()
        assert manager.get_status() == "Connected"

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self) -> None:
        """Test disconnecting when not connected."""
        manager = DatabaseManagerImpl()

        # Should not raise an exception
        await manager.disconnect()
        assert manager.get_status() == "Disconnected"

    @pytest.mark.asyncio
    async def test_get_session_not_connected(self) -> None:
        """Test getting session when not connected."""
        manager = DatabaseManagerImpl()

        with pytest.raises(RuntimeError, match="Database not connected"):
            await manager._get_session()

    @pytest.mark.asyncio
    async def test_get_session_no_session_maker(self, clean_database) -> None:
        """Test getting session when session maker is not initialized."""
        manager = clean_database
        manager._session_maker = None

        with pytest.raises(RuntimeError, match="Session maker not initialized"):
            await manager._get_session()

    @pytest.mark.asyncio
    async def test_save_agent_state_exception_handling(self, clean_database) -> None:
        """Test exception handling in save_agent_state."""
        manager = clean_database
        agent_state = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="Test description",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt",
        )

        # Mock the repository to raise an exception
        with patch.object(manager, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # Mock repository to raise exception
            mock_repository = MagicMock()
            mock_repository.get_by_id.side_effect = Exception("Database error")

            with (
                patch(
                    "novitas.database.connection.AgentStateRepository",
                    return_value=mock_repository,
                ),
                pytest.raises(Exception, match="Database error"),
            ):
                await manager.save_agent_state(agent_state)

    @pytest.mark.asyncio
    async def test_load_agent_state_exception_handling(self, clean_database) -> None:
        """Test exception handling in load_agent_state."""
        manager = clean_database
        agent_id = uuid4()

        # Mock the repository to raise an exception
        with patch.object(manager, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # Mock repository to raise exception
            mock_repository = MagicMock()
            mock_repository.get_by_id.side_effect = Exception("Database error")

            with (
                patch(
                    "novitas.database.connection.AgentStateRepository",
                    return_value=mock_repository,
                ),
                pytest.raises(Exception, match="Database error"),
            ):
                await manager.load_agent_state(agent_id)

    @pytest.mark.asyncio
    async def test_save_change_proposal_exception_handling(
        self, clean_database
    ) -> None:
        """Test exception handling in save_change_proposal."""
        manager = clean_database
        proposal = ChangeProposal(
            agent_id=uuid4(),
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/test.py",
            description="Test improvement",
            reasoning="Test reasoning",
            proposed_changes={"test": "change"},
            confidence_score=0.8,
        )

        # Mock the repository to raise an exception
        with patch.object(manager, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # Mock repository to raise exception
            mock_repository = MagicMock()
            mock_repository.get_by_id.side_effect = Exception("Database error")

            with (
                patch(
                    "novitas.database.connection.ChangeProposalRepository",
                    return_value=mock_repository,
                ),
                pytest.raises(Exception, match="Database error"),
            ):
                await manager.save_change_proposal(proposal)

    @pytest.mark.asyncio
    async def test_get_change_proposals_exception_handling(
        self, clean_database
    ) -> None:
        """Test exception handling in get_change_proposals."""
        manager = clean_database
        cycle_id = uuid4()

        # Mock the repository to raise an exception
        with patch.object(manager, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # Mock repository to raise exception
            mock_repository = MagicMock()
            mock_repository.get_by_cycle_id.side_effect = Exception("Database error")

            with (
                patch(
                    "novitas.database.connection.ChangeProposalRepository",
                    return_value=mock_repository,
                ),
                pytest.raises(Exception, match="Database error"),
            ):
                await manager.get_change_proposals(cycle_id)

    @pytest.mark.asyncio
    async def test_save_improvement_cycle_exception_handling(
        self, clean_database
    ) -> None:
        """Test exception handling in save_improvement_cycle."""
        manager = clean_database
        cycle = ImprovementCycle(
            id=uuid4(),
            cycle_number=1,
        )

        # Mock the repository to raise an exception
        with patch.object(manager, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # Mock repository to raise exception
            mock_repository = MagicMock()
            mock_repository.get_by_id.side_effect = Exception("Database error")

            with (
                patch(
                    "novitas.database.connection.ImprovementCycleRepository",
                    return_value=mock_repository,
                ),
                pytest.raises(Exception, match="Database error"),
            ):
                await manager.save_improvement_cycle(cycle)

    @pytest.mark.asyncio
    async def test_get_latest_cycle_exception_handling(self, clean_database) -> None:
        """Test exception handling in get_latest_cycle."""
        manager = clean_database

        # Mock the repository to raise an exception
        with patch.object(manager, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # Mock repository to raise exception
            mock_repository = MagicMock()
            mock_repository.get_latest.side_effect = Exception("Database error")

            with (
                patch(
                    "novitas.database.connection.ImprovementCycleRepository",
                    return_value=mock_repository,
                ),
                pytest.raises(Exception, match="Database error"),
            ):
                await manager.get_latest_cycle()

    @pytest.mark.asyncio
    async def test_get_all_agents_exception_handling(self, clean_database) -> None:
        """Test exception handling in get_all_agents."""
        manager = clean_database

        # Mock the repository to raise an exception
        with patch.object(manager, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # Mock repository to raise exception
            mock_repository = MagicMock()
            mock_repository.get_all.side_effect = Exception("Database error")

            with (
                patch(
                    "novitas.database.connection.AgentStateRepository",
                    return_value=mock_repository,
                ),
                pytest.raises(Exception, match="Database error"),
            ):
                await manager.get_all_agents()

    @pytest.mark.asyncio
    async def test_get_recent_cycles_exception_handling(self, clean_database) -> None:
        """Test exception handling in get_recent_cycles."""
        manager = clean_database

        # Mock the repository to raise an exception
        with patch.object(manager, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session

            # Mock repository to raise exception
            mock_repository = MagicMock()
            mock_repository.get_recent.side_effect = Exception("Database error")

            with (
                patch(
                    "novitas.database.connection.ImprovementCycleRepository",
                    return_value=mock_repository,
                ),
                pytest.raises(Exception, match="Database error"),
            ):
                await manager.get_recent_cycles(5)

    @pytest.mark.asyncio
    async def test_migrate_not_connected(self) -> None:
        """Test migrate when not connected."""
        manager = DatabaseManagerImpl()

        with pytest.raises(RuntimeError, match="Database not connected"):
            await manager.migrate()

    @pytest.mark.asyncio
    async def test_migrate_no_engine(self, clean_database) -> None:
        """Test migrate when engine is not initialized."""
        manager = clean_database
        manager._engine = None

        with pytest.raises(RuntimeError, match="Database engine not initialized"):
            await manager.migrate()

    @pytest.mark.asyncio
    async def test_reset_not_connected(self) -> None:
        """Test reset when not connected."""
        manager = DatabaseManagerImpl()

        with pytest.raises(RuntimeError, match="Database not connected"):
            await manager.reset()

    @pytest.mark.asyncio
    async def test_reset_no_engine(self, clean_database) -> None:
        """Test reset when engine is not initialized."""
        manager = clean_database
        manager._engine = None

        with pytest.raises(RuntimeError, match="Database engine not initialized"):
            await manager.reset()

    def test_get_database_manager(self) -> None:
        """Test get_database_manager function."""
        manager = get_database_manager()
        assert isinstance(manager, DatabaseManagerImpl)

    @pytest.mark.asyncio
    async def test_session_reuse(self, clean_database) -> None:
        """Test that sessions are reused."""
        manager = clean_database

        # Get session multiple times
        session1 = await manager._get_session()
        session2 = await manager._get_session()

        # Should be the same session instance
        assert session1 is session2

    @pytest.mark.asyncio
    async def test_multiple_operations_same_session(self, clean_database) -> None:
        """Test multiple operations using the same session."""
        manager = clean_database

        # Create multiple agent states
        agent1 = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Agent 1",
            description="First agent",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt 1",
        )

        agent2 = AgentState(
            id=uuid4(),
            agent_type=AgentType.TEST_AGENT,
            name="Agent 2",
            description="Second agent",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt 2",
        )

        # Save both agents
        await manager.save_agent_state(agent1)
        await manager.save_agent_state(agent2)

        # Load both agents
        loaded1 = await manager.load_agent_state(agent1.id)
        loaded2 = await manager.load_agent_state(agent2.id)

        # Verify both were saved and loaded correctly
        assert loaded1 is not None
        assert loaded1.id == agent1.id
        assert loaded1.name == agent1.name

        assert loaded2 is not None
        assert loaded2.id == agent2.id
        assert loaded2.name == agent2.name
