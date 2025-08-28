"""Tests for LLM Provider Selector."""

import pytest

from novitas.agents.llm_provider_selector import DefaultLLMProviderSelector
from novitas.agents.llm_provider_selector import LLMProviderSelector
from novitas.core.exceptions import AgentError


class TestLLMProviderSelector:
    """Test cases for LLM Provider Selector."""

    def test_llm_provider_selector_protocol(self):
        """Test that LLMProviderSelector is a proper protocol."""
        # This test ensures the protocol is properly defined
        assert callable(LLMProviderSelector)

    def test_default_llm_provider_selector_creation(self):
        """Test DefaultLLMProviderSelector can be instantiated."""
        selector = DefaultLLMProviderSelector()
        assert isinstance(selector, DefaultLLMProviderSelector)

    def test_select_provider_for_orchestrator_anthropic_preferred(self):
        """Test that Anthropic is preferred for orchestrator when available."""
        selector = DefaultLLMProviderSelector()
        available_providers = {
            "anthropic": {
                "api_key": "test_key",
                "temperature": 0.5,
            },
            "openai": {
                "api_key": "test_key",
                "temperature": 0.5,
            },
        }

        result = selector.select_provider_for_orchestrator(available_providers)

        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["temperature"] == 0.1
        assert "api_key" in result

    def test_select_provider_for_orchestrator_openai_fallback(self):
        """Test that OpenAI is used as fallback when Anthropic not available."""
        selector = DefaultLLMProviderSelector()
        available_providers = {
            "openai": {
                "api_key": "test_key",
                "temperature": 0.5,
            }
        }

        result = selector.select_provider_for_orchestrator(available_providers)

        assert result["model"] == "gpt-4-turbo-preview"
        assert result["temperature"] == 0.1
        assert "api_key" in result

    def test_select_provider_for_orchestrator_no_providers(self):
        """Test that error is raised when no providers available."""
        selector = DefaultLLMProviderSelector()
        available_providers = {}

        with pytest.raises(AgentError, match="No LLM providers available"):
            selector.select_provider_for_orchestrator(available_providers)

    def test_select_provider_for_agent_type_code_agent(self):
        """Test provider selection for code agent."""
        selector = DefaultLLMProviderSelector()
        available_providers = {
            "anthropic": {
                "api_key": "test_key",
                "temperature": 0.5,
            }
        }

        result = selector.select_provider_for_agent_type(
            "code_agent", available_providers
        )

        assert result["provider_name"] == "anthropic"
        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["temperature"] == 0.1

    def test_select_provider_for_agent_type_documentation_agent(self):
        """Test provider selection for documentation agent."""
        selector = DefaultLLMProviderSelector()
        available_providers = {
            "anthropic": {
                "api_key": "test_key",
                "temperature": 0.5,
            }
        }

        result = selector.select_provider_for_agent_type(
            "documentation_agent", available_providers
        )

        assert result["provider_name"] == "anthropic"
        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["temperature"] == 0.3

    def test_select_provider_for_agent_type_test_agent(self):
        """Test provider selection for test agent."""
        selector = DefaultLLMProviderSelector()
        available_providers = {
            "anthropic": {
                "api_key": "test_key",
                "temperature": 0.5,
            }
        }

        result = selector.select_provider_for_agent_type(
            "test_agent", available_providers
        )

        assert result["provider_name"] == "anthropic"
        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["temperature"] == 0.2

    def test_select_provider_for_agent_type_default_fallback(self):
        """Test default provider selection when specific type not handled."""
        selector = DefaultLLMProviderSelector()
        available_providers = {
            "anthropic": {
                "api_key": "test_key",
                "temperature": 0.5,
                "model": "claude-sonnet-4-20250514",
            }
        }

        result = selector.select_provider_for_agent_type(
            "unknown_agent", available_providers
        )

        assert result["provider_name"] == "anthropic"
        assert "model" in result
        assert "temperature" in result

    def test_select_provider_for_agent_type_no_providers(self):
        """Test error when no providers available for agent type."""
        selector = DefaultLLMProviderSelector()
        available_providers = {}

        with pytest.raises(AgentError, match="No LLM providers available"):
            selector.select_provider_for_agent_type("code_agent", available_providers)
