"""Example usage of the LLM Provider Layer."""

import asyncio

from pydantic import BaseModel
from pydantic import Field

from novitas.llm import LLMConfig
from novitas.llm import create_llm_provider
from novitas.llm import generate_response
from novitas.llm import generate_structured_response
from novitas.llm import stream_response


class CodeAnalysis(BaseModel):
    """Structured response for code analysis."""

    issues: list[str] = Field(description="List of identified issues")
    suggestions: list[str] = Field(description="List of improvement suggestions")
    complexity_score: float = Field(description="Code complexity score (0-10)")


async def main():
    """Demonstrate LLM provider usage."""

    # Configuration - LangChain will automatically detect the provider from the model name
    config = LLMConfig(
        model="gpt-4o-mini",  # OpenAI model
        api_key="your-api-key-here",  # Set your actual API key
        temperature=0.1,
        max_tokens=1000,
    )

    # Create the provider
    provider = create_llm_provider(config)

    # Example 1: Simple text generation
    print("=== Simple Text Generation ===")
    response = await generate_response(
        provider, "Explain the benefits of using Protocols in Python"
    )
    print(f"Response: {response}\n")

    # Example 2: Structured response generation
    print("=== Structured Response Generation ===")
    code_sample = """
    def calculate_fibonacci(n):
        if n <= 1:
            return n
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
    """

    analysis = await generate_structured_response(
        provider,
        f"Analyze this Python code and provide structured feedback:\n{code_sample}",
        CodeAnalysis,
    )

    print(f"Issues: {analysis.issues}")
    print(f"Suggestions: {analysis.suggestions}")
    print(f"Complexity Score: {analysis.complexity_score}\n")

    # Example 3: Streaming response
    print("=== Streaming Response ===")
    print("Streaming response: ", end="", flush=True)
    async for chunk in stream_response(
        provider, "Write a short poem about programming"
    ):
        print(chunk, end="", flush=True)
    print("\n")

    # Example 4: Using different providers
    print("=== Different Provider (Anthropic) ===")
    anthropic_config = LLMConfig(
        model="claude-3-haiku",  # Anthropic model
        api_key="your-anthropic-api-key-here",  # Set your actual API key
        temperature=0.1,
    )

    anthropic_provider = create_llm_provider(anthropic_config)
    response = await generate_response(
        anthropic_provider,
        "What are the key differences between Python and JavaScript?",
    )
    print(f"Anthropic Response: {response}\n")


if __name__ == "__main__":
    # Note: Set your API keys in environment variables or replace in the code
    # export OPENAI_API_KEY="your-key-here"
    # export ANTHROPIC_API_KEY="your-key-here"

    print("LLM Provider Example")
    print("Note: Set your API keys before running this example\n")

    asyncio.run(main())
