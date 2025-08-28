"""Core package for Novitas."""

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
    # Models
    "AgentType",
    "AgentStatus",
    "ImprovementType",
    "ChangeProposal",
    "AgentState",
    "ImprovementCycle",
    "SystemMetrics",
    "AgentAction",
    "PromptTemplate",
    # Exceptions
    "NovitasError",
    "AgentError",
    "DatabaseError",
    "ImprovementCycleError",
    "ChangeProposalError",
    "ConfigurationError",
    "GitHubError",
    "PromptError",
    # Protocols
    "Agent",
    "DatabaseManager",
    "MessageBroker",
    "PromptManager",
    "GitManager",
    "LLMClient",
    "AgentFactory",
]
