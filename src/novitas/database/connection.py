"""Database connection and management for the Novitas AI system."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from ..config.logging import get_logger
from ..config.settings import settings
from ..core.models import AgentState
from ..core.models import ChangeProposal
from ..core.models import ImprovementCycle
from ..core.protocols import DatabaseManager
from .models import Base
from .repositories import AgentStateRepository
from .repositories import ChangeProposalRepository
from .repositories import ImprovementCycleRepository

logger = get_logger(__name__)


class DatabaseManagerImpl(DatabaseManager):
    """Implementation of the database manager."""

    def __init__(self) -> None:
        """Initialize the database manager."""
        self._connected = False
        self._engine: AsyncEngine | None = None
        self._session_maker = None
        self._session: AsyncSession | None = None

    async def connect(self) -> None:
        """Connect to the database."""
        if self._connected:
            return

        try:
            # Create async engine
            self._engine = create_async_engine(
                settings.database_url,
                echo=settings.debug,
                pool_pre_ping=True,
            )

            # Create tables if they don't exist
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # Create session maker
            self._session_maker = sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            self._connected = True
            logger.info("Database connected successfully")

        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        if not self._connected:
            return

        try:
            if self._session:
                await self._session.close()

            if self._engine:
                await self._engine.dispose()

            self._connected = False
            self._session = None
            self._engine = None
            self._session_maker = None

            logger.info("Database disconnected successfully")

        except Exception as e:
            logger.error("Failed to disconnect from database", error=str(e))
            raise

    async def _get_session(self) -> AsyncSession:
        """Get a database session."""
        if not self._connected:
            raise RuntimeError("Database not connected")

        if not self._session_maker:
            raise RuntimeError("Session maker not initialized")

        if not self._session:
            self._session = self._session_maker()

        return self._session

    async def save_agent_state(self, agent_state: AgentState) -> None:
        """Save an agent's state to the database."""
        session = await self._get_session()
        repository = AgentStateRepository(session)

        try:
            # Check if agent exists
            existing = await repository.get_by_id(str(agent_state.id))
            if existing:
                await repository.update(agent_state)
                logger.info("Updated agent state", agent_id=agent_state.id)
            else:
                await repository.create(agent_state)
                logger.info("Created agent state", agent_id=agent_state.id)

        except Exception as e:
            logger.error(
                "Failed to save agent state", agent_id=agent_state.id, error=str(e)
            )
            raise

    async def load_agent_state(self, agent_id: UUID) -> AgentState | None:
        """Load an agent's state from the database."""
        session = await self._get_session()
        repository = AgentStateRepository(session)

        try:
            agent_state = await repository.get_by_id(str(agent_id))
            if agent_state:
                logger.info("Loaded agent state", agent_id=agent_id)
            else:
                logger.info("Agent state not found", agent_id=agent_id)

            return agent_state

        except Exception as e:
            logger.error("Failed to load agent state", agent_id=agent_id, error=str(e))
            raise

    async def save_change_proposal(self, proposal: ChangeProposal) -> None:
        """Save a change proposal to the database."""
        session = await self._get_session()
        repository = ChangeProposalRepository(session)

        try:
            # Check if proposal exists
            existing = await repository.get_by_id(str(proposal.id))
            if existing:
                await repository.update(proposal)
                logger.info("Updated change proposal", proposal_id=proposal.id)
            else:
                await repository.create(proposal)
                logger.info("Created change proposal", proposal_id=proposal.id)

        except Exception as e:
            logger.error(
                "Failed to save change proposal", proposal_id=proposal.id, error=str(e)
            )
            raise

    async def get_change_proposals(self, cycle_id: UUID) -> list[ChangeProposal]:
        """Get all change proposals for a cycle."""
        session = await self._get_session()
        repository = ChangeProposalRepository(session)

        try:
            proposals = await repository.get_by_cycle_id(str(cycle_id))
            logger.info(
                "Retrieved change proposals", cycle_id=cycle_id, count=len(proposals)
            )
            return proposals

        except Exception as e:
            logger.error(
                "Failed to get change proposals", cycle_id=cycle_id, error=str(e)
            )
            raise

    async def save_improvement_cycle(self, cycle: ImprovementCycle) -> None:
        """Save an improvement cycle to the database."""
        session = await self._get_session()
        repository = ImprovementCycleRepository(session)

        try:
            # Check if cycle exists
            existing = await repository.get_by_id(str(cycle.id))
            if existing:
                await repository.update(cycle)
                logger.info("Updated improvement cycle", cycle_id=cycle.id)
            else:
                await repository.create(cycle)
                logger.info("Created improvement cycle", cycle_id=cycle.id)

        except Exception as e:
            logger.error(
                "Failed to save improvement cycle", cycle_id=cycle.id, error=str(e)
            )
            raise

    async def get_latest_cycle(self) -> ImprovementCycle | None:
        """Get the latest improvement cycle."""
        session = await self._get_session()
        repository = ImprovementCycleRepository(session)

        try:
            cycle = await repository.get_latest()
            if cycle:
                logger.info("Retrieved latest cycle", cycle_id=cycle.id)
            else:
                logger.info("No cycles found")

            return cycle

        except Exception as e:
            logger.error("Failed to get latest cycle", error=str(e))
            raise

    async def get_all_agents(self) -> list[AgentState]:
        """Get all agents from the database."""
        session = await self._get_session()
        repository = AgentStateRepository(session)

        try:
            agents = await repository.get_all()
            logger.info("Retrieved all agents", count=len(agents))
            return agents

        except Exception as e:
            logger.error("Failed to get all agents", error=str(e))
            raise

    async def get_recent_cycles(self, count: int) -> list[ImprovementCycle]:
        """Get recent improvement cycles."""
        session = await self._get_session()
        repository = ImprovementCycleRepository(session)

        try:
            cycles = await repository.get_recent(count)
            logger.info("Retrieved recent cycles", count=len(cycles))
            return cycles

        except Exception as e:
            logger.error("Failed to get recent cycles", error=str(e))
            raise

    async def migrate(self) -> None:
        """Run database migrations."""
        if not self._connected:
            raise RuntimeError("Database not connected")

        if not self._engine:
            raise RuntimeError("Database engine not initialized")

        try:
            # For now, just create tables
            # In the future, this would use Alembic for migrations
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database migrations completed")

        except Exception as e:
            logger.error("Failed to run migrations", error=str(e))
            raise

    async def reset(self) -> None:
        """Reset the database."""
        if not self._connected:
            raise RuntimeError("Database not connected")

        if not self._engine:
            raise RuntimeError("Database engine not initialized")

        try:
            # Drop all tables and recreate them
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database reset completed")

        except Exception as e:
            logger.error("Failed to reset database", error=str(e))
            raise

    def get_status(self) -> str:
        """Get database status."""
        if not self._connected:
            return "Disconnected"
        return "Connected"


def get_database_manager() -> DatabaseManager:
    """Get a database manager instance."""
    return DatabaseManagerImpl()
