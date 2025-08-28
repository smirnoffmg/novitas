# Novitas Makefile

.PHONY: help install test lint format clean config demo

help:
	@echo "install  - Install dependencies"
	@echo "test     - Run unit tests"
	@echo "test-fast - Run tests with 10s timeout"
	@echo "lint     - Run linters"
	@echo "format   - Format code"
	@echo "clean    - Clean cache files"
	@echo "config   - Config management (ENV=<env>)"
	@echo "demo     - Run AI demo"

install:
	uv sync --all-extras

test:
	uv run pytest tests/unit/ -v -m "not integration and not slow" --timeout=30 --timeout-method=thread

test-fast:
	uv run pytest tests/unit/ -v -m "not integration and not slow" --timeout=10 --timeout-method=thread

lint:
	uv run ruff check .
	uv run bandit -r src/ --skip B404,B603,B608

format:
	uv run ruff format .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

config:
	@if [ -z "$(ENV)" ]; then echo "Usage: make config ENV=<env>"; exit 1; fi
	uv run python scripts/config.py setup $(ENV)

demo:
	LOG_LEVEL=INFO uv run python -m novitas.main
