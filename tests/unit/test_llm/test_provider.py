"""Tests for LLM Provider implementation."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pydantic import BaseModel
from pydantic import Field

from novitas.core.exceptions import LLMProviderError
from novitas.llm.provider import LLMConfig
from novitas.llm.provider import create_llm_provider
from novitas.llm.provider import generate_response
from novitas.llm.provider import generate_structured_response
from novitas.llm.provider import stream_response


class TestLLMConfig:
    """Test LLMConfig class."""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values."""
        config = LLMConfig(model="gpt-4o-mini", api_key="test-key")

        assert config.model == "gpt-4o-mini"
        assert config.api_key == "test-key"
        assert config.temperature == 0.1
        assert config.max_tokens is None
        assert config.timeout == 30

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values."""
        config = LLMConfig(
            model="claude-3-haiku",
            api_key="test-key",
            temperature=0.5,
            max_tokens=1000,
            timeout=60,
        )

        assert config.model == "claude-3-haiku"
        assert config.api_key == "test-key"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.timeout == 60

    def test_config_validation_temperature_range(self):
        """Test temperature validation."""
        with pytest.raises(ValueError):
            LLMConfig(model="gpt-4o-mini", api_key="test-key", temperature=3.0)

    def test_config_validation_negative_temperature(self):
        """Test negative temperature validation."""
        with pytest.raises(ValueError):
            LLMConfig(model="gpt-4o-mini", api_key="test-key", temperature=-0.1)

    def test_config_validation_max_tokens_negative(self):
        """Test negative max_tokens validation."""
        with pytest.raises(ValueError):
            LLMConfig(model="gpt-4o-mini", api_key="test-key", max_tokens=-100)


class TestCreateLLMProvider:
    """Test create_llm_provider function."""

    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        config = LLMConfig(model="gpt-4o-mini", api_key="test-key")

        with patch("novitas.llm.provider.init_chat_model") as mock_init_chat_model:
            mock_model = AsyncMock()
            mock_init_chat_model.return_value = mock_model

            provider = create_llm_provider(config)

            mock_init_chat_model.assert_called_once_with(
                model="gpt-4o-mini", temperature=0.1, timeout=30
            )
            assert provider == mock_model

    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        config = LLMConfig(model="claude-3-haiku", api_key="test-key")

        with patch("novitas.llm.provider.init_chat_model") as mock_init_chat_model:
            mock_model = AsyncMock()
            mock_init_chat_model.return_value = mock_model

            provider = create_llm_provider(config)

            mock_init_chat_model.assert_called_once_with(
                model="claude-3-haiku", temperature=0.1, timeout=30
            )
            assert provider == mock_model

    def test_create_provider_error(self):
        """Test handling initialization errors."""
        config = LLMConfig(model="gpt-4o-mini", api_key="test-key")

        with (
            patch(
                "novitas.llm.provider.init_chat_model",
                side_effect=Exception("Init error"),
            ),
            pytest.raises(LLMProviderError, match="Failed to initialize LLM provider"),
        ):
            create_llm_provider(config)


class TestGenerateResponse:
    """Test generate_response function."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_generate_response_with_string(self, mock_provider):
        """Test generating response with string prompt."""
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_provider.ainvoke.return_value = mock_response

        response = await generate_response(mock_provider, "Test prompt")

        assert response == "Test response"
        mock_provider.ainvoke.assert_called_once_with(
            [{"role": "user", "content": "Test prompt"}]
        )

    @pytest.mark.asyncio
    async def test_generate_response_with_messages(self, mock_provider):
        """Test generating response with message list."""
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_provider.ainvoke.return_value = mock_response

        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
        ]

        response = await generate_response(mock_provider, messages)

        assert response == "Test response"
        mock_provider.ainvoke.assert_called_once_with(messages)

    @pytest.mark.asyncio
    async def test_generate_response_error(self, mock_provider):
        """Test handling of generation errors."""
        mock_provider.ainvoke.side_effect = Exception("Model error")

        with pytest.raises(LLMProviderError, match="Failed to generate response"):
            await generate_response(mock_provider, "Test prompt")


class TestGenerateStructuredResponse:
    """Test generate_structured_response function."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""
        provider = AsyncMock()
        # with_structured_output should return the provider itself, not a coroutine
        provider.with_structured_output = MagicMock(return_value=provider)
        return provider

    @pytest.mark.asyncio
    async def test_generate_structured_response_success(self, mock_provider):
        """Test successful structured response generation."""

        class TestSchema(BaseModel):
            answer: str = Field(description="The answer")
            confidence: float = Field(description="Confidence score")

        mock_response = TestSchema(answer="Test answer", confidence=0.95)
        mock_provider.ainvoke.return_value = mock_response

        response = await generate_structured_response(
            mock_provider, "Test prompt", TestSchema
        )

        assert isinstance(response, TestSchema)
        assert response.answer == "Test answer"
        assert response.confidence == 0.95
        mock_provider.with_structured_output.assert_called_once_with(TestSchema)
        mock_provider.ainvoke.assert_called_once_with(
            [{"role": "user", "content": "Test prompt"}]
        )

    @pytest.mark.asyncio
    async def test_generate_structured_response_with_messages(self, mock_provider):
        """Test structured response generation with message list."""

        class TestSchema(BaseModel):
            answer: str = Field(description="The answer")

        mock_response = TestSchema(answer="Test answer")
        mock_provider.ainvoke.return_value = mock_response

        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
        ]

        response = await generate_structured_response(
            mock_provider, messages, TestSchema
        )

        assert isinstance(response, TestSchema)
        assert response.answer == "Test answer"
        mock_provider.ainvoke.assert_called_once_with(messages)

    @pytest.mark.asyncio
    async def test_generate_structured_response_error(self, mock_provider):
        """Test handling of structured response errors."""

        class TestSchema(BaseModel):
            answer: str = Field(description="The answer")

        mock_provider.ainvoke.side_effect = Exception("Model error")

        with pytest.raises(
            LLMProviderError, match="Failed to generate structured response"
        ):
            await generate_structured_response(mock_provider, "Test prompt", TestSchema)


class TestStreamResponse:
    """Test stream_response function."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""
        provider = AsyncMock()
        return provider

    @pytest.mark.asyncio
    async def test_stream_response_success(self, mock_provider):
        """Test successful streaming response."""

        # Create an async iterator for the mock
        async def mock_astream(*args, **kwargs):
            mock_chunks = [
                MagicMock(content="Hello"),
                MagicMock(content=" "),
                MagicMock(content="world"),
            ]
            for chunk in mock_chunks:
                yield chunk

        mock_provider.astream = mock_astream

        chunks = []
        async for chunk in stream_response(mock_provider, "Test prompt"):
            chunks.append(chunk)

        assert chunks == ["Hello", " ", "world"]

    @pytest.mark.asyncio
    async def test_stream_response_with_messages(self, mock_provider):
        """Test streaming response with message list."""

        # Create an async iterator for the mock
        async def mock_astream(*args, **kwargs):
            mock_chunks = [MagicMock(content="Hello"), MagicMock(content=" world")]
            for chunk in mock_chunks:
                yield chunk

        mock_provider.astream = mock_astream

        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
        ]

        chunks = []
        async for chunk in stream_response(mock_provider, messages):
            chunks.append(chunk)

        assert chunks == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_stream_response_error(self, mock_provider):
        """Test handling of streaming errors."""
        mock_provider.astream.side_effect = Exception("Stream error")

        with pytest.raises(LLMProviderError, match="Failed to stream response"):
            async for _ in stream_response(mock_provider, "Test prompt"):
                pass
