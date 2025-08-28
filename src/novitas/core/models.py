"""Core data models for the Novitas AI system."""

from datetime import datetime
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator


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
    proposed_changes: Dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("confidence_score")
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
    memory: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    def increment_version(self) -> None:
        """Increment the agent's version."""
        self.version += 1
        self.last_active = datetime.utcnow()


class ImprovementCycle(BaseModel):
    """A single improvement cycle."""

    id: UUID = Field(default_factory=uuid4)
    cycle_number: int
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    agents_used: List[UUID] = Field(default_factory=list)
    changes_proposed: List[UUID] = Field(default_factory=list)
    changes_accepted: List[UUID] = Field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None

    def complete(
        self, success: bool = True, error_message: Optional[str] = None
    ) -> None:
        """Mark the cycle as complete."""
        self.end_time = datetime.utcnow()
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
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class AgentAction(BaseModel):
    """An action performed by an agent."""

    id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    action_type: str
    details: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None


class PromptTemplate(BaseModel):
    """A prompt template for agents."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    agent_type: AgentType
    template: str
    version: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def update_template(self, new_template: str) -> None:
        """Update the template and increment version."""
        self.template = new_template
        self.version += 1
        self.updated_at = datetime.utcnow()
