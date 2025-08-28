# Novitas 🤖

*Self-Improving AI Multi-Agent System*

[![CI](https://github.com/smirnoffmg/novitas/workflows/CI/badge.svg)](https://github.com/smirnoffmg/novitas/actions)
[![Daily Improvement](https://github.com/smirnoffmg/novitas/workflows/Daily%20Self-Improvement/badge.svg)](https://github.com/smirnoffmg/novitas/actions)
[![Coverage](https://codecov.io/gh/smirnoffmg/novitas/branch/main/graph/badge.svg)](https://codecov.io/gh/smirnoffmg/novitas)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Vision

Novitas is an autonomous AI system that continuously improves itself by generating daily improvements to its own code, tests, documentation, and architecture. Think of it as a self-evolving software organism that gets better over time through the collaborative intelligence of specialized AI agents.

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Daily Execution"
        GHA[GitHub Actions Trigger]
        GHA --> ORCH[Orchestrator Agent]
    end
    
    subgraph "Agent Ecosystem"
        ORCH --> CA[Code Agent]
        ORCH --> TA[Test Agent]  
        ORCH --> DA[Documentation Agent]
        ORCH --> PA[Prompt Agent]
        CA --> ORCH
        TA --> ORCH
        DA --> ORCH
        PA --> ORCH
    end
    
    subgraph "Persistence Layer"
        DB[(PostgreSQL)]
        REDIS[(Redis)]
        ORCH --> DB
        ORCH --> REDIS
    end
    
    subgraph "Output"
        ORCH --> PR[Pull Request]
        PR --> REVIEW[Human Review]
        REVIEW --> MERGE[Auto/Manual Merge]
    end
```

### 🎯 Core Principles

1. **Autonomous Evolution**: The system improves itself without human intervention
2. **Agent Specialization**: Each agent has specific expertise (code, tests, docs, etc.)
3. **Central Coordination**: Orchestrator prevents conflicts and ensures coherence
4. **Quality Gates**: All changes must pass tests, linting, and quality checks
5. **Human Oversight**: Transparent reasoning and human-reviewable pull requests
6. **Persistent Memory**: Agents learn from past decisions and maintain context

## 🧠 Agent Types

### 🎼 Orchestrator Agent

- **Role**: Central coordinator and decision maker
- **Responsibilities**:
  - Creates daily execution sessions
  - Assigns tasks to specialized agents
  - Resolves conflicts between proposed changes
  - Manages agent lifecycle (creation, retirement, archival)
  - Creates pull requests with consolidated changes

### 💻 Code Agent

- **Role**: Code improvement specialist
- **Responsibilities**:
  - Analyzes code quality and performance
  - Suggests refactoring and optimizations
  - Identifies bugs and potential issues
  - Proposes new features based on codebase analysis

### 🧪 Test Agent

- **Role**: Testing and quality assurance
- **Responsibilities**:
  - Improves test coverage
  - Adds missing test cases
  - Updates tests for code changes
  - Suggests testing strategies

### 📚 Documentation Agent

- **Role**: Documentation maintenance
- **Responsibilities**:
  - Updates README and documentation
  - Adds missing docstrings
  - Maintains API documentation
  - Creates architectural diagrams

### 🎯 Prompt Agent

- **Role**: Self-improvement of AI interactions
- **Responsibilities**:
  - Refines agent prompts for better performance
  - Updates system prompts based on outcomes
  - Optimizes LLM interactions

## 🔄 Daily Workflow

```mermaid
sequenceDiagram
    participant GHA as GitHub Actions
    participant ORCH as Orchestrator
    participant AGENTS as Agent Pool
    participant DB as Database
    participant GIT as Git/GitHub
    
    GHA->>ORCH: Trigger daily session
    ORCH->>DB: Create execution session
    ORCH->>ORCH: Analyze codebase
    ORCH->>AGENTS: Assign tasks
    
    loop For each agent
        AGENTS->>AGENTS: Execute assigned tasks
        AGENTS->>ORCH: Propose changes
    end
    
    ORCH->>ORCH: Evaluate & score changes
    ORCH->>ORCH: Resolve conflicts
    ORCH->>GIT: Create improvement branch
    ORCH->>GIT: Apply selected changes
    ORCH->>GIT: Create pull request
    ORCH->>DB: Update session status
```

## 🎮 Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (modern Python package manager)
- PostgreSQL 15+
- Redis 7+
- GitHub account with repository access

### 🚀 Quick Start

1. **Clone and Setup**

   ```bash
   git clone https://github.com/smirnoffmg/novitas.git
   cd novitas
   uv sync --all-extras
   ```

2. **Environment Configuration**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Dependencies**

   ```bash
   docker-compose up -d postgres redis
   ```

4. **Initialize System**

   ```bash
   uv run novitas init
   ```

5. **Run First Session**

   ```bash
   uv run novitas session start --dry-run
   ```

### 📋 Environment Variables

```bash
# Database
DB_URL=postgresql+asyncpg://novitas:password@localhost/novitas

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your-openai-key

# GitHub
GITHUB_TOKEN=your-github-token
GITHUB_REPOSITORY=smirnoffmg/novitas

# System
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🛠️ Commands

```bash
# System Management
uv run novitas init                    # Initialize new project
uv run novitas status                  # Show system status
uv run novitas config                  # Show configuration

# Agent Management
uv run novitas agent list              # List all agents
uv run novitas agent create            # Create new agent
uv run novitas agent retire <id>       # Retire an agent

# Session Management
uv run novitas session start           # Start improvement session
uv run novitas session list            # List recent sessions
uv run novitas session status <id>     # Show session details
```

## 📊 Monitoring & Observability

### 📈 Key Metrics

- **Agent Success Rate**: Percentage of successful tasks per agent
- **Change Acceptance Rate**: Percentage of changes that get merged
- **System Evolution**: Version progression and feature additions
- **Code Quality Trends**: Coverage, complexity, and quality metrics

### 🔍 Logging

- Structured logging with contextual information
- Agent decision trails and reasoning
- Task execution timelines
- Error tracking and debugging information

## 🧪 Development

### 🏃‍♂️ Running Tests

```bash
# Unit tests
uv run pytest tests/unit/

# Integration tests  
uv run pytest tests/integration/

# All tests with coverage
uv run pytest --cov=src/novitas --cov-report=html
```

### 🔧 Code Quality

```bash
# Linting and formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src/

# Security scan
uv run bandit -r src/
```

### 🏗️ Database Migrations

```bash
# Create migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head
```

## 📚 Implementation Phases

### 🚀 Phase 1: Foundation (Weeks 1-2)
- [x] Project structure and modern Python tooling
- [ ] Core domain models and database schema
- [ ] Base agent infrastructure
- [ ] CLI interface
- [ ] Basic orchestrator

### 🧠 Phase 2: Intelligence (Weeks 3-4)
- [ ] LLM provider integration
- [ ] Prompt engineering system
- [ ] Code analysis capabilities
- [ ] Change proposal generation
- [ ] Simple agent implementations

### 🔄 Phase 3: Automation (Weeks 5-6)
- [ ] GitHub Actions integration
- [ ] Automated PR creation
- [ ] Quality gate enforcement
- [ ] Session management
- [ ] Basic self-improvement loop

### 🌟 Phase 4: Evolution (Weeks 7-8)
- [ ] Agent performance tracking
- [ ] Dynamic agent creation/retirement
- [ ] Advanced conflict resolution
- [ ] Learning from outcomes
- [ ] Self-modifying prompts

### 🎯 Phase 5: Optimization (Weeks 9-10)
- [ ] Performance optimization
- [ ] Advanced analytics
- [ ] Multi-repository support
- [ ] Advanced agent behaviors
- [ ] Production hardening

## 🤝 Contributing

We welcome contributions from the community! However, keep in mind that Novitas is designed to improve itself autonomously. Here's how you can help:

### 🎭 For Humans
- **Bug Reports**: Found an issue? Please report it!
- **Feature Requests**: Have ideas? We'd love to hear them!
- **Code Reviews**: Help review agent-generated PRs
- **Documentation**: Improve human-readable docs

### 🤖 For Agents
- **Self-Improvement**: The primary contribution mechanism
- **Prompt Refinement**: Agents can improve their own prompts
- **New Agent Creation**: Orchestrator can create specialized agents

### 📖 Development Guidelines
1. Follow conventional commit format
2. Include reasoning in PR descriptions  
3. Ensure all tests pass
4. Update documentation as needed
5. Consider the impact on agent behavior

## 🔮 Future Vision

### 🌐 Multi-Repository Evolution
- Coordinate improvements across multiple projects
- Share learnings between different codebases
- Cross-pollinate successful patterns

### 🧬 Advanced Agent Evolution
- Genetic algorithm-inspired agent breeding
- Automatic specialization discovery
- Emergent behavior development

### 🏢 Enterprise Features
- Team-specific customization
- Compliance and governance controls
- Advanced security and auditing

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the concept of self-improving systems
- Built with modern Python ecosystem tools
- Powered by advances in large language models
- Community-driven development principles

---

**"The best way to predict the future is to create it... and then let it improve itself."** 🚀