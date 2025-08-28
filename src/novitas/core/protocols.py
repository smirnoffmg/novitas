"""Protocol definitions for the Novitas AI system."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Protocol
from typing import runtime_checkable
from uuid import UUID

from .models import AgentState
from .models import ChangeProposal
from .models import ImprovementCycle


@runtime_checkable
class Agent(Protocol):
    """Protocol for all agents in the system."""

    id: UUID
    name: str
    agent_type: str
    state: AgentState

    async def initialize(self) -> None:
        """Initialize the agent."""
        ...

    async def execute(self, context: Dict[str, Any]) -> List[ChangeProposal]:
        """Execute the agent's main logic.

        Args:
            context: Context information for the execution

        Returns:
            List of proposed changes
        """
        ...

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        ...

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get the agent's performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        ...


@runtime_checkable
class DatabaseManager(Protocol):
    """Protocol for database management."""

    async def connect(self) -> None:
        """Connect to the database."""
        ...

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        ...

    async def save_agent_state(self, agent_state: AgentState) -> None:
        """Save an agent's state to the database."""
        ...

    async def load_agent_state(self, agent_id: UUID) -> Optional[AgentState]:
        """Load an agent's state from the database."""
        ...

    async def save_change_proposal(self, proposal: ChangeProposal) -> None:
        """Save a change proposal to the database."""
        ...

    async def get_change_proposals(self, cycle_id: UUID) -> List[ChangeProposal]:
        """Get all change proposals for a cycle."""
        ...

    async def save_improvement_cycle(self, cycle: ImprovementCycle) -> None:
        """Save an improvement cycle to the database."""
        ...

    async def get_latest_cycle(self) -> Optional[ImprovementCycle]:
        """Get the latest improvement cycle."""
        ...


@runtime_checkable
class MessageBroker(Protocol):
    """Protocol for message passing between agents."""

    async def send_message(self, to_agent: UUID, message: Dict[str, Any]) -> None:
        """Send a message to an agent."""
        ...

    async def receive_message(self, agent_id: UUID) -> Optional[Dict[str, Any]]:
        """Receive a message for an agent."""
        ...

    async def broadcast_message(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all agents."""
        ...


@runtime_checkable
class PromptManager(Protocol):
    """Protocol for prompt template management."""

    async def get_prompt(self, agent_type: str, prompt_name: str) -> str:
        """Get a prompt template for an agent type."""
        ...

    async def update_prompt(
        self, agent_type: str, prompt_name: str, new_prompt: str
    ) -> None:
        """Update a prompt template."""
        ...

    async def validate_prompt(self, prompt: str) -> bool:
        """Validate a prompt template."""
        ...


@runtime_checkable
class GitManager(Protocol):
    """Protocol for Git operations."""

    async def create_branch(self, branch_name: str) -> None:
        """Create a new branch."""
        ...

    async def commit_changes(self, message: str, files: List[str]) -> None:
        """Commit changes to the repository."""
        ...

    async def push_branch(self, branch_name: str) -> None:
        """Push a branch to the remote repository."""
        ...

    async def create_pull_request(self, title: str, body: str, branch_name: str) -> str:
        """Create a pull request.

        Returns:
            URL of the created pull request
        """
        ...


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM client operations."""

    async def generate_response(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate a response from the LLM."""
        ...

    async def evaluate_proposal(self, proposal: ChangeProposal) -> float:
        """Evaluate a change proposal and return a score."""
        ...

    async def analyze_code(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code and return insights."""
        ...


class AgentFactory(ABC):
    """Abstract factory for creating agents."""

    @abstractmethod
    async def create_agent(self, agent_type: str, **kwargs: Any) -> Agent:
        """Create a new agent of the specified type."""
        pass

    @abstractmethod
    async def retire_agent(self, agent_id: UUID) -> None:
        """Retire an agent and archive its state."""
        pass

    @abstractmethod
    async def get_active_agents(self) -> List[Agent]:
        """Get all currently active agents."""
        pass
