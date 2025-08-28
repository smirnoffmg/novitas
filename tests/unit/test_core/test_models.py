"""Tests for core data models."""

from datetime import datetime
from uuid import uuid4

import pytest

from novitas.core.models import AgentAction
from novitas.core.models import AgentState
from novitas.core.models import AgentStatus
from novitas.core.models import AgentType
from novitas.core.models import ChangeProposal
from novitas.core.models import ImprovementCycle
from novitas.core.models import ImprovementType
from novitas.core.models import PromptTemplate
from novitas.core.models import SystemMetrics


class TestChangeProposal:
    """Test ChangeProposal model."""

    def test_create_change_proposal(self) -> None:
        """Test creating a change proposal."""
        agent_id = uuid4()
        proposal = ChangeProposal(
            agent_id=agent_id,
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/test.py",
            description="Test improvement",
            reasoning="This is a test",
            proposed_changes={"content": "new code"},
            confidence_score=0.8,
        )

        assert proposal.agent_id == agent_id
        assert proposal.improvement_type == ImprovementType.CODE_IMPROVEMENT
        assert proposal.file_path == "src/test.py"
        assert proposal.description == "Test improvement"
        assert proposal.reasoning == "This is a test"
        assert proposal.proposed_changes == {"content": "new code"}
        assert proposal.confidence_score == 0.8
        assert isinstance(proposal.created_at, datetime)

    def test_confidence_score_validation_valid(self) -> None:
        """Test confidence score validation with valid values."""
        # Test valid values
        for score in [0.0, 0.5, 1.0]:
            agent_id = uuid4()
            proposal = ChangeProposal(
                agent_id=agent_id,
                improvement_type=ImprovementType.CODE_IMPROVEMENT,
                file_path="src/test.py",
                description="Test improvement",
                reasoning="This is a test",
                proposed_changes={"content": "new code"},
                confidence_score=score,
            )
            assert proposal.confidence_score == score

    def test_confidence_score_validation_invalid(self) -> None:
        """Test confidence score validation with invalid values."""
        # Test the custom validator directly

        # Test values that would pass Field validation but fail custom validator
        for score in [1.1, 2.0]:
            with pytest.raises(
                ValueError, match="confidence_score must be between 0.0 and 1.0"
            ):
                ChangeProposal.validate_confidence(score)


class TestAgentState:
    """Test AgentState model."""

    def test_create_agent_state(self) -> None:
        """Test creating an agent state."""
        agent_state = AgentState(
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="A test agent",
            prompt="You are a test agent.",
        )

        assert agent_state.agent_type == AgentType.CODE_AGENT
        assert agent_state.name == "Test Agent"
        assert agent_state.description == "A test agent"
        assert agent_state.prompt == "You are a test agent."
        assert agent_state.status == AgentStatus.ACTIVE
        assert agent_state.version == 1
        assert agent_state.memory == {}
        assert agent_state.performance_metrics == {}
        assert isinstance(agent_state.created_at, datetime)
        assert isinstance(agent_state.last_active, datetime)

    def test_increment_version(self) -> None:
        """Test incrementing agent version."""
        agent_state = AgentState(
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="A test agent",
            prompt="You are a test agent.",
        )

        initial_version = agent_state.version
        initial_last_active = agent_state.last_active

        agent_state.increment_version()

        assert agent_state.version == initial_version + 1
        assert agent_state.last_active > initial_last_active


class TestImprovementCycle:
    """Test ImprovementCycle model."""

    def test_create_improvement_cycle(self) -> None:
        """Test creating an improvement cycle."""
        cycle = ImprovementCycle(cycle_number=1)

        assert cycle.cycle_number == 1
        assert cycle.start_time is not None
        assert cycle.end_time is None
        assert cycle.agents_used == []
        assert cycle.changes_proposed == []
        assert cycle.changes_accepted == []
        assert cycle.success is True
        assert cycle.error_message is None

    def test_complete_cycle_success(self) -> None:
        """Test completing a cycle successfully."""
        cycle = ImprovementCycle(cycle_number=1)
        initial_start_time = cycle.start_time

        cycle.complete(success=True, error_message=None)

        assert cycle.end_time is not None
        assert cycle.end_time > initial_start_time
        assert cycle.success is True
        assert cycle.error_message is None

    def test_complete_cycle_failure(self) -> None:
        """Test completing a cycle with failure."""
        cycle = ImprovementCycle(cycle_number=1)
        error_msg = "Something went wrong"

        cycle.complete(success=False, error_message=error_msg)

        assert cycle.end_time is not None
        assert cycle.success is False
        assert cycle.error_message == error_msg


class TestSystemMetrics:
    """Test SystemMetrics model."""

    def test_create_system_metrics(self) -> None:
        """Test creating system metrics."""
        metrics = SystemMetrics()

        assert metrics.total_cycles == 0
        assert metrics.successful_cycles == 0
        assert metrics.total_agents_created == 0
        assert metrics.total_agents_retired == 0
        assert metrics.total_changes_proposed == 0
        assert metrics.total_changes_accepted == 0
        assert metrics.average_cycle_duration == 0.0
        assert isinstance(metrics.last_updated, datetime)

    def test_system_metrics_with_values(self) -> None:
        """Test system metrics with custom values."""
        metrics = SystemMetrics(
            total_cycles=10,
            successful_cycles=8,
            total_agents_created=5,
            total_agents_retired=2,
            total_changes_proposed=20,
            total_changes_accepted=15,
            average_cycle_duration=30.5,
        )

        assert metrics.total_cycles == 10
        assert metrics.successful_cycles == 8
        assert metrics.total_agents_created == 5
        assert metrics.total_agents_retired == 2
        assert metrics.total_changes_proposed == 20
        assert metrics.total_changes_accepted == 15
        assert metrics.average_cycle_duration == 30.5


class TestAgentAction:
    """Test AgentAction model."""

    def test_create_agent_action(self) -> None:
        """Test creating an agent action."""
        agent_id = uuid4()
        action = AgentAction(
            agent_id=agent_id,
            action_type="code_review",
            details={"file": "src/test.py", "lines": [1, 10]},
        )

        assert action.agent_id == agent_id
        assert action.action_type == "code_review"
        assert action.details == {"file": "src/test.py", "lines": [1, 10]}
        assert action.success is True
        assert action.error_message is None
        assert action.duration_seconds is None
        assert isinstance(action.timestamp, datetime)

    def test_agent_action_with_failure(self) -> None:
        """Test creating an agent action with failure."""
        agent_id = uuid4()
        action = AgentAction(
            agent_id=agent_id,
            action_type="code_review",
            details={"file": "src/test.py"},
            success=False,
            error_message="Failed to review code",
            duration_seconds=5.5,
        )

        assert action.success is False
        assert action.error_message == "Failed to review code"
        assert action.duration_seconds == 5.5


class TestPromptTemplate:
    """Test PromptTemplate model."""

    def test_create_prompt_template(self) -> None:
        """Test creating a prompt template."""
        template = PromptTemplate(
            name="Code Review Template",
            agent_type=AgentType.CODE_AGENT,
            template="Review the following code: {code}",
        )

        assert template.name == "Code Review Template"
        assert template.agent_type == AgentType.CODE_AGENT
        assert template.template == "Review the following code: {code}"
        assert template.version == 1
        assert template.is_active is True
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)

    def test_update_template(self) -> None:
        """Test updating a prompt template."""
        template = PromptTemplate(
            name="Code Review Template",
            agent_type=AgentType.CODE_AGENT,
            template="Review the following code: {code}",
        )

        initial_version = template.version
        initial_updated_at = template.updated_at

        template.update_template("New template: {code}")

        assert template.template == "New template: {code}"
        assert template.version == initial_version + 1
        assert template.updated_at > initial_updated_at


class TestEnums:
    """Test enum values."""

    def test_agent_type_values(self) -> None:
        """Test AgentType enum values."""
        assert AgentType.ORCHESTRATOR == "orchestrator"
        assert AgentType.CODE_AGENT == "code_agent"
        assert AgentType.TEST_AGENT == "test_agent"
        assert AgentType.DOCUMENTATION_AGENT == "documentation_agent"

    def test_agent_status_values(self) -> None:
        """Test AgentStatus enum values."""
        assert AgentStatus.ACTIVE == "active"
        assert AgentStatus.INACTIVE == "inactive"
        assert AgentStatus.RETIRED == "retired"
        assert AgentStatus.ARCHIVED == "archived"

    def test_improvement_type_values(self) -> None:
        """Test ImprovementType enum values."""
        assert ImprovementType.CODE_IMPROVEMENT == "code_improvement"
        assert ImprovementType.TEST_IMPROVEMENT == "test_improvement"
        assert ImprovementType.DOCUMENTATION_IMPROVEMENT == "documentation_improvement"
        assert ImprovementType.PROMPT_IMPROVEMENT == "prompt_improvement"
        assert ImprovementType.CONFIG_IMPROVEMENT == "config_improvement"
