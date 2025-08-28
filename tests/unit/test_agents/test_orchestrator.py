"""Tests for the Orchestrator Agent."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from novitas.agents.orchestrator import OrchestratorAgent
from novitas.core.models import AgentType
from novitas.core.models import ChangeProposal
from novitas.core.models import ImprovementType


class TestOrchestratorAgent:
    """Test cases for the Orchestrator Agent."""

    @pytest.fixture
    def mock_database_manager(self):
        """Create a mock database manager."""
        mock = AsyncMock()
        mock.load_agent_state.return_value = None
        return mock

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        mock = AsyncMock()
        # Mock the with_structured_output method
        structured_mock = AsyncMock()
        structured_mock.ainvoke.return_value = AsyncMock()
        mock.with_structured_output.return_value = structured_mock
        return mock

    @pytest.fixture
    def mock_message_broker(self):
        """Create a mock message broker."""
        return AsyncMock()

    @pytest.fixture(autouse=True)
    def mock_llm_provider(self, mock_llm_client, monkeypatch):
        """Mock LLM provider creation for all tests."""

        def mock_create_llm_provider(config):
            return mock_llm_client

        # Mock the create_llm_provider function in the orchestrator module
        monkeypatch.setattr(
            "novitas.agents.orchestrator.create_llm_provider", mock_create_llm_provider
        )

    @pytest.fixture
    def orchestrator(self, mock_database_manager, mock_llm_client, mock_message_broker):
        """Create an Orchestrator Agent instance."""
        # Create mock available providers
        available_providers = {
            "anthropic": {
                "api_key": "test-anthropic-key",
            }
        }

        return OrchestratorAgent(
            database_manager=mock_database_manager,
            available_llm_providers=available_providers,
            message_broker=mock_message_broker,
            agent_id=uuid4(),
            name="Test Orchestrator",
            description="A test orchestrator agent",
            prompt="You are an orchestrator agent.",
        )

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.name == "Test Orchestrator"
        assert orchestrator.agent_type == AgentType.ORCHESTRATOR
        assert orchestrator.state.status.value == "active"  # Default status is active
        assert len(orchestrator.managed_agents) == 0

    @pytest.mark.asyncio
    async def test_initialize_orchestrator(self, orchestrator):
        """Test orchestrator initialization."""
        await orchestrator.initialize()

        assert orchestrator.state.status.value == "active"
        assert orchestrator._initialized is True

    @pytest.mark.asyncio
    async def test_create_specialized_agent(self, orchestrator, monkeypatch):
        """Test creating a specialized agent."""
        await orchestrator.initialize()

        # Mock the generate_structured_response function
        async def mock_generate_structured_response(provider, prompt, schema, **kwargs):
            from novitas.core.schemas import AgentPrompt

            return AgentPrompt(
                prompt="You are a code analysis expert focused on Python code quality.",
                reasoning="This prompt focuses the agent on code analysis tasks",
                focus_areas=["code_analysis", "improvement_proposals"],
            )

        monkeypatch.setattr(
            "novitas.agents.orchestrator.generate_structured_response",
            mock_generate_structured_response,
        )

        agent_id = await orchestrator.create_specialized_agent(
            agent_type="code_agent",
            name="Code Analyzer",
            description="Analyzes code and suggests improvements",
            capabilities=["code_analysis", "improvement_proposals"],
        )

        assert agent_id is not None
        assert agent_id in orchestrator.managed_agents
        assert orchestrator.managed_agents[agent_id]["name"] == "Code Analyzer"
        assert orchestrator.managed_agents[agent_id]["type"] == "code_agent"

    @pytest.mark.asyncio
    async def test_retire_agent(self, orchestrator):
        """Test retiring an agent."""
        await orchestrator.initialize()

        # Create an agent first
        agent_id = uuid4()
        orchestrator.managed_agents[agent_id] = {
            "name": "Test Agent",
            "type": "test_agent",
            "created_at": "2023-01-01",
            "performance": 0.5,
        }

        await orchestrator.retire_agent(agent_id, "Low performance")

        assert agent_id not in orchestrator.managed_agents
        assert agent_id in orchestrator.retired_agents

    @pytest.mark.asyncio
    async def test_coordinate_improvement_cycle(self, orchestrator, monkeypatch):
        """Test coordinating an improvement cycle."""
        await orchestrator.initialize()

        # Mock context for improvement cycle
        context = {
            "files_to_analyze": ["src/main.py", "tests/test_main.py"],
            "file_contents": {
                "src/main.py": "def main():\n    pass",
                "tests/test_main.py": "def test_main():\n    assert True",
            },
            "previous_analysis": "Previous analysis results",
        }

        # Mock the generate_response function
        responses = [
            "Create Code Agent for analysis",
            "Create Documentation Agent for docs",
            "Coordinate workflow between agents",
            "Evaluate proposals and select best ones",
        ]
        response_index = 0

        async def mock_generate_response(provider, prompt):
            nonlocal response_index
            response = responses[response_index % len(responses)]
            response_index += 1
            return response

        monkeypatch.setattr(
            "novitas.llm.provider.generate_response", mock_generate_response
        )

        # Mock agent execution
        mock_proposal = ChangeProposal(
            agent_id=uuid4(),
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/main.py",
            description="Add docstring to main function",
            reasoning="Improves code documentation",
            proposed_changes={"add_docstring": True},
            confidence_score=0.8,
        )

        orchestrator._execute_agent_workflow = AsyncMock(return_value=[mock_proposal])
        orchestrator._evaluate_proposals = AsyncMock(return_value=[mock_proposal])

        results = await orchestrator.coordinate_improvement_cycle(context)

        assert len(results) > 0
        assert all(isinstance(proposal, ChangeProposal) for proposal in results)

    @pytest.mark.asyncio
    async def test_evaluate_proposals(self, orchestrator, monkeypatch):
        """Test evaluating change proposals."""
        await orchestrator.initialize()

        # Mock proposals
        proposals = [
            ChangeProposal(
                agent_id=uuid4(),
                improvement_type=ImprovementType.CODE_IMPROVEMENT,
                file_path="src/main.py",
                description="Add type hints",
                reasoning="Improves code clarity",
                proposed_changes={"add_types": True},
                confidence_score=0.9,
            ),
            ChangeProposal(
                agent_id=uuid4(),
                improvement_type=ImprovementType.DOCUMENTATION_IMPROVEMENT,
                file_path="README.md",
                description="Update documentation",
                reasoning="Improves user understanding",
                proposed_changes={"update_docs": True},
                confidence_score=0.7,
            ),
        ]

        # Mock the generate_response function
        async def mock_generate_response(provider, prompt):
            return """
            Proposal Evaluation:

            1. Add type hints (Score: 0.9)
               - High impact, low effort
               - Improves code quality significantly
               - Recommended for implementation

            2. Update documentation (Score: 0.7)
               - Medium impact, low effort
               - Good for user experience
               - Recommended for implementation
            """

        monkeypatch.setattr(
            "novitas.llm.provider.generate_response", mock_generate_response
        )

        selected_proposals = await orchestrator._evaluate_proposals(proposals)

        assert len(selected_proposals) > 0
        assert all(
            isinstance(proposal, ChangeProposal) for proposal in selected_proposals
        )

    @pytest.mark.asyncio
    async def test_monitor_agent_performance(self, orchestrator, monkeypatch):
        """Test monitoring agent performance."""
        await orchestrator.initialize()

        # Create some test agents
        agent1_id = uuid4()
        agent2_id = uuid4()

        orchestrator.managed_agents[agent1_id] = {
            "name": "High Performer",
            "type": "code_agent",
            "performance": 0.9,
            "analyses_count": 50,
            "success_rate": 0.95,
        }

        orchestrator.managed_agents[agent2_id] = {
            "name": "Low Performer",
            "type": "code_agent",
            "performance": 0.3,
            "analyses_count": 10,
            "success_rate": 0.4,
        }

        # Mock the generate_response function
        async def mock_generate_response(provider, prompt):
            return """
            Performance Analysis:

            High Performer: Excellent performance, keep active
            Low Performer: Poor performance, recommend retirement
            """

        monkeypatch.setattr(
            "novitas.llm.provider.generate_response", mock_generate_response
        )

        performance_report = await orchestrator.monitor_agent_performance()

        assert "High Performer" in str(performance_report["agent_performance"])
        assert "Low Performer" in str(performance_report["agent_performance"])
        assert performance_report["recommendations"] is not None

    @pytest.mark.asyncio
    async def test_evolve_agent_prompts(self, orchestrator, monkeypatch):
        """Test evolving agent prompts based on performance."""
        await orchestrator.initialize()

        # Mock performance data
        performance_data = {
            "code_agent": {
                "success_rate": 0.8,
                "common_issues": ["missing type hints", "no docstrings"],
                "strengths": ["good naming", "clear logic"],
            }
        }

        # Mock the generate_response function
        async def mock_generate_response(provider, prompt):
            return """
            Evolved Prompt for Code Agent:
            
            You are a code analysis expert. Focus on:
            1. Type hint enforcement
            2. Docstring generation
            3. Maintain existing strengths in naming and logic
            
            Updated prompt: You are a Python code quality expert...
            """

        monkeypatch.setattr(
            "novitas.llm.provider.generate_response", mock_generate_response
        )

        evolved_prompts = await orchestrator.evolve_agent_prompts(performance_data)

        assert "evolution_strategy" in evolved_prompts
        assert evolved_prompts["evolution_strategy"] is not None

    @pytest.mark.asyncio
    async def test_execute_agent(self, orchestrator):
        """Test orchestrator execution."""
        await orchestrator.initialize()

        context = {
            "action": "improvement_cycle",
            "files_to_analyze": ["src/main.py"],
            "file_contents": {"src/main.py": "def main():\n    pass"},
        }

        # Mock the coordination workflow
        orchestrator.coordinate_improvement_cycle = AsyncMock(return_value=[])

        results = await orchestrator.execute(context)

        assert isinstance(results, list)
        orchestrator.coordinate_improvement_cycle.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_communication(self, orchestrator):
        """Test inter-agent communication."""
        await orchestrator.initialize()

        recipient_id = uuid4()
        message_content = {"type": "analysis_request", "files": ["test.py"]}

        await orchestrator.send_message(
            recipient_id, "analysis_request", message_content
        )

        orchestrator.message_broker.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, orchestrator, monkeypatch):
        """Test error handling in orchestrator."""
        await orchestrator.initialize()

        # Mock the generate_response function to raise an error
        async def mock_generate_response(provider, prompt):
            raise Exception("LLM Error")

        monkeypatch.setattr(
            "novitas.llm.provider.generate_response", mock_generate_response
        )

        context = {"action": "improvement_cycle", "files_to_analyze": ["test.py"]}

        # Should handle the error gracefully
        results = await orchestrator.execute(context)

        assert isinstance(results, list)
        assert len(results) == 0  # Should return empty list on error

    @pytest.mark.asyncio
    async def test_cleanup_orchestrator(self, orchestrator):
        """Test orchestrator cleanup."""
        await orchestrator.initialize()

        # Add some managed agents
        agent_id = uuid4()
        orchestrator.managed_agents[agent_id] = {"name": "Test Agent", "type": "test"}

        await orchestrator.cleanup()

        # Should cleanup all managed agents
        assert len(orchestrator.managed_agents) == 0
        # Note: Base agent doesn't change status during cleanup, so it remains active

    def test_get_performance_metrics(self, orchestrator):
        """Test getting orchestrator performance metrics."""
        # Set up some test data
        orchestrator._total_cycles = 10
        orchestrator._successful_cycles = 8
        orchestrator._total_proposals = 25
        orchestrator._accepted_proposals = 20

        metrics = orchestrator.get_performance_metrics()

        assert metrics["total_cycles"] == 10
        assert metrics["successful_cycles"] == 8
        assert metrics["success_rate"] == 0.8
        assert metrics["proposal_acceptance_rate"] == 0.8

    @pytest.mark.asyncio
    async def test_agent_lifecycle_management(self, orchestrator, monkeypatch):
        """Test complete agent lifecycle management."""
        await orchestrator.initialize()

        # Mock the generate_structured_response function
        async def mock_generate_structured_response(provider, prompt, schema, **kwargs):
            from novitas.core.schemas import AgentPrompt

            return AgentPrompt(
                prompt="Test agent prompt and configuration",
                reasoning="Test reasoning",
                focus_areas=["test_capability"],
            )

        monkeypatch.setattr(
            "novitas.agents.orchestrator.generate_structured_response",
            mock_generate_structured_response,
        )

        # Create agent
        agent_id = await orchestrator.create_specialized_agent(
            "test_agent", "Test Agent", "Test description", ["test_capability"]
        )

        assert agent_id in orchestrator.managed_agents

        # Update performance
        orchestrator.managed_agents[agent_id]["performance"] = 0.3

        # Monitor and potentially retire
        await orchestrator.monitor_agent_performance()

        # Retire low-performing agent
        await orchestrator.retire_agent(agent_id, "Low performance")

        assert agent_id not in orchestrator.managed_agents
        assert agent_id in orchestrator.retired_agents

    @pytest.mark.asyncio
    async def test_system_evolution(self, orchestrator, monkeypatch):
        """Test system evolution capabilities."""
        await orchestrator.initialize()

        # Mock performance data for evolution
        performance_data = {
            "code_agent": {"success_rate": 0.7},
            "doc_agent": {"success_rate": 0.9},
        }

        # Mock the generate_response function
        async def mock_generate_response(provider, prompt):
            return """
            Evolution Strategy:
            1. Retire underperforming code_agent
            2. Create new specialized agent for testing
            3. Evolve doc_agent prompt for better performance
            """

        monkeypatch.setattr(
            "novitas.llm.provider.generate_response", mock_generate_response
        )

        evolution_plan = await orchestrator.plan_system_evolution(performance_data)

        assert evolution_plan is not None
        assert "actions" in evolution_plan
