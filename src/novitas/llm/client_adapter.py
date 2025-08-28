"""Adapter to make LLMProvider compatible with LLMClient protocol."""

from typing import Any

from ..core.models import ChangeProposal
from ..core.protocols import LLMClient
from .provider import LLMProvider


class LLMClientAdapter(LLMClient):
    """Adapter to make LLMProvider compatible with LLMClient protocol."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the adapter with an LLM provider.

        Args:
            llm_provider: The LLM provider to adapt
        """
        self.llm_provider = llm_provider

    async def generate_response(
        self, prompt: str, context: dict[str, Any] | None = None  # noqa: ARG002
    ) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            context: Additional context (currently unused)

        Returns:
            The generated response
        """
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_provider.ainvoke(messages)
        return response.content if hasattr(response, "content") else str(response)

    async def evaluate_proposal(self, proposal: ChangeProposal) -> float:
        """Evaluate a change proposal and return a score.

        Args:
            proposal: The change proposal to evaluate

        Returns:
            Evaluation score between 0 and 1
        """
        # For now, return the confidence score from the proposal
        # In a real implementation, this would use the LLM to evaluate
        return proposal.confidence_score

    async def analyze_code(self, code: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze code and return insights.

        Args:
            code: The code to analyze
            context: Additional context for analysis

        Returns:
            Analysis results
        """
        prompt = (
            f"Analyze this code and provide insights:\n\n{code}\n\nContext: {context}"
        )
        response = await self.generate_response(prompt, context)
        return {"analysis": response, "code_length": len(code)}
