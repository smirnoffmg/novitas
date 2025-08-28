"""Logging configuration for the Novitas AI system."""

import logging
from typing import Any

import structlog
from structlog.processors import JSONRenderer
from structlog.processors import TimeStamper
from structlog.stdlib import LoggerFactory

from .settings import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""

    # Configure standard library logging first

    # Set the log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger to show logs
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        force=True,  # Override any existing configuration
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                JSONRenderer()
                if settings.environment == "production"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


def log_agent_action(
    logger: Any,
    agent_id: str,
    action: str,
    details: dict[str, Any],
    success: bool = True,
) -> None:
    """Log an agent action with structured data.

    Args:
        logger: Logger instance
        agent_id: ID of the agent performing the action
        action: Description of the action
        details: Additional details about the action
        success: Whether the action was successful
    """
    logger.info(
        "agent_action",
        agent_id=agent_id,
        action=action,
        details=details,
        success=success,
    )


def log_improvement_cycle(
    logger: Any,
    cycle_id: str,
    agents_used: int,
    changes_proposed: int,
    success: bool = True,
) -> None:
    """Log an improvement cycle summary.

    Args:
        logger: Logger instance
        cycle_id: Unique identifier for the improvement cycle
        agents_used: Number of agents that participated
        changes_proposed: Number of changes proposed
        success: Whether the cycle was successful
    """
    logger.info(
        "improvement_cycle",
        cycle_id=cycle_id,
        agents_used=agents_used,
        changes_proposed=changes_proposed,
        success=success,
    )
