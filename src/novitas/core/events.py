"""Domain events for event sourcing in the Novitas AI system."""

from datetime import UTC
from datetime import datetime
from typing import Any
from typing import Protocol
from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field

from .models import AgentStatus
from .models import AgentType
from .models import ImprovementType


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    id: UUID = Field(default_factory=uuid4)
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: UUID
    version: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        frozen = True


# Agent Events
class AgentCreated(DomainEvent):
    """Event raised when an agent is created."""

    event_type: str = "agent.created"
    agent_id: UUID
    agent_type: AgentType
    name: str
    description: str
    prompt: str


class AgentInitialized(DomainEvent):
    """Event raised when an agent is initialized."""

    event_type: str = "agent.initialized"
    agent_id: UUID
    initialization_time: datetime


class AgentExecuted(DomainEvent):
    """Event raised when an agent executes."""

    event_type: str = "agent.executed"
    agent_id: UUID
    execution_context: dict[str, Any]
    execution_time: datetime
    proposals_generated: int


class AgentCompleted(DomainEvent):
    """Event raised when an agent completes execution."""

    event_type: str = "agent.completed"
    agent_id: UUID
    completion_time: datetime
    success: bool
    error_message: str | None = None


class AgentStatusChanged(DomainEvent):
    """Event raised when an agent's status changes."""

    event_type: str = "agent.status_changed"
    agent_id: UUID
    old_status: AgentStatus
    new_status: AgentStatus
    reason: str | None = None


class AgentRetired(DomainEvent):
    """Event raised when an agent is retired."""

    event_type: str = "agent.retired"
    agent_id: UUID
    retirement_reason: str
    performance_metrics: dict[str, float]


# Improvement Cycle Events
class ImprovementCycleStarted(DomainEvent):
    """Event raised when an improvement cycle starts."""

    event_type: str = "improvement_cycle.started"
    cycle_id: UUID
    cycle_number: int
    agents_to_use: list[UUID]


class ImprovementCycleCompleted(DomainEvent):
    """Event raised when an improvement cycle completes."""

    event_type: str = "improvement_cycle.completed"
    cycle_id: UUID
    success: bool
    proposals_generated: int
    proposals_accepted: int
    error_message: str | None = None


class ImprovementCycleFailed(DomainEvent):
    """Event raised when an improvement cycle fails."""

    event_type: str = "improvement_cycle.failed"
    cycle_id: UUID
    error_message: str
    failure_reason: str


# Change Proposal Events
class ChangeProposalCreated(DomainEvent):
    """Event raised when a change proposal is created."""

    event_type: str = "change_proposal.created"
    proposal_id: UUID
    agent_id: UUID
    improvement_type: ImprovementType
    file_path: str
    description: str
    confidence_score: float


class ChangeProposalAccepted(DomainEvent):
    """Event raised when a change proposal is accepted."""

    event_type: str = "change_proposal.accepted"
    proposal_id: UUID
    accepted_by: UUID
    acceptance_reason: str | None = None


class ChangeProposalRejected(DomainEvent):
    """Event raised when a change proposal is rejected."""

    event_type: str = "change_proposal.rejected"
    proposal_id: UUID
    rejected_by: UUID
    rejection_reason: str


class ChangeProposalApplied(DomainEvent):
    """Event raised when a change proposal is applied to the codebase."""

    event_type: str = "change_proposal.applied"
    proposal_id: UUID
    applied_by: UUID
    application_time: datetime
    git_commit_hash: str | None = None


# System Events
class SystemInitialized(DomainEvent):
    """Event raised when the system is initialized."""

    event_type: str = "system.initialized"
    system_id: UUID
    configuration_hash: str
    environment: str


class SystemShutdown(DomainEvent):
    """Event raised when the system shuts down."""

    event_type: str = "system.shutdown"
    system_id: UUID
    shutdown_reason: str
    uptime_seconds: float


# Event Factory
class EventFactory:
    """Factory for creating domain events."""

    @staticmethod
    def create_agent_created(
        agent_id: UUID,
        agent_type: AgentType,
        name: str,
        description: str,
        prompt: str,
        aggregate_id: UUID | None = None,
    ) -> AgentCreated:
        """Create an AgentCreated event."""
        return AgentCreated(
            aggregate_id=aggregate_id or agent_id,
            agent_id=agent_id,
            agent_type=agent_type,
            name=name,
            description=description,
            prompt=prompt,
        )

    @staticmethod
    def create_agent_initialized(
        agent_id: UUID,
        initialization_time: datetime | None = None,
        aggregate_id: UUID | None = None,
    ) -> AgentInitialized:
        """Create an AgentInitialized event."""
        return AgentInitialized(
            aggregate_id=aggregate_id or agent_id,
            agent_id=agent_id,
            initialization_time=initialization_time or datetime.now(UTC),
        )

    @staticmethod
    def create_improvement_cycle_started(
        cycle_id: UUID,
        cycle_number: int,
        agents_to_use: list[UUID],
    ) -> ImprovementCycleStarted:
        """Create an ImprovementCycleStarted event."""
        return ImprovementCycleStarted(
            aggregate_id=cycle_id,
            cycle_id=cycle_id,
            cycle_number=cycle_number,
            agents_to_use=agents_to_use,
        )

    @staticmethod
    def create_change_proposal_created(
        proposal_id: UUID,
        agent_id: UUID,
        improvement_type: ImprovementType,
        file_path: str,
        description: str,
        confidence_score: float,
    ) -> ChangeProposalCreated:
        """Create a ChangeProposalCreated event."""
        return ChangeProposalCreated(
            aggregate_id=proposal_id,
            proposal_id=proposal_id,
            agent_id=agent_id,
            improvement_type=improvement_type,
            file_path=file_path,
            description=description,
            confidence_score=confidence_score,
        )


# Event Handler Protocol
class EventHandler(Protocol):
    """Protocol for event handlers."""

    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event."""
        ...


# Event Store Protocol
class EventStore(Protocol):
    """Protocol for event storage."""

    async def store(self, event: DomainEvent) -> None:
        """Store a domain event."""
        ...

    async def get_events(self, aggregate_id: UUID) -> list[DomainEvent]:
        """Get all events for an aggregate."""
        ...

    async def get_events_by_type(self, event_type: str) -> list[DomainEvent]:
        """Get all events of a specific type."""
        ...
