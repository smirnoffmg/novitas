#!/bin/bash

# Setup script for Docker Compose environment variables
# This script helps you set up the necessary environment variables for running Novitas with Docker Compose

echo "Setting up environment variables for Novitas Docker Compose..."

# Check if .env file exists
if [ -f .env ]; then
    echo "Warning: .env file already exists. This script will not overwrite it."
    echo "Please manually update your .env file with the following variables:"
else
    echo "Creating .env file..."
    cat > .env << EOF
# Environment
NOVITAS_ENVIRONMENT=development

# Database (PostgreSQL via Docker Compose)
DATABASE_URL=postgresql+asyncpg://novitas:novitas@localhost:5432/novitas

# Redis (via Docker Compose)
REDIS_URL=redis://localhost:6379/0

# LLM Providers (set these to your actual API keys)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# GitHub (optional)
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=owner/novitas

# Agent Configuration
MAX_AGENTS_PER_CYCLE=3
AGENT_TIMEOUT_SECONDS=300

# System Configuration
LOG_LEVEL=DEBUG
DEBUG=true

# Improvement Cycle Configuration
DAILY_IMPROVEMENT_ENABLED=true
IMPROVEMENT_BRANCH_PREFIX=daily-improvement

# Dry run mode (set to false for actual changes)
DRY_RUN=true
EOF
    echo "Created .env file successfully!"
fi

echo ""
echo "Required environment variables:"
echo "================================"
echo "ANTHROPIC_API_KEY - Your Anthropic API key (required for LLM functionality)"
echo "OPENAI_API_KEY    - Your OpenAI API key (optional, alternative to Anthropic)"
echo "GITHUB_TOKEN      - Your GitHub token (optional, for repository access)"
echo ""
echo "Optional environment variables:"
echo "================================"
echo "GITHUB_REPO                    - GitHub repository (default: owner/novitas)"
echo "MAX_AGENTS_PER_CYCLE           - Maximum agents per cycle (default: 3)"
echo "AGENT_TIMEOUT_SECONDS          - Agent timeout (default: 300)"
echo "LOG_LEVEL                      - Logging level (default: DEBUG)"
echo "DEBUG                          - Debug mode (default: true)"
echo "DAILY_IMPROVEMENT_ENABLED      - Enable daily improvements (default: true)"
echo "IMPROVEMENT_BRANCH_PREFIX      - Branch prefix (default: daily-improvement)"
echo "DRY_RUN                        - Dry run mode (default: true)"
echo ""
echo "To get API keys:"
echo "=================="
echo "Anthropic: https://console.anthropic.com/"
echo "OpenAI:    https://platform.openai.com/"
echo "GitHub:    https://github.com/settings/tokens"
echo ""
echo "After setting up your .env file, you can run:"
echo "  docker-compose up -d"
echo ""
echo "To run in development mode with local code:"
echo "  docker-compose up"
