"""Command-line interface for the Novitas AI system."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich.table import Table

from .config.logging import configure_logging
from .config.logging import get_logger
from .config.settings import settings

# Initialize CLI app
app = typer.Typer(
    name="novitas",
    help="Self-Improving AI Multi-Agent System",
    add_completion=False,
)

console = Console()
logger = get_logger(__name__)


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
) -> None:
    """Novitas - Self-Improving AI Multi-Agent System."""
    if verbose:
        settings.log_level = "DEBUG"
    if debug:
        settings.debug = True

    configure_logging()


@app.command()
def version() -> None:
    """Show the current version."""
    console.print(
        f"[bold blue]Novitas[/bold blue] version [bold]{settings.version}[/bold]"
    )


@app.command()
def config() -> None:
    """Show current configuration."""
    table = Table(title="Novitas Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Environment", settings.environment)
    table.add_row("Log Level", settings.log_level)
    table.add_row("Debug Mode", str(settings.debug))
    table.add_row("Database URL", settings.database_url)
    table.add_row("Redis URL", settings.redis_url)
    table.add_row("OpenAI Model", settings.openai_model)
    table.add_row("Max Agents per Cycle", str(settings.max_agents_per_cycle))
    table.add_row("Agent Timeout", f"{settings.agent_timeout_seconds}s")

    console.print(table)


@app.command()
async def improve(
    daily: bool = typer.Option(False, "--daily", help="Run daily improvement cycle"),
    force: bool = typer.Option(
        False, "--force", help="Force execution even if recent cycle exists"
    ),
    max_agents: Optional[int] = typer.Option(
        None, "--max-agents", help="Override max agents per cycle"
    ),
) -> None:
    """Run an improvement cycle."""
    try:
        from .main import run_improvement_cycle

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running improvement cycle...", total=None)

            # Override settings if provided
            if max_agents:
                settings.max_agents_per_cycle = max_agents

            await run_improvement_cycle(daily=daily, force=force)

            progress.update(task, description="Improvement cycle completed!")

        console.print(
            "[bold green]✓[/bold green] Improvement cycle completed successfully!"
        )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Improvement cycle failed: {e}")
        logger.error("Improvement cycle failed", error=str(e))
        raise typer.Exit(1)


@app.command()
async def agents(
    list: bool = typer.Option(False, "--list", "-l", help="List all agents"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    show_metrics: bool = typer.Option(
        False, "--metrics", "-m", help="Show performance metrics"
    ),
) -> None:
    """Manage agents."""
    try:
        from .database.connection import get_database_manager

        db_manager = get_database_manager()
        await db_manager.connect()

        if list:
            agents = await db_manager.get_all_agents()

            table = Table(title="Novitas Agents")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Type", style="yellow")
            table.add_column("Status", style="magenta")
            table.add_column("Version", style="blue")
            table.add_column("Last Active", style="white")

            for agent in agents:
                if status and agent.status != status:
                    continue

                table.add_row(
                    str(agent.id)[:8] + "...",
                    agent.name,
                    agent.agent_type.value,
                    agent.status.value,
                    str(agent.version),
                    agent.last_active.strftime("%Y-%m-%d %H:%M"),
                )

            console.print(table)

            if show_metrics:
                console.print("\n[bold]Performance Metrics:[/bold]")
                for agent in agents:
                    if agent.performance_metrics:
                        console.print(f"\n[cyan]{agent.name}:[/cyan]")
                        for metric, value in agent.performance_metrics.items():
                            console.print(f"  {metric}: {value}")

        await db_manager.disconnect()

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to manage agents: {e}")
        logger.error("Agent management failed", error=str(e))
        raise typer.Exit(1)


@app.command()
async def cycles(
    list: bool = typer.Option(False, "--list", "-l", help="List recent cycles"),
    count: int = typer.Option(10, "--count", "-c", help="Number of cycles to show"),
    show_details: bool = typer.Option(
        False, "--details", "-d", help="Show cycle details"
    ),
) -> None:
    """View improvement cycles."""
    try:
        from .database.connection import get_database_manager

        db_manager = get_database_manager()
        await db_manager.connect()

        if list:
            cycles = await db_manager.get_recent_cycles(count)

            table = Table(title=f"Recent Improvement Cycles (Last {count})")
            table.add_column("Cycle #", style="cyan")
            table.add_column("Start Time", style="green")
            table.add_column("Duration", style="yellow")
            table.add_column("Status", style="magenta")
            table.add_column("Agents Used", style="blue")
            table.add_column("Proposals", style="white")

            for cycle in cycles:
                duration = "N/A"
                if cycle.end_time:
                    duration = str(cycle.end_time - cycle.start_time).split(".")[0]

                status_style = "green" if cycle.success else "red"
                status_text = "✓ Success" if cycle.success else "✗ Failed"

                table.add_row(
                    str(cycle.cycle_number),
                    cycle.start_time.strftime("%Y-%m-%d %H:%M"),
                    duration,
                    f"[{status_style}]{status_text}[/{status_style}]",
                    str(len(cycle.agents_used)),
                    str(len(cycle.changes_proposed)),
                )

            console.print(table)

            if show_details and cycles:
                latest_cycle = cycles[0]
                console.print(
                    f"\n[bold]Latest Cycle Details (Cycle #{latest_cycle.cycle_number}):[/bold]"
                )
                console.print(f"  Start Time: {latest_cycle.start_time}")
                console.print(f"  End Time: {latest_cycle.end_time or 'In Progress'}")
                console.print(f"  Success: {latest_cycle.success}")
                if latest_cycle.error_message:
                    console.print(f"  Error: {latest_cycle.error_message}")
                console.print(f"  Agents Used: {len(latest_cycle.agents_used)}")
                console.print(
                    f"  Changes Proposed: {len(latest_cycle.changes_proposed)}"
                )
                console.print(
                    f"  Changes Accepted: {len(latest_cycle.changes_accepted)}"
                )

        await db_manager.disconnect()

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to view cycles: {e}")
        logger.error("Cycle viewing failed", error=str(e))
        raise typer.Exit(1)


@app.command()
async def db(
    migrate: bool = typer.Option(False, "--migrate", help="Run database migrations"),
    reset: bool = typer.Option(
        False, "--reset", help="Reset database (WARNING: destructive)"
    ),
    status: bool = typer.Option(False, "--status", help="Show database status"),
) -> None:
    """Database management commands."""
    try:
        from .database.connection import get_database_manager

        db_manager = get_database_manager()

        if status:
            await db_manager.connect()
            status_info = await db_manager.get_status()
            console.print(
                f"[bold green]✓[/bold green] Database connection: {status_info}"
            )
            await db_manager.disconnect()

        elif migrate:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running database migrations...", total=None)
                await db_manager.migrate()
                progress.update(task, description="Migrations completed!")
            console.print("[bold green]✓[/bold green] Database migrations completed!")

        elif reset:
            if not typer.confirm("This will delete all data. Are you sure?"):
                console.print("Database reset cancelled.")
                return

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Resetting database...", total=None)
                await db_manager.reset()
                progress.update(task, description="Database reset completed!")
            console.print("[bold green]✓[/bold green] Database reset completed!")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Database operation failed: {e}")
        logger.error("Database operation failed", error=str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
