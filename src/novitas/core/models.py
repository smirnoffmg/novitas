"""Core data models for the Novitas AI system."""

from datetime import UTC
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class AgentType(str, Enum):
    """Types of agents in the system."""

    ORCHESTRATOR = "orchestrator"
    CODE_AGENT = "code_agent"
    TEST_AGENT = "test_agent"
    DOCUMENTATION_AGENT = "documentation_agent"


class AgentStatus(str, Enum):
    """Status of an agent."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"
    ARCHIVED = "archived"


class ImprovementType(str, Enum):
    """Types of improvements that can be made."""

    CODE_IMPROVEMENT = "code_improvement"
    TEST_IMPROVEMENT = "test_improvement"
    DOCUMENTATION_IMPROVEMENT = "documentation_improvement"
    PROMPT_IMPROVEMENT = "prompt_improvement"
    CONFIG_IMPROVEMENT = "config_improvement"


class ChangeProposal(BaseModel):
    """A proposed change to the codebase."""

    id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    improvement_type: ImprovementType
    file_path: str
    description: str
    reasoning: str
    proposed_changes: dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return v


class AgentState(BaseModel):
    """State of an agent."""

    id: UUID = Field(default_factory=uuid4)
    agent_type: AgentType
    name: str
    description: str
    status: AgentStatus = AgentStatus.ACTIVE
    version: int = 1
    prompt: str
    memory: dict[str, Any] = Field(default_factory=dict)
    performance_metrics: dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_active: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def increment_version(self) -> None:
        """Increment the agent's version."""
        self.version += 1
        self.last_active = datetime.now(UTC)


class ImprovementCycle(BaseModel):
    """A single improvement cycle."""

    id: UUID = Field(default_factory=uuid4)
    cycle_number: int
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    agents_used: list[UUID] = Field(default_factory=list)
    changes_proposed: list[UUID] = Field(default_factory=list)
    changes_accepted: list[UUID] = Field(default_factory=list)
    success: bool = True
    error_message: str | None = None

    def complete(self, success: bool = True, error_message: str | None = None) -> None:
        """Mark the cycle as complete."""
        self.end_time = datetime.now(UTC)
        self.success = success
        self.error_message = error_message


class SystemMetrics(BaseModel):
    """System-wide metrics."""

    total_cycles: int = 0
    successful_cycles: int = 0
    total_agents_created: int = 0
    total_agents_retired: int = 0
    total_changes_proposed: int = 0
    total_changes_accepted: int = 0
    average_cycle_duration: float = 0.0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentAction(BaseModel):
    """An action performed by an agent."""

    id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    action_type: str
    details: dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    success: bool = True
    error_message: str | None = None
    duration_seconds: float | None = None


class MemoryType(str, Enum):
    """Types of memory items."""

    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    EXPERIENCE = "experience"
    TASK_RESULT = "task_result"
    ERROR = "error"
    METADATA = "metadata"


class MemoryItem(BaseModel):
    """A memory item for agents."""

    id: UUID = Field(default_factory=uuid4)
    memory_type: MemoryType
    content: dict[str, Any]
    tags: list[str] = Field(default_factory=list)
    importance: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ttl: float | None = None  # Time to live in seconds
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("importance")
    @classmethod
    def validate_importance(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("importance must be between 0.0 and 1.0")
        return v


class MessageType(str, Enum):
    """Types of messages between agents."""

    TEXT = "text"
    COMMAND = "command"
    RESPONSE = "response"
    ERROR = "error"
    STATUS = "status"


class AgentMessage(BaseModel):
    """A message between agents."""

    id: UUID = Field(default_factory=uuid4)
    sender_id: UUID
    recipient_id: UUID | None = None
    message_type: MessageType
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_broadcast: bool = False

    def is_valid(self) -> bool:
        """Check if the message is valid."""
        return bool(self.content.strip() and self.sender_id)


class PromptTemplate(BaseModel):
    """A prompt template for agents."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    agent_type: AgentType
    template: str
    version: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def update_template(self, new_template: str) -> None:
        """Update the template and increment version."""
        self.template = new_template
        self.version += 1
        self.updated_at = datetime.now(UTC)
