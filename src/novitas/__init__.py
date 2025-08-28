"""Novitas - Self-Improving AI Multi-Agent System."""

__version__ = "0.1.0"
__author__ = "Maksim Smirnov"
__email__ = "smirnoffmg@gmail.com"

from .config.logging import configure_logging
from .config.logging import get_logger
from .config.settings import settings

# Configure logging on import
configure_logging()

__all__ = [
    "configure_logging",
    "get_logger",
    "settings",
]
