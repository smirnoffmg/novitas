"""Main module for the Novitas AI system."""

import asyncio
from uuid import uuid4

from .agents.orchestrator import OrchestratorAgent
from .config.logging import configure_logging
from .config.logging import get_logger
from .config.settings import settings
from .core.exceptions import ImprovementCycleError
from .core.models import ImprovementCycle
from .database.connection import get_database_manager
from .messaging import get_message_broker

logger = get_logger(__name__)


async def initialize_system_components():
    """Initialize system components (database, message broker, LLM)."""
    # Check for available LLM providers
    available_providers = {}
    if settings.anthropic_api_key:
        available_providers["anthropic"] = {
            "api_key": settings.anthropic_api_key,
        }
    if settings.openai_api_key:
        available_providers["openai"] = {
            "api_key": settings.openai_api_key,
        }

    if not available_providers:
        logger.error("No LLM provider configured")
        logger.info("Please set either ANTHROPIC_API_KEY or OPENAI_API_KEY")
        logger.info("Example: export ANTHROPIC_API_KEY='your-api-key-here'")
        logger.info("Or: export OPENAI_API_KEY='your-api-key-here'")
        logger.info("You can get API keys at:")
        logger.info("  - Anthropic: https://console.anthropic.com/")
        logger.info("  - OpenAI: https://platform.openai.com/")
        raise ImprovementCycleError("No LLM provider configured")

    logger.info(f"Available LLM providers: {list(available_providers.keys())}")

    # Initialize database manager
    logger.info("Initializing database manager...")
    database_manager = get_database_manager()
    await database_manager.connect()
    logger.info("Database manager initialized successfully")

    # Initialize message broker
    logger.info("Initializing message broker...")
    message_broker = get_message_broker()
    # Skip message broker connection for demo to avoid potential deadlock
    # await message_broker.connect()
    logger.info("Message broker initialization skipped for demo")

    return database_manager, message_broker, available_providers


async def create_orchestrator_agent(
    database_manager, message_broker, available_providers
):
    """Create and initialize the orchestrator agent."""
    logger.info("Creating Orchestrator Agent...")

    # Let the Orchestrator decide which LLM provider to use
    logger.info("Orchestrator will select the best LLM provider and model...")

    orchestrator = OrchestratorAgent(
        database_manager=database_manager,
        available_llm_providers=available_providers,
        message_broker=message_broker,
        agent_id=uuid4(),
        name="Novitas Orchestrator",
        description="Central orchestrator for managing specialized agents",
        prompt="""You are the Novitas Orchestrator Agent, responsible for coordinating
        specialized agents to improve the codebase. You create, manage, and coordinate
        agents for code analysis, documentation, and testing. Always think strategically
        and provide clear, actionable plans. When creating agents, provide detailed,
        specific prompts that will make them effective at their tasks.
        
        You are also responsible for selecting the best LLM provider and model for each task
        based on the available options. Consider factors like model capabilities, cost,
        and performance when making your decisions.""",
    )

    logger.info(f"Created Orchestrator Agent: {orchestrator.name}")

    # Initialize the orchestrator
    logger.info("Initializing Orchestrator...")
    await orchestrator.initialize()
    logger.info("Orchestrator initialized successfully")

    return orchestrator


async def run_improvement_cycle(
    daily: bool = False,
    force: bool = False,  # noqa: ARG001
    dry_run: bool = False,
) -> None:
    print("DEMO: Entered run_improvement_cycle function")
    """Run a complete improvement cycle.

    Args:
        daily: Whether this is a daily improvement cycle
        force: Force execution even if recent cycle exists
        dry_run: Run in dry-run mode (no actual changes)
    """
    print("DEMO: About to configure logging")
    # Configure logging
    configure_logging()
    print("DEMO: Logging configured in improvement cycle")

    cycle_id = uuid4()
    cycle = ImprovementCycle(
        id=cycle_id,
        cycle_number=1,  # TODO: Get from database
    )

    print(
        f"DEMO: Starting improvement cycle - cycle_id: {cycle_id}, daily: {daily}, dry_run: {dry_run}"
    )
    logger.info(
        "Starting improvement cycle", cycle_id=cycle_id, daily=daily, dry_run=dry_run
    )

    try:
        print("DEMO: STEP 1: About to initialize system components")
        logger.info("STEP 1: About to initialize system components")
        # Initialize system components
        database_manager, message_broker, available_providers = (
            await initialize_system_components()
        )
        logger.info("STEP 1 COMPLETE: System components initialized")

        logger.info("STEP 2: About to create orchestrator agent")
        # Create orchestrator agent
        orchestrator = await create_orchestrator_agent(
            database_manager, message_broker, available_providers
        )
        logger.info("STEP 2 COMPLETE: Orchestrator agent created")

        logger.info("STEP 3: About to create specialized agents")
        # Create specialized agents for code analysis
        logger.info("Creating specialized agents for code analysis...")

        logger.info("Creating Code Quality Analyzer...")
        code_agent_id = await orchestrator.create_specialized_agent(
            agent_type="code_agent",
            name="Code Quality Analyzer",
            description="Analyzes code quality and suggests improvements",
            capabilities=[
                "code_analysis",
                "type_hints",
                "docstrings",
                "best_practices",
            ],
        )
        logger.info(f"Created Code Agent: {code_agent_id}")

        logger.info("Creating Documentation Specialist...")
        doc_agent_id = await orchestrator.create_specialized_agent(
            agent_type="documentation_agent",
            name="Documentation Specialist",
            description="Improves documentation and README files",
            capabilities=["documentation", "readme", "api_docs", "examples"],
        )
        logger.info(f"Created Documentation Agent: {doc_agent_id}")
        logger.info("STEP 3 COMPLETE: Specialized agents created")

        logger.info("STEP 4: About to show managed agents")
        # Show managed agents
        logger.info(f"Managed Agents: {len(orchestrator.managed_agents)}")
        for _agent_id, agent_data in orchestrator.managed_agents.items():
            logger.info(f"  - {agent_data['name']} ({agent_data['type']})")
            logger.info(f"    Created: {agent_data['created_at']}")
            logger.info(f"    Capabilities: {', '.join(agent_data['capabilities'])}")
            logger.info(f"    Performance: {agent_data['performance']:.2f}")
        logger.info("STEP 4 COMPLETE: Managed agents displayed")

        logger.info("STEP 5: About to run improvement cycle")
        # Run improvement cycle on current codebase
        logger.info("Running improvement cycle on current codebase...")
        context = {
            "action": "improvement_cycle",
            "files_to_analyze": [
                "src/novitas/agents/orchestrator.py",
                "src/novitas/core/models.py",
                "README.md",
            ],
            "dry_run": dry_run,
        }

        logger.info("STEP 5.1: About to execute orchestrator")
        logger.info("Executing improvement cycle...")
        proposals = await orchestrator.execute(context)
        logger.info("STEP 5.1 COMPLETE: Orchestrator executed")

        print(f"\n🎉 DEMO SUCCESS! Generated {len(proposals)} improvement proposals:")
        logger.info(f"Generated {len(proposals)} improvement proposals:")
        for i, proposal in enumerate(proposals, 1):
            print(f"\n📋 PROPOSAL {i}:")
            print(f"   Title: {proposal.description}")
            print(f"   File: {proposal.file_path}")
            print(f"   Type: {proposal.improvement_type}")
            print(f"   Confidence: {proposal.confidence_score:.2f}")
            print(f"   Reasoning: {proposal.reasoning[:200]}...")
            if "diff" in proposal.proposed_changes:
                print("   Diff:")
                print(f"   {proposal.proposed_changes['diff']}")
            else:
                print(f"   Changes: {proposal.proposed_changes}")

            logger.info(f"  {i}. {proposal.description}")
            logger.info(f"     File: {proposal.file_path}")
            logger.info(f"     Type: {proposal.improvement_type}")
            logger.info(f"     Confidence: {proposal.confidence_score:.2f}")
            logger.info(f"     Reasoning: {proposal.reasoning[:150]}...")

        # Monitor agent performance
        logger.info("Monitoring agent performance...")
        performance_report = await orchestrator.monitor_agent_performance()
        logger.info(f"Total agents: {performance_report['total_agents']}")
        logger.info(
            f"Performance data: {len(performance_report['agent_performance'])} agents tracked"
        )

        # Show performance metrics
        logger.info("Orchestrator Performance Metrics:")
        metrics = orchestrator.get_performance_metrics()
        for key, value in metrics.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")

        # Cleanup
        await orchestrator.cleanup()
        # Skip message broker disconnect for demo
        # await message_broker.disconnect()
        await database_manager.disconnect()

        logger.info("Improvement cycle completed successfully", cycle_id=cycle_id)
        cycle.complete(success=True)

    except Exception as e:
        logger.error("Improvement cycle failed", cycle_id=cycle_id, error=str(e))
        cycle.complete(success=False, error_message=str(e))
        raise ImprovementCycleError(f"Improvement cycle failed: {e}") from e


async def main() -> None:
    """Main entry point for the application."""
    print("DEMO: Starting Novitas AI system")
    configure_logging()
    print("DEMO: Logging configured")
    logger.info("Starting Novitas AI system")

    try:
        print("DEMO: About to run improvement cycle")
        # Run improvement cycle (with dry-run mode if specified)
        await run_improvement_cycle(dry_run=settings.dry_run)

    except Exception as e:
        logger.error("Application failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
