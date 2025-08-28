"""Tests for SQLAlchemy database models."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from novitas.core.models import AgentStatus
from novitas.core.models import AgentType
from novitas.core.models import ImprovementType
from novitas.database.models import AgentStateModel
from novitas.database.models import ChangeProposalModel
from novitas.database.models import ImprovementCycleModel


class TestAgentStateModel:
    """Test AgentStateModel."""

    @pytest.mark.asyncio
    async def test_create_agent_state(self, async_session: AsyncSession) -> None:
        """Test creating an agent state."""
        # Arrange
        agent_state = AgentStateModel(
            id="test-id",
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="Test description",
            status=AgentStatus.ACTIVE,
            version=1,
            prompt="Test prompt",
            memory={"key": "value"},
            performance_metrics={"metric": 0.5},
        )

        # Act
        async_session.add(agent_state)
        await async_session.commit()

        # Assert
        result = await async_session.execute(
            select(AgentStateModel).where(AgentStateModel.id == "test-id")
        )
        saved_agent = result.scalar_one()
        assert saved_agent.name == "Test Agent"
        assert saved_agent.agent_type == AgentType.CODE_AGENT
        assert saved_agent.status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_agent_state_memory_json(self, async_session: AsyncSession) -> None:
        """Test that agent state memory is stored as JSON."""
        # Arrange
        memory_data = {"key1": "value1", "key2": {"nested": "value"}}
        agent_state = AgentStateModel(
            id="test-id",
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="Test description",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt",
            memory=memory_data,
        )

        # Act
        async_session.add(agent_state)
        await async_session.commit()

        # Assert
        result = await async_session.execute(
            select(AgentStateModel).where(AgentStateModel.id == "test-id")
        )
        saved_agent = result.scalar_one()
        assert saved_agent.memory == memory_data


class TestChangeProposalModel:
    """Test ChangeProposalModel."""

    @pytest.mark.asyncio
    async def test_create_change_proposal(self, async_session: AsyncSession) -> None:
        """Test creating a change proposal."""
        # Arrange
        proposal = ChangeProposalModel(
            id="test-id",
            agent_id="agent-id",
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/test.py",
            description="Test improvement",
            reasoning="Test reasoning",
            proposed_changes={"content": "new code"},
            confidence_score=0.8,
        )

        # Act
        async_session.add(proposal)
        await async_session.commit()

        # Assert
        result = await async_session.execute(
            select(ChangeProposalModel).where(ChangeProposalModel.id == "test-id")
        )
        saved_proposal = result.scalar_one()
        assert saved_proposal.file_path == "src/test.py"
        assert saved_proposal.improvement_type == ImprovementType.CODE_IMPROVEMENT
        assert saved_proposal.confidence_score == 0.8

    @pytest.mark.asyncio
    async def test_change_proposal_changes_json(
        self, async_session: AsyncSession
    ) -> None:
        """Test that proposed changes are stored as JSON."""
        # Arrange
        changes_data = {"file": "test.py", "lines": [1, 2, 3], "content": "new code"}
        proposal = ChangeProposalModel(
            id="test-id",
            agent_id="agent-id",
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/test.py",
            description="Test improvement",
            reasoning="Test reasoning",
            proposed_changes=changes_data,
            confidence_score=0.8,
        )

        # Act
        async_session.add(proposal)
        await async_session.commit()

        # Assert
        result = await async_session.execute(
            select(ChangeProposalModel).where(ChangeProposalModel.id == "test-id")
        )
        saved_proposal = result.scalar_one()
        assert saved_proposal.proposed_changes == changes_data


class TestImprovementCycleModel:
    """Test ImprovementCycleModel."""

    @pytest.mark.asyncio
    async def test_create_improvement_cycle(self, async_session: AsyncSession) -> None:
        """Test creating an improvement cycle."""
        # Arrange
        cycle = ImprovementCycleModel(
            id="test-id",
            cycle_number=1,
            agents_used=["agent1", "agent2"],
            changes_proposed=["change1", "change2"],
            changes_accepted=["change1"],
            success=True,
        )

        # Act
        async_session.add(cycle)
        await async_session.commit()

        # Assert
        result = await async_session.execute(
            select(ImprovementCycleModel).where(ImprovementCycleModel.id == "test-id")
        )
        saved_cycle = result.scalar_one()
        assert saved_cycle.cycle_number == 1
        assert saved_cycle.agents_used == ["agent1", "agent2"]
        assert saved_cycle.changes_proposed == ["change1", "change2"]
        assert saved_cycle.changes_accepted == ["change1"]
        assert saved_cycle.success is True

    @pytest.mark.asyncio
    async def test_improvement_cycle_lists_json(
        self, async_session: AsyncSession
    ) -> None:
        """Test that cycle lists are stored as JSON."""
        # Arrange
        agents_used = ["agent1", "agent2", "agent3"]
        changes_proposed = ["change1", "change2"]
        changes_accepted = ["change1"]

        cycle = ImprovementCycleModel(
            id="test-id",
            cycle_number=1,
            agents_used=agents_used,
            changes_proposed=changes_proposed,
            changes_accepted=changes_accepted,
        )

        # Act
        async_session.add(cycle)
        await async_session.commit()

        # Assert
        result = await async_session.execute(
            select(ImprovementCycleModel).where(ImprovementCycleModel.id == "test-id")
        )
        saved_cycle = result.scalar_one()
        assert saved_cycle.agents_used == agents_used
        assert saved_cycle.changes_proposed == changes_proposed
        assert saved_cycle.changes_accepted == changes_accepted
