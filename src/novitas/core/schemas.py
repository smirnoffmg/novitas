"""Pydantic schemas for structured LLM responses."""

from pydantic import BaseModel
from pydantic import Field


class ImprovementProposal(BaseModel):
    """Schema for a single improvement proposal from LLM."""

    title: str = Field(description="Brief improvement title")
    description: str = Field(description="Detailed description of the improvement")
    reasoning: str = Field(description="Why this improvement is needed and beneficial")
    improvement_type: str = Field(
        description="Type of improvement",
        pattern="^(code_improvement|test_improvement|documentation_improvement|prompt_improvement|config_improvement)$",
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Confidence score between 0 and 1"
    )
    diff: str = Field(description="Code diff showing the exact changes needed")


class ImprovementAnalysis(BaseModel):
    """Schema for LLM analysis response containing multiple proposals."""

    proposals: list[ImprovementProposal] = Field(
        description="List of improvement proposals", min_length=1, max_length=3
    )


class AgentPrompt(BaseModel):
    """Schema for agent prompt generation."""

    prompt: str = Field(description="Generated prompt for the agent")
    reasoning: str = Field(default="", description="Reasoning for the prompt design")
    focus_areas: list[str] = Field(
        default_factory=list, description="Key focus areas for the agent"
    )


class ProposalEvaluation(BaseModel):
    """Schema for proposal evaluation response."""

    selected_proposals: list[str] = Field(
        description="IDs or descriptions of selected proposals"
    )
    reasoning: str = Field(default="", description="Reasoning for selection")
    criteria_used: list[str] = Field(
        default_factory=list, description="Evaluation criteria applied"
    )


class PerformanceAnalysis(BaseModel):
    """Schema for performance analysis response."""

    recommendations: list[str] = Field(description="Performance recommendations")
    agents_to_retire: list[str] = Field(
        default_factory=list, description="Agent IDs to retire"
    )
    agents_to_evolve: list[str] = Field(
        default_factory=list, description="Agent IDs to evolve"
    )
    new_agents_needed: list[str] = Field(
        default_factory=list, description="New agent types needed"
    )
    reasoning: str = Field(default="", description="Reasoning for recommendations")
