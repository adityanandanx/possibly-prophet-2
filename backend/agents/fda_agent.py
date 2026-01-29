"""
FDA (Formal Description of Animation) Agent for Educational Content Generator

This agent generates a Formal Description of Animation (FDA) from educational content.
The FDA includes explicit rules and specifications for animations that will be
converted into Manim code by the Manim Generation Agent.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json

from .base_agent import BaseEducationalAgent
from .exceptions import AgentExecutionError, AgentValidationError

logger = logging.getLogger(__name__)


class AnimationIntent(Enum):
    """Types of animation intents for educational content"""
    INTRODUCE = "introduce"  # Introducing new concept
    EXPLAIN = "explain"  # Explaining with visuals
    DEMONSTRATE = "demonstrate"  # Showing examples
    TRANSITION = "transition"  # Moving between concepts
    EMPHASIZE = "emphasize"  # Highlighting key points
    COMPARE = "compare"  # Comparing concepts
    SUMMARIZE = "summarize"  # Summarizing content
    ASSESS = "assess"  # Assessment/quiz elements


class VisualElement(Enum):
    """Types of visual elements"""
    TEXT = "text"
    EQUATION = "equation"
    DIAGRAM = "diagram"
    GRAPH = "graph"
    SHAPE = "shape"
    ARROW = "arrow"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    IMAGE = "image"


@dataclass
class AnimationRule:
    """A single animation rule in the FDA"""
    rule_id: str
    intent: str
    visual_elements: List[Dict[str, Any]]
    animations: List[Dict[str, Any]]
    timing: Dict[str, Any]
    narration: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "intent": self.intent,
            "visual_elements": self.visual_elements,
            "animations": self.animations,
            "timing": self.timing,
            "narration": self.narration,
            "notes": self.notes
        }


@dataclass
class SlideSpecification:
    """Specification for a single slide in the presentation"""
    slide_id: str
    slide_number: int
    title: str
    slide_type: str
    content: Dict[str, Any]
    animation_rules: List[AnimationRule]
    duration_seconds: float
    transition_in: str = "fade_in"
    transition_out: str = "fade_out"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slide_id": self.slide_id,
            "slide_number": self.slide_number,
            "title": self.title,
            "slide_type": self.slide_type,
            "content": self.content,
            "animation_rules": [rule.to_dict() for rule in self.animation_rules],
            "duration_seconds": self.duration_seconds,
            "transition_in": self.transition_in,
            "transition_out": self.transition_out
        }


@dataclass
class FDAOutput:
    """Complete FDA output structure"""
    title: str
    topic: str
    total_duration_seconds: float
    difficulty_level: str
    target_audience: str
    slides: List[SlideSpecification]
    global_settings: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "topic": self.topic,
            "total_duration_seconds": self.total_duration_seconds,
            "difficulty_level": self.difficulty_level,
            "target_audience": self.target_audience,
            "slides": [slide.to_dict() for slide in self.slides],
            "global_settings": self.global_settings,
            "metadata": self.metadata
        }


class FDAAgent(BaseEducationalAgent):
    """
    FDA (Formal Description of Animation) Agent.
    
    This agent takes educational content (either expanded by the Pedagogical Agent
    for text input, or raw content from file/URL sources) and generates a 
    Formal Description of Animation (FDA).
    
    The FDA includes:
    - Slide specifications with content and layout
    - Animation rules with explicit timing and effects
    - Visual element definitions
    - Narration scripts for each slide
    - Global presentation settings
    
    The FDA output is then used by the Manim Generation Agent to produce
    the actual Manim code.
    """

    def __init__(self, **kwargs):
        """Initialize the FDA Agent"""
        super().__init__("fda", **kwargs)
        
        # Default presentation settings
        self.default_settings = {
            "background_color": "WHITE",
            "primary_color": "BLUE",
            "secondary_color": "DARK_GRAY",
            "accent_color": "RED",
            "title_font_size": 48,
            "body_font_size": 28,
            "caption_font_size": 20,
            "default_animation_duration": 1.0,
            "default_wait_time": 2.0,
            "slide_margin": 0.5,
        }
        
        logger.info("Initialized FDA Agent for animation description generation")

    def process_content(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process educational content and generate FDA.
        
        Args:
            content: Educational content (may be expanded by Pedagogical Agent or raw from file/URL)
            context: Additional context including:
                - topic: Topic name
                - difficulty_level: beginner/intermediate/advanced
                - target_audience: Target audience description
                - learning_goals: List of learning goals
                - input_type: text/file/url (determines if content was expanded)
                - pedagogical_output: Output from Pedagogical Agent (for text input)
                
        Returns:
            FDA specification dictionary
        """
        context = context or {}
        
        # Validate input
        if not content or len(content.strip()) < 20:
            raise AgentValidationError(
                "Content too short for FDA generation. Minimum 20 characters required.",
                agent_type="fda"
            )

        try:
            logger.info(f"Starting FDA generation for content of length {len(content)}")
            
            # Build the FDA generation prompt
            prompt = self._build_fda_prompt(content, context)
            
            # Execute the agent
            result = self.agent(prompt)
            
            # Parse the response
            parsed_result = self._parse_fda_output(result, context)
            
            logger.info(f"Successfully generated FDA with {len(parsed_result.get('slides', []))} slides")
            return parsed_result

        except AgentValidationError:
            raise
        except Exception as e:
            logger.error(f"FDA generation failed: {str(e)}")
            raise AgentExecutionError(
                f"Failed to generate FDA: {str(e)}",
                agent_type="fda",
                original_error=e
            )

    def _build_fda_prompt(self, content: str, context: Dict[str, Any]) -> str:
        """Build the prompt for FDA generation"""
        
        topic = context.get("topic", "Educational Content")
        difficulty_level = context.get("difficulty_level", "intermediate")
        target_audience = context.get("target_audience", "general")
        learning_goals = context.get("learning_goals", [])
        input_type = context.get("input_type", "text")
        
        # Get pedagogical output if available (text input only)
        pedagogical_output = context.get("pedagogical_output", {})
        
        # Build learning objectives section
        objectives_text = ""
        if pedagogical_output.get("learning_objectives"):
            objectives_text = "\n\nLEARNING OBJECTIVES (from pedagogical analysis):\n"
            for obj in pedagogical_output["learning_objectives"]:
                objectives_text += f"- {obj}\n"
        elif learning_goals:
            objectives_text = "\n\nLEARNING GOALS:\n"
            for goal in learning_goals:
                objectives_text += f"- {goal}\n"
        
        # Build structure suggestion if available
        structure_text = ""
        if pedagogical_output.get("suggested_structure"):
            structure_text = "\n\nSUGGESTED STRUCTURE (from pedagogical analysis):\n"
            for section in pedagogical_output["suggested_structure"]:
                structure_text += f"- {section.get('title', 'Section')}: {section.get('description', '')}\n"

        prompt = f"""Generate a Formal Description of Animation (FDA) for the following educational content.

PRESENTATION CONTEXT:
- Topic: {topic}
- Difficulty Level: {difficulty_level}
- Target Audience: {target_audience}
- Content Source: {input_type}
{objectives_text}
{structure_text}

EDUCATIONAL CONTENT:
{content}

YOUR TASK:
Create a detailed FDA (Formal Description of Animation) that specifies exactly how this content should be presented as an animated educational video.

Output your FDA in the following JSON structure:

```json
{{
    "title": "Presentation Title",
    "topic": "{topic}",
    "total_duration_seconds": 0,
    "difficulty_level": "{difficulty_level}",
    "target_audience": "{target_audience}",
    "global_settings": {{
        "background_color": "WHITE",
        "primary_color": "BLUE",
        "secondary_color": "DARK_GRAY",
        "accent_color": "RED",
        "title_font_size": 48,
        "body_font_size": 28
    }},
    "slides": [
        {{
            "slide_id": "slide_1",
            "slide_number": 1,
            "title": "Slide Title",
            "slide_type": "title|concept|example|diagram|equation|summary|assessment",
            "duration_seconds": 10,
            "content": {{
                "main_text": "Main content text",
                "bullet_points": ["Point 1", "Point 2"],
                "equations": ["E = mc^2"],
                "visual_description": "Description of any diagrams or visuals"
            }},
            "animation_rules": [
                {{
                    "rule_id": "rule_1",
                    "intent": "introduce|explain|emphasize|transition",
                    "visual_elements": [
                        {{
                            "type": "text|equation|shape|arrow|diagram",
                            "content": "Element content or description",
                            "position": "center|top|bottom|left|right",
                            "style": {{
                                "color": "BLUE",
                                "font_size": 36
                            }}
                        }}
                    ],
                    "animations": [
                        {{
                            "action": "write|fade_in|fade_out|transform|move|highlight",
                            "target": "element reference",
                            "duration": 1.0,
                            "delay": 0
                        }}
                    ],
                    "timing": {{
                        "start": 0,
                        "duration": 3,
                        "wait_after": 2
                    }},
                    "narration": "What the narrator should say during this animation"
                }}
            ],
            "transition_in": "fade_in",
            "transition_out": "fade_out"
        }}
    ]
}}
```

ANIMATION GUIDELINES:
1. TITLE SLIDE: Start with a title slide introducing the topic
2. CONCEPT SLIDES: Break down main concepts into digestible slides
3. VISUAL HIERARCHY: Use animations to guide attention
4. PACING: Include appropriate wait times for comprehension
5. EMPHASIS: Use color changes and highlights for key points
6. TRANSITIONS: Smooth transitions between sections
7. SUMMARY: End with a summary slide
8. TIMING: Total duration should be appropriate for the content depth

Ensure each slide has:
- Clear title
- Specific visual elements with exact content
- Animation sequence with timing
- Narration script for voiceover
- Appropriate duration

Generate a complete FDA that can be directly converted to Manim code."""

        return prompt

    def _parse_fda_output(
        self,
        agent_response: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse the agent response into structured FDA output.
        Uses Strands SDK response format.
        """
        # Get the text content from the Strands response
        if hasattr(agent_response, 'message'):
            response_text = str(agent_response.message)
        elif hasattr(agent_response, 'content'):
            response_text = str(agent_response.content)
        else:
            response_text = str(agent_response)
        
        # Try to extract JSON from the response
        fda_dict = self._extract_json(response_text)
        
        if fda_dict:
            # Validate and enhance the parsed FDA
            fda_dict = self._validate_and_enhance_fda(fda_dict, context)
        else:
            # Fallback: Create basic FDA from content
            logger.warning("Could not parse JSON from FDA response, creating fallback FDA")
            fda_dict = self._create_fallback_fda(response_text, context)
        
        # Add metadata
        fda_dict["metadata"] = {
            "agent_type": "fda",
            "input_type": context.get("input_type", "text"),
            "generation_successful": True,
            "slide_count": len(fda_dict.get("slides", [])),
        }
        
        return fda_dict

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from response text"""
        # Find JSON content between code blocks or as plain JSON
        json_start = -1
        json_end = -1
        
        # Look for JSON in code blocks
        if "```json" in text:
            json_start = text.find("```json") + 7
            json_end = text.find("```", json_start)
        elif "```" in text:
            json_start = text.find("```") + 3
            json_end = text.find("```", json_start)
        
        # Try to find JSON object directly
        if json_start == -1:
            for i, char in enumerate(text):
                if char == '{':
                    json_start = i
                    break
        
        if json_start == -1:
            return None
        
        # Find matching closing brace
        if json_end == -1:
            brace_count = 0
            for i in range(json_start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
        
        if json_end == -1:
            return None
        
        json_str = text[json_start:json_end].strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            return None

    def _validate_and_enhance_fda(
        self,
        fda_dict: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and enhance the parsed FDA"""
        
        # Ensure required fields
        if "title" not in fda_dict:
            fda_dict["title"] = context.get("topic", "Educational Presentation")
        
        if "topic" not in fda_dict:
            fda_dict["topic"] = context.get("topic", "Educational Content")
        
        if "difficulty_level" not in fda_dict:
            fda_dict["difficulty_level"] = context.get("difficulty_level", "intermediate")
        
        if "target_audience" not in fda_dict:
            fda_dict["target_audience"] = context.get("target_audience", "general")
        
        if "global_settings" not in fda_dict:
            fda_dict["global_settings"] = self.default_settings.copy()
        
        if "slides" not in fda_dict:
            fda_dict["slides"] = []
        
        # Calculate total duration
        total_duration = sum(
            slide.get("duration_seconds", 10) 
            for slide in fda_dict.get("slides", [])
        )
        fda_dict["total_duration_seconds"] = total_duration
        
        # Ensure each slide has required fields
        for i, slide in enumerate(fda_dict.get("slides", [])):
            if "slide_id" not in slide:
                slide["slide_id"] = f"slide_{i + 1}"
            if "slide_number" not in slide:
                slide["slide_number"] = i + 1
            if "duration_seconds" not in slide:
                slide["duration_seconds"] = 10
            if "animation_rules" not in slide:
                slide["animation_rules"] = []
            if "transition_in" not in slide:
                slide["transition_in"] = "fade_in"
            if "transition_out" not in slide:
                slide["transition_out"] = "fade_out"
        
        return fda_dict

    def _create_fallback_fda(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a fallback FDA when parsing fails"""
        topic = context.get("topic", "Educational Content")
        
        # Create basic structure
        fda = {
            "title": topic,
            "topic": topic,
            "total_duration_seconds": 60,
            "difficulty_level": context.get("difficulty_level", "intermediate"),
            "target_audience": context.get("target_audience", "general"),
            "global_settings": self.default_settings.copy(),
            "slides": [
                {
                    "slide_id": "slide_1",
                    "slide_number": 1,
                    "title": topic,
                    "slide_type": "title",
                    "duration_seconds": 5,
                    "content": {
                        "main_text": topic,
                        "subtitle": f"Difficulty: {context.get('difficulty_level', 'intermediate')}"
                    },
                    "animation_rules": [
                        {
                            "rule_id": "rule_1",
                            "intent": "introduce",
                            "visual_elements": [
                                {
                                    "type": "text",
                                    "content": topic,
                                    "position": "center",
                                    "style": {"font_size": 48, "color": "BLUE"}
                                }
                            ],
                            "animations": [
                                {"action": "write", "target": "title", "duration": 1.0}
                            ],
                            "timing": {"start": 0, "duration": 2, "wait_after": 2},
                            "narration": f"Welcome to this lesson on {topic}"
                        }
                    ],
                    "transition_in": "fade_in",
                    "transition_out": "fade_out"
                },
                {
                    "slide_id": "slide_2",
                    "slide_number": 2,
                    "title": "Content Overview",
                    "slide_type": "concept",
                    "duration_seconds": 30,
                    "content": {
                        "main_text": content[:500] if len(content) > 500 else content
                    },
                    "animation_rules": [
                        {
                            "rule_id": "rule_2",
                            "intent": "explain",
                            "visual_elements": [
                                {
                                    "type": "text",
                                    "content": content[:500] if len(content) > 500 else content,
                                    "position": "center",
                                    "style": {"font_size": 28}
                                }
                            ],
                            "animations": [
                                {"action": "fade_in", "target": "content", "duration": 1.0}
                            ],
                            "timing": {"start": 0, "duration": 25, "wait_after": 3},
                            "narration": "Let's explore the main concepts"
                        }
                    ],
                    "transition_in": "fade_in",
                    "transition_out": "fade_out"
                },
                {
                    "slide_id": "slide_3",
                    "slide_number": 3,
                    "title": "Summary",
                    "slide_type": "summary",
                    "duration_seconds": 10,
                    "content": {
                        "main_text": f"Key takeaways from {topic}"
                    },
                    "animation_rules": [
                        {
                            "rule_id": "rule_3",
                            "intent": "summarize",
                            "visual_elements": [
                                {
                                    "type": "text",
                                    "content": "Summary",
                                    "position": "top",
                                    "style": {"font_size": 48}
                                }
                            ],
                            "animations": [
                                {"action": "write", "target": "title", "duration": 1.0}
                            ],
                            "timing": {"start": 0, "duration": 5, "wait_after": 3},
                            "narration": "Let's summarize what we've learned"
                        }
                    ],
                    "transition_in": "fade_in",
                    "transition_out": "fade_out"
                }
            ]
        }
        
        return fda
