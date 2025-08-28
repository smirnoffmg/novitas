"""Tests for Agent Factory."""

from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch
from uuid import UUID

import pytest

from novitas.agents.agent_factory import AgentFactory
from novitas.agents.agent_factory import DefaultAgentFactory
from novitas.agents.code_agent import CodeAgent
from novitas.core.exceptions import AgentError
from novitas.core.models import AgentType
from novitas.core.protocols import DatabaseManager
from novitas.core.protocols import MessageBroker


class TestAgentFactory:
    """Test cases for Agent Factory."""

    def test_agent_factory_protocol(self):
        """Test that AgentFactory is a proper protocol."""
        # This test ensures the protocol is properly defined
        assert hasattr(AgentFactory, "create_agent")
        assert hasattr(AgentFactory, "retire_agent")
        assert hasattr(AgentFactory, "get_active_agents")

    def test_default_agent_factory_creation(self):
        """Test DefaultAgentFactory can be instantiated."""
        mock_db = Mock(spec=DatabaseManager)
        mock_broker = Mock(spec=MessageBroker)
        available_providers = {"anthropic": {"api_key": "test"}}

        factory = DefaultAgentFactory(
            database_manager=mock_db,
            message_broker=mock_broker,
            available_llm_providers=available_providers,
        )

        assert isinstance(factory, DefaultAgentFactory)
        assert factory.database_manager == mock_db
        assert factory.message_broker == mock_broker
        assert factory.available_llm_providers == available_providers

    @pytest.mark.asyncio
    async def test_create_code_agent(self):
        """Test creating a code agent."""
        mock_db = Mock(spec=DatabaseManager)
        mock_broker = Mock(spec=MessageBroker)
        available_providers = {
            "anthropic": {
                "api_key": "test_key",
                "temperature": 0.5,
            }
        }

        # Mock the LLM provider creation and structured response
        with (
            patch(
                "novitas.agents.agent_factory.create_llm_provider"
            ) as mock_create_provider,
            patch(
                "novitas.agents.agent_factory.generate_structured_response"
            ) as mock_generate_response,
        ):

            # Mock the LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            # Mock the structured response
            mock_response = Mock()
            mock_response.prompt = "Test prompt for code agent"
            mock_generate_response.return_value = mock_response

            # Mock agent initialization
            with patch.object(CodeAgent, "initialize") as mock_init:
                mock_init.return_value = None

                factory = DefaultAgentFactory(
                    database_manager=mock_db,
                    message_broker=mock_broker,
                    available_llm_providers=available_providers,
                )

                agent = await factory.create_agent(
                    agent_type="code_agent",
                    name="Test Code Agent",
                    description="A test code agent",
                    capabilities=["code_analysis", "refactoring"],
                )

                assert agent.name == "Test Code Agent"
                assert agent.description == "A test code agent"
                assert agent.agent_type == AgentType.CODE_AGENT.value
                assert agent.id is not None

    @pytest.mark.asyncio
    async def test_create_agent_invalid_type(self):
        """Test creating an agent with invalid type raises error."""
        mock_db = Mock(spec=DatabaseManager)
        mock_broker = Mock(spec=MessageBroker)
        available_providers = {"anthropic": {"api_key": "test"}}

        factory = DefaultAgentFactory(
            database_manager=mock_db,
            message_broker=mock_broker,
            available_llm_providers=available_providers,
        )

        with pytest.raises(AgentError, match="Unknown agent type"):
            await factory.create_agent(
                agent_type="invalid_agent",
                name="Test Agent",
                description="A test agent",
                capabilities=["test"],
            )

    @pytest.mark.asyncio
    async def test_create_agent_no_providers(self):
        """Test creating an agent with no LLM providers raises error."""
        mock_db = Mock(spec=DatabaseManager)
        mock_broker = Mock(spec=MessageBroker)
        available_providers = {}

        factory = DefaultAgentFactory(
            database_manager=mock_db,
            message_broker=mock_broker,
            available_llm_providers=available_providers,
        )

        with pytest.raises(AgentError, match="No LLM providers available"):
            await factory.create_agent(
                agent_type="code_agent",
                name="Test Agent",
                description="A test agent",
                capabilities=["test"],
            )

    @pytest.mark.asyncio
    async def test_retire_agent(self):
        """Test retiring an agent."""
        mock_db = Mock(spec=DatabaseManager)
        mock_broker = Mock(spec=MessageBroker)
        available_providers = {"anthropic": {"api_key": "test"}}

        # Mock the LLM provider creation and structured response
        with (
            patch(
                "novitas.agents.agent_factory.create_llm_provider"
            ) as mock_create_provider,
            patch(
                "novitas.agents.agent_factory.generate_structured_response"
            ) as mock_generate_response,
        ):

            # Mock the LLM provider
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider

            # Mock the structured response
            mock_response = Mock()
            mock_response.prompt = "Test prompt for code agent"
            mock_generate_response.return_value = mock_response

            # Mock agent initialization
            with patch.object(CodeAgent, "initialize") as mock_init:
                mock_init.return_value = None

                factory = DefaultAgentFactory(
                    database_manager=mock_db,
                    message_broker=mock_broker,
                    available_llm_providers=available_providers,
                )

                # Create an agent first
                agent = await factory.create_agent(
                    agent_type="code_agent",
                    name="Test Agent",
                    description="A test agent",
                    capabilities=["test"],
                )

                # Retire the agent
                await factory.retire_agent(agent.id, "Test retirement")

                # Verify the agent is no longer in active agents
                active_agents = await factory.get_active_agents()
                assert agent.id not in [a.id for a in active_agents]

    @pytest.mark.asyncio
    async def test_get_active_agents(self):
        """Test getting active agents."""
        mock_db = Mock(spec=DatabaseManager)
        mock_broker = Mock(spec=MessageBroker)
        available_providers = {"anthropic": {"api_key": "test"}}

        factory = DefaultAgentFactory(
            database_manager=mock_db,
            message_broker=mock_broker,
            available_llm_providers=available_providers,
        )

        # Create multiple agents
        agent1 = await factory.create_agent(
            agent_type="code_agent",
            name="Agent 1",
            description="First agent",
            capabilities=["test"],
        )

        agent2 = await factory.create_agent(
            agent_type="code_agent",
            name="Agent 2",
            description="Second agent",
            capabilities=["test"],
        )

        # Get active agents
        active_agents = await factory.get_active_agents()

        assert len(active_agents) == 2
        agent_ids = [a.id for a in active_agents]
        assert agent1.id in agent_ids
        assert agent2.id in agent_ids

    @pytest.mark.asyncio
    async def test_retire_nonexistent_agent(self):
        """Test retiring a non-existent agent raises error."""
        mock_db = Mock(spec=DatabaseManager)
        mock_broker = Mock(spec=MessageBroker)
        available_providers = {"anthropic": {"api_key": "test"}}

        factory = DefaultAgentFactory(
            database_manager=mock_db,
            message_broker=mock_broker,
            available_llm_providers=available_providers,
        )

        fake_id = UUID("12345678-1234-5678-1234-567812345678")

        with pytest.raises(AgentError, match="Agent not found"):
            await factory.retire_agent(fake_id, "Test retirement")
