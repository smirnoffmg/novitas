"""Agent lifecycle management for the Novitas AI system."""

import asyncio
from collections.abc import Callable
from collections.abc import Coroutine
from enum import Enum
from typing import Any
from uuid import UUID

from ..config.logging import get_logger
from ..core.exceptions import AgentError
from ..core.exceptions import AgentStateError
from ..core.protocols import Agent
from ..core.protocols import DatabaseManager


class AgentStatus(Enum):
    """Agent lifecycle status."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"
    ERROR = "error"
    CLEANING_UP = "cleaning_up"
    TERMINATED = "terminated"


class LifecycleEvent(Enum):
    """Lifecycle events that can be monitored."""

    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    PAUSED = "paused"
    RESUMED = "resumed"
    ERROR = "error"
    CLEANUP_STARTED = "cleanup_started"
    CLEANUP_COMPLETED = "cleanup_completed"
    TERMINATED = "terminated"


class AgentLifecycleManager:
    """Manages the lifecycle of agents in the system."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initialize the lifecycle manager.

        Args:
            database_manager: Database manager for state persistence
        """
        self.database_manager = database_manager
        self.logger = get_logger("agent.lifecycle")
        self._agents: dict[UUID, Agent] = {}
        self._status: dict[UUID, AgentStatus] = {}
        self._event_handlers: dict[LifecycleEvent, list[Callable]] = {
            event: [] for event in LifecycleEvent
        }
        self._health_checks: dict[UUID, Callable[[], Coroutine[Any, Any, bool]]] = {}

    async def register_agent(self, agent: Agent) -> None:
        """Register an agent with the lifecycle manager.

        Args:
            agent: Agent to register

        Raises:
            AgentError: If agent is already registered
        """
        if agent.id in self._agents:
            raise AgentError(f"Agent {agent.id} is already registered")

        self._agents[agent.id] = agent
        self._status[agent.id] = AgentStatus.CREATED

        self.logger.info("Agent registered", agent_id=agent.id, agent_name=agent.name)
        await self._emit_event(LifecycleEvent.CREATED, agent.id)

    async def unregister_agent(self, agent_id: UUID) -> None:
        """Unregister an agent from the lifecycle manager.

        Args:
            agent_id: ID of the agent to unregister

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        agent = self._agents[agent_id]

        # Ensure agent is cleaned up
        if self._status[agent_id] != AgentStatus.TERMINATED:
            await self.terminate_agent(agent_id)

        del self._agents[agent_id]
        del self._status[agent_id]

        if agent_id in self._health_checks:
            del self._health_checks[agent_id]

        self.logger.info("Agent unregistered", agent_id=agent_id)

    async def initialize_agent(self, agent_id: UUID) -> None:
        """Initialize an agent.

        Args:
            agent_id: ID of the agent to initialize

        Raises:
            AgentError: If agent is not registered or already initialized
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        if self._status[agent_id] != AgentStatus.CREATED:
            raise AgentStateError(
                f"Agent {agent_id} cannot be initialized from status {self._status[agent_id]}"
            )

        agent = self._agents[agent_id]
        self._status[agent_id] = AgentStatus.INITIALIZING

        self.logger.info("Initializing agent", agent_id=agent_id)
        await self._emit_event(LifecycleEvent.INITIALIZING, agent_id)

        try:
            await agent.initialize()
            self._status[agent_id] = AgentStatus.READY

            self.logger.info("Agent initialized successfully", agent_id=agent_id)
            await self._emit_event(LifecycleEvent.INITIALIZED, agent_id)

        except Exception as e:
            self._status[agent_id] = AgentStatus.ERROR
            self.logger.error(
                "Agent initialization failed", agent_id=agent_id, error=str(e)
            )
            await self._emit_event(LifecycleEvent.ERROR, agent_id, error=str(e))
            raise AgentError(f"Failed to initialize agent {agent_id}: {e}") from e

    async def execute_agent(self, agent_id: UUID, context: dict[str, Any]) -> list[Any]:
        """Execute an agent.

        Args:
            agent_id: ID of the agent to execute
            context: Execution context

        Returns:
            Execution results

        Raises:
            AgentError: If agent is not ready or execution fails
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        if self._status[agent_id] != AgentStatus.READY:
            raise AgentStateError(
                f"Agent {agent_id} cannot be executed from status {self._status[agent_id]}"
            )

        agent = self._agents[agent_id]
        self._status[agent_id] = AgentStatus.EXECUTING

        self.logger.info("Executing agent", agent_id=agent_id)
        await self._emit_event(LifecycleEvent.EXECUTION_STARTED, agent_id)

        try:
            results = await agent.execute(context)
            self._status[agent_id] = AgentStatus.READY

            self.logger.info("Agent execution completed", agent_id=agent_id)
            await self._emit_event(LifecycleEvent.EXECUTION_COMPLETED, agent_id)

            return results

        except Exception as e:
            self._status[agent_id] = AgentStatus.ERROR
            self.logger.error("Agent execution failed", agent_id=agent_id, error=str(e))
            await self._emit_event(
                LifecycleEvent.EXECUTION_FAILED, agent_id, error=str(e)
            )
            raise AgentError(f"Agent {agent_id} execution failed: {e}") from e

    async def pause_agent(self, agent_id: UUID) -> None:
        """Pause an agent.

        Args:
            agent_id: ID of the agent to pause

        Raises:
            AgentError: If agent is not in a pausable state
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        if self._status[agent_id] not in [AgentStatus.READY, AgentStatus.EXECUTING]:
            raise AgentStateError(
                f"Agent {agent_id} cannot be paused from status {self._status[agent_id]}"
            )

        self._status[agent_id] = AgentStatus.PAUSED

        self.logger.info("Agent paused", agent_id=agent_id)
        await self._emit_event(LifecycleEvent.PAUSED, agent_id)

    async def resume_agent(self, agent_id: UUID) -> None:
        """Resume a paused agent.

        Args:
            agent_id: ID of the agent to resume

        Raises:
            AgentError: If agent is not paused
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        if self._status[agent_id] != AgentStatus.PAUSED:
            raise AgentStateError(
                f"Agent {agent_id} cannot be resumed from status {self._status[agent_id]}"
            )

        self._status[agent_id] = AgentStatus.READY

        self.logger.info("Agent resumed", agent_id=agent_id)
        await self._emit_event(LifecycleEvent.RESUMED, agent_id)

    async def terminate_agent(self, agent_id: UUID) -> None:
        """Terminate an agent.

        Args:
            agent_id: ID of the agent to terminate

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        agent = self._agents[agent_id]
        self._status[agent_id] = AgentStatus.CLEANING_UP

        self.logger.info("Terminating agent", agent_id=agent_id)
        await self._emit_event(LifecycleEvent.CLEANUP_STARTED, agent_id)

        try:
            await agent.cleanup()
            self._status[agent_id] = AgentStatus.TERMINATED

            self.logger.info("Agent terminated successfully", agent_id=agent_id)
            await self._emit_event(LifecycleEvent.CLEANUP_COMPLETED, agent_id)
            await self._emit_event(LifecycleEvent.TERMINATED, agent_id)

        except Exception as e:
            self._status[agent_id] = AgentStatus.ERROR
            self.logger.error(
                "Agent termination failed", agent_id=agent_id, error=str(e)
            )
            await self._emit_event(LifecycleEvent.ERROR, agent_id, error=str(e))
            raise AgentError(f"Failed to terminate agent {agent_id}: {e}") from e

    def get_agent_status(self, agent_id: UUID) -> AgentStatus:
        """Get the current status of an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Current agent status

        Raises:
            AgentError: If agent is not registered
        """
        if agent_id not in self._agents:
            raise AgentError(f"Agent {agent_id} is not registered")

        return self._status[agent_id]

    def get_all_agents(self) -> dict[UUID, Agent]:
        """Get all registered agents.

        Returns:
            Dictionary of agent ID to agent instance
        """
        return self._agents.copy()

    def get_agents_by_status(self, status: AgentStatus) -> list[Agent]:
        """Get all agents with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of agents with the specified status
        """
        return [
            agent
            for agent_id, agent in self._agents.items()
            if self._status[agent_id] == status
        ]

    async def add_event_handler(
        self, event: LifecycleEvent, handler: Callable[[UUID, dict[str, Any]], None]
    ) -> None:
        """Add an event handler for lifecycle events.

        Args:
            event: Event to handle
            handler: Handler function
        """
        self._event_handlers[event].append(handler)

    async def remove_event_handler(
        self, event: LifecycleEvent, handler: Callable[[UUID, dict[str, Any]], None]
    ) -> None:
        """Remove an event handler.

        Args:
            event: Event to remove handler from
            handler: Handler function to remove
        """
        if handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)

    async def _emit_event(
        self, event: LifecycleEvent, agent_id: UUID, **kwargs: Any
    ) -> None:
        """Emit a lifecycle event to all registered handlers.

        Args:
            event: Event to emit
            agent_id: ID of the agent
            **kwargs: Additional event data
        """
        event_data = {
            "agent_id": agent_id,
            "timestamp": asyncio.get_event_loop().time(),
            **kwargs,
        }

        for handler in self._event_handlers[event]:
            try:
                handler(agent_id, event_data)
            except Exception as e:
                self.logger.error(
                    "Event handler failed",
                    event=event.value,
                    agent_id=agent_id,
                    error=str(e),
                )

    async def add_health_check(
        self, agent_id: UUID, health_check: Callable[[], Coroutine[Any, Any, bool]]
    ) -> None:
        """Add a health check for an agent.

        Args:
            agent_id: ID of the agent
            health_check: Health check function that returns True if healthy
        """
        self._health_checks[agent_id] = health_check

    async def check_agent_health(self, agent_id: UUID) -> bool:
        """Check the health of an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            True if agent is healthy, False otherwise
        """
        if agent_id not in self._health_checks:
            return True  # No health check defined, assume healthy

        try:
            return await self._health_checks[agent_id]()
        except Exception as e:
            self.logger.error("Health check failed", agent_id=agent_id, error=str(e))
            return False

    async def check_all_agents_health(self) -> dict[UUID, bool]:
        """Check health of all agents.

        Returns:
            Dictionary of agent ID to health status
        """
        health_status = {}

        for agent_id in self._agents:
            health_status[agent_id] = await self.check_agent_health(agent_id)

        return health_status
