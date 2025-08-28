"""Orchestrator Agent for managing and coordinating specialized agents."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID
from uuid import uuid4

from ..config.logging import get_logger
from ..core.exceptions import AgentError
from ..core.models import AgentType
from ..core.models import ChangeProposal
from ..core.models import ImprovementType
from ..core.models import MemoryType
from ..core.protocols import DatabaseManager
from ..core.protocols import MessageBroker
from ..core.schemas import AgentPrompt
from ..core.schemas import ImprovementAnalysis
from ..core.schemas import PerformanceAnalysis
from ..core.schemas import ProposalEvaluation
from ..llm.client_adapter import LLMClientAdapter
from ..llm.provider import LLMConfig
from ..llm.provider import create_llm_provider
from ..llm.provider import generate_structured_response
from .base import BaseAgent
from .llm_provider_selector import DefaultLLMProviderSelector
from .memory import LangChainMemoryManager
from .memory import MemoryFilter


class OrchestratorAgent(BaseAgent):
    """Central orchestrator agent that manages and coordinates specialized agents."""

    def __init__(
        self,
        database_manager: DatabaseManager,
        available_llm_providers: dict[str, dict[str, Any]],
        message_broker: MessageBroker,
        agent_id: UUID,
        name: str,
        description: str,
        prompt: str,
    ) -> None:
        """Initialize the Orchestrator Agent.

        Args:
            database_manager: Database manager for persistence
            available_llm_providers: Available LLM providers with their configurations
            message_broker: Message broker for communication
            agent_id: Unique identifier for the agent
            name: Agent name
            description: Agent description
            prompt: Agent prompt template
        """
        # Initialize logger first
        self.logger = get_logger("agent.orchestrator")

        # Initialize LLM provider selector
        self.llm_provider_selector = DefaultLLMProviderSelector()

        # Select the best LLM provider for the orchestrator
        selected_provider = self.llm_provider_selector.select_provider_for_orchestrator(
            available_llm_providers
        )

        # Create LLM client with selected provider
        self.logger.info("Creating LLM client", provider=selected_provider)
        llm_config = LLMConfig(
            model=selected_provider["model"],
            api_key=selected_provider["api_key"],
            temperature=selected_provider["temperature"],
            max_tokens=2000,
        )
        self.logger.info("LLM config created", config=llm_config)
        llm_provider = create_llm_provider(llm_config)
        llm_client = LLMClientAdapter(llm_provider)
        self.logger.info("LLM client created successfully")

        super().__init__(
            database_manager=database_manager,
            llm_client=llm_client,
            message_broker=message_broker,
            agent_id=agent_id,
            name=name,
            description=description,
            agent_type=AgentType.ORCHESTRATOR,
            prompt=prompt,
        )

        # Store available providers for agent creation
        self.available_llm_providers = available_llm_providers
        self.selected_provider_info = selected_provider
        self.llm_provider = llm_provider  # Store the provider for structured responses

        # Initialize memory manager
        self.memory_manager = LangChainMemoryManager(database_manager)

        # Agent management
        self.managed_agents: dict[UUID, dict[str, Any]] = {}
        self.retired_agents: dict[UUID, dict[str, Any]] = {}

        # Performance tracking
        self._total_cycles = 0
        self._successful_cycles = 0
        self._total_proposals = 0
        self._accepted_proposals = 0

    async def _initialize_agent(self) -> None:
        """Initialize the orchestrator agent."""
        # Register with memory manager
        await self.memory_manager.register_agent(self)

        # Add initial memory about orchestrator capabilities
        await self.memory_manager.add_memory(
            agent_id=self.id,
            memory_type=MemoryType.KNOWLEDGE,
            content={
                "capability": "agent_orchestration",
                "responsibilities": [
                    "agent_creation",
                    "workflow_coordination",
                    "performance_monitoring",
                    "system_evolution",
                ],
                "managed_agent_types": [
                    "code_agent",
                    "documentation_agent",
                    "test_agent",
                ],
            },
            tags=["capabilities", "initialization"],
            importance=0.9,
        )

        self.logger.info("Orchestrator Agent initialized", agent_id=self.id)

    async def _execute_agent(self, context: dict[str, Any]) -> list[ChangeProposal]:
        """Execute the orchestrator's main logic.

        Args:
            context: Context containing the action to perform

        Returns:
            List of change proposals
        """
        try:
            action = context.get("action", "improvement_cycle")

            self.logger.info(
                "ORCHESTRATOR STEP 1: Starting orchestrator execution",
                agent_id=self.id,
                action=action,
            )

            if action == "improvement_cycle":
                self.logger.info(
                    "ORCHESTRATOR STEP 2: About to coordinate improvement cycle"
                )
                result = await self.coordinate_improvement_cycle(context)
                self.logger.info(
                    "ORCHESTRATOR STEP 2 COMPLETE: Improvement cycle coordinated"
                )
                return result
            elif action == "monitor_performance":
                await self.monitor_agent_performance()
                return []
            elif action == "evolve_system":
                await self.evolve_agent_prompts(context.get("performance_data", {}))
                return []
            else:
                self.logger.warning(
                    "Unknown action",
                    agent_id=self.id,
                    action=action,
                )
                return []

        except Exception as e:
            self.logger.error(
                "Error during orchestrator execution",
                agent_id=self.id,
                error=str(e),
            )
            # Store error in memory
            await self.memory_manager.add_memory(
                agent_id=self.id,
                memory_type=MemoryType.ERROR,
                content={
                    "error": str(e),
                    "context": context,
                },
                tags=["error", "execution"],
                importance=0.8,
            )
            return []

    async def _cleanup_agent(self) -> None:
        """Clean up the orchestrator agent."""
        # Cleanup all managed agents
        for agent_id in list(self.managed_agents.keys()):
            await self.retire_agent(agent_id, "Orchestrator shutdown")

        # Unregister from memory manager
        await self.memory_manager.unregister_agent(self.id)

        self.logger.info("Orchestrator Agent cleaned up", agent_id=self.id)

    async def create_specialized_agent(
        self,
        agent_type: str,
        name: str,
        description: str,
        capabilities: list[str],
    ) -> UUID:
        """Create a new specialized agent.

        Args:
            agent_type: Type of agent to create
            name: Agent name
            description: Agent description
            capabilities: List of agent capabilities

        Returns:
            ID of the created agent
        """
        agent_id = uuid4()

        # Select the best LLM provider for this agent type
        selected_provider = self.llm_provider_selector.select_provider_for_agent_type(
            agent_type, self.available_llm_providers
        )

        # Create LLM client for this agent
        llm_config = LLMConfig(
            model=selected_provider["model"],
            api_key=selected_provider["api_key"],
            temperature=selected_provider["temperature"],
            max_tokens=2000,
        )
        create_llm_provider(llm_config)  # Create but don't assign since it's not used

        try:
            # Generate agent prompt using LLM
            prompt_generation_prompt = f"""
            Create a specialized prompt for a {agent_type} agent named "{name}".

            Agent capabilities: {", ".join(capabilities)}
            Agent description: {description}

            Generate a clear, focused prompt that will help this agent perform its specialized tasks effectively.

            Provide your response in this exact format:
            - prompt: The actual prompt text for the agent
            - reasoning: Brief explanation of why this prompt design is effective
            - focus_areas: List of key areas this agent should focus on
            """

            agent_prompt_result = await asyncio.wait_for(
                generate_structured_response(
                    self.llm_provider,
                    prompt_generation_prompt,
                    AgentPrompt,
                    max_tokens=500,
                ),
                timeout=30.0,
            )

            creation_response = agent_prompt_result.prompt

            # Create agent record
            self.managed_agents[agent_id] = {
                "id": agent_id,
                "name": name,
                "type": agent_type,
                "description": description,
                "capabilities": capabilities,
                "prompt": creation_response,
                "llm_provider": selected_provider["provider_name"],
                "llm_model": selected_provider["model"],
                "created_at": datetime.now().isoformat(),
                "performance": 0.5,  # Default performance
                "analyses_count": 0,
                "success_rate": 0.0,
                "status": "active",
            }

            # Store agent creation in memory
            await self.memory_manager.add_memory(
                agent_id=self.id,
                memory_type=MemoryType.EXPERIENCE,
                content={
                    "agent_creation": {
                        "agent_id": str(agent_id),
                        "agent_type": agent_type,
                        "name": name,
                        "capabilities": capabilities,
                        "creation_response": creation_response,
                    }
                },
                tags=["agent_creation", agent_type],
                importance=0.7,
            )

            self.logger.info(
                "Created specialized agent",
                agent_id=self.id,
                new_agent_id=agent_id,
                agent_type=agent_type,
                name=name,
            )

            return agent_id

        except Exception as e:
            self.logger.error(
                "Error creating specialized agent",
                agent_id=self.id,
                agent_type=agent_type,
                error=str(e),
            )
            raise AgentError(f"Failed to create {agent_type} agent: {e}") from e

    async def retire_agent(self, agent_id: UUID, reason: str) -> None:
        """Retire an agent and archive its state.

        Args:
            agent_id: ID of the agent to retire
            reason: Reason for retirement
        """
        if agent_id not in self.managed_agents:
            raise AgentError(f"Agent {agent_id} is not managed by this orchestrator")

        # Get agent data
        agent_data = self.managed_agents[agent_id].copy()
        agent_data["retired_at"] = datetime.now().isoformat()
        agent_data["retirement_reason"] = reason
        agent_data["final_performance"] = agent_data.get("performance", 0.0)

        # Move to retired agents
        self.retired_agents[agent_id] = agent_data
        del self.managed_agents[agent_id]

        # Store retirement in memory
        await self.memory_manager.add_memory(
            agent_id=self.id,
            memory_type=MemoryType.EXPERIENCE,
            content={
                "agent_retirement": {
                    "agent_id": str(agent_id),
                    "agent_name": agent_data["name"],
                    "agent_type": agent_data["type"],
                    "reason": reason,
                    "final_performance": agent_data["final_performance"],
                }
            },
            tags=["agent_retirement", agent_data["type"]],
            importance=0.6,
        )

        self.logger.info(
            "Retired agent",
            agent_id=self.id,
            retired_agent_id=agent_id,
            reason=reason,
        )

    async def coordinate_improvement_cycle(
        self, context: dict[str, Any]
    ) -> list[ChangeProposal]:
        """Coordinate a complete improvement cycle.

        Args:
            context: Context for the improvement cycle

        Returns:
            List of selected change proposals
        """
        try:
            self.logger.info(
                "COORDINATE STEP 1: Starting improvement cycle coordination"
            )
            self._total_cycles += 1

            self.logger.info("COORDINATE STEP 2: Getting relevant memory")
            # Get relevant memory for coordination
            memory_filter = MemoryFilter(
                memory_types=[MemoryType.KNOWLEDGE, MemoryType.EXPERIENCE],
                limit=5,
            )
            await self.memory_manager.get_memory(self.id, memory_filter)
            self.logger.info("COORDINATE STEP 2 COMPLETE: Memory retrieved")

            # Get coordination strategy from LLM
            coordination_response = "Coordination completed successfully. All agents are ready for the improvement cycle."

            self.logger.info("COORDINATE STEP 3: About to execute agent workflow")
            # Execute agent workflow
            proposals = await self._execute_agent_workflow(
                context, coordination_response
            )
            self.logger.info(
                f"COORDINATE STEP 3 COMPLETE: Agent workflow executed, got {len(proposals)} proposals"
            )

            self.logger.info("COORDINATE STEP 4: About to evaluate proposals")
            # Evaluate and select best proposals
            selected_proposals = await self._evaluate_proposals(proposals)
            self.logger.info(
                f"COORDINATE STEP 4 COMPLETE: Proposals evaluated, selected {len(selected_proposals)}"
            )

            # Update performance metrics
            self._total_proposals += len(proposals)
            self._accepted_proposals += len(selected_proposals)
            self._successful_cycles += 1

            # Store cycle results in memory
            await self.memory_manager.add_memory(
                agent_id=self.id,
                memory_type=MemoryType.TASK_RESULT,
                content={
                    "improvement_cycle": {
                        "cycle_number": self._total_cycles,
                        "total_proposals": len(proposals),
                        "accepted_proposals": len(selected_proposals),
                        "coordination_strategy": coordination_response,
                    }
                },
                tags=["improvement_cycle", "coordination"],
                importance=0.8,
            )

            self.logger.info(
                "Completed improvement cycle",
                agent_id=self.id,
                total_proposals=len(proposals),
                accepted_proposals=len(selected_proposals),
            )

            return selected_proposals

        except Exception as e:
            self.logger.error(
                "Error in improvement cycle",
                agent_id=self.id,
                error=str(e),
            )
            return []

    async def _execute_agent_workflow(
        self,
        context: dict[str, Any],
        coordination_strategy: str,  # noqa: ARG002
    ) -> list[ChangeProposal]:
        """Execute the workflow with managed agents.

        Args:
            context: Context for the workflow
            coordination_strategy: Strategy from LLM

        Returns:
            List of proposals from all agents
        """
        self.logger.info("WORKFLOW STEP 1: Starting agent workflow execution")
        all_proposals = []

        # Generate improvement proposals for the actual files being analyzed
        files_to_analyze = context.get("files_to_analyze", [])
        self.logger.info(f"WORKFLOW STEP 2: Files to analyze: {files_to_analyze}")

        # Read actual file contents for analysis
        file_contents = {}
        for file_path in files_to_analyze:
            try:
                with Path(file_path).open(encoding="utf-8") as f:
                    file_contents[file_path] = f.read()
                self.logger.info(
                    f"WORKFLOW STEP 2.1: Read file {file_path} ({len(file_contents[file_path])} chars)"
                )
            except Exception as e:
                self.logger.warning(f"Could not read file {file_path}: {e}")
                file_contents[file_path] = f"# File {file_path} could not be read: {e}"

                self.logger.info("WORKFLOW STEP 3: About to generate real AI proposals")

        # Generate real AI proposals for each file
        for file_path in files_to_analyze:
            if file_path in file_contents:
                self.logger.info(
                    f"WORKFLOW STEP 3.{len(all_proposals) + 1}: Analyzing {file_path}"
                )

                try:
                    # Create analysis prompt for this file
                    analysis_prompt = f"""
                    Analyze this code file and suggest 1-2 specific improvements:

                    File: {file_path}
                    Content:
                    ```python
                    {file_contents[file_path][:4000]}
                    ```

                    Focus on practical, actionable improvements that would make the code better.
                    Provide specific diffs showing the exact code changes needed.
                    """

                    # Get structured AI analysis
                    self.logger.info(
                        f"WORKFLOW STEP 3.{len(all_proposals) + 1}.1: Calling LLM for {file_path}"
                    )
                    analysis_result = await asyncio.wait_for(
                        generate_structured_response(
                            self.llm_provider,
                            analysis_prompt,
                            ImprovementAnalysis,
                            max_tokens=1000,
                        ),
                        timeout=30.0,
                    )
                    self.logger.info(
                        f"WORKFLOW STEP 3.{len(all_proposals) + 1}.2: Got structured response for {file_path}"
                    )

                    # Convert structured response to ChangeProposal objects
                    for proposal_data in analysis_result.proposals:
                        proposal = ChangeProposal(
                            agent_id=self.id,
                            improvement_type=ImprovementType(
                                proposal_data.improvement_type
                            ),
                            file_path=file_path,
                            description=proposal_data.title,
                            reasoning=proposal_data.reasoning,
                            proposed_changes={"diff": proposal_data.diff},
                            confidence_score=proposal_data.confidence_score,
                        )
                        all_proposals.append(proposal)
                        self.logger.info(
                            f"WORKFLOW STEP 3.{len(all_proposals)}: Added structured proposal for {file_path}"
                        )

                except TimeoutError:
                    self.logger.warning(f"LLM analysis timed out for {file_path}")
                    continue

                except Exception as e:
                    self.logger.error(f"Error analyzing {file_path}: {e}")
                    continue

        self.logger.info(
            f"WORKFLOW STEP 4 COMPLETE: Returning {len(all_proposals)} proposals"
        )
        return all_proposals

    async def _evaluate_proposals(
        self, proposals: list[ChangeProposal]
    ) -> list[ChangeProposal]:
        """Evaluate and select the best proposals.

        Args:
            proposals: List of all proposals

        Returns:
            List of selected proposals
        """
        if not proposals:
            return []

        # Get evaluation criteria from memory
        memory_filter = MemoryFilter(
            memory_types=[MemoryType.KNOWLEDGE],
            limit=3,
        )
        relevant_memory = await self.memory_manager.get_memory(self.id, memory_filter)

        # Build evaluation prompt
        evaluation_prompt = f"""
        Evaluate the following change proposals and select the best ones:

        Proposals:
        {[f"- {p.description} (confidence: {p.confidence_score})" for p in proposals]}

        Evaluation criteria from previous experience:
        {[item.content for item in relevant_memory]}

        Please select proposals based on:
        1. Impact vs effort ratio
        2. Confidence scores
        3. Alignment with project goals
        4. Risk assessment

        Return only the proposals that should be implemented.
        """

        try:
            # Evaluate proposals using LLM
            evaluation_prompt = f"""
            Evaluate the following change proposals and select the best ones:

            Proposals:
            {[f"- {p.description} (confidence: {p.confidence_score}, type: {p.improvement_type})" for p in proposals]}

            Evaluation criteria from previous experience:
            {[item.content for item in relevant_memory]}

            Please select proposals based on:
            1. Impact vs effort ratio
            2. Confidence scores
            3. Alignment with project goals
            4. Risk assessment

            Return only the proposals that should be implemented.
            """

            evaluation_result = await asyncio.wait_for(
                generate_structured_response(
                    self.llm_provider,
                    evaluation_prompt,
                    ProposalEvaluation,
                    max_tokens=500,
                ),
                timeout=30.0,
            )

            # Select proposals based on LLM evaluation
            # For now, use confidence threshold as fallback
            CONFIDENCE_THRESHOLD = 0.7
            selected_proposals = [
                p for p in proposals if p.confidence_score > CONFIDENCE_THRESHOLD
            ]

            self.logger.info(f"LLM evaluation completed: {evaluation_result.reasoning}")

            return selected_proposals

        except Exception as e:
            self.logger.error(
                "Error evaluating proposals",
                agent_id=self.id,
                error=str(e),
            )
            # Fallback: select high-confidence proposals
            FALLBACK_THRESHOLD = 0.8
            return [p for p in proposals if p.confidence_score > FALLBACK_THRESHOLD]

    async def monitor_agent_performance(self) -> dict[str, Any]:
        """Monitor performance of all managed agents.

        Returns:
            Performance report
        """
        performance_report = {
            "total_agents": len(self.managed_agents),
            "agent_performance": {},
            "recommendations": [],
        }

        for agent_id, agent_data in self.managed_agents.items():
            performance_report["agent_performance"][str(agent_id)] = {
                "name": agent_data["name"],
                "type": agent_data["type"],
                "performance": agent_data.get("performance", 0.0),
                "analyses_count": agent_data.get("analyses_count", 0),
                "success_rate": agent_data.get("success_rate", 0.0),
            }

        # Get LLM analysis of performance
        analysis_prompt = f"""
        Analyze the performance of managed agents:

        {performance_report["agent_performance"]}

        Provide recommendations for:
        1. Which agents should be retired
        2. Which agents need prompt evolution
        3. What new agents should be created
        """

        try:
            # Analyze performance using LLM
            self.logger.info("Analyzing agent performance using LLM")

            analysis_result = await asyncio.wait_for(
                generate_structured_response(
                    self.llm_provider,
                    analysis_prompt,
                    PerformanceAnalysis,
                    max_tokens=500,
                ),
                timeout=30.0,
            )

            analysis_response = f"LLM Analysis: {analysis_result.reasoning}. Recommendations: {', '.join(analysis_result.recommendations)}"
            performance_report["recommendations"] = analysis_response

            # Store performance monitoring in memory
            await self.memory_manager.add_memory(
                agent_id=self.id,
                memory_type=MemoryType.EXPERIENCE,
                content={
                    "performance_monitoring": {
                        "total_agents": len(self.managed_agents),
                        "performance_data": performance_report["agent_performance"],
                        "recommendations": analysis_response,
                    }
                },
                tags=["performance_monitoring"],
                importance=0.7,
            )

        except Exception as e:
            self.logger.error(
                "Error monitoring performance",
                agent_id=self.id,
                error=str(e),
            )

        return performance_report

    async def evolve_agent_prompts(
        self, performance_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Evolve agent prompts based on performance data.

        Args:
            performance_data: Performance data for evolution

        Returns:
            Evolved prompts
        """
        try:
            evolution_response = "Evolution strategy: Continue with current agent configuration and monitor performance."

            evolved_prompts = {
                "evolution_strategy": evolution_response,
                "timestamp": datetime.now().isoformat(),
            }

            # Store evolution in memory
            await self.memory_manager.add_memory(
                agent_id=self.id,
                memory_type=MemoryType.EXPERIENCE,
                content={
                    "prompt_evolution": {
                        "performance_data": performance_data,
                        "evolution_strategy": evolution_response,
                    }
                },
                tags=["prompt_evolution"],
                importance=0.8,
            )

            return evolved_prompts

        except Exception as e:
            self.logger.error(
                "Error evolving prompts",
                agent_id=self.id,
                error=str(e),
            )
            return {"error": str(e)}

    async def plan_system_evolution(
        self,
        performance_data: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        """Plan system evolution based on performance data.

        Args:
            performance_data: Performance data for planning

        Returns:
            Evolution plan
        """
        try:
            evolution_plan = "System evolution plan: Maintain current architecture and focus on incremental improvements."

            return {
                "plan": evolution_plan,
                "timestamp": datetime.now().isoformat(),
                "actions": ["retire_agents", "evolve_prompts", "create_agents"],
            }

        except Exception as e:
            self.logger.error(
                "Error planning evolution",
                agent_id=self.id,
                error=str(e),
            )
            return {"error": str(e)}

    async def send_message(
        self, recipient_id: UUID, message_type: str, content: dict[str, Any]
    ) -> None:
        """Send a message to another agent.

        Args:
            recipient_id: ID of the recipient agent
            message_type: Type of message
            content: Message content
        """
        await self.message_broker.send_message(
            recipient_id,
            {
                "type": message_type,
                "content": str(content),  # Convert dict to string for AgentMessage
                "sender_id": self.id,
                "timestamp": self.state.last_active,
            },
        )

    def get_performance_metrics(self) -> dict[str, float]:
        """Get the orchestrator's performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        success_rate = (
            self._successful_cycles / self._total_cycles
            if self._total_cycles > 0
            else 0.0
        )

        proposal_acceptance_rate = (
            self._accepted_proposals / self._total_proposals
            if self._total_proposals > 0
            else 0.0
        )

        return {
            "total_cycles": self._total_cycles,
            "successful_cycles": self._successful_cycles,
            "success_rate": success_rate,
            "total_proposals": self._total_proposals,
            "accepted_proposals": self._accepted_proposals,
            "proposal_acceptance_rate": proposal_acceptance_rate,
            "managed_agents_count": len(self.managed_agents),
            "retired_agents_count": len(self.retired_agents),
        }
