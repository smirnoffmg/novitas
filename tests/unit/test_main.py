"""Tests for the main module."""

from unittest.mock import patch

import pytest

from novitas.core.exceptions import ImprovementCycleError
from novitas.main import run_improvement_cycle


class TestMain:
    """Test main module functionality."""

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_success(self) -> None:
        """Test successful improvement cycle execution."""
        # The current implementation is just a skeleton, so we test the basic flow
        await run_improvement_cycle(daily=False, force=False)
        # If we get here without exception, the test passes

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_failure(self) -> None:
        """Test improvement cycle execution failure."""
        # Mock the ImprovementCycle.complete method to raise an exception on the first call
        with patch("novitas.main.ImprovementCycle") as mock_cycle_class:
            mock_cycle = mock_cycle_class.return_value
            # Make the first call to complete raise an exception
            mock_cycle.complete.side_effect = [Exception("Test failure"), None]

            with pytest.raises(ImprovementCycleError, match="Improvement cycle failed"):
                await run_improvement_cycle(daily=False, force=False)

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_daily_mode(self) -> None:
        """Test improvement cycle in daily mode."""
        # The current implementation accepts daily parameter but doesn't use it
        await run_improvement_cycle(daily=True, force=False)
        # If we get here without exception, the test passes

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_force_mode(self) -> None:
        """Test improvement cycle in force mode."""
        # The current implementation accepts force parameter but doesn't use it
        await run_improvement_cycle(daily=False, force=True)
        # If we get here without exception, the test passes

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_with_cycle_creation(self) -> None:
        """Test improvement cycle with cycle creation."""
        # The current implementation creates an ImprovementCycle
        with patch("novitas.main.ImprovementCycle") as mock_cycle_class:
            mock_cycle = mock_cycle_class.return_value

            await run_improvement_cycle(daily=False, force=False)

            # Verify that the cycle was created
            mock_cycle_class.assert_called_once()
            # Verify that complete was called with success=True
            mock_cycle.complete.assert_called_once_with(success=True)

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_logging(self) -> None:
        """Test that improvement cycle logs appropriately."""
        with patch("novitas.main.logger") as mock_logger:
            await run_improvement_cycle(daily=False, force=False)

            # Verify that logging was called
            assert mock_logger.info.called
            assert mock_logger.error.call_count == 0  # No errors in success case

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_error_logging(self) -> None:
        """Test that improvement cycle logs errors appropriately."""
        with patch("novitas.main.ImprovementCycle") as mock_cycle_class:
            mock_cycle = mock_cycle_class.return_value
            # Make the first call to complete raise an exception
            mock_cycle.complete.side_effect = [Exception("Test failure"), None]

            with patch("novitas.main.logger") as mock_logger:
                with pytest.raises(ImprovementCycleError):
                    await run_improvement_cycle(daily=False, force=False)

                # Verify that error logging was called
                assert mock_logger.error.called

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_cycle_completion(self) -> None:
        """Test that the cycle is properly completed."""
        with patch("novitas.main.ImprovementCycle") as mock_cycle_class:
            mock_cycle = mock_cycle_class.return_value

            await run_improvement_cycle(daily=False, force=False)

            # Verify that the cycle was completed successfully
            mock_cycle.complete.assert_called_once_with(success=True)

    @pytest.mark.asyncio
    async def test_run_improvement_cycle_cycle_completion_on_error(self) -> None:
        """Test that the cycle is properly completed on error."""
        with patch("novitas.main.ImprovementCycle") as mock_cycle_class:
            mock_cycle = mock_cycle_class.return_value
            # Make the first call to complete raise an exception
            mock_cycle.complete.side_effect = [Exception("Test failure"), None]

            with pytest.raises(ImprovementCycleError):
                await run_improvement_cycle(daily=False, force=False)

            # Verify that the cycle was completed with failure
            # The mock should have been called twice: once for success (which failed) and once for failure
            assert mock_cycle.complete.call_count == 2
            # Check the second call (the failure call)
            mock_cycle.complete.assert_any_call(
                success=False, error_message="Test failure"
            )
