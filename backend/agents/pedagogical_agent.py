"""
Pedagogical Agent for expanding and enriching educational content context.

This agent is used ONLY for text input to expand the raw context into
a more comprehensive educational framework before FDA generation.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .base_agent import BaseEducationalAgent
from .exceptions import AgentExecutionError, AgentValidationError

logger = logging.getLogger(__name__)


@dataclass
class PedagogicalOutput:
    """Output from the Pedagogical Agent"""
    expanded_content: str
    learning_objectives: list[str]
    key_concepts: list[str]
    difficulty_assessment: str
    suggested_structure: list[Dict[str, Any]]
    prerequisites: list[str]
    metadata: Dict[str, Any]


class PedagogicalAgent(BaseEducationalAgent):
    """
    Pedagogical Agent for expanding raw text context.
    
    This agent analyzes raw text input and expands it into a comprehensive
    educational framework with:
    - Expanded content with additional context and explanations
    - Identified learning objectives
    - Key concepts extraction
    - Difficulty assessment
    - Suggested content structure
    - Prerequisites identification
    
    NOTE: This agent should ONLY be used for text input. 
    File uploads and web URLs should skip this agent as their content
    should remain biased towards the original source material.
    """

    def __init__(self, **kwargs):
        """Initialize the Pedagogical Agent"""
        super().__init__("pedagogical", **kwargs)
        logger.info("Initialized Pedagogical Agent for text context expansion")

    def process_content(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process and expand raw text content into comprehensive educational context.
        
        Args:
            content: Raw text content to expand
            context: Additional context (topic, difficulty_level, target_audience, learning_goals)
            
        Returns:
            Expanded content with educational framework
        """
        context = context or {}
        
        # Validate input
        if not content or len(content.strip()) < 50:
            raise AgentValidationError(
                "Content too short for pedagogical expansion. Minimum 50 characters required.",
                agent_type="pedagogical"
            )

        try:
            logger.info(f"Starting pedagogical expansion for content of length {len(content)}")
            
            # Build the prompt for context expansion
            prompt = self._build_expansion_prompt(content, context)
            
            # Execute the agent
            result = self.agent(prompt)
            
            # Parse the response using Strands output
            parsed_result = self._parse_pedagogical_output(result, context)
            
            logger.info("Successfully completed pedagogical expansion")
            return parsed_result

        except AgentValidationError:
            raise
        except Exception as e:
            logger.error(f"Pedagogical expansion failed: {str(e)}")
            raise AgentExecutionError(
                f"Failed to expand content pedagogically: {str(e)}",
                agent_type="pedagogical",
                original_error=e
            )

    def _build_expansion_prompt(self, content: str, context: Dict[str, Any]) -> str:
        """Build the prompt for pedagogical expansion"""
        
        topic = context.get("topic", "")
        difficulty_level = context.get("difficulty_level", "intermediate")
        target_audience = context.get("target_audience", "general")
        learning_goals = context.get("learning_goals", [])
        
        goals_text = ""
        if learning_goals:
            goals_text = f"\n\nSpecified Learning Goals:\n" + "\n".join(f"- {goal}" for goal in learning_goals)
        
        prompt = f"""Analyze and expand the following educational content into a comprehensive teaching framework.

TARGET CONTEXT:
- Topic: {topic if topic else "To be determined from content"}
- Difficulty Level: {difficulty_level}
- Target Audience: {target_audience}
{goals_text}

ORIGINAL CONTENT:
{content}

YOUR TASK:
Expand this content into a comprehensive educational framework. Provide your response in the following structured format:

## EXPANDED CONTENT
[Provide an enriched version of the content with additional context, explanations, examples, and connections to related concepts. Make it more comprehensive while maintaining accuracy.]

## LEARNING OBJECTIVES
[List 3-5 clear, measurable learning objectives using action verbs (understand, analyze, apply, create, evaluate)]
- Objective 1
- Objective 2
- Objective 3

## KEY CONCEPTS
[List the essential concepts that students must understand]
- Concept 1: Brief description
- Concept 2: Brief description
- Concept 3: Brief description

## DIFFICULTY ASSESSMENT
[Assess the actual difficulty level: beginner, intermediate, or advanced]
Level: [level]
Justification: [brief explanation]

## SUGGESTED STRUCTURE
[Propose how the content should be organized for optimal learning]
1. Section Title - Brief description (estimated duration in minutes)
2. Section Title - Brief description (estimated duration in minutes)
3. Section Title - Brief description (estimated duration in minutes)

## PREREQUISITES
[List any prior knowledge required]
- Prerequisite 1
- Prerequisite 2

Ensure your expansion maintains the core meaning while making the content more suitable for educational video presentation."""

        return prompt

    def _parse_pedagogical_output(
        self,
        agent_response: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse the agent response into structured output.
        Uses the Strands SDK response format (not regex).
        """
        # Get the text content from the Strands response
        if hasattr(agent_response, 'message'):
            response_text = str(agent_response.message)
        elif hasattr(agent_response, 'content'):
            response_text = str(agent_response.content)
        else:
            response_text = str(agent_response)
        
        # Initialize output structure
        result = {
            "agent_type": "pedagogical",
            "expanded_content": "",
            "learning_objectives": [],
            "key_concepts": [],
            "difficulty_assessment": context.get("difficulty_level", "intermediate"),
            "suggested_structure": [],
            "prerequisites": [],
            "metadata": {
                "original_length": len(context.get("original_content", "")),
                "expanded": True,
                "target_audience": context.get("target_audience", "general"),
            }
        }
        
        # Parse sections using text processing (not regex for parsing structured LLM output)
        lines = response_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Detect section headers
            if line_stripped.startswith("## EXPANDED CONTENT"):
                if current_section and current_content:
                    self._save_section(result, current_section, current_content)
                current_section = "expanded_content"
                current_content = []
            elif line_stripped.startswith("## LEARNING OBJECTIVES"):
                if current_section and current_content:
                    self._save_section(result, current_section, current_content)
                current_section = "learning_objectives"
                current_content = []
            elif line_stripped.startswith("## KEY CONCEPTS"):
                if current_section and current_content:
                    self._save_section(result, current_section, current_content)
                current_section = "key_concepts"
                current_content = []
            elif line_stripped.startswith("## DIFFICULTY ASSESSMENT"):
                if current_section and current_content:
                    self._save_section(result, current_section, current_content)
                current_section = "difficulty_assessment"
                current_content = []
            elif line_stripped.startswith("## SUGGESTED STRUCTURE"):
                if current_section and current_content:
                    self._save_section(result, current_section, current_content)
                current_section = "suggested_structure"
                current_content = []
            elif line_stripped.startswith("## PREREQUISITES"):
                if current_section and current_content:
                    self._save_section(result, current_section, current_content)
                current_section = "prerequisites"
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            self._save_section(result, current_section, current_content)
        
        # Ensure we have expanded content
        if not result["expanded_content"]:
            result["expanded_content"] = response_text
        
        return result

    def _save_section(
        self,
        result: Dict[str, Any],
        section: str,
        content: list[str]
    ) -> None:
        """Save parsed section content to result"""
        content_text = '\n'.join(content).strip()
        
        if section == "expanded_content":
            result["expanded_content"] = content_text
        
        elif section == "learning_objectives":
            objectives = []
            for line in content:
                line = line.strip()
                if line.startswith("- ") or line.startswith("* "):
                    objectives.append(line[2:].strip())
                elif line and not line.startswith("#"):
                    objectives.append(line)
            result["learning_objectives"] = [obj for obj in objectives if obj]
        
        elif section == "key_concepts":
            concepts = []
            for line in content:
                line = line.strip()
                if line.startswith("- ") or line.startswith("* "):
                    concepts.append(line[2:].strip())
                elif line and not line.startswith("#"):
                    concepts.append(line)
            result["key_concepts"] = [c for c in concepts if c]
        
        elif section == "difficulty_assessment":
            for line in content:
                line_lower = line.lower().strip()
                if "level:" in line_lower:
                    level = line_lower.split("level:")[-1].strip()
                    if "beginner" in level:
                        result["difficulty_assessment"] = "beginner"
                    elif "advanced" in level:
                        result["difficulty_assessment"] = "advanced"
                    else:
                        result["difficulty_assessment"] = "intermediate"
                    break
        
        elif section == "suggested_structure":
            structure = []
            for line in content:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Extract section info
                    section_text = line.lstrip("0123456789.-) ").strip()
                    if section_text:
                        structure.append({
                            "title": section_text.split(" - ")[0] if " - " in section_text else section_text,
                            "description": section_text
                        })
            result["suggested_structure"] = structure
        
        elif section == "prerequisites":
            prereqs = []
            for line in content:
                line = line.strip()
                if line.startswith("- ") or line.startswith("* "):
                    prereqs.append(line[2:].strip())
                elif line and not line.startswith("#"):
                    prereqs.append(line)
            result["prerequisites"] = [p for p in prereqs if p]
