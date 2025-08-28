"""Configuration settings for the Novitas AI system."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Version
    version: str = "0.1.0"

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://novitas:novitas@localhost:5432/novitas",
        description="PostgreSQL database URL",
    )

    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and session storage",
    )

    # OpenAI settings
    openai_api_key: Optional[str] = Field(
        default=None, description="OpenAI API key for LLM access"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview", description="OpenAI model to use for agents"
    )
    openai_temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Temperature for OpenAI API calls"
    )

    # GitHub settings
    github_token: Optional[str] = Field(
        default=None, description="GitHub token for repository access"
    )
    github_repo: str = Field(
        default="owner/novitas", description="GitHub repository in format owner/repo"
    )

    # Agent settings
    max_agents_per_cycle: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of agents to run per improvement cycle",
    )
    agent_timeout_seconds: int = Field(
        default=300, ge=60, description="Timeout for agent operations in seconds"
    )

    # System settings
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # Improvement cycle settings
    daily_improvement_enabled: bool = Field(
        default=True, description="Enable daily improvement cycles"
    )
    improvement_branch_prefix: str = Field(
        default="daily-improvement", description="Prefix for improvement branch names"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
