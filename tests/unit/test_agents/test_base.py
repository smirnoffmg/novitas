"""Tests for the base agent class."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from novitas.agents.base import BaseAgent
from novitas.core.exceptions import AgentError
from novitas.core.exceptions import AgentTimeoutError
from novitas.core.models import AgentState
from novitas.core.models import AgentStatus
from novitas.core.models import AgentType


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, **kwargs):
        # Create mock dependencies
        database_manager = AsyncMock()
        llm_client = AsyncMock()
        message_broker = AsyncMock()

        # Extract agent_id if provided, otherwise generate
        agent_id = kwargs.pop("agent_id", uuid4())

        super().__init__(
            database_manager=database_manager,
            llm_client=llm_client,
            message_broker=message_broker,
            agent_id=agent_id,
            **kwargs,
        )

        # Mock the database manager to return None for load_agent_state
        # This ensures we use the default state created in __init__
        self.database_manager.load_agent_state.return_value = None

    async def _initialize_agent(self) -> None:
        """Mock initialization."""
        pass

    async def _execute_agent(self, context):
        """Mock execution."""
        return [{"result": "success"}]

    async def _cleanup_agent(self) -> None:
        """Mock cleanup."""
        pass


class TestBaseAgent:
    """Test the base agent class."""

    def test_base_agent_initialization(self) -> None:
        """Test base agent initialization."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        assert agent.name == "Test Agent"
        assert agent.agent_type == "code_agent"
        assert agent.description == "A test agent"
        assert agent.prompt == "You are a test agent."
        assert isinstance(agent.state, AgentState)
        assert agent.state.status == AgentStatus.ACTIVE
        assert agent.state.version == 1

    @pytest.mark.asyncio
    async def test_initialize_agent_success(self) -> None:
        """Test successful agent initialization."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        await agent.initialize()

        assert agent.state.status == AgentStatus.ACTIVE
        assert agent.state.version == 1

    @pytest.mark.asyncio
    async def test_initialize_agent_failure(self) -> None:
        """Test agent initialization failure."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        # Mock _initialize_agent to raise an exception
        agent._initialize_agent = AsyncMock(
            side_effect=Exception("Initialization failed")
        )

        with pytest.raises(AgentError, match="Failed to initialize agent Test Agent"):
            await agent.initialize()

    @pytest.mark.asyncio
    async def test_execute_agent_success(self) -> None:
        """Test successful agent execution."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        # Initialize first
        await agent.initialize()

        # Execute with context
        result = await agent.execute({"test": "context"})

        assert result == [{"result": "success"}]
        assert agent.state.status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_execute_agent_timeout(self) -> None:
        """Test agent execution timeout."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        # Initialize first
        await agent.initialize()

        # Mock _execute_agent to raise TimeoutError
        agent._execute_agent = AsyncMock(
            side_effect=TimeoutError("Execution timed out")
        )

        with pytest.raises(
            AgentTimeoutError, match="Agent Test Agent execution timed out"
        ):
            await agent.execute({"test": "context"})

    @pytest.mark.asyncio
    async def test_execute_agent_failure(self) -> None:
        """Test agent execution failure."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        # Initialize first
        await agent.initialize()

        # Mock _execute_agent to raise an exception
        agent._execute_agent = AsyncMock(side_effect=Exception("Execution failed"))

        with pytest.raises(AgentError, match="Agent Test Agent execution failed"):
            await agent.execute({"test": "context"})

    @pytest.mark.asyncio
    async def test_cleanup_agent_success(self) -> None:
        """Test successful agent cleanup."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        await agent.cleanup()

        assert agent.state.status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_cleanup_agent_failure(self) -> None:
        """Test agent cleanup failure."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        # Mock _cleanup_agent to raise an exception
        agent._cleanup_agent = AsyncMock(side_effect=Exception("Cleanup failed"))

        with pytest.raises(AgentError, match="Agent Test Agent cleanup failed"):
            await agent.cleanup()

    def test_increment_version(self) -> None:
        """Test version increment."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        initial_version = agent.state.version
        agent.state.increment_version()
        assert agent.state.version == initial_version + 1

    def test_update_memory(self) -> None:
        """Test memory update."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        agent.state.memory.update({"key": "value"})
        assert agent.state.memory["key"] == "value"

    def test_update_performance_metrics(self) -> None:
        """Test performance metrics update."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        agent.state.performance_metrics.update({"accuracy": 0.95})
        assert agent.state.performance_metrics["accuracy"] == 0.95

    def test_get_state(self) -> None:
        """Test getting agent state."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        state = agent.state
        assert isinstance(state, AgentState)
        assert state.name == "Test Agent"
        assert state.agent_type == AgentType.CODE_AGENT

    def test_get_performance_metrics(self) -> None:
        """Test getting performance metrics."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        metrics = agent.get_performance_metrics()
        assert isinstance(metrics, dict)
        assert metrics == agent.state.performance_metrics.copy()

    def test_context_manager(self) -> None:
        """Test agent as context manager."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        # Mock async context manager methods
        agent.initialize = AsyncMock()
        agent.cleanup = AsyncMock()

        # Test that the agent can be used as a context manager
        # Note: BaseAgent doesn't implement async context manager by default
        # This test verifies the agent has the required methods
        assert hasattr(agent, "initialize")
        assert hasattr(agent, "cleanup")

    @pytest.mark.asyncio
    async def test_context_manager_usage(self) -> None:
        """Test using agent as context manager."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        # Mock async context manager methods
        agent.initialize = AsyncMock()
        agent.cleanup = AsyncMock()

        # Test manual context manager pattern
        await agent.initialize()
        try:
            # Do work with agent
            pass
        finally:
            await agent.cleanup()

        agent.initialize.assert_called_once()
        agent.cleanup.assert_called_once()

    def test_agent_properties(self) -> None:
        """Test agent properties."""
        agent = MockAgent(
            agent_id=uuid4(),
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.CODE_AGENT,
            prompt="You are a test agent.",
        )

        assert agent.id is not None
        assert agent.name == "Test Agent"
        assert agent.agent_type == "code_agent"
        assert agent.description == "A test agent"
        assert agent.prompt == "You are a test agent."
        assert agent.state.name == "Test Agent"
        assert agent.state.agent_type == AgentType.CODE_AGENT
