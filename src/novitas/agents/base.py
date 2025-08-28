"""Base agent class for the Novitas AI system."""

import asyncio
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID
from uuid import uuid4

from ..config.logging import get_logger
from ..core.exceptions import AgentError
from ..core.exceptions import AgentTimeoutError
from ..core.models import AgentState
from ..core.models import AgentType
from ..core.models import ChangeProposal
from ..core.protocols import Agent
from ..core.protocols import DatabaseManager
from ..core.protocols import LLMClient
from ..core.protocols import MessageBroker


class BaseAgent(Agent):
    """Base class for all agents in the system."""

    def __init__(
        self,
        name: str,
        agent_type: AgentType,
        description: str,
        prompt: str,
        database_manager: DatabaseManager,
        llm_client: LLMClient,
        message_broker: MessageBroker,
        agent_id: Optional[UUID] = None,
    ) -> None:
        """Initialize the base agent.

        Args:
            name: Agent name
            agent_type: Type of agent
            description: Agent description
            prompt: Agent's prompt template
            database_manager: Database manager instance
            llm_client: LLM client instance
            message_broker: Message broker instance
            agent_id: Optional agent ID (generated if not provided)
        """
        self.id = agent_id or uuid4()
        self.name = name
        self.agent_type = agent_type.value
        self.description = description
        self.prompt = prompt
        self.database_manager = database_manager
        self.llm_client = llm_client
        self.message_broker = message_broker
        self.logger = get_logger(f"agent.{self.agent_type}.{self.name}")

        # Initialize state
        self.state = AgentState(
            id=self.id,
            agent_type=agent_type,
            name=name,
            description=description,
            prompt=prompt,
        )

        self._initialized = False
        self._execution_count = 0

    async def initialize(self) -> None:
        """Initialize the agent and load its state."""
        try:
            # Load existing state if available
            existing_state = await self.database_manager.load_agent_state(self.id)
            if existing_state:
                self.state = existing_state
                self.logger.info("Loaded existing agent state", agent_id=self.id)

            # Run agent-specific initialization
            await self._initialize_agent()

            # Save initial state
            await self.database_manager.save_agent_state(self.state)

            self._initialized = True
            self.logger.info("Agent initialized successfully", agent_id=self.id)

        except Exception as e:
            self.logger.error(
                "Failed to initialize agent", agent_id=self.id, error=str(e)
            )
            raise AgentError(f"Failed to initialize agent {self.name}: {e}")

    @abstractmethod
    async def _initialize_agent(self) -> None:
        """Agent-specific initialization logic."""
        pass

    async def execute(self, context: Dict[str, Any]) -> List[ChangeProposal]:
        """Execute the agent's main logic.

        Args:
            context: Context information for the execution

        Returns:
            List of proposed changes
        """
        if not self._initialized:
            raise AgentError(f"Agent {self.name} is not initialized")

        start_time = asyncio.get_event_loop().time()
        self._execution_count += 1

        try:
            self.logger.info(
                "Starting agent execution",
                agent_id=self.id,
                execution_count=self._execution_count,
                context_keys=list(context.keys()),
            )

            # Execute agent-specific logic
            proposals = await self._execute_agent(context)

            # Update performance metrics
            duration = asyncio.get_event_loop().time() - start_time
            self.state.performance_metrics.update(
                {
                    "last_execution_duration": duration,
                    "total_executions": self._execution_count,
                    "average_execution_duration": (
                        (
                            self.state.performance_metrics.get(
                                "average_execution_duration", 0
                            )
                            * (self._execution_count - 1)
                            + duration
                        )
                        / self._execution_count
                    ),
                    "proposals_generated": len(proposals),
                }
            )

            # Update state
            self.state.increment_version()
            await self.database_manager.save_agent_state(self.state)

            self.logger.info(
                "Agent execution completed",
                agent_id=self.id,
                proposals_generated=len(proposals),
                duration=duration,
            )

            return proposals

        except asyncio.TimeoutError:
            self.logger.error("Agent execution timed out", agent_id=self.id)
            raise AgentTimeoutError(f"Agent {self.name} execution timed out")
        except Exception as e:
            self.logger.error("Agent execution failed", agent_id=self.id, error=str(e))
            raise AgentError(f"Agent {self.name} execution failed: {e}")

    @abstractmethod
    async def _execute_agent(self, context: Dict[str, Any]) -> List[ChangeProposal]:
        """Agent-specific execution logic.

        Args:
            context: Context information for the execution

        Returns:
            List of proposed changes
        """
        pass

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        try:
            await self._cleanup_agent()
            self.logger.info("Agent cleanup completed", agent_id=self.id)
        except Exception as e:
            self.logger.error("Agent cleanup failed", agent_id=self.id, error=str(e))
            raise AgentError(f"Agent {self.name} cleanup failed: {e}")

    async def _cleanup_agent(self) -> None:
        """Agent-specific cleanup logic."""
        pass

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get the agent's performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        return self.state.performance_metrics.copy()

    async def update_prompt(self, new_prompt: str) -> None:
        """Update the agent's prompt.

        Args:
            new_prompt: New prompt template
        """
        self.prompt = new_prompt
        self.state.prompt = new_prompt
        self.state.increment_version()
        await self.database_manager.save_agent_state(self.state)

        self.logger.info("Agent prompt updated", agent_id=self.id)

    async def send_message(self, to_agent: UUID, message: Dict[str, Any]) -> None:
        """Send a message to another agent.

        Args:
            to_agent: ID of the target agent
            message: Message content
        """
        await self.message_broker.send_message(to_agent, message)

    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message for this agent.

        Returns:
            Message content or None if no message available
        """
        return await self.message_broker.receive_message(self.id)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"

    def __repr__(self) -> str:
        return self.__str__()
