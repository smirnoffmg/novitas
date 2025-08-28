"""SQLAlchemy database models for the Novitas AI system."""

from datetime import UTC
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import declarative_base

from ..core.models import AgentStatus
from ..core.models import AgentType
from ..core.models import ImprovementType

# Use JSON for both PostgreSQL and SQLite for compatibility
JSONType = JSON

Base = declarative_base()


class AgentStateModel(Base):
    """SQLAlchemy model for agent state."""

    __tablename__ = "agent_states"

    id = Column(String, primary_key=True)
    agent_type = Column(Enum(AgentType), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(AgentStatus), nullable=False, default=AgentStatus.ACTIVE)
    version = Column(Integer, nullable=False, default=1)
    prompt = Column(Text, nullable=False)
    memory = Column(JSONType, nullable=False, default=dict)
    performance_metrics = Column(JSONType, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    last_active = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<AgentStateModel(id='{self.id}', name='{self.name}', type='{self.agent_type}')>"


class ChangeProposalModel(Base):
    """SQLAlchemy model for change proposals."""

    __tablename__ = "change_proposals"

    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False)
    improvement_type = Column(Enum(ImprovementType), nullable=False)
    file_path = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    proposed_changes = Column(JSONType, nullable=False)
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<ChangeProposalModel(id='{self.id}', file='{self.file_path}', type='{self.improvement_type}')>"


class ImprovementCycleModel(Base):
    """SQLAlchemy model for improvement cycles."""

    __tablename__ = "improvement_cycles"

    id = Column(String, primary_key=True)
    cycle_number = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    end_time = Column(DateTime, nullable=True)
    agents_used = Column(JSONType, nullable=False, default=list)
    changes_proposed = Column(JSONType, nullable=False, default=list)
    changes_accepted = Column(JSONType, nullable=False, default=list)
    success = Column(
        String(10), nullable=False, default="true"
    )  # SQLite boolean workaround
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ImprovementCycleModel(id='{self.id}', cycle_number={self.cycle_number})>"
        )


class AgentActionModel(Base):
    """SQLAlchemy model for agent actions."""

    __tablename__ = "agent_actions"

    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False)
    action_type = Column(String(100), nullable=False)
    details = Column(JSONType, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    success = Column(
        String(10), nullable=False, default="true"
    )  # SQLite boolean workaround
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentActionModel(id='{self.id}', agent_id='{self.agent_id}', action_type='{self.action_type}')>"


class PromptTemplateModel(Base):
    """SQLAlchemy model for prompt templates."""

    __tablename__ = "prompt_templates"

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    agent_type = Column(Enum(AgentType), nullable=False)
    template = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(
        String(10), nullable=False, default="true"
    )  # SQLite boolean workaround
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<PromptTemplateModel(id='{self.id}', name='{self.name}', agent_type='{self.agent_type}')>"
