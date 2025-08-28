"""LLM Provider Selector for choosing appropriate LLM providers for different agent types."""

from typing import Any
from typing import Protocol

from ..config.logging import get_logger
from ..core.exceptions import AgentError


class LLMProviderSelector(Protocol):
    """Protocol for LLM provider selection strategies."""

    def select_provider_for_orchestrator(
        self, available_providers: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Select the best LLM provider for the orchestrator agent.

        Args:
            available_providers: Dictionary of available providers with their configs

        Returns:
            Selected provider configuration with model and temperature selected

        Raises:
            AgentError: If no providers are available
        """
        ...

    def select_provider_for_agent_type(
        self, agent_type: str, available_providers: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Select the best LLM provider for a specific agent type.

        Args:
            agent_type: Type of agent being created
            available_providers: Dictionary of available providers with their configs

        Returns:
            Selected provider configuration with provider_name, model, and temperature added

        Raises:
            AgentError: If no providers are available
        """
        ...


class DefaultLLMProviderSelector:
    """Default implementation of LLM provider selection strategy."""

    def __init__(self) -> None:
        """Initialize the default LLM provider selector."""
        self.logger = get_logger("agent.llm_provider_selector")

    def select_provider_for_orchestrator(
        self, available_providers: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Select the best LLM provider for the orchestrator agent.

        Args:
            available_providers: Dictionary of available providers with their configs

        Returns:
            Selected provider configuration with model and temperature selected

        Raises:
            AgentError: If no providers are available
        """
        self.logger.info(
            "Selecting LLM provider for orchestrator",
            available_providers=list(available_providers.keys()),
        )

        if not available_providers:
            raise AgentError("No LLM providers available")

        # Prefer Anthropic Claude models for orchestration (better reasoning)
        if "anthropic" in available_providers:
            provider_info = available_providers["anthropic"].copy()
            # Select the best Anthropic model for orchestration
            provider_info["model"] = (
                "claude-sonnet-4-20250514"  # Best for reasoning and coordination
            )
            provider_info["temperature"] = (
                0.1  # Low temperature for consistent orchestration decisions
            )
            self.logger.info(
                "Selected Anthropic provider for orchestrator",
                model=provider_info["model"],
                temperature=provider_info["temperature"],
            )
            return provider_info

        # Fallback to OpenAI
        if "openai" in available_providers:
            provider_info = available_providers["openai"].copy()
            # Select the best OpenAI model for orchestration
            provider_info["model"] = (
                "gpt-4-turbo-preview"  # Best for reasoning and coordination
            )
            provider_info["temperature"] = (
                0.1  # Low temperature for consistent orchestration decisions
            )
            self.logger.info(
                "Selected OpenAI provider for orchestrator",
                model=provider_info["model"],
                temperature=provider_info["temperature"],
            )
            return provider_info

        # If we get here, something is wrong
        raise AgentError(
            f"No suitable LLM provider found. Available: {list(available_providers.keys())}"
        )

    def select_provider_for_agent_type(
        self, agent_type: str, available_providers: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Select the best LLM provider for a specific agent type.

        Args:
            agent_type: Type of agent being created
            available_providers: Dictionary of available providers with their configs

        Returns:
            Selected provider configuration with provider_name, model, and temperature added

        Raises:
            AgentError: If no providers are available
        """
        if not available_providers:
            raise AgentError("No LLM providers available")

        # Different agent types may benefit from different providers, models, and temperatures
        if agent_type == "code_agent":
            # Code agents benefit from strong reasoning and code understanding
            # Prefer Claude models for code analysis
            if "anthropic" in available_providers:
                provider_info = available_providers["anthropic"].copy()
                provider_info["provider_name"] = "anthropic"
                provider_info["model"] = (
                    "claude-sonnet-4-20250514"  # Best for code analysis
                )
                provider_info["temperature"] = (
                    0.1  # Low temperature for consistent code analysis
                )
                self.logger.info(
                    "Selected Anthropic for code agent",
                    model=provider_info["model"],
                    temperature=provider_info["temperature"],
                )
                return provider_info

        elif agent_type == "documentation_agent":
            # Documentation agents benefit from clear writing and structure
            # Both Claude and GPT-4 are good, prefer Claude for consistency
            if "anthropic" in available_providers:
                provider_info = available_providers["anthropic"].copy()
                provider_info["provider_name"] = "anthropic"
                provider_info["model"] = "claude-sonnet-4-20250514"  # Best for writing
                provider_info["temperature"] = (
                    0.3  # Slightly higher for creative documentation
                )
                self.logger.info(
                    "Selected Anthropic for documentation agent",
                    model=provider_info["model"],
                    temperature=provider_info["temperature"],
                )
                return provider_info

        elif agent_type == "test_agent" and "anthropic" in available_providers:
            # Test agents need systematic thinking and edge case detection
            # Prefer Claude for systematic reasoning
            provider_info = available_providers["anthropic"].copy()
            provider_info["provider_name"] = "anthropic"
            provider_info["model"] = (
                "claude-sonnet-4-20250514"  # Best for systematic thinking
            )
            provider_info["temperature"] = (
                0.2  # Medium temperature for creative test cases
            )
            self.logger.info(
                "Selected Anthropic for test agent",
                model=provider_info["model"],
                temperature=provider_info["temperature"],
            )
            return provider_info

        # Default: use the first available provider
        provider_name = next(iter(available_providers.keys()))
        provider_info = available_providers[provider_name].copy()
        provider_info["provider_name"] = provider_name

        # Set reasonable defaults if not already set
        if "model" not in provider_info:
            if provider_name == "anthropic":
                provider_info["model"] = "claude-sonnet-4-20250514"
            elif provider_name == "openai":
                provider_info["model"] = "gpt-4-turbo-preview"

        if "temperature" not in provider_info:
            provider_info["temperature"] = 0.2  # Default temperature

        self.logger.info(
            f"Selected default provider for {agent_type}",
            model=provider_info["model"],
            temperature=provider_info["temperature"],
        )
        return provider_info
