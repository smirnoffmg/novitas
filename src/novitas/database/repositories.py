"""Repository pattern implementation for database operations."""

from abc import ABC
from abc import abstractmethod
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import AgentState
from ..core.models import ChangeProposal
from ..core.models import ImprovementCycle
from .models import AgentStateModel
from .models import ChangeProposalModel
from .models import ImprovementCycleModel


class BaseRepository(ABC):
    """Base repository interface following SOLID principles."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session

    @abstractmethod
    async def create(self, entity) -> None:
        """Create a new entity."""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: str):
        """Get entity by ID."""
        pass

    @abstractmethod
    async def update(self, entity) -> None:
        """Update an entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> None:
        """Delete an entity."""
        pass


class AgentStateRepository(BaseRepository):
    """Repository for agent state operations."""

    async def create(self, agent_state: AgentState) -> None:
        """Create a new agent state."""
        model = AgentStateModel(
            id=str(agent_state.id),
            agent_type=agent_state.agent_type,
            name=agent_state.name,
            description=agent_state.description,
            status=agent_state.status,
            version=agent_state.version,
            prompt=agent_state.prompt,
            memory=agent_state.memory,
            performance_metrics=agent_state.performance_metrics,
            created_at=agent_state.created_at,
            last_active=agent_state.last_active,
        )
        self.session.add(model)
        await self.session.commit()

    async def get_by_id(self, agent_id: str) -> AgentState | None:
        """Get agent state by ID."""
        result = await self.session.execute(
            select(AgentStateModel).where(AgentStateModel.id == agent_id)
        )
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return AgentState(
            id=UUID(model.id),
            agent_type=model.agent_type,
            name=model.name,
            description=model.description,
            status=model.status,
            version=model.version,
            prompt=model.prompt,
            memory=model.memory,
            performance_metrics=model.performance_metrics,
            created_at=model.created_at,
            last_active=model.last_active,
        )

    async def update(self, agent_state: AgentState) -> None:
        """Update an agent state."""
        result = await self.session.execute(
            select(AgentStateModel).where(AgentStateModel.id == str(agent_state.id))
        )
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Agent state with id {agent_state.id} not found")

        model.agent_type = agent_state.agent_type
        model.name = agent_state.name
        model.description = agent_state.description
        model.status = agent_state.status
        model.version = agent_state.version
        model.prompt = agent_state.prompt
        model.memory = agent_state.memory
        model.performance_metrics = agent_state.performance_metrics
        model.last_active = agent_state.last_active

        await self.session.commit()

    async def delete(self, agent_id: str) -> None:
        """Delete an agent state."""
        result = await self.session.execute(
            select(AgentStateModel).where(AgentStateModel.id == agent_id)
        )
        model = result.scalar_one_or_none()

        if model is not None:
            await self.session.delete(model)
            await self.session.commit()

    async def get_all(self) -> list[AgentState]:
        """Get all agent states."""
        result = await self.session.execute(select(AgentStateModel))
        models = result.scalars().all()

        return [
            AgentState(
                id=UUID(model.id),
                agent_type=model.agent_type,
                name=model.name,
                description=model.description,
                status=model.status,
                version=model.version,
                prompt=model.prompt,
                memory=model.memory,
                performance_metrics=model.performance_metrics,
                created_at=model.created_at,
                last_active=model.last_active,
            )
            for model in models
        ]

    async def get_by_status(self, status) -> list[AgentState]:
        """Get agent states by status."""
        result = await self.session.execute(
            select(AgentStateModel).where(AgentStateModel.status == status)
        )
        models = result.scalars().all()

        return [
            AgentState(
                id=UUID(model.id),
                agent_type=model.agent_type,
                name=model.name,
                description=model.description,
                status=model.status,
                version=model.version,
                prompt=model.prompt,
                memory=model.memory,
                performance_metrics=model.performance_metrics,
                created_at=model.created_at,
                last_active=model.last_active,
            )
            for model in models
        ]


class ChangeProposalRepository(BaseRepository):
    """Repository for change proposal operations."""

    async def create(self, proposal: ChangeProposal) -> None:
        """Create a new change proposal."""
        model = ChangeProposalModel(
            id=str(proposal.id),
            agent_id=str(proposal.agent_id),
            improvement_type=proposal.improvement_type,
            file_path=proposal.file_path,
            description=proposal.description,
            reasoning=proposal.reasoning,
            proposed_changes=proposal.proposed_changes,
            confidence_score=proposal.confidence_score,
            created_at=proposal.created_at,
        )
        self.session.add(model)
        await self.session.commit()

    async def get_by_id(self, proposal_id: str) -> ChangeProposal | None:
        """Get change proposal by ID."""
        result = await self.session.execute(
            select(ChangeProposalModel).where(ChangeProposalModel.id == proposal_id)
        )
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ChangeProposal(
            id=UUID(model.id),
            agent_id=UUID(model.agent_id),
            improvement_type=model.improvement_type,
            file_path=model.file_path,
            description=model.description,
            reasoning=model.reasoning,
            proposed_changes=model.proposed_changes,
            confidence_score=model.confidence_score,
            created_at=model.created_at,
        )

    async def update(self, proposal: ChangeProposal) -> None:
        """Update a change proposal."""
        result = await self.session.execute(
            select(ChangeProposalModel).where(
                ChangeProposalModel.id == str(proposal.id)
            )
        )
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Change proposal with id {proposal.id} not found")

        model.agent_id = str(proposal.agent_id)
        model.improvement_type = proposal.improvement_type
        model.file_path = proposal.file_path
        model.description = proposal.description
        model.reasoning = proposal.reasoning
        model.proposed_changes = proposal.proposed_changes
        model.confidence_score = proposal.confidence_score

        await self.session.commit()

    async def delete(self, proposal_id: str) -> None:
        """Delete a change proposal."""
        result = await self.session.execute(
            select(ChangeProposalModel).where(ChangeProposalModel.id == proposal_id)
        )
        model = result.scalar_one_or_none()

        if model is not None:
            await self.session.delete(model)
            await self.session.commit()

    async def get_by_cycle_id(
        self,
        cycle_id: str,  # noqa: ARG002
    ) -> list[ChangeProposal]:
        """Get change proposals by cycle ID."""
        # This would need a cycle_id field in the model or a join table
        # For now, return all proposals
        result = await self.session.execute(select(ChangeProposalModel))
        models = result.scalars().all()

        return [
            ChangeProposal(
                id=UUID(model.id),
                agent_id=UUID(model.agent_id),
                improvement_type=model.improvement_type,
                file_path=model.file_path,
                description=model.description,
                reasoning=model.reasoning,
                proposed_changes=model.proposed_changes,
                confidence_score=model.confidence_score,
                created_at=model.created_at,
            )
            for model in models
        ]


class ImprovementCycleRepository(BaseRepository):
    """Repository for improvement cycle operations."""

    async def create(self, cycle: ImprovementCycle) -> None:
        """Create a new improvement cycle."""
        model = ImprovementCycleModel(
            id=str(cycle.id),
            cycle_number=cycle.cycle_number,
            start_time=cycle.start_time,
            end_time=cycle.end_time,
            agents_used=[str(agent_id) for agent_id in cycle.agents_used],
            changes_proposed=[str(change_id) for change_id in cycle.changes_proposed],
            changes_accepted=[str(change_id) for change_id in cycle.changes_accepted],
            success=str(cycle.success).lower(),
            error_message=cycle.error_message,
        )
        self.session.add(model)
        await self.session.commit()

    async def get_by_id(self, cycle_id: str) -> ImprovementCycle | None:
        """Get improvement cycle by ID."""
        result = await self.session.execute(
            select(ImprovementCycleModel).where(ImprovementCycleModel.id == cycle_id)
        )
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ImprovementCycle(
            id=UUID(model.id),
            cycle_number=model.cycle_number,
            start_time=model.start_time,
            end_time=model.end_time,
            agents_used=[UUID(agent_id) for agent_id in model.agents_used],
            changes_proposed=[UUID(change_id) for change_id in model.changes_proposed],
            changes_accepted=[UUID(change_id) for change_id in model.changes_accepted],
            success=model.success.lower() == "true",
            error_message=model.error_message,
        )

    async def update(self, cycle: ImprovementCycle) -> None:
        """Update an improvement cycle."""
        result = await self.session.execute(
            select(ImprovementCycleModel).where(
                ImprovementCycleModel.id == str(cycle.id)
            )
        )
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Improvement cycle with id {cycle.id} not found")

        model.cycle_number = cycle.cycle_number
        model.start_time = cycle.start_time
        model.end_time = cycle.end_time
        model.agents_used = [str(agent_id) for agent_id in cycle.agents_used]
        model.changes_proposed = [
            str(change_id) for change_id in cycle.changes_proposed
        ]
        model.changes_accepted = [
            str(change_id) for change_id in cycle.changes_accepted
        ]
        model.success = str(cycle.success).lower()
        model.error_message = cycle.error_message

        await self.session.commit()

    async def delete(self, cycle_id: str) -> None:
        """Delete an improvement cycle."""
        result = await self.session.execute(
            select(ImprovementCycleModel).where(ImprovementCycleModel.id == cycle_id)
        )
        model = result.scalar_one_or_none()

        if model is not None:
            await self.session.delete(model)
            await self.session.commit()

    async def get_latest(self) -> ImprovementCycle | None:
        """Get the latest improvement cycle."""
        result = await self.session.execute(
            select(ImprovementCycleModel)
            .order_by(ImprovementCycleModel.cycle_number.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ImprovementCycle(
            id=UUID(model.id),
            cycle_number=model.cycle_number,
            start_time=model.start_time,
            end_time=model.end_time,
            agents_used=[UUID(agent_id) for agent_id in model.agents_used],
            changes_proposed=[UUID(change_id) for change_id in model.changes_proposed],
            changes_accepted=[UUID(change_id) for change_id in model.changes_accepted],
            success=model.success.lower() == "true",
            error_message=model.error_message,
        )

    async def get_recent(self, count: int) -> list[ImprovementCycle]:
        """Get recent improvement cycles."""
        result = await self.session.execute(
            select(ImprovementCycleModel)
            .order_by(ImprovementCycleModel.cycle_number.desc())
            .limit(count)
        )
        models = result.scalars().all()

        return [
            ImprovementCycle(
                id=UUID(model.id),
                cycle_number=model.cycle_number,
                start_time=model.start_time,
                end_time=model.end_time,
                agents_used=[UUID(agent_id) for agent_id in model.agents_used],
                changes_proposed=[
                    UUID(change_id) for change_id in model.changes_proposed
                ],
                changes_accepted=[
                    UUID(change_id) for change_id in model.changes_accepted
                ],
                success=model.success.lower() == "true",
                error_message=model.error_message,
            )
            for model in models
        ]
