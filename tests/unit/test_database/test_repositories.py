"""Tests for database repositories."""

from datetime import UTC
from datetime import datetime
from uuid import uuid4

import pytest

from novitas.core.models import AgentState
from novitas.core.models import AgentStatus
from novitas.core.models import AgentType
from novitas.core.models import ChangeProposal
from novitas.core.models import ImprovementCycle
from novitas.core.models import ImprovementType
from novitas.database.repositories import AgentStateRepository
from novitas.database.repositories import ChangeProposalRepository
from novitas.database.repositories import ImprovementCycleRepository


class TestAgentStateRepository:
    """Test AgentStateRepository."""

    @pytest.mark.asyncio
    async def test_create_agent_state(self, async_session) -> None:
        """Test creating an agent state."""
        repository = AgentStateRepository(async_session)
        agent_state = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="Test description",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt",
        )

        await repository.create(agent_state)

        # Verify it was created
        loaded = await repository.get_by_id(str(agent_state.id))
        assert loaded is not None
        assert loaded.id == agent_state.id
        assert loaded.name == agent_state.name
        assert loaded.agent_type == agent_state.agent_type

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, async_session) -> None:
        """Test getting agent state by ID when not found."""
        repository = AgentStateRepository(async_session)
        nonexistent_id = str(uuid4())

        result = await repository.get_by_id(nonexistent_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_agent_state(self, async_session) -> None:
        """Test updating an agent state."""
        repository = AgentStateRepository(async_session)
        agent_state = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Original Name",
            description="Original description",
            status=AgentStatus.ACTIVE,
            prompt="Original prompt",
        )

        # Create the agent state
        await repository.create(agent_state)

        # Update the agent state
        agent_state.name = "Updated Name"
        agent_state.status = AgentStatus.INACTIVE
        await repository.update(agent_state)

        # Verify the update
        loaded = await repository.get_by_id(str(agent_state.id))
        assert loaded is not None
        assert loaded.name == "Updated Name"
        assert loaded.status == AgentStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_update_agent_state_not_found(self, async_session) -> None:
        """Test updating an agent state that doesn't exist."""
        repository = AgentStateRepository(async_session)
        agent_state = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="Test description",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt",
        )

        with pytest.raises(
            ValueError, match=f"Agent state with id {agent_state.id} not found"
        ):
            await repository.update(agent_state)

    @pytest.mark.asyncio
    async def test_delete_agent_state(self, async_session) -> None:
        """Test deleting an agent state."""
        repository = AgentStateRepository(async_session)
        agent_state = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="Test description",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt",
        )

        # Create the agent state
        await repository.create(agent_state)

        # Verify it exists
        loaded = await repository.get_by_id(str(agent_state.id))
        assert loaded is not None

        # Delete it
        await repository.delete(str(agent_state.id))

        # Verify it's gone
        loaded = await repository.get_by_id(str(agent_state.id))
        assert loaded is None

    @pytest.mark.asyncio
    async def test_get_all_agent_states(self, async_session) -> None:
        """Test getting all agent states."""
        repository = AgentStateRepository(async_session)

        # Create multiple agent states
        agent1 = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Agent 1",
            description="First agent",
            status=AgentStatus.ACTIVE,
            prompt="Prompt 1",
        )
        agent2 = AgentState(
            id=uuid4(),
            agent_type=AgentType.TEST_AGENT,
            name="Agent 2",
            description="Second agent",
            status=AgentStatus.INACTIVE,
            prompt="Prompt 2",
        )

        await repository.create(agent1)
        await repository.create(agent2)

        # Get all agents
        all_agents = await repository.get_all()

        # Verify we got both agents
        assert len(all_agents) >= 2
        agent_ids = [agent.id for agent in all_agents]
        assert agent1.id in agent_ids
        assert agent2.id in agent_ids

    @pytest.mark.asyncio
    async def test_get_all_empty(self, async_session) -> None:
        """Test getting all agent states when none exist."""
        repository = AgentStateRepository(async_session)

        all_agents = await repository.get_all()
        assert len(all_agents) == 0

    @pytest.mark.asyncio
    async def test_agent_state_with_memory_and_metrics(self, async_session) -> None:
        """Test agent state with memory and performance metrics."""
        repository = AgentStateRepository(async_session)
        agent_state = AgentState(
            id=uuid4(),
            agent_type=AgentType.CODE_AGENT,
            name="Test Agent",
            description="Test description",
            status=AgentStatus.ACTIVE,
            prompt="Test prompt",
            memory={"key": "value", "count": 42},
            performance_metrics={"accuracy": 0.95, "speed": 100.0},
        )

        await repository.create(agent_state)

        loaded = await repository.get_by_id(str(agent_state.id))
        assert loaded is not None
        assert loaded.memory == {"key": "value", "count": 42}
        assert loaded.performance_metrics == {"accuracy": 0.95, "speed": 100.0}


class TestChangeProposalRepository:
    """Test ChangeProposalRepository."""

    @pytest.mark.asyncio
    async def test_create_change_proposal(self, async_session) -> None:
        """Test creating a change proposal."""
        repository = ChangeProposalRepository(async_session)
        proposal = ChangeProposal(
            agent_id=uuid4(),
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/test.py",
            description="Test improvement",
            reasoning="Test reasoning",
            proposed_changes={"content": "new code"},
            confidence_score=0.8,
        )

        await repository.create(proposal)

        # Verify it was created
        loaded = await repository.get_by_id(str(proposal.id))
        assert loaded is not None
        assert loaded.id == proposal.id
        assert loaded.file_path == proposal.file_path
        assert loaded.confidence_score == proposal.confidence_score

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, async_session) -> None:
        """Test getting change proposal by ID when not found."""
        repository = ChangeProposalRepository(async_session)
        nonexistent_id = str(uuid4())

        result = await repository.get_by_id(nonexistent_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_change_proposal(self, async_session) -> None:
        """Test updating a change proposal."""
        repository = ChangeProposalRepository(async_session)
        proposal = ChangeProposal(
            agent_id=uuid4(),
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/original.py",
            description="Original description",
            reasoning="Original reasoning",
            proposed_changes={"original": "content"},
            confidence_score=0.5,
        )

        # Create the proposal
        await repository.create(proposal)

        # Update the proposal
        proposal.file_path = "src/updated.py"
        proposal.confidence_score = 0.9
        await repository.update(proposal)

        # Verify the update
        loaded = await repository.get_by_id(str(proposal.id))
        assert loaded is not None
        assert loaded.file_path == "src/updated.py"
        assert loaded.confidence_score == 0.9

    @pytest.mark.asyncio
    async def test_update_change_proposal_not_found(self, async_session) -> None:
        """Test updating a change proposal that doesn't exist."""
        repository = ChangeProposalRepository(async_session)
        proposal = ChangeProposal(
            agent_id=uuid4(),
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/test.py",
            description="Test description",
            reasoning="Test reasoning",
            proposed_changes={"test": "content"},
            confidence_score=0.8,
        )

        with pytest.raises(
            ValueError, match=f"Change proposal with id {proposal.id} not found"
        ):
            await repository.update(proposal)

    @pytest.mark.asyncio
    async def test_delete_change_proposal(self, async_session) -> None:
        """Test deleting a change proposal."""
        repository = ChangeProposalRepository(async_session)
        proposal = ChangeProposal(
            agent_id=uuid4(),
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/test.py",
            description="Test description",
            reasoning="Test reasoning",
            proposed_changes={"test": "content"},
            confidence_score=0.8,
        )

        # Create the proposal
        await repository.create(proposal)

        # Verify it exists
        loaded = await repository.get_by_id(str(proposal.id))
        assert loaded is not None

        # Delete it
        await repository.delete(str(proposal.id))

        # Verify it's gone
        loaded = await repository.get_by_id(str(proposal.id))
        assert loaded is None

    @pytest.mark.asyncio
    async def test_get_by_cycle_id(self, async_session) -> None:
        """Test getting change proposals by cycle ID."""
        repository = ChangeProposalRepository(async_session)
        cycle_id = uuid4()

        # Create proposals for the same cycle
        proposal1 = ChangeProposal(
            agent_id=uuid4(),
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/file1.py",
            description="First improvement",
            reasoning="First reasoning",
            proposed_changes={"change1": "content1"},
            confidence_score=0.8,
        )
        proposal2 = ChangeProposal(
            agent_id=uuid4(),
            improvement_type=ImprovementType.TEST_IMPROVEMENT,
            file_path="src/file2.py",
            description="Second improvement",
            reasoning="Second reasoning",
            proposed_changes={"change2": "content2"},
            confidence_score=0.9,
        )

        await repository.create(proposal1)
        await repository.create(proposal2)

        # Get proposals by cycle ID (currently returns all since cycle_id filtering isn't implemented)
        proposals = await repository.get_by_cycle_id(str(cycle_id))

        # Should return all proposals since filtering isn't implemented yet
        assert len(proposals) >= 2

    @pytest.mark.asyncio
    async def test_change_proposal_with_complex_changes(self, async_session) -> None:
        """Test change proposal with complex proposed changes."""
        repository = ChangeProposalRepository(async_session)
        proposal = ChangeProposal(
            agent_id=uuid4(),
            improvement_type=ImprovementType.CODE_IMPROVEMENT,
            file_path="src/complex.py",
            description="Complex improvement",
            reasoning="Complex reasoning",
            proposed_changes={
                "additions": ["line1", "line2"],
                "deletions": ["old_line1"],
                "modifications": {"line3": "new_content"},
                "metadata": {"complexity": "high", "priority": "medium"},
            },
            confidence_score=0.75,
        )

        await repository.create(proposal)

        loaded = await repository.get_by_id(str(proposal.id))
        assert loaded is not None
        assert loaded.proposed_changes == proposal.proposed_changes


class TestImprovementCycleRepository:
    """Test ImprovementCycleRepository."""

    @pytest.mark.asyncio
    async def test_create_improvement_cycle(self, async_session) -> None:
        """Test creating an improvement cycle."""
        repository = ImprovementCycleRepository(async_session)
        cycle = ImprovementCycle(
            id=uuid4(),
            cycle_number=1,
            start_time=datetime.now(UTC),
        )

        await repository.create(cycle)

        # Verify it was created
        loaded = await repository.get_by_id(str(cycle.id))
        assert loaded is not None
        assert loaded.id == cycle.id
        assert loaded.cycle_number == cycle.cycle_number

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, async_session) -> None:
        """Test getting improvement cycle by ID when not found."""
        repository = ImprovementCycleRepository(async_session)
        nonexistent_id = str(uuid4())

        result = await repository.get_by_id(nonexistent_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_improvement_cycle(self, async_session) -> None:
        """Test updating an improvement cycle."""
        repository = ImprovementCycleRepository(async_session)
        cycle = ImprovementCycle(
            id=uuid4(),
            cycle_number=1,
            start_time=datetime.now(UTC),
        )

        # Create the cycle
        await repository.create(cycle)

        # Update the cycle
        cycle.success = False
        cycle.error_message = "Something went wrong"
        cycle.complete(success=False, error_message="Something went wrong")
        await repository.update(cycle)

        # Verify the update
        loaded = await repository.get_by_id(str(cycle.id))
        assert loaded is not None
        assert loaded.success is False
        assert loaded.error_message == "Something went wrong"
        assert loaded.end_time is not None

    @pytest.mark.asyncio
    async def test_update_improvement_cycle_not_found(self, async_session) -> None:
        """Test updating an improvement cycle that doesn't exist."""
        repository = ImprovementCycleRepository(async_session)
        cycle = ImprovementCycle(
            id=uuid4(),
            cycle_number=1,
        )

        with pytest.raises(
            ValueError, match=f"Improvement cycle with id {cycle.id} not found"
        ):
            await repository.update(cycle)

    @pytest.mark.asyncio
    async def test_delete_improvement_cycle(self, async_session) -> None:
        """Test deleting an improvement cycle."""
        repository = ImprovementCycleRepository(async_session)
        cycle = ImprovementCycle(
            id=uuid4(),
            cycle_number=1,
        )

        # Create the cycle
        await repository.create(cycle)

        # Verify it exists
        loaded = await repository.get_by_id(str(cycle.id))
        assert loaded is not None

        # Delete it
        await repository.delete(str(cycle.id))

        # Verify it's gone
        loaded = await repository.get_by_id(str(cycle.id))
        assert loaded is None

    @pytest.mark.asyncio
    async def test_get_latest_cycle(self, async_session) -> None:
        """Test getting the latest improvement cycle."""
        repository = ImprovementCycleRepository(async_session)

        # Create multiple cycles
        cycle1 = ImprovementCycle(
            id=uuid4(),
            cycle_number=1,
            start_time=datetime.now(UTC),
        )
        cycle2 = ImprovementCycle(
            id=uuid4(),
            cycle_number=2,
            start_time=datetime.now(UTC),
        )

        await repository.create(cycle1)
        await repository.create(cycle2)

        # Get the latest cycle
        latest = await repository.get_latest()

        # Should return the cycle with the highest cycle_number
        assert latest is not None
        assert latest.cycle_number == 2

    @pytest.mark.asyncio
    async def test_get_latest_cycle_empty(self, async_session) -> None:
        """Test getting the latest cycle when none exist."""
        repository = ImprovementCycleRepository(async_session)

        latest = await repository.get_latest()
        assert latest is None

    @pytest.mark.asyncio
    async def test_get_recent_cycles(self, async_session) -> None:
        """Test getting recent improvement cycles."""
        repository = ImprovementCycleRepository(async_session)

        # Create multiple cycles
        cycle1 = ImprovementCycle(
            id=uuid4(),
            cycle_number=1,
            start_time=datetime.now(UTC),
        )
        cycle2 = ImprovementCycle(
            id=uuid4(),
            cycle_number=2,
            start_time=datetime.now(UTC),
        )
        cycle3 = ImprovementCycle(
            id=uuid4(),
            cycle_number=3,
            start_time=datetime.now(UTC),
        )

        await repository.create(cycle1)
        await repository.create(cycle2)
        await repository.create(cycle3)

        # Get recent cycles (limit 2)
        recent = await repository.get_recent(2)

        # Should return the 2 most recent cycles
        assert len(recent) == 2
        cycle_numbers = [cycle.cycle_number for cycle in recent]
        assert 2 in cycle_numbers
        assert 3 in cycle_numbers

    @pytest.mark.asyncio
    async def test_get_recent_cycles_empty(self, async_session) -> None:
        """Test getting recent cycles when none exist."""
        repository = ImprovementCycleRepository(async_session)

        recent = await repository.get_recent(5)
        assert len(recent) == 0

    @pytest.mark.asyncio
    async def test_improvement_cycle_with_agents_and_changes(
        self, async_session
    ) -> None:
        """Test improvement cycle with agents and changes lists."""
        repository = ImprovementCycleRepository(async_session)
        cycle = ImprovementCycle(
            id=uuid4(),
            cycle_number=1,
            agents_used=[uuid4(), uuid4()],
            changes_proposed=[uuid4()],
            changes_accepted=[uuid4()],
        )

        await repository.create(cycle)

        loaded = await repository.get_by_id(str(cycle.id))
        assert loaded is not None
        assert len(loaded.agents_used) == 2
        assert len(loaded.changes_proposed) == 1
        assert len(loaded.changes_accepted) == 1

    @pytest.mark.asyncio
    async def test_improvement_cycle_completion(self, async_session) -> None:
        """Test improvement cycle completion."""
        repository = ImprovementCycleRepository(async_session)
        cycle = ImprovementCycle(
            id=uuid4(),
            cycle_number=1,
        )

        await repository.create(cycle)

        # Complete the cycle
        cycle.complete(success=True, error_message=None)
        await repository.update(cycle)

        loaded = await repository.get_by_id(str(cycle.id))
        assert loaded is not None
        assert loaded.success is True
        assert loaded.error_message is None
        assert loaded.end_time is not None
        assert loaded.end_time > loaded.start_time
