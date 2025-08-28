"""LLM Provider implementation for Novitas.

This module provides a simple interface for LLM providers using LangChain,
leveraging their existing capabilities rather than reimplementing them.
"""

import logging
import os
from collections.abc import AsyncIterator
from typing import Any
from typing import Protocol

from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from novitas.core.exceptions import LLMProviderError

# Constants
MAX_TEMPERATURE = 2.0

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol defining the interface for LLM providers."""

    async def ainvoke(self, messages: list[dict], **kwargs: Any) -> Any:
        """Invoke the model with messages."""
        ...

    async def astream(self, messages: list[dict], **kwargs: Any) -> AsyncIterator[Any]:
        """Stream responses from the model."""
        ...

    def with_structured_output(self, schema: type[BaseModel]) -> Any:
        """Create a model with structured output capability."""
        ...


class LLMConfig(BaseModel):
    """Configuration for LLM provider."""

    model: str = Field(
        ..., description="Model name/identifier (e.g., gpt-4o-mini, claude-3-haiku)"
    )
    api_key: str = Field(..., description="API key for the provider")
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Temperature for generation"
    )
    max_tokens: int | None = Field(
        default=None, gt=0, description="Maximum tokens to generate"
    )
    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within valid range."""
        if not 0.0 <= v <= MAX_TEMPERATURE:
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int | None) -> int | None:
        """Validate max_tokens is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("max_tokens must be positive")
        return v


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """Create an LLM provider using LangChain's automatic provider detection.

    Args:
        config: Configuration for the LLM provider

    Returns:
        Configured LLM provider instance

    Raises:
        LLMProviderError: If initialization fails
    """
    try:
        # Set API key in environment for LangChain to use
        if "gpt" in config.model.lower():
            os.environ["OPENAI_API_KEY"] = config.api_key
        elif "claude" in config.model.lower():
            os.environ["ANTHROPIC_API_KEY"] = config.api_key
        # Add more providers as needed - LangChain will handle them automatically

        # Filter out None values to avoid validation errors
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
            "timeout": config.timeout,
        }
        if config.max_tokens is not None:
            kwargs["max_tokens"] = config.max_tokens

        return init_chat_model(**kwargs)

    except Exception as e:
        raise LLMProviderError(f"Failed to initialize LLM provider: {e}") from e


async def generate_response(
    provider: LLMProvider, prompt: str | list[dict], **kwargs: Any
) -> str:
    """Generate a response from the LLM.

    Args:
        provider: LLM provider instance
        prompt: Text prompt or list of messages
        **kwargs: Additional arguments to pass to the model

    Returns:
        Generated response text

    Raises:
        LLMProviderError: If generation fails
    """
    try:
        # Handle different input types
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        response = await provider.ainvoke(messages, **kwargs)
        return response.content

    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        raise LLMProviderError(f"Failed to generate response: {e}") from e


async def generate_structured_response(
    provider: LLMProvider,
    prompt: str | list[dict],
    schema: type[BaseModel],
    **kwargs: Any,
) -> BaseModel:
    """Generate a structured response using LangChain's built-in capabilities.

    Args:
        provider: LLM provider instance
        prompt: Text prompt or list of messages
        schema: Pydantic model class for the expected response structure
        **kwargs: Additional arguments to pass to the model

    Returns:
        Parsed response as Pydantic model instance

    Raises:
        LLMProviderError: If generation fails
    """
    try:
        # Use LangChain's built-in structured output
        structured_provider = provider.with_structured_output(schema)

        # Handle different input types
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        response = await structured_provider.ainvoke(messages, **kwargs)
        return response

    except Exception as e:
        logger.error(f"Failed to generate structured response: {e}")
        raise LLMProviderError(f"Failed to generate structured response: {e}") from e


async def stream_response(
    provider: LLMProvider, prompt: str | list[dict], **kwargs: Any
) -> AsyncIterator[str]:
    """Stream a response from the LLM using LangChain's built-in streaming.

    Args:
        provider: LLM provider instance
        prompt: Text prompt or list of messages
        **kwargs: Additional arguments to pass to the model

    Yields:
        Response chunks as they are generated

    Raises:
        LLMProviderError: If streaming fails
    """
    try:
        # Handle different input types
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        async for chunk in provider.astream(messages, **kwargs):
            yield chunk.content

    except Exception as e:
        logger.error(f"Failed to stream response: {e}")
        raise LLMProviderError(f"Failed to stream response: {e}") from e
