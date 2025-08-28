"""Core package for Novitas."""

from .events import AgentCompleted
from .events import AgentCreated
from .events import AgentExecuted
from .events import AgentInitialized
from .events import AgentRetired
from .events import AgentStatusChanged
from .events import ChangeProposalAccepted
from .events import ChangeProposalApplied
from .events import ChangeProposalCreated
from .events import ChangeProposalRejected
from .events import DomainEvent
from .events import EventFactory
from .events import EventHandler
from .events import EventStore
from .events import ImprovementCycleCompleted
from .events import ImprovementCycleFailed
from .events import ImprovementCycleStarted
from .events import SystemInitialized
from .events import SystemShutdown
from .exceptions import AgentError
from .exceptions import ChangeProposalError
from .exceptions import ConfigurationError
from .exceptions import DatabaseError
from .exceptions import GitHubError
from .exceptions import ImprovementCycleError
from .exceptions import NovitasError
from .exceptions import PromptError
from .models import AgentAction
from .models import AgentState
from .models import AgentStatus
from .models import AgentType
from .models import ChangeProposal
from .models import ImprovementCycle
from .models import ImprovementType
from .models import PromptTemplate
from .models import SystemMetrics
from .protocols import Agent
from .protocols import AgentFactory
from .protocols import DatabaseManager
from .protocols import GitManager
from .protocols import LLMClient
from .protocols import MessageBroker
from .protocols import PromptManager

__all__ = [
    # Protocols
    "Agent",
    # Models
    "AgentAction",
    # Events
    "AgentCompleted",
    "AgentCreated",
    # Exceptions
    "AgentError",
    "AgentExecuted",
    "AgentFactory",
    "AgentInitialized",
    "AgentRetired",
    "AgentState",
    "AgentStatus",
    "AgentStatusChanged",
    "AgentType",
    "ChangeProposal",
    "ChangeProposalAccepted",
    "ChangeProposalApplied",
    "ChangeProposalCreated",
    "ChangeProposalError",
    "ChangeProposalRejected",
    "ConfigurationError",
    "DatabaseError",
    "DatabaseManager",
    "DomainEvent",
    "EventFactory",
    "EventHandler",
    "EventStore",
    "GitHubError",
    "GitManager",
    "ImprovementCycle",
    "ImprovementCycleCompleted",
    "ImprovementCycleError",
    "ImprovementCycleFailed",
    "ImprovementCycleStarted",
    "ImprovementType",
    "LLMClient",
    "MessageBroker",
    "NovitasError",
    "PromptError",
    "PromptManager",
    "PromptTemplate",
    "SystemInitialized",
    "SystemMetrics",
    "SystemShutdown",
]
