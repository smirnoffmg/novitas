"""Pytest configuration and fixtures for Novitas tests."""

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from novitas.core.models import AgentState
from novitas.core.models import AgentStatus
from novitas.core.models import AgentType
from novitas.core.models import ChangeProposal
from novitas.core.models import ImprovementCycle
from novitas.core.models import ImprovementType
from novitas.database.connection import DatabaseManagerImpl
from novitas.database.models import Base


@pytest.fixture
def sample_agent_state() -> AgentState:
    """Create a sample agent state for testing."""
    return AgentState(
        id=uuid4(),
        agent_type=AgentType.CODE_AGENT,
        name="Test Code Agent",
        description="A test code agent",
        status=AgentStatus.ACTIVE,
        prompt="You are a code improvement agent.",
    )


@pytest.fixture
def sample_change_proposal(sample_agent_state: AgentState) -> ChangeProposal:
    """Create a sample change proposal for testing."""
    return ChangeProposal(
        id=uuid4(),
        agent_id=sample_agent_state.id,
        improvement_type=ImprovementType.CODE_IMPROVEMENT,
        file_path="src/test.py",
        description="Improve code quality",
        reasoning="This change improves code readability",
        proposed_changes={"content": "new code"},
        confidence_score=0.8,
    )


@pytest.fixture
def sample_improvement_cycle() -> ImprovementCycle:
    """Create a sample improvement cycle for testing."""
    return ImprovementCycle(
        id=uuid4(),
        cycle_number=1,
        agents_used=[uuid4()],
        changes_proposed=[uuid4()],
        changes_accepted=[uuid4()],
    )


@pytest_asyncio.fixture
async def async_session() -> AsyncSession:
    """Create an async database session for testing."""
    # Create in-memory SQLite database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create and yield session
    async with async_session_maker() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def clean_database() -> DatabaseManagerImpl:
    """Create a clean database manager for testing."""

    # Create a custom database manager for testing with SQLite
    class TestDatabaseManager(DatabaseManagerImpl):
        async def connect(self) -> None:
            """Connect to the test database."""
            if self._connected:
                return

            try:
                # Create async engine with SQLite for testing
                self._engine = create_async_engine(
                    "sqlite+aiosqlite:///:memory:",
                    echo=False,
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

            except Exception:
                raise

    db_manager = TestDatabaseManager()
    await db_manager.connect()

    yield db_manager

    # Cleanup
    await db_manager.disconnect()
