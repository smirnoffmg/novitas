"""Code Agent for analyzing and improving code."""

import asyncio
from typing import Any
from uuid import UUID

from ..config.logging import get_logger
from ..core.models import AgentType
from ..core.models import ChangeProposal
from ..core.models import ImprovementType
from ..core.models import MemoryType
from ..core.protocols import DatabaseManager
from ..core.protocols import LLMClient
from ..core.protocols import MessageBroker
from .base import BaseAgent
from .memory import LangChainMemoryManager
from .memory import MemoryFilter


class CodeAgent(BaseAgent):
    """Agent responsible for analyzing code and suggesting improvements."""

    def __init__(
        self,
        database_manager: DatabaseManager,
        llm_client: LLMClient,
        message_broker: MessageBroker,
        agent_id: UUID,
        name: str,
        description: str,
        prompt: str,
    ) -> None:
        """Initialize the Code Agent.

        Args:
            database_manager: Database manager for persistence
            llm_client: LLM client for code analysis
            message_broker: Message broker for communication
            agent_id: Unique identifier for the agent
            name: Agent name
            description: Agent description
            prompt: Agent prompt template
        """
        super().__init__(
            database_manager=database_manager,
            llm_client=llm_client,
            message_broker=message_broker,
            agent_id=agent_id,
            name=name,
            description=description,
            agent_type=AgentType.CODE_AGENT,
            prompt=prompt,
        )

        # Initialize memory manager
        self.memory_manager = LangChainMemoryManager(database_manager)

        # Performance tracking
        self._total_analyses = 0
        self._total_proposals = 0
        self._successful_analyses = 0

        self.logger = get_logger("agent.code")

    async def _initialize_agent(self) -> None:
        """Initialize the code agent."""
        # Register with memory manager
        await self.memory_manager.register_agent(self)

        # Add initial memory about agent capabilities
        await self.memory_manager.add_memory(
            agent_id=self.id,
            memory_type=MemoryType.KNOWLEDGE,
            content={
                "capability": "code_analysis",
                "specialties": ["python", "code_quality", "best_practices"],
                "improvement_types": [
                    "type_hints",
                    "docstrings",
                    "naming",
                    "structure",
                ],
            },
            tags=["capabilities", "initialization"],
            importance=0.9,
        )

        self.logger.info("Code Agent initialized", agent_id=self.id)

    async def _execute_agent(self, context: dict[str, Any]) -> list[ChangeProposal]:
        """Execute the code agent's main logic.

        Args:
            context: Context containing files to analyze

        Returns:
            List of change proposals
        """
        try:
            self.logger.info(
                "Starting code analysis",
                agent_id=self.id,
                context_keys=list(context.keys()),
            )

            # Extract files to analyze
            files_to_analyze = context.get("files_to_analyze", [])
            file_contents = context.get("file_contents", {})
            previous_analysis = context.get("previous_analysis")

            if not files_to_analyze:
                self.logger.warning("No files to analyze", agent_id=self.id)
                return []

            # Analyze the codebase
            analysis_results = await self.analyze_codebase(file_contents)

            # Store analysis in memory
            await self.memory_manager.add_memory(
                agent_id=self.id,
                memory_type=MemoryType.EXPERIENCE,
                content={
                    "analysis_session": {
                        "files_analyzed": len(files_to_analyze),
                        "analysis_results": analysis_results,
                        "previous_analysis": previous_analysis,
                    }
                },
                tags=["analysis", "session"],
                importance=0.7,
            )

            # Generate improvement proposals
            proposals = await self.generate_improvement_proposals(analysis_results)

            # Update performance metrics
            self._total_analyses += 1
            self._total_proposals += len(proposals)
            self._successful_analyses += 1

            self.logger.info(
                "Code analysis completed",
                agent_id=self.id,
                files_analyzed=len(files_to_analyze),
                proposals_generated=len(proposals),
            )

            return proposals

        except Exception as e:
            self.logger.error(
                "Error during code analysis",
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
                tags=["error", "analysis"],
                importance=0.8,
            )
            return []

    async def _cleanup_agent(self) -> None:
        """Clean up the code agent."""
        # Unregister from memory manager
        await self.memory_manager.unregister_agent(self.id)

        self.logger.info("Code Agent cleaned up", agent_id=self.id)

    async def analyze_code_file(
        self, file_path: str, file_content: str
    ) -> dict[str, Any]:
        """Analyze a single code file.

        Args:
            file_path: Path to the file
            file_content: Content of the file

        Returns:
            Analysis results
        """
        # Get relevant memory for context
        memory_filter = MemoryFilter(
            memory_types=[MemoryType.KNOWLEDGE, MemoryType.EXPERIENCE],
            limit=5,
        )
        relevant_memory = await self.memory_manager.get_memory(self.id, memory_filter)

        # Build context from memory
        memory_context = ""
        for item in relevant_memory:
            memory_context += f"\nPrevious knowledge: {item.content}\n"

        # Create analysis prompt
        analysis_prompt = f"""
You are a code analysis expert. Analyze the following code file and provide detailed feedback.

File: {file_path}

Code:
{file_content}

{memory_context}

Please provide:
1. **Code Quality Assessment**: Evaluate the overall code quality
2. **Issues Found**: List any problems or areas for improvement
3. **Suggestions**: Provide specific, actionable suggestions
4. **Best Practices**: Identify any violations of best practices
5. **Security Considerations**: Note any security concerns
6. **Performance Insights**: Suggest performance improvements if applicable

Format your response as a structured analysis with clear sections.
"""

        try:
            # Get LLM analysis
            analysis_response = await self.llm_client.generate_response(
                prompt=analysis_prompt,
                context={"file_path": file_path, "file_content": file_content},
            )

            # Parse the response to extract suggestions
            suggestions = self._extract_suggestions(analysis_response)

            result = {
                "file_path": file_path,
                "analysis": analysis_response,
                "suggestions": suggestions,
                "timestamp": self.state.last_active,
            }

            # Store analysis in memory
            await self.memory_manager.add_memory(
                agent_id=self.id,
                memory_type=MemoryType.EXPERIENCE,
                content={
                    "file_analysis": {
                        "file_path": file_path,
                        "analysis": analysis_response,
                        "suggestions": suggestions,
                    }
                },
                tags=["analysis", "file", file_path.split("/")[-1]],
                importance=0.6,
            )

            return result

        except Exception as e:
            self.logger.error(
                "Error analyzing file",
                agent_id=self.id,
                file_path=file_path,
                error=str(e),
            )
            return {
                "file_path": file_path,
                "analysis": f"Error analyzing file: {e!s}",
                "suggestions": [],
                "error": True,
            }

    async def analyze_codebase(
        self, file_contents: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Analyze an entire codebase.

        Args:
            file_contents: Dictionary mapping file paths to content

        Returns:
            List of analysis results
        """
        results = []

        for file_path, content in file_contents.items():
            result = await self.analyze_code_file(file_path, content)
            results.append(result)

            # Small delay to avoid overwhelming the LLM
            await asyncio.sleep(0.1)

        return results

    async def generate_improvement_proposals(
        self, analysis_results: list[dict[str, Any]]
    ) -> list[ChangeProposal]:
        """Generate improvement proposals based on analysis results.

        Args:
            analysis_results: Results from code analysis

        Returns:
            List of change proposals
        """
        if not analysis_results:
            return []

        # Get relevant memory for proposal generation
        memory_filter = MemoryFilter(
            memory_types=[MemoryType.KNOWLEDGE, MemoryType.EXPERIENCE],
            limit=3,
        )
        relevant_memory = await self.memory_manager.get_memory(self.id, memory_filter)

        # Build context from memory
        memory_context = ""
        for item in relevant_memory:
            memory_context += f"\nPrevious experience: {item.content}\n"

        # Create proposal generation prompt
        proposal_prompt = f"""
Based on the following code analysis results, generate specific improvement proposals.

Analysis Results:
{analysis_results}

{memory_context}

For each improvement, provide:
1. **Description**: Clear description of the improvement
2. **File Path**: Which file needs to be changed
3. **Reasoning**: Why this improvement is valuable
4. **Confidence**: Confidence score (0.0 to 1.0)
5. **Priority**: High, Medium, or Low priority
6. **Proposed Changes**: Specific changes to make

Format each proposal as a structured improvement with clear sections.
"""

        try:
            # Get LLM proposals
            proposal_response = await self.llm_client.generate_response(
                prompt=proposal_prompt,
                context={"analysis_results": analysis_results},
            )

            # Parse proposals from response
            proposals = self._parse_proposals(proposal_response, analysis_results)

            # Store proposals in memory
            await self.memory_manager.add_memory(
                agent_id=self.id,
                memory_type=MemoryType.TASK_RESULT,
                content={
                    "proposals_generated": {
                        "count": len(proposals),
                        "proposals": [p.description for p in proposals],
                    }
                },
                tags=["proposals", "generation"],
                importance=0.8,
            )

            return proposals

        except Exception as e:
            self.logger.error(
                "Error generating proposals",
                agent_id=self.id,
                error=str(e),
            )
            return []

    async def prioritize_improvements(self, suggestions: list[str]) -> list[str]:
        """Prioritize improvements based on impact and effort.

        Args:
            suggestions: List of improvement suggestions

        Returns:
            Prioritized list of suggestions
        """
        if not suggestions:
            return []

        priority_prompt = f"""
Prioritize the following code improvement suggestions based on:
1. **Impact**: How much the improvement will help
2. **Effort**: How much work is required
3. **Risk**: Potential risks of the change
4. **Urgency**: How quickly it needs to be done

Suggestions to prioritize:
{chr(10).join(f"- {suggestion}" for suggestion in suggestions)}

Return the suggestions in order of priority (highest first) with brief reasoning for each.
"""

        try:
            prioritized_response = await self.llm_client.generate_response(
                prompt=priority_prompt,
                context={"suggestions": suggestions},
            )

            # Extract prioritized list
            return self._extract_prioritized_list(prioritized_response)

        except Exception as e:
            self.logger.error(
                "Error prioritizing improvements",
                agent_id=self.id,
                error=str(e),
            )
            return suggestions  # Return original order if prioritization fails

    def _extract_suggestions(self, analysis_response: str) -> list[str]:
        """Extract suggestions from analysis response.

        Args:
            analysis_response: Raw analysis response from LLM

        Returns:
            List of extracted suggestions
        """
        suggestions = []

        # Simple extraction - look for bullet points or numbered lists
        lines = analysis_response.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("-", "*", "•", "1.", "2.", "3.")):
                # Remove the bullet/number and clean up
                suggestion = line.lstrip("-*•1234567890. ").strip()
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions

    def _parse_proposals(
        self, proposal_response: str, analysis_results: list[dict[str, Any]]
    ) -> list[ChangeProposal]:
        """Parse proposals from LLM response.

        Args:
            proposal_response: Raw proposal response from LLM
            analysis_results: Original analysis results

        Returns:
            List of ChangeProposal objects
        """
        proposals = []

        # Simple parsing - in a real implementation, you might use structured output
        # For now, we'll create a basic proposal based on the first analysis result
        if analysis_results:
            first_result = analysis_results[0]

            # Create a basic proposal
            proposal = ChangeProposal(
                agent_id=self.id,
                improvement_type=ImprovementType.CODE_IMPROVEMENT,
                file_path=first_result.get("file_path", "unknown"),
                description="Code improvement based on analysis",
                reasoning=(
                    proposal_response[:200] + "..."
                    if len(proposal_response) > 200
                    else proposal_response
                ),
                proposed_changes={"analysis": proposal_response},
                confidence_score=0.7,  # Default confidence
            )
            proposals.append(proposal)

        return proposals

    def _extract_prioritized_list(self, prioritized_response: str) -> list[str]:
        """Extract prioritized list from response.

        Args:
            prioritized_response: Raw prioritized response from LLM

        Returns:
            List of prioritized suggestions
        """
        # Simple extraction - look for numbered items
        lines = prioritized_response.split("\n")
        prioritized = []

        for line in lines:
            line = line.strip()
            if line.startswith(("1.", "2.", "3.", "4.", "5.")):
                # Remove the number and clean up
                item = line.lstrip("1234567890. ").strip()
                if item:
                    prioritized.append(item)

        return prioritized

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
                "content": content,
                "sender_id": self.id,
                "timestamp": self.state.last_active,
            },
        )

    def get_performance_metrics(self) -> dict[str, float]:
        """Get the agent's performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        success_rate = (
            self._successful_analyses / self._total_analyses
            if self._total_analyses > 0
            else 0.0
        )

        return {
            "total_analyses": self._total_analyses,
            "total_proposals": self._total_proposals,
            "successful_analyses": self._successful_analyses,
            "success_rate": success_rate,
            "average_proposals_per_analysis": (
                self._total_proposals / self._total_analyses
                if self._total_analyses > 0
                else 0.0
            ),
        }
