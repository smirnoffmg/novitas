"""Simple test for database layer."""

from uuid import uuid4

import pytest

from novitas.config.settings import settings
from novitas.core.models import AgentState
from novitas.core.models import AgentStatus
from novitas.core.models import AgentType
from novitas.database.connection import get_database_manager


@pytest.mark.asyncio
async def test_database_basic_operations() -> None:
    """Test basic database operations."""
    # Override settings for testing
    original_url = settings.database_url
    settings.database_url = "sqlite+aiosqlite:///:memory:"

    try:
        # Get database manager
        db_manager = get_database_manager()

        # Connect
        await db_manager.connect()
        assert db_manager.get_status() == "Connected"

        # Create and save agent state
        agent_state = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="Test description",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt",
        )

        await db_manager.save_agent_state(agent_state)

        # Load agent state
        loaded_agent = await db_manager.load_agent_state(agent_state.id)
        assert loaded_agent is not None
        assert loaded_agent.name == "Test Agent"
        assert loaded_agent.agent_type == AgentType.CODE_AGENT

        # Update agent state
        agent_state.name = "Updated Agent"
        agent_state.status = AgentStatus.INACTIVE
        await db_manager.save_agent_state(agent_state)

        # Verify update
        updated_agent = await db_manager.load_agent_state(agent_state.id)
        assert updated_agent is not None
        assert updated_agent.name == "Updated Agent"
        assert updated_agent.status == AgentStatus.INACTIVE

        # Get all agents
        all_agents = await db_manager.get_all_agents()
        assert len(all_agents) == 1
        assert all_agents[0].id == agent_state.id

        # Disconnect
        await db_manager.disconnect()
        assert db_manager.get_status() == "Disconnected"

    finally:
        # Restore original settings
        settings.database_url = original_url
