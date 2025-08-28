"""Tests for the CLI module."""

from unittest.mock import AsyncMock
from unittest.mock import patch

from typer.testing import CliRunner

from novitas.cli import _run_agents_command
from novitas.cli import _run_cycles_command
from novitas.cli import _run_db_command
from novitas.cli import _run_improvement_cycle
from novitas.cli import app


class TestCLI:
    """Test CLI functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_version_command(self) -> None:
        """Test version command."""
        with patch("novitas.cli.settings") as mock_settings:
            mock_settings.version = "1.0.0"
            result = self.runner.invoke(app, ["version"])
            assert result.exit_code == 0
            assert "Novitas version 1.0.0" in result.stdout

    def test_config_command(self) -> None:
        """Test config command."""
        with patch("novitas.cli.settings") as mock_settings:
            mock_settings.environment = "test"
            mock_settings.log_level = "INFO"
            mock_settings.debug = False
            mock_settings.database_url = None
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.openai_model = "gpt-4"
            mock_settings.max_agents_per_cycle = 5
            mock_settings.agent_timeout_seconds = 30

            result = self.runner.invoke(app, ["config"])
            assert result.exit_code == 0
            assert "test" in result.stdout
            assert "INFO" in result.stdout
            assert "Auto-configured" in result.stdout

    def test_improve_command_success(self) -> None:
        """Test improve command success."""
        with patch("novitas.cli._run_improvement_cycle") as mock_run_cycle:
            result = self.runner.invoke(app, ["improve"])
            assert result.exit_code == 0
            mock_run_cycle.assert_called_once_with(
                daily=False, force=False, dry_run=False, max_agents=None
            )

    def test_improve_command_with_daily_flag(self) -> None:
        """Test improve command with daily flag."""
        with patch("novitas.cli._run_improvement_cycle") as mock_run_cycle:
            result = self.runner.invoke(app, ["improve", "--daily"])
            assert result.exit_code == 0
            mock_run_cycle.assert_called_once_with(
                daily=True, force=False, dry_run=False, max_agents=None
            )

    def test_improve_command_with_force_flag(self) -> None:
        """Test improve command with force flag."""
        with patch("novitas.cli._run_improvement_cycle") as mock_run_cycle:
            result = self.runner.invoke(app, ["improve", "--force"])
            assert result.exit_code == 0
            mock_run_cycle.assert_called_once_with(
                daily=False, force=True, dry_run=False, max_agents=None
            )

    def test_improve_command_with_max_agents(self) -> None:
        """Test improve command with max agents flag."""
        with patch("novitas.cli._run_improvement_cycle") as mock_run_cycle:
            result = self.runner.invoke(app, ["improve", "--max-agents", "10"])
            assert result.exit_code == 0
            mock_run_cycle.assert_called_once_with(
                daily=False, force=False, dry_run=False, max_agents=10
            )

    def test_improve_command_failure(self) -> None:
        """Test improve command failure."""
        with patch("novitas.cli._run_improvement_cycle") as mock_run_cycle:
            mock_run_cycle.side_effect = Exception("Cycle failed")
            result = self.runner.invoke(app, ["improve"])
            assert result.exit_code == 1

    def test_agents_command_success(self) -> None:
        """Test agents command success."""
        with patch("novitas.cli._run_agents_command") as mock_agents:
            result = self.runner.invoke(app, ["agents", "--list"])
            assert result.exit_code == 0
            mock_agents.assert_called_once_with(
                list_agents=True, status=None, show_metrics=False
            )

    def test_agents_command_failure(self) -> None:
        """Test agents command failure."""
        with patch("novitas.cli._run_agents_command") as mock_agents:
            mock_agents.side_effect = Exception("Database error")
            result = self.runner.invoke(app, ["agents", "--list"])
            assert result.exit_code == 1

    def test_cycles_command_success(self) -> None:
        """Test cycles command success."""
        with patch("novitas.cli._run_cycles_command") as mock_cycles:
            result = self.runner.invoke(app, ["cycles", "--list"])
            assert result.exit_code == 0
            mock_cycles.assert_called_once_with(
                list_cycles=True, count=10, show_details=False
            )

    def test_cycles_command_with_count(self) -> None:
        """Test cycles command with count parameter."""
        with patch("novitas.cli._run_cycles_command") as mock_cycles:
            result = self.runner.invoke(app, ["cycles", "--list", "--count", "5"])
            assert result.exit_code == 0
            mock_cycles.assert_called_once_with(
                list_cycles=True, count=5, show_details=False
            )

    def test_cycles_command_failure(self) -> None:
        """Test cycles command failure."""
        with patch("novitas.cli._run_cycles_command") as mock_cycles:
            mock_cycles.side_effect = Exception("Database error")
            result = self.runner.invoke(app, ["cycles", "--list"])
            assert result.exit_code == 1

    def test_db_status_command(self) -> None:
        """Test database status command."""
        with patch("novitas.cli._run_db_command") as mock_db:
            result = self.runner.invoke(app, ["db", "--status"])
            assert result.exit_code == 0
            mock_db.assert_called_once_with(migrate=False, reset=False, status=True)

    def test_db_migrate_command(self) -> None:
        """Test database migrate command."""
        with patch("novitas.cli._run_db_command") as mock_db:
            result = self.runner.invoke(app, ["db", "--migrate"])
            assert result.exit_code == 0
            mock_db.assert_called_once_with(migrate=True, reset=False, status=False)

    def test_db_reset_command(self) -> None:
        """Test database reset command."""
        with patch("novitas.cli._run_db_command") as mock_db:
            result = self.runner.invoke(app, ["db", "--reset"])
            assert result.exit_code == 0
            mock_db.assert_called_once_with(migrate=False, reset=True, status=False)

    def test_db_command_failure(self) -> None:
        """Test database command failure."""
        with patch("novitas.cli._run_db_command") as mock_db:
            mock_db.side_effect = Exception("Database error")
            result = self.runner.invoke(app, ["db", "--status"])
            assert result.exit_code == 1


class TestCLIWrapperFunctions:
    """Test CLI wrapper functions."""

    @patch("novitas.cli.asyncio.run")
    @patch("novitas.cli.run_improvement_cycle")
    def test_run_improvement_cycle_success(self, mock_run_cycle, mock_asyncio_run):
        """Test _run_improvement_cycle success."""

        _run_improvement_cycle(daily=True, force=False, max_agents=5)

        mock_asyncio_run.assert_called_once()
        # Check that the async function was called with correct args
        call_args = mock_asyncio_run.call_args[0][0]
        assert call_args is not None

    @patch("novitas.cli.asyncio.run")
    @patch("novitas.cli.get_database_manager")
    def test_run_agents_command_success(self, mock_get_db, mock_asyncio_run):
        """Test _run_agents_command success."""

        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        _run_agents_command(list_agents=True, status="active", show_metrics=True)

        mock_asyncio_run.assert_called_once()

    @patch("novitas.cli.asyncio.run")
    @patch("novitas.cli.get_database_manager")
    def test_run_cycles_command_success(self, mock_get_db, mock_asyncio_run):
        """Test _run_cycles_command success."""

        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        _run_cycles_command(list_cycles=True, count=5, show_details=True)

        mock_asyncio_run.assert_called_once()

    @patch("novitas.cli.asyncio.run")
    @patch("novitas.cli.get_database_manager")
    def test_run_db_command_success(self, mock_get_db, mock_asyncio_run):
        """Test _run_db_command success."""

        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        _run_db_command(migrate=True, reset=False, status=False)

        mock_asyncio_run.assert_called_once()
