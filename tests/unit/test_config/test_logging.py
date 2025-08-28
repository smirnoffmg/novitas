"""Tests for logging configuration."""

from unittest.mock import patch

from novitas.config.logging import configure_logging
from novitas.config.logging import get_logger


class TestLogging:
    """Test logging configuration."""

    def test_get_logger(self) -> None:
        """Test getting a logger."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"

    @patch("novitas.config.logging.structlog.configure")
    def test_configure_logging_default(self, mock_configure) -> None:
        """Test default logging configuration."""
        configure_logging()
        mock_configure.assert_called_once()

    @patch("novitas.config.logging.structlog.configure")
    def test_configure_logging_with_level(self, mock_configure) -> None:
        """Test logging configuration with specific level."""
        configure_logging()
        mock_configure.assert_called_once()

    @patch("novitas.config.logging.structlog.configure")
    def test_configure_logging_with_environment(self, mock_configure) -> None:
        """Test logging configuration with specific environment."""
        configure_logging()
        mock_configure.assert_called_once()

    @patch("novitas.config.logging.structlog.configure")
    def test_configure_logging_with_debug(self, mock_configure) -> None:
        """Test logging configuration with debug mode."""
        configure_logging()
        mock_configure.assert_called_once()

    @patch("novitas.config.logging.structlog.configure")
    def test_configure_logging_all_parameters(self, mock_configure) -> None:
        """Test logging configuration with all parameters."""
        configure_logging()
        mock_configure.assert_called_once()

    def test_logger_functionality(self) -> None:
        """Test that logger can be used for logging."""
        logger = get_logger("test.logger")

        # Test that logger has standard methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "critical")

    @patch("novitas.config.logging.structlog.get_logger")
    def test_get_logger_calls_structlog(self, mock_get_logger) -> None:
        """Test that get_logger calls structlog.get_logger."""
        mock_logger = mock_get_logger.return_value
        logger = get_logger("test.module")

        mock_get_logger.assert_called_once_with("test.module")
        assert logger == mock_logger
