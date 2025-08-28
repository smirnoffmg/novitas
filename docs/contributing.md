# Contributing to Novitas

Thank you for your interest in contributing to Novitas! This document provides guidelines for contributing to the project.

## Project Overview

Novitas is a self-improving AI multi-agent system that autonomously enhances its own codebase. The system runs daily improvement cycles, generating pull requests with proposed changes to code, tests, documentation, and configuration.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15 or higher
- Redis 7 or higher
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/novitas.git
   cd novitas
   ```

2. **Install dependencies**
   ```bash
   # Install uv (recommended package manager)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install project dependencies
   uv sync --dev
   ```

3. **Set up environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your configuration
   # Required: OPENAI_API_KEY, GITHUB_TOKEN
   ```

4. **Start services**
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d postgres redis
   
   # Run database migrations
   uv run novitas db migrate
   ```

5. **Run tests**
   ```bash
   uv run pytest
   ```

## Development Workflow

### Code Style

We use several tools to maintain code quality:

- **Ruff**: Linting and formatting
- **MyPy**: Type checking
- **Black**: Code formatting
- **Pre-commit**: Automated checks

Run quality checks:
```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type check
uv run mypy src/

# Run all checks
uv run pre-commit run --all-files
```

### Testing

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **Coverage**: Maintain minimum 80% coverage

Run tests:
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=novitas

# Run specific test categories
uv run pytest -m unit
uv run pytest -m integration
```

### Documentation

- **Docstrings**: All public functions and classes
- **Type Hints**: Comprehensive type annotations
- **README**: Project overview and setup
- **Architecture**: System design documentation

## Agent Development

### Creating New Agents

1. **Extend BaseAgent**
   ```python
   from novitas.agents.base import BaseAgent
   from novitas.core.models import AgentType, ChangeProposal
   
   class MySpecializedAgent(BaseAgent):
       def __init__(self, **kwargs):
           super().__init__(
               name="My Agent",
               agent_type=AgentType.CODE_AGENT,
               description="Specialized agent for specific tasks",
               **kwargs
           )
       
       async def _initialize_agent(self) -> None:
           # Agent-specific initialization
           pass
       
       async def _execute_agent(self, context: Dict[str, Any]) -> List[ChangeProposal]:
           # Agent-specific execution logic
           return []
   ```

2. **Create Prompt Template**
   - Add prompt file in `src/novitas/prompts/`
   - Follow existing prompt structure
   - Include clear instructions and constraints

3. **Add Tests**
   - Unit tests for agent logic
   - Integration tests for agent interactions
   - Mock external dependencies

### Agent Guidelines

- **Single Responsibility**: Each agent should have a focused purpose
- **Stateless Design**: Agents should be stateless, using database for persistence
- **Error Handling**: Robust error handling and recovery
- **Performance**: Efficient execution with timeout handling
- **Documentation**: Clear documentation of agent capabilities

## Database Development

### Models

- **Pydantic Models**: Use Pydantic for data validation
- **Migrations**: Create migrations for schema changes
- **Indexing**: Add appropriate database indexes
- **Constraints**: Use database constraints for data integrity

### Example Model
```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class MyModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## API Development

### External APIs

- **Rate Limiting**: Implement rate limiting for external APIs
- **Error Handling**: Handle API failures gracefully
- **Retry Logic**: Implement exponential backoff
- **Caching**: Cache responses when appropriate

### Example API Client
```python
from tenacity import retry, stop_after_attempt, wait_exponential

class APIClient:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def make_request(self, endpoint: str) -> Dict[str, Any]:
        # API request implementation
        pass
```

## Pull Request Process

### Before Submitting

1. **Run Tests**: Ensure all tests pass
2. **Code Quality**: Run linting and type checking
3. **Documentation**: Update relevant documentation
4. **Commit Messages**: Use conventional commit format

### Pull Request Template

- **Description**: Clear description of changes
- **Testing**: How to test the changes
- **Breaking Changes**: Any breaking changes
- **Related Issues**: Link to related issues

### Review Process

- **Code Review**: At least one approval required
- **CI Checks**: All automated checks must pass
- **Documentation**: Documentation updated as needed
- **Testing**: Adequate test coverage

## Release Process

### Versioning

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Steps

1. **Update Version**: Update version in `pyproject.toml`
2. **Update CHANGELOG**: Document changes
3. **Create Tag**: Create git tag for version
4. **Deploy**: Deploy to production
5. **Announce**: Announce release

## Community Guidelines

### Code of Conduct

- **Respect**: Treat all contributors with respect
- **Inclusion**: Welcome contributors from all backgrounds
- **Collaboration**: Work together constructively
- **Learning**: Help others learn and grow

### Communication

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Pull Requests**: Use pull requests for code contributions
- **Documentation**: Contribute to documentation improvements

## Getting Help

- **Documentation**: Check the docs/ directory
- **Issues**: Search existing issues
- **Discussions**: Ask questions in discussions
- **Contributors**: Reach out to maintainers

## License

By contributing to Novitas, you agree that your contributions will be licensed under the MIT License.
