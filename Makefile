# Novitas Makefile - Laconic and efficient

.PHONY: help install test lint format clean db-test config-list config-validate config-setup demo

# Default target
help:
	@echo "Novitas Development Commands:"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run all tests (fast unit tests only)"
	@echo "  test-unit  - Run unit tests only"
	@echo "  test-db    - Run database tests only"
	@echo "  test-fast  - Run fast tests only (skip slow/integration)"
	@echo "  lint       - Run linters (ruff, mypy)"
	@echo "  format     - Format code (ruff format)"
	@echo "  clean      - Clean cache and temporary files"
	@echo "  db-test    - Run database layer test"
	@echo ""
	@echo "12-Factor Configuration Commands:"
	@echo "  config-list     - List available environments"
	@echo "  config-validate - Validate environment config (ENV=<env>)"
	@echo "  config-setup    - Setup environment config (ENV=<env>)"
	@echo ""
	@echo "Demo Commands:"
	@echo "  demo           - Run dry-run improvement cycle on current codebase"

# Install dependencies
install:
	uv sync --all-extras

# 12-Factor Configuration Management
config-list:
	uv run python scripts/config.py list

config-validate:
	@echo "Usage: make config-validate ENV=<environment>"
	@echo "Example: make config-validate ENV=development"
	@if [ -z "$(ENV)" ]; then echo "Error: ENV variable is required"; exit 1; fi
	uv run python scripts/config.py validate $(ENV)

config-setup:
	@echo "Usage: make config-setup ENV=<environment>"
	@echo "Example: make config-setup ENV=development"
	@if [ -z "$(ENV)" ]; then echo "Error: ENV variable is required"; exit 1; fi
	uv run python scripts/config.py setup $(ENV)

# Run all tests (fast unit tests only)
test:
	uv run pytest tests/ -v --no-cov -m "not integration and not slow"

# Run unit tests only (fast)
test-unit:
	uv run pytest tests/unit/ -v -m "not integration and not slow"

# Run database tests only
test-db:
	uv run pytest tests/unit/test_database/ -v -m "not integration and not slow"

# Run fast tests only (skip slow/integration tests)
test-fast:
	uv run pytest tests/unit/ -v -m "not integration and not slow" --tb=short -x

# Run linters
lint:
	uv run ruff check .
	uv run mypy src/

# Format code
format:
	uv run ruff format .

# Clean cache and temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Run database layer test
db-test:
	uv run pytest tests/unit/test_database/test_simple.py::test_database_basic_operations -v --no-cov

# Run demo (dry-run improvement cycle)
demo:
	@echo "Starting Novitas AI System Demo (Dry-Run Mode)..."
	@echo "This will analyze the current codebase and suggest improvements."
	@echo "No actual changes will be made."
	@echo ""
	LOG_LEVEL=INFO DEBUG=true uv run python -m novitas.main
