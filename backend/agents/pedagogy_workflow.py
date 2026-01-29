"""
Pedagogy Workflow for orchestrating educational content generation agents
"""

from strands import Agent
from typing import Dict, Any, List, Optional
from .agent_factory import AgentFactory
from .exceptions import (
    WorkflowError,
    WorkflowExecutionError,
    WorkflowTimeoutError,
    AgentError,
)
from .retry_handler import RetryHandler
from config.agents_config import get_workflow_config
import logging
import asyncio
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class PedagogyWorkflow:
    """Workflow for orchestrating pedagogy agents in educational content generation with enhanced error handling"""

    def __init__(self, **kwargs):
        """
        Initialize pedagogy workflow

        Raises:
            WorkflowError: If workflow initialization fails
        """
        try:
            self.config = get_workflow_config()
            self.config.update(kwargs)

            # Initialize agents with error handling
            try:
                self.agents = AgentFactory.create_all_agents()
                logger.info("Initialized pedagogy workflow with all agents")
            except Exception as e:
                logger.error(f"Failed to initialize agents: {str(e)}")
                raise WorkflowError(
                    "Failed to initialize pedagogy agents", original_error=e
                )

            # Track workflow statistics
            self.execution_count = 0
            self.failure_count = 0
            self.last_execution_time: Optional[datetime] = None

        except WorkflowError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing workflow: {str(e)}")
            raise WorkflowError(
                "Unexpected error during workflow initialization", original_error=e
            )

    def execute(
        self, input_content: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete pedagogy workflow with enhanced error handling

        Args:
            input_content: Raw educational content to process
            context: Additional context for processing

        Returns:
            Complete educational script with all agent contributions

        Raises:
            WorkflowExecutionError: If workflow execution fails
            WorkflowTimeoutError: If workflow execution times out
        """
        self.execution_count += 1
        self.last_execution_time = datetime.now()

        failed_agents = []
        partial_results = {}

        try:
            logger.info(f"Starting pedagogy workflow execution #{self.execution_count}")

            # Initialize workflow context
            workflow_context = context or {}
            workflow_context["original_content"] = input_content
            workflow_context["execution_id"] = self.execution_count
            workflow_context["start_time"] = datetime.now().isoformat()

            # Execute agents in sequence with error handling
            try:
                results = self._execute_agent_sequence_with_fallback(
                    input_content, workflow_context, failed_agents, partial_results
                )
            except Exception as e:
                logger.error(f"Agent sequence execution failed: {str(e)}")
                raise WorkflowExecutionError(
                    "Failed to execute agent sequence",
                    failed_agents=failed_agents,
                    partial_results=partial_results,
                    original_error=e,
                )

            # Check if we have enough results to continue
            if not self._has_minimum_results(results):
                raise WorkflowExecutionError(
                    "Insufficient agent results to generate educational script",
                    failed_agents=failed_agents,
                    partial_results=results,
                )

            # Compile final educational script
            try:
                educational_script = self._compile_educational_script(
                    results, workflow_context
                )
            except Exception as e:
                logger.error(f"Failed to compile educational script: {str(e)}")
                raise WorkflowExecutionError(
                    "Failed to compile educational script from agent results",
                    failed_agents=failed_agents,
                    partial_results=results,
                    original_error=e,
                )

            # Add workflow metadata
            educational_script["workflow_metadata"] = {
                "execution_id": self.execution_count,
                "failed_agents": failed_agents,
                "successful_agents": [
                    k for k in results.keys() if "error" not in results[k]
                ],
                "execution_time": (
                    datetime.now()
                    - datetime.fromisoformat(workflow_context["start_time"])
                ).total_seconds(),
            }

            logger.info(
                f"Successfully completed pedagogy workflow execution #{self.execution_count}"
            )
            return educational_script

        except WorkflowExecutionError:
            self.failure_count += 1
            raise
        except Exception as e:
            self.failure_count += 1
            logger.error(f"Unexpected error in pedagogy workflow execution: {str(e)}")
            raise WorkflowExecutionError(
                "Unexpected error during workflow execution",
                failed_agents=failed_agents,
                partial_results=partial_results,
                original_error=e,
            )

    def _execute_agent_sequence_with_fallback(
        self,
        content: str,
        context: Dict[str, Any],
        failed_agents: List[str],
        partial_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute agents in defined sequence with fallback mechanisms

        Args:
            content: Content to process
            context: Processing context
            failed_agents: List to track failed agents
            partial_results: Dict to store partial results

        Returns:
            Dictionary of agent results
        """
        results = {}
        current_content = content

        # Define agent execution order
        agent_sequence = [
            "content_structuring",
            "learning_objectives",
            "assessment",
            "visualization",
            "narrative",
        ]

        # Track which agents are critical vs optional
        critical_agents = {"content_structuring", "learning_objectives"}

        for agent_type in agent_sequence:
            try:
                logger.info(f"Executing {agent_type} agent")

                # Update context with previous results
                agent_context = context.copy()
                agent_context["previous_results"] = results
                agent_context["failed_agents"] = failed_agents

                # Execute agent with error handling
                agent_result = self._execute_single_agent(
                    agent_type, current_content, agent_context
                )

                # Store result
                results[agent_type] = agent_result
                partial_results[agent_type] = agent_result

                logger.info(f"Completed {agent_type} agent execution")

            except AgentError as e:
                logger.error(f"Agent error executing {agent_type}: {str(e)}")
                failed_agents.append(agent_type)

                # Store error information
                results[agent_type] = {
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "error_details": e.to_dict() if hasattr(e, "to_dict") else {},
                }

                # If critical agent fails, try fallback
                if agent_type in critical_agents:
                    logger.warning(
                        f"Critical agent {agent_type} failed, attempting fallback"
                    )
                    fallback_result = self._create_fallback_result(
                        agent_type, content, context
                    )
                    if fallback_result:
                        results[agent_type] = fallback_result
                        logger.info(f"Using fallback result for {agent_type}")
                    else:
                        logger.error(f"Fallback failed for critical agent {agent_type}")
                        raise WorkflowExecutionError(
                            f"Critical agent {agent_type} failed and fallback unavailable",
                            failed_agents=failed_agents,
                            partial_results=results,
                        )
                else:
                    logger.warning(
                        f"Optional agent {agent_type} failed, continuing workflow"
                    )

            except Exception as e:
                logger.error(f"Unexpected error executing {agent_type} agent: {str(e)}")
                failed_agents.append(agent_type)
                results[agent_type] = {"error": str(e), "error_type": "UnexpectedError"}

                # Critical agents must succeed
                if agent_type in critical_agents:
                    raise WorkflowExecutionError(
                        f"Critical agent {agent_type} failed with unexpected error",
                        failed_agents=failed_agents,
                        partial_results=results,
                        original_error=e,
                    )

        return results

    def _execute_single_agent(
        self, agent_type: str, content: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single agent with retry logic

        Args:
            agent_type: Type of agent to execute
            content: Content to process
            context: Processing context

        Returns:
            Agent result

        Raises:
            AgentError: If agent execution fails
        """
        if agent_type not in self.agents:
            raise WorkflowExecutionError(
                f"Agent {agent_type} not found in workflow", failed_agents=[agent_type]
            )

        agent = self.agents[agent_type]

        # Execute with agent's built-in retry and error handling
        return agent.process_content(content, context)

    def _create_fallback_result(
        self, agent_type: str, content: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create fallback result for failed agent

        Args:
            agent_type: Type of agent that failed
            content: Original content
            context: Processing context

        Returns:
            Fallback result or None if not available
        """
        logger.info(f"Creating fallback result for {agent_type}")

        # Basic fallback strategies for different agent types
        if agent_type == "content_structuring":
            return {
                "agent_type": agent_type,
                "processed_content": content,
                "metadata": {
                    "agent_name": f"{agent_type} (fallback)",
                    "processing_timestamp": datetime.now().isoformat(),
                    "fallback": True,
                },
                "sections": [{"title": "Main Content", "content": content}],
            }

        elif agent_type == "learning_objectives":
            return {
                "agent_type": agent_type,
                "processed_content": "Generate learning objectives based on content",
                "metadata": {
                    "agent_name": f"{agent_type} (fallback)",
                    "processing_timestamp": datetime.now().isoformat(),
                    "fallback": True,
                },
                "objectives": [
                    "Understand the main concepts",
                    "Apply knowledge to examples",
                ],
            }

        # No fallback available for other agents
        return None

    def _has_minimum_results(self, results: Dict[str, Any]) -> bool:
        """
        Check if we have minimum required results to continue

        Args:
            results: Agent results

        Returns:
            True if minimum requirements met
        """
        # Must have at least content_structuring or learning_objectives
        critical_agents = {"content_structuring", "learning_objectives"}

        successful_critical = sum(
            1
            for agent in critical_agents
            if agent in results and "error" not in results[agent]
        )

        return successful_critical >= 1

    def _compile_educational_script(
        self, agent_results: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile agent results into final educational script"""

        educational_script = {
            "title": "Generated Educational Content",
            "original_content": context.get("original_content", ""),
            "learning_objectives": [],
            "sections": [],
            "assessments": [],
            "animations": [],
            "metadata": {
                "generation_timestamp": None,  # Will be set by calling service
                "agents_used": list(agent_results.keys()),
                "workflow_version": "1.0",
            },
        }

        # Extract structured content from agent results
        for agent_type, result in agent_results.items():
            if "error" in result:
                logger.warning(f"Skipping {agent_type} due to error: {result['error']}")
                continue

            # Process each agent's contribution
            if agent_type == "content_structuring":
                educational_script["sections"] = self._extract_sections(result)
            elif agent_type == "learning_objectives":
                educational_script["learning_objectives"] = self._extract_objectives(
                    result
                )
            elif agent_type == "assessment":
                educational_script["assessments"] = self._extract_assessments(result)
            elif agent_type == "visualization":
                educational_script["animations"] = self._extract_animations(result)
            elif agent_type == "narrative":
                educational_script["narrative_flow"] = self._extract_narrative(result)

        return educational_script

    def _extract_sections(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract structured sections from content structuring agent"""
        try:
            # Check if we have enhanced structured content
            if "structured_content" in result:
                structured_content = result["structured_content"]

                # If we have a content analysis with sections
                if (
                    isinstance(structured_content, dict)
                    and "sections" in structured_content
                ):
                    sections = structured_content["sections"]
                    if isinstance(sections, list):
                        return [
                            (
                                section
                                if isinstance(section, dict)
                                else {"title": "Section", "content": str(section)}
                            )
                            for section in sections
                        ]

                # If we have raw response, try to parse it
                raw_response = structured_content.get("raw_response", "")
                if raw_response:
                    return self._parse_sections_from_response(raw_response)

            # Fallback: create basic section from processed content
            processed_content = result.get("processed_content", "")
            if processed_content:
                # Try to split content into logical sections
                sections = self._create_basic_sections(processed_content)
                return sections

            # Ultimate fallback
            return [
                {
                    "title": "Main Content",
                    "content": result.get("processed_content", ""),
                }
            ]

        except Exception as e:
            logger.warning(f"Error extracting sections: {str(e)}")
            return [
                {
                    "title": "Main Content",
                    "content": result.get("processed_content", ""),
                }
            ]

    def _parse_sections_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse sections from agent response text"""
        sections = []

        # Look for section markers in the response
        section_patterns = [
            r"(?:^|\n)(?:Section|Chapter|Part)\s*\d*[:\-\s]*(.+?)(?=\n(?:Section|Chapter|Part)|\n\n|\Z)",
            r"(?:^|\n)#{1,3}\s*(.+?)(?=\n#|\n\n|\Z)",  # Markdown headers
            r"(?:^|\n)([A-Z][A-Za-z\s]{5,50}):?\n",  # Title-like lines
        ]

        for pattern in section_patterns:
            matches = re.findall(pattern, response, re.MULTILINE | re.DOTALL)
            if matches:
                for i, match in enumerate(matches):
                    if isinstance(match, tuple):
                        title = match[0].strip()
                        content = match[1].strip() if len(match) > 1 else ""
                    else:
                        title = match.strip()
                        content = ""

                    if title and len(title) > 2:
                        sections.append(
                            {
                                "title": title,
                                "content": content or f"Content for {title}",
                                "order": i,
                                "section_type": "main_concept",
                            }
                        )
                break  # Use first successful pattern

        # If no sections found, create from paragraphs
        if not sections:
            sections = self._create_basic_sections(response)

        return sections[:10]  # Limit to 10 sections

    def _create_basic_sections(self, content: str) -> List[Dict[str, Any]]:
        """Create basic sections from content"""
        sections = []

        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        if len(paragraphs) <= 1:
            return [
                {
                    "title": "Main Content",
                    "content": content,
                    "section_type": "main_concept",
                }
            ]

        # Group paragraphs into sections
        section_size = max(1, len(paragraphs) // 3)  # Aim for ~3 sections
        current_section = []
        section_count = 0

        for i, paragraph in enumerate(paragraphs):
            current_section.append(paragraph)

            # Create section when we have enough content or reach the end
            if len(current_section) >= section_size or i == len(paragraphs) - 1:
                section_content = "\n\n".join(current_section)

                # Generate section title
                first_sentence = current_section[0].split(".")[0].strip()
                if len(first_sentence) < 80:
                    title = first_sentence
                else:
                    title = f"Section {section_count + 1}"

                sections.append(
                    {
                        "title": title,
                        "content": section_content,
                        "order": section_count,
                        "section_type": (
                            "main_concept" if section_count > 0 else "introduction"
                        ),
                    }
                )

                current_section = []
                section_count += 1

        return sections

    def _extract_objectives(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract learning objectives from learning objectives agent"""
        try:
            # Check if we have structured objectives
            if "learning_objectives" in result:
                objectives = result["learning_objectives"]
                if isinstance(objectives, list):
                    return [
                        {
                            "objective": (
                                obj
                                if isinstance(obj, str)
                                else obj.get("objective", str(obj))
                            ),
                            "bloom_level": "understand",  # Default Bloom's level
                            "measurable": True,
                        }
                        for obj in objectives
                    ]

            # Try to parse from processed content or raw response
            content = result.get("processed_content", "") or result.get(
                "raw_response", ""
            )
            if content:
                objectives = self._parse_objectives_from_text(content)
                if objectives:
                    return objectives

            # Fallback objectives based on content analysis
            return [
                {
                    "objective": "Understand the main concepts presented",
                    "bloom_level": "understand",
                    "measurable": True,
                },
                {
                    "objective": "Apply knowledge to practical examples",
                    "bloom_level": "apply",
                    "measurable": True,
                },
            ]

        except Exception as e:
            logger.warning(f"Error extracting objectives: {str(e)}")
            return [
                {
                    "objective": "Understand the main concepts",
                    "bloom_level": "understand",
                    "measurable": True,
                },
                {
                    "objective": "Apply knowledge effectively",
                    "bloom_level": "apply",
                    "measurable": True,
                },
            ]

    def _extract_assessments(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract assessments from assessment agent"""
        try:
            # Check if we have structured assessments
            if "assessments" in result:
                assessments = result["assessments"]
                if isinstance(assessments, list):
                    return assessments

            # Try to parse from processed content
            content = result.get("processed_content", "") or result.get(
                "raw_response", ""
            )
            if content:
                assessments = self._parse_assessments_from_text(content)
                if assessments:
                    return assessments

            # Generate basic assessment based on content
            return [
                {
                    "type": "quiz",
                    "title": "Knowledge Check",
                    "questions": [
                        {
                            "question": "What are the main concepts covered in this content?",
                            "question_type": "open_ended",
                            "points": 10,
                        },
                        {
                            "question": "How would you apply this knowledge in practice?",
                            "question_type": "open_ended",
                            "points": 15,
                        },
                    ],
                    "rubric": "Assess understanding of key concepts and practical application",
                }
            ]

        except Exception as e:
            logger.warning(f"Error extracting assessments: {str(e)}")
            return [
                {
                    "type": "quiz",
                    "title": "Basic Assessment",
                    "questions": [],
                    "rubric": "Basic assessment",
                }
            ]

    def _extract_animations(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract animation specifications from visualization agent"""
        try:
            # Check if we have structured animations
            if "animations" in result:
                animations = result["animations"]
                if isinstance(animations, list):
                    return animations

            # Try to parse from processed content
            content = result.get("processed_content", "") or result.get(
                "raw_response", ""
            )
            if content:
                animations = self._parse_animations_from_text(content)
                if animations:
                    return animations

            # Generate basic animation suggestions
            return [
                {
                    "concept": "Introduction",
                    "type": "text_animation",
                    "description": "Animated title and key points introduction",
                    "duration": 5,
                },
                {
                    "concept": "Main Content",
                    "type": "content_reveal",
                    "description": "Progressive content revelation with emphasis",
                    "duration": 10,
                },
            ]

        except Exception as e:
            logger.warning(f"Error extracting animations: {str(e)}")
            return [
                {
                    "concept": "Basic Animation",
                    "type": "text",
                    "description": "Simple text animation",
                }
            ]

    def _extract_narrative(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract narrative flow from narrative agent"""
        try:
            # Check if we have structured narrative
            if "narrative_flow" in result:
                return result["narrative_flow"]

            # Generate basic narrative structure
            return {
                "flow": "sequential",
                "tone": "educational",
                "pacing": "moderate",
                "engagement_strategies": ["questions", "examples", "visual_aids"],
            }

        except Exception as e:
            logger.warning(f"Error extracting narrative: {str(e)}")
            return {"flow": "sequential", "tone": "educational"}

    def _parse_objectives_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse learning objectives from text content"""
        objectives = []

        # Look for objective patterns in text
        objective_patterns = [
            r"(?:objective|goal|aim|learn|understand|apply)[:\-\s]*(.+?)(?=\n|$)",
            r"(?:students? will|learners? will|you will)[:\-\s]*(.+?)(?=\n|$)",
            r"(?:by the end|after this|upon completion)[:\-\s]*(.+?)(?=\n|$)",
        ]

        for pattern in objective_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                objective_text = match.strip()
                if len(objective_text) > 10 and len(objective_text) < 200:
                    objectives.append(
                        {
                            "objective": objective_text,
                            "bloom_level": self._determine_blooms_level(objective_text),
                            "measurable": self._is_measurable_objective(objective_text),
                        }
                    )

        # If no objectives found, generate from content analysis
        if not objectives:
            objectives = self._generate_objectives_from_content(text)

        return objectives[:5]  # Limit to 5 objectives

    def _parse_assessments_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse assessments from text content"""
        assessments = []

        # Look for question patterns
        question_patterns = [
            r"(?:question|quiz|test|assess)[:\-\s]*(.+?)(?=\n|$)",
            r"(?:\?|\d+\.)\s*(.+?\?)",
            r"(?:evaluate|measure|check)[:\-\s]*(.+?)(?=\n|$)",
        ]

        questions = []
        for pattern in question_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                question_text = match.strip()
                if len(question_text) > 10:
                    questions.append(
                        {
                            "question": question_text,
                            "question_type": "open_ended",
                            "points": 10,
                        }
                    )

        if questions:
            assessments.append(
                {
                    "type": "quiz",
                    "title": "Content Assessment",
                    "questions": questions[:5],  # Limit to 5 questions
                    "rubric": "Assess understanding and application of key concepts",
                }
            )

        return assessments

    def _parse_animations_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse animation suggestions from text content"""
        animations = []

        # Look for visual/animation keywords
        visual_keywords = [
            "diagram",
            "chart",
            "graph",
            "illustration",
            "visual",
            "animation",
            "demonstrate",
            "show",
            "display",
            "visualize",
            "animate",
        ]

        sentences = text.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in visual_keywords):
                animations.append(
                    {
                        "concept": (
                            sentence[:50] + "..." if len(sentence) > 50 else sentence
                        ),
                        "type": "visual_aid",
                        "description": f"Visual representation of: {sentence}",
                        "duration": 8,
                    }
                )

        return animations[:3]  # Limit to 3 animations

    def _determine_blooms_level(self, objective_text: str) -> str:
        """Determine Bloom's taxonomy level from objective text"""
        text_lower = objective_text.lower()

        if any(
            word in text_lower
            for word in ["create", "design", "develop", "compose", "construct"]
        ):
            return "create"
        elif any(
            word in text_lower
            for word in ["evaluate", "assess", "critique", "judge", "compare"]
        ):
            return "evaluate"
        elif any(
            word in text_lower
            for word in ["analyze", "examine", "investigate", "categorize"]
        ):
            return "analyze"
        elif any(
            word in text_lower
            for word in ["apply", "use", "implement", "demonstrate", "solve"]
        ):
            return "apply"
        elif any(
            word in text_lower
            for word in ["understand", "explain", "describe", "summarize"]
        ):
            return "understand"
        else:
            return "remember"

    def _is_measurable_objective(self, objective_text: str) -> bool:
        """Check if objective contains measurable action verbs"""
        measurable_verbs = [
            "identify",
            "list",
            "describe",
            "explain",
            "demonstrate",
            "apply",
            "analyze",
            "evaluate",
            "create",
            "solve",
            "calculate",
            "compare",
        ]
        text_lower = objective_text.lower()
        return any(verb in text_lower for verb in measurable_verbs)

    def _generate_objectives_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Generate basic objectives from content analysis"""
        # Simple content analysis to generate objectives
        word_count = len(content.split())

        objectives = [
            {
                "objective": "Understand the key concepts presented in the content",
                "bloom_level": "understand",
                "measurable": True,
            }
        ]

        if word_count > 500:
            objectives.append(
                {
                    "objective": "Analyze the relationships between different concepts",
                    "bloom_level": "analyze",
                    "measurable": True,
                }
            )

        if word_count > 1000:
            objectives.append(
                {
                    "objective": "Apply the learned concepts to practical scenarios",
                    "bloom_level": "apply",
                    "measurable": True,
                }
            )

        return objectives
