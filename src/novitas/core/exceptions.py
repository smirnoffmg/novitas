"""Custom exceptions for the Novitas AI system."""


class NovitasError(Exception):
    """Base exception for all Novitas errors."""

    pass


class AgentError(NovitasError):
    """Base exception for agent-related errors."""

    pass


class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out."""

    pass


class AgentCommunicationError(AgentError):
    """Raised when there's an error in agent communication."""

    pass


class AgentStateError(AgentError):
    """Raised when there's an error with agent state."""

    pass


class DatabaseError(NovitasError):
    """Base exception for database-related errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when there's an error connecting to the database."""

    pass


class DatabaseMigrationError(DatabaseError):
    """Raised when there's an error during database migration."""

    pass


class ImprovementCycleError(NovitasError):
    """Base exception for improvement cycle errors."""

    pass


class CycleTimeoutError(ImprovementCycleError):
    """Raised when an improvement cycle times out."""

    pass


class CycleValidationError(ImprovementCycleError):
    """Raised when there's an error validating an improvement cycle."""

    pass


class ChangeProposalError(NovitasError):
    """Base exception for change proposal errors."""

    pass


class InvalidChangeProposalError(ChangeProposalError):
    """Raised when a change proposal is invalid."""

    pass


class ChangeConflictError(ChangeProposalError):
    """Raised when there's a conflict between change proposals."""

    pass


class ConfigurationError(NovitasError):
    """Raised when there's an error with system configuration."""

    pass


class GitHubError(NovitasError):
    """Base exception for GitHub-related errors."""

    pass


class GitHubAuthenticationError(GitHubError):
    """Raised when there's an authentication error with GitHub."""

    pass


class GitHubAPIError(GitHubError):
    """Raised when there's an error with the GitHub API."""

    pass


class PromptError(NovitasError):
    """Base exception for prompt-related errors."""

    pass


class PromptTemplateError(PromptError):
    """Raised when there's an error with prompt templates."""

    pass


class PromptValidationError(PromptError):
    """Raised when a prompt fails validation."""

    pass


class LLMError(NovitasError):
    """Base exception for LLM-related errors."""

    pass


class LLMProviderError(LLMError):
    """Raised when there's an error with LLM provider operations."""

    pass


class LLMResponseError(LLMError):
    """Raised when there's an error with LLM response processing."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when an LLM operation times out."""

    pass
