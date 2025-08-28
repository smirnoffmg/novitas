"""Configuration settings for the Novitas AI system following 12-factor app principles."""

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings following 12-factor app methodology.

    Factor III: Config - Store config in the environment
    Factor IV: Backing services - Treat backing services as attached resources
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 12-factor: Config - Allow environment variable overrides
    )

    # Version
    version: str = "0.1.0"

    # Environment (12-factor: Config)
    environment: str = Field(
        default="development",
        description="Environment (development, testing, staging, production)",
        alias="NOVITAS_ENVIRONMENT",
    )

    # Database configuration (12-factor: Backing services)
    # Allow explicit database URL override
    database_url: str | None = Field(
        default=None,
        description="Database URL (overrides auto-configuration)",
        alias="DATABASE_URL",
    )

    # Database connection parameters (used when DATABASE_URL not provided)
    database_host: str = Field(
        default="localhost",
        description="Database host",
        alias="DATABASE_HOST",
    )
    database_port: int = Field(
        default=5432,
        description="Database port",
        alias="DATABASE_PORT",
    )
    database_name: str = Field(
        default="novitas",
        description="Database name",
        alias="DATABASE_NAME",
    )
    database_user: str = Field(
        default="novitas",
        description="Database username",
        alias="DATABASE_USER",
    )
    database_password: str = Field(
        default="novitas",
        description="Database password",
        alias="DATABASE_PASSWORD",
    )

    # Redis configuration (12-factor: Backing services)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and session storage",
        alias="REDIS_URL",
    )

    # OpenAI configuration (12-factor: Backing services)
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key for LLM access",
        alias="OPENAI_API_KEY",
    )

    # Anthropic configuration (12-factor: Backing services)
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key for LLM access",
        alias="ANTHROPIC_API_KEY",
    )

    # GitHub configuration (12-factor: Backing services)
    github_token: str | None = Field(
        default=None,
        description="GitHub token for repository access",
        alias="GITHUB_TOKEN",
    )
    github_repo: str = Field(
        default="owner/novitas",
        description="GitHub repository in format owner/repo",
        alias="GITHUB_REPO",
    )

    # Agent configuration (12-factor: Config)
    max_agents_per_cycle: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of agents to run per improvement cycle",
        alias="MAX_AGENTS_PER_CYCLE",
    )
    agent_timeout_seconds: int = Field(
        default=300,
        ge=60,
        description="Timeout for agent operations in seconds",
        alias="AGENT_TIMEOUT_SECONDS",
    )

    # System configuration (12-factor: Config)
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        alias="LOG_LEVEL",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        alias="DEBUG",
    )

    # Improvement cycle configuration (12-factor: Config)
    daily_improvement_enabled: bool = Field(
        default=True,
        description="Enable daily improvement cycles",
        alias="DAILY_IMPROVEMENT_ENABLED",
    )
    improvement_branch_prefix: str = Field(
        default="daily-improvement",
        description="Prefix for improvement branch names",
        alias="IMPROVEMENT_BRANCH_PREFIX",
    )
    dry_run: bool = Field(
        default=False,
        description="Run in dry-run mode (no actual changes)",
        alias="NOVITAS_DRY_RUN",
    )

    @property
    def resolved_database_url(self) -> str:
        """
        Get the resolved database URL based on environment.

        Follows 12-factor app principles:
        - Factor III: Config - Environment-based configuration
        - Factor IV: Backing services - Treat database as attached resource
        """
        # If DATABASE_URL is explicitly set, use it (12-factor: Config)
        if self.database_url:
            return self.database_url

        # Auto-configure based on environment (12-factor: Dev/prod parity)
        if self.environment in ["development", "testing"]:
            # Use SQLite for development and testing (fast, no external dependencies)
            return "sqlite+aiosqlite:///./novitas.db"
        else:
            # Use PostgreSQL for staging and production (robust, scalable)
            return f"postgresql+asyncpg://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == "staging"

    def validate_config(self) -> None:
        """
        Validate configuration following 12-factor app principles.

        Ensures all required configuration is present for the current environment.
        """
        errors = []

        # Validate required configuration for production
        if self.is_production:
            if not self.openai_api_key:
                errors.append("OPENAI_API_KEY is required in production")
            if not self.github_token:
                errors.append("GITHUB_TOKEN is required in production")
            if not self.database_url and not all(
                [
                    self.database_host,
                    self.database_name,
                    self.database_user,
                    self.database_password,
                ]
            ):
                errors.append("Database configuration is incomplete for production")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")


# Global settings instance
settings = Settings()

# Validate configuration on import
try:
    settings.validate_config()
except ValueError as e:
    import warnings

    warnings.warn(f"Configuration warning: {e}", stacklevel=2)
