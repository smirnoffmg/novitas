"""Agent Factory for creating and managing specialized agents."""

import asyncio
from typing import Any
from typing import Protocol
from uuid import UUID
from uuid import uuid4

from ..config.logging import get_logger
from ..core.exceptions import AgentError
from ..core.protocols import Agent
from ..core.protocols import DatabaseManager
from ..core.protocols import MessageBroker
from ..core.schemas import AgentPrompt
from ..llm.provider import LLMConfig
from ..llm.provider import create_llm_provider
from ..llm.provider import generate_structured_response
from .llm_provider_selector import DefaultLLMProviderSelector
from .orchestrator import OrchestratorAgent


class AgentFactory(Protocol):
    """Protocol for agent factory implementations."""

    async def create_agent(
        self,
        name: str,
        description: str,
        capabilities: list[str],
    ) -> Agent:
        """Create a new orchestrator agent.

        Args:
            name: Agent name
            description: Agent description
            capabilities: List of agent capabilities

        Returns:
            Created agent instance

        Raises:
            AgentError: If agent creation fails
        """
        ...

    async def retire_agent(self, agent_id: UUID, reason: str) -> None:
        """Retire an agent and archive its state.

        Args:
            agent_id: ID of the agent to retire
            reason: Reason for retirement

        Raises:
            AgentError: If agent retirement fails
        """
        ...

    async def get_active_agents(self) -> list[Agent]:
        """Get all currently active agents.

        Returns:
            List of active agents
        """
        ...


class DefaultAgentFactory:
    """Default implementation of agent factory."""

    def __init__(
        self,
        database_manager: DatabaseManager,
        message_broker: MessageBroker,
        available_llm_providers: dict[str, dict[str, Any]],
    ) -> None:
        """Initialize the agent factory.

        Args:
            database_manager: Database manager for persistence
            message_broker: Message broker for communication
            available_llm_providers: Available LLM providers with their configurations
        """
        self.database_manager = database_manager
        self.message_broker = message_broker
        self.available_llm_providers = available_llm_providers
        self.llm_provider_selector = DefaultLLMProviderSelector()
        self.logger = get_logger("agent.factory")

        # Track active agents
        self.active_agents: dict[UUID, Agent] = {}

    async def create_agent(
        self,
        name: str,
        description: str,
        capabilities: list[str],
    ) -> Agent:
        """Create a new orchestrator agent.

        Args:
            name: Agent name
            description: Agent description
            capabilities: List of agent capabilities

        Returns:
            Created agent instance

        Raises:
            AgentError: If agent creation fails
        """
        self.logger.info(
            "Creating orchestrator agent",
            name=name,
            capabilities=capabilities,
        )

        if not self.available_llm_providers:
            raise AgentError("No LLM providers available")

        # Select the best LLM provider for the orchestrator
        selected_provider = self.llm_provider_selector.select_provider_for_orchestrator(
            self.available_llm_providers
        )

        # Create LLM client for this agent
        llm_config = LLMConfig(
            model=selected_provider["model"],
            api_key=selected_provider["api_key"],
            temperature=selected_provider["temperature"],
            max_tokens=2000,
        )
        llm_provider = create_llm_provider(llm_config)

        try:
            # Generate agent prompt using LLM
            prompt_generation_prompt = f"""
            Create a specialized prompt for an orchestrator agent named "{name}".

            Agent capabilities: {", ".join(capabilities)}
            Agent description: {description}

            Generate a clear, focused prompt that will help this agent perform its specialized tasks effectively.

            Provide your response in this exact format:
            - prompt: The actual prompt text for the agent
            - reasoning: Brief explanation of why this prompt design is effective
            - focus_areas: List of key areas this agent should focus on
            """

            agent_prompt_result = await asyncio.wait_for(
                generate_structured_response(
                    llm_provider,
                    prompt_generation_prompt,
                    AgentPrompt,
                    max_tokens=500,
                ),
                timeout=30.0,
            )

            prompt = agent_prompt_result.prompt

            # Create the orchestrator agent
            agent = OrchestratorAgent(
                database_manager=self.database_manager,
                available_llm_providers=self.available_llm_providers,
                message_broker=self.message_broker,
                agent_id=uuid4(),  # Generate new ID
                name=name,
                description=description,
                prompt=prompt,
            )

            # Initialize the agent
            await agent.initialize()

            # Track the agent
            self.active_agents[agent.id] = agent

            self.logger.info(
                "Created orchestrator agent successfully",
                agent_id=agent.id,
                name=name,
            )

            return agent

        except Exception as e:
            self.logger.error(
                "Error creating orchestrator agent",
                name=name,
                error=str(e),
            )
            raise AgentError(f"Failed to create orchestrator agent: {e}") from e

    async def retire_agent(self, agent_id: UUID, reason: str) -> None:
        """Retire an agent and archive its state.

        Args:
            agent_id: ID of the agent to retire
            reason: Reason for retirement

        Raises:
            AgentError: If agent retirement fails
        """
        if agent_id not in self.active_agents:
            raise AgentError(f"Agent not found: {agent_id}")

        agent = self.active_agents[agent_id]

        try:
            # Clean up the agent
            await agent.cleanup()

            # Remove from active agents
            del self.active_agents[agent_id]

            self.logger.info(
                "Retired agent successfully",
                agent_id=agent_id,
                reason=reason,
            )

        except Exception as e:
            self.logger.error(
                "Error retiring agent",
                agent_id=agent_id,
                error=str(e),
            )
            raise AgentError(f"Failed to retire agent {agent_id}: {e}") from e

    async def get_active_agents(self) -> list[Agent]:
        """Get all currently active agents.

        Returns:
            List of active agents
        """
        return list(self.active_agents.values())
