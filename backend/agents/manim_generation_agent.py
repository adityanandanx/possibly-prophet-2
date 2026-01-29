"""
Manim Generation Agent for Educational Content Generator

This agent converts FDA (Formal Description of Animation) specifications into
executable Manim code. It takes the structured animation specifications from
the FDA Agent and generates Python code that creates the educational video.

The Manim Agent is the final stage in the pipeline:
    Text Input -> Pedagogical Agent -> FDA Agent -> Manim Agent
    File/URL Input -> FDA Agent -> Manim Agent
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseEducationalAgent
from .exceptions import AgentExecutionError, AgentValidationError

logger = logging.getLogger(__name__)


class AnimationType(Enum):
    """Types of Manim animations"""

    CREATION = "creation"  # Write, Create, DrawBorderThenFill
    TRANSFORMATION = "transformation"  # Transform, ReplacementTransform, MorphingText
    FADE = "fade"  # FadeIn, FadeOut, FadeTransform
    MOVEMENT = "movement"  # Shift, MoveTo, MoveAlongPath
    EMPHASIS = "emphasis"  # Indicate, Circumscribe, Flash, Wiggle
    GROWING = "growing"  # GrowFromCenter, GrowFromEdge, GrowArrow
    UNCREATION = "uncreation"  # Uncreate, Unwrite, ShrinkToCenter
    COMPOSITION = "composition"  # AnimationGroup, Succession, LaggedStart


class SlideType(Enum):
    """Types of presentation slides"""

    TITLE = "title"
    OBJECTIVES = "objectives"
    CONCEPT = "concept"
    DEFINITION = "definition"
    EXAMPLE = "example"
    DIAGRAM = "diagram"
    EQUATION = "equation"
    CODE = "code"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    SUMMARY = "summary"
    ASSESSMENT = "assessment"
    CONCLUSION = "conclusion"


@dataclass
class SlideSpec:
    """Specification for a presentation slide"""

    slide_type: SlideType
    title: str
    content: Dict[str, Any]
    animations: List[str]
    duration: float  # in seconds
    notes: str  # Speaker notes or additional context

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slide_type": self.slide_type.value,
            "title": self.title,
            "content": self.content,
            "animations": self.animations,
            "duration": self.duration,
            "notes": self.notes,
        }


# Comprehensive Manim Documentation Knowledge Base
MANIM_DOCUMENTATION = """
# Manim Community Edition - Complete API Reference

## Core Concepts

### Scene Class
The Scene is the canvas for all animations. Every Manim animation must define a Scene subclass with a construct() method.

```python
from manim import *

class MyScene(Scene):
    def construct(self):
        # All animations go here
        pass
```

### Mobjects (Mathematical Objects)
Mobjects are the fundamental visual elements in Manim.

#### Text and Typography
- **Text(text, font_size=48, color=WHITE)**: Basic text rendering
- **Tex(latex_string)**: LaTeX-rendered text
- **MathTex(latex_math)**: LaTeX math mode
- **MarkupText(text)**: Pango markup support
- **Title(text)**: Centered title text
- **BulletedList(*items)**: Creates a bulleted list
- **Paragraph(*lines)**: Multi-line text block

#### Geometric Shapes
- **Circle(radius=1, color=WHITE)**: Circle shape
- **Square(side_length=2)**: Square shape
- **Rectangle(width=4, height=2)**: Rectangle
- **Triangle()**: Equilateral triangle
- **Polygon(*vertices)**: Custom polygon
- **Arc(radius=1, start_angle=0, angle=TAU/4)**: Arc segment
- **Ellipse(width=4, height=2)**: Ellipse shape
- **RoundedRectangle(corner_radius=0.5)**: Rounded corners
- **Star(n=5, outer_radius=2)**: Star shape
- **RegularPolygon(n=6)**: Regular n-gon

#### Lines and Arrows
- **Line(start, end)**: Line segment
- **Arrow(start, end)**: Arrow with tip
- **DoubleArrow(start, end)**: Double-headed arrow
- **DashedLine(start, end)**: Dashed line
- **CurvedArrow(start, end)**: Curved arrow
- **Vector(direction)**: Vector from origin
- **NumberLine(x_range, length)**: Number line
- **Brace(mobject, direction)**: Curly brace
- **BraceBetweenPoints(p1, p2)**: Brace between points

#### Groups and Containers
- **VGroup(*mobjects)**: Vertical group
- **HGroup(*mobjects)**: Horizontal group  
- **Group(*mobjects)**: Generic group
- **Table(data, row_labels, col_labels)**: Table structure

#### SVG and Images
- **SVGMobject(file_path)**: Load SVG file
- **ImageMobject(file_path)**: Load image
- **Code(file_name, language)**: Syntax-highlighted code

### Animations

#### Creation Animations
- **Create(mobject)**: Draws mobject stroke then fills
- **Write(mobject)**: Handwriting-style creation
- **DrawBorderThenFill(mobject)**: Draw border first, then fill
- **AddTextLetterByLetter(text)**: Type text letter by letter
- **AddTextWordByWord(text)**: Type text word by word

#### Fade Animations
- **FadeIn(mobject, shift=UP)**: Fade in with optional shift
- **FadeOut(mobject, shift=DOWN)**: Fade out with optional shift
- **FadeTransform(mob1, mob2)**: Fade between mobjects
- **FadeToColor(mobject, color)**: Fade to new color

#### Transform Animations
- **Transform(mob1, mob2)**: Morph mob1 into mob2
- **ReplacementTransform(mob1, mob2)**: Replace mob1 with mob2
- **TransformFromCopy(mob1, mob2)**: Transform copy of mob1
- **ClockwiseTransform(mob1, mob2)**: Clockwise morph
- **CounterclockwiseTransform(mob1, mob2)**: Counter-clockwise morph
- **MoveToTarget(mobject)**: Move to mobject.target

#### Movement Animations
- **Shift(mobject, direction)**: Shift by direction vector
- **MoveTo(mobject, point)**: Move to specific point
- **MoveAlongPath(mobject, path)**: Move along a path
- **Rotate(mobject, angle)**: Rotate by angle
- **Circumscribe(mobject)**: Draw circle around mobject
- **Homotopy(func, mobject)**: Custom path animation

#### Emphasis Animations
- **Indicate(mobject)**: Briefly highlight
- **Flash(mobject)**: Flash effect
- **Wiggle(mobject)**: Wiggle effect
- **FocusOn(point)**: Focus camera effect
- **ShowPassingFlash(mobject)**: Passing flash
- **ApplyWave(mobject)**: Wave effect

#### Uncreation Animations
- **Uncreate(mobject)**: Reverse of Create
- **Unwrite(mobject)**: Reverse of Write
- **ShrinkToCenter(mobject)**: Shrink to center point
- **FadeOut(mobject)**: Fade away

#### Animation Modifiers
- **AnimationGroup(*anims)**: Play animations together
- **Succession(*anims)**: Play in sequence
- **LaggedStart(*anims, lag_ratio=0.5)**: Staggered start
- **LaggedStartMap(anim_class, mobjects)**: Map animation to group
- **Wait(duration=1)**: Pause for duration

### Positioning Methods

#### Relative Positioning
- **next_to(mobject, direction, buff=0.25)**: Position relative to another
- **align_to(mobject, direction)**: Align edge with another
- **move_to(point)**: Move center to point
- **shift(direction)**: Shift by vector
- **to_edge(edge, buff=0.5)**: Move to screen edge
- **to_corner(corner)**: Move to screen corner

#### Edge Constants
- UP, DOWN, LEFT, RIGHT, UL, UR, DL, DR
- ORIGIN (center of screen)

### Colors
Manim provides predefined colors:
- WHITE, BLACK, GRAY, GREY
- RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, PINK
- TEAL, MAROON, GOLD, PURE_RED, PURE_GREEN, PURE_BLUE
- Color gradients: color_gradient([color1, color2], n_colors)

### Camera and Background
- **self.camera.background_color = color**: Set background
- **self.camera.frame.scale(factor)**: Zoom camera
- **self.camera.frame.move_to(point)**: Pan camera

### Useful Methods

#### Scene Methods
- **self.play(*animations, run_time=1)**: Play animations
- **self.wait(duration=1)**: Pause
- **self.add(mobject)**: Add without animation
- **self.remove(mobject)**: Remove without animation
- **self.clear()**: Remove all mobjects

#### Mobject Methods  
- **set_color(color)**: Change color
- **set_fill(color, opacity=1)**: Set fill
- **set_stroke(color, width)**: Set stroke
- **scale(factor)**: Scale size
- **rotate(angle)**: Rotate
- **copy()**: Create copy
- **get_center()**: Get center point

## Best Practices for Educational Presentations

### Visual Hierarchy
1. Use consistent font sizes: Title (48-60), Subtitle (32-36), Body (24-28), Caption (18-20)
2. Limit text per slide to maintain readability
3. Use color to highlight key concepts
4. Maintain adequate spacing (buff) between elements

### Animation Pacing
1. Use self.wait() strategically for comprehension pauses
2. Keep animations between 0.5-2 seconds for most content
3. Use longer animations (2-3s) for complex transformations
4. Use LaggedStart for lists to improve readability

### Color Schemes for Education
1. Dark background (BLACK/DARK_GRAY) with light text for focus
2. Light background (WHITE/LIGHT_GRAY) for printable content
3. Use accent colors sparingly for emphasis
4. Maintain sufficient contrast for accessibility

### Slide Transitions
1. Use FadeOut/FadeIn for smooth transitions between sections
2. Clear all mobjects between conceptually different slides
3. Use Transform to show concept evolution
4. Use AnimationGroup for simultaneous related animations

### Mathematical Content
1. Use MathTex for equations: MathTex(r"E = mc^2")
2. Use Tex for mixed text and math: Tex(r"Energy: $E = mc^2$")
3. Highlight parts using set_color_by_tex()
4. Use TransformMatchingTex for equation evolution

### Code Presentation
1. Use Code mobject with appropriate language parameter
2. Use Indicate to highlight specific lines
3. Show output transformations with arrows
4. Keep code snippets focused and readable
"""


class ManimGenerationAgent(BaseEducationalAgent):
    """
    Manim Generation Agent that converts FDA to Manim code.

    This agent takes FDA (Formal Description of Animation) specifications
    and generates executable Manim Python code. The FDA contains explicit
    animation rules, visual elements, and timing that are translated into
    Manim API calls.
    
    Pipeline position:
    - After FDA Agent in the workflow
    - Receives structured animation specifications
    - Outputs Python code for Manim rendering
    """

    def __init__(self, **kwargs):
        """Initialize the Manim generation agent"""
        super().__init__("manim_generation", **kwargs)

        # Store Manim documentation for context
        self.manim_docs = MANIM_DOCUMENTATION

        # Default presentation settings
        self.default_settings = {
            "background_color": "WHITE",
            "title_font_size": 48,
            "subtitle_font_size": 32,
            "body_font_size": 24,
            "title_color": "BLUE",
            "text_color": "BLACK",
            "accent_color": "RED",
            "default_wait": 2,
            "animation_run_time": 1.0,
        }

        logger.info("Initialized ManimGenerationAgent for FDA-to-code conversion")

    def process_content(
        self,
        fda: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process FDA and generate Manim code.
        
        This is the main entry point following the new workflow.
        
        Args:
            fda: FDA (Formal Description of Animation) specification from FDA Agent
            context: Additional context including:
                - topic: Topic name
                - output_path: Where to save generated code
                
        Returns:
            Dictionary containing:
                - manim_code: Complete Python code for Manim presentation
                - metadata: Generation metadata
        """
        context = context or {}
        
        # Validate FDA input
        if not fda or not isinstance(fda, dict):
            raise AgentValidationError(
                "Invalid FDA input. Expected dictionary with animation specifications.",
                agent_type="manim_generation"
            )
        
        if not fda.get("slides"):
            raise AgentValidationError(
                "FDA must contain at least one slide specification.",
                agent_type="manim_generation"
            )
        
        try:
            logger.info(f"Starting Manim code generation from FDA with {len(fda.get('slides', []))} slides")
            
            # Merge FDA global settings with defaults
            settings = {**self.default_settings}
            if fda.get("global_settings"):
                settings.update(fda["global_settings"])
            
            # Generate Manim code using the agent with FDA context
            manim_code = self._generate_code_from_fda(fda, settings)
            
            # Validate generated code
            validation_result = self._validate_manim_code(manim_code)
            
            if not validation_result["valid"]:
                logger.warning(f"Generated code has issues: {validation_result['errors']}")
                manim_code = self._fix_common_issues(manim_code, validation_result["errors"])
                
                # Re-validate after fixes
                validation_result = self._validate_manim_code(manim_code)
                
                if not validation_result["valid"]:
                    # If still invalid, use fallback
                    logger.error(f"Code still invalid after fixes, using fallback: {validation_result['errors']}")
                    manim_code = self._generate_fallback_from_fda(fda, settings)
                    validation_result = self._validate_manim_code(manim_code)
            
            # Estimate duration from FDA
            total_duration = fda.get("total_duration_seconds", 0)
            if total_duration == 0:
                total_duration = sum(
                    slide.get("duration_seconds", 10) 
                    for slide in fda.get("slides", [])
                )
            
            return {
                "manim_code": manim_code,
                "metadata": {
                    "total_slides": len(fda.get("slides", [])),
                    "estimated_duration_seconds": total_duration,
                    "fda_title": fda.get("title", "Educational Presentation"),
                    "difficulty_level": fda.get("difficulty_level", "intermediate"),
                    "validation": validation_result,
                    "generation_timestamp": str(__import__("datetime").datetime.now()),
                },
            }
            
        except AgentValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating Manim code from FDA: {str(e)}")
            raise AgentExecutionError(
                f"Failed to generate Manim code: {str(e)}",
                agent_type="manim_generation",
                original_error=e,
            )

    def _generate_code_from_fda(
        self,
        fda: Dict[str, Any],
        settings: Dict[str, Any],
    ) -> str:
        """
        Generate Manim code from FDA specification using the AI agent.
        """
        prompt = self._build_fda_to_code_prompt(fda, settings)
        
        try:
            # Call the agent with the prompt
            result = self.agent(prompt)
            
            # Extract code from result
            if hasattr(result, "message") and hasattr(result.message, "content"):
                response_text = ""
                for block in result.message.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                
                code = self._extract_code_from_response(response_text)
                if code:
                    return code
            
            # Fallback to string conversion
            response_str = str(result)
            code = self._extract_code_from_response(response_str)
            if code:
                return code
            
            # If no code extracted, generate fallback from FDA
            logger.warning("Could not extract code from agent response, using FDA fallback")
            return self._generate_fallback_from_fda(fda, settings)
            
        except Exception as e:
            logger.error(f"Agent FDA-to-code generation failed: {str(e)}")
            return self._generate_fallback_from_fda(fda, settings)

    def _build_fda_to_code_prompt(
        self,
        fda: Dict[str, Any],
        settings: Dict[str, Any],
    ) -> str:
        """Build prompt for converting FDA to Manim code"""
        
        # Format slide specifications
        slide_specs = []
        for slide in fda.get("slides", []):
            slide_json = json.dumps(slide, indent=2)
            slide_specs.append(f"### Slide {slide.get('slide_number', '?')}: {slide.get('title', 'Untitled')}\n{slide_json}")
        
        prompt = f"""You are an expert Manim developer. Convert the following FDA (Formal Description of Animation) into executable Manim Python code.

## MANIM DOCUMENTATION REFERENCE
{self.manim_docs}

## FDA (Formal Description of Animation)
Title: {fda.get('title', 'Educational Presentation')}
Topic: {fda.get('topic', 'Educational Content')}
Difficulty: {fda.get('difficulty_level', 'intermediate')}
Total Duration: {fda.get('total_duration_seconds', 60)} seconds

## GLOBAL SETTINGS
{json.dumps(settings, indent=2)}

## SLIDE SPECIFICATIONS
{chr(10).join(slide_specs)}

## CONVERSION REQUIREMENTS
1. Generate a complete, self-contained Python file with proper Manim imports
2. Create a single Scene class named 'EducationalPresentation'
3. Follow the animation rules EXACTLY as specified in the FDA
4. Use the visual elements with their specified positions and styles
5. Implement the timing from the FDA (duration, wait_after, delays)
6. Use FadeOut to clear slides before transitions
7. Escape special characters in text strings
8. Handle long text by splitting into multiple lines
9. The code must be syntactically correct and executable

## ANIMATION MAPPING
- "write" -> Write(mobject)
- "fade_in" -> FadeIn(mobject)
- "fade_out" -> FadeOut(mobject)
- "transform" -> Transform(mob1, mob2)
- "move" -> mobject.shift() or mobject.move_to()
- "highlight" -> Indicate(mobject)
- "create" -> Create(mobject)

## OUTPUT FORMAT
Return ONLY the Python code wrapped in ```python and ``` markers.

Generate the complete Manim code:"""

        return prompt

    def _generate_fallback_from_fda(
        self,
        fda: Dict[str, Any],
        settings: Dict[str, Any],
    ) -> str:
        """Generate fallback Manim code directly from FDA structure"""
        
        code_parts = [
            "from manim import *\n",
            "\n",
            "class EducationalPresentation(Scene):",
            '    """Generated from FDA specification"""',
            "    ",
            "    def construct(self):",
            '        """Main presentation construction"""',
            f'        self.camera.background_color = {settings.get("background_color", "WHITE")}',
            "        ",
        ]
        
        for slide in fda.get("slides", []):
            slide_code = self._generate_slide_from_fda(slide, settings)
            code_parts.extend(slide_code)
            code_parts.append("        ")
        
        return "\n".join(code_parts)

    def _generate_slide_from_fda(
        self,
        slide: Dict[str, Any],
        settings: Dict[str, Any]
    ) -> List[str]:
        """Generate Manim code for a single slide from FDA specification"""
        code_lines = []
        slide_id = slide.get("slide_id", "slide").replace("-", "_")
        # Clean slide_id to be a valid Python identifier
        slide_id = re.sub(r'[^a-zA-Z0-9_]', '_', slide_id)
        if slide_id[0].isdigit():
            slide_id = f"s_{slide_id}"
        
        slide_type = slide.get("slide_type", "concept")
        title = self._clean_text(slide.get("title", "Untitled"))
        content = slide.get("content", {})
        duration = slide.get("duration_seconds", 5)
        
        # Track how many content items we've added for positioning
        content_count = 0
        
        code_lines.append(f"        # {slide_id}: {title}")
        
        # Generate title
        title_var = f"{slide_id}_title"
        if slide_type == "title":
            font_size = settings.get("title_font_size", 48)
        else:
            font_size = settings.get("subtitle_font_size", 32)
        
        code_lines.append(
            f'        {title_var} = Text("{title}", font_size={font_size}, color={settings.get("title_color", "BLUE")})'
        )
        
        if slide_type == "title":
            code_lines.append(f"        {title_var}.move_to(ORIGIN)")
        else:
            code_lines.append(f"        {title_var}.to_edge(UP)")
        
        code_lines.append(f"        self.play(Write({title_var}))")
        
        # Generate content based on slide type
        if slide_type == "title":
            subtitle = content.get("subtitle", content.get("main_text", ""))
            if subtitle:
                sub_var = f"{slide_id}_subtitle"
                subtitle_text = self._clean_text(subtitle)
                code_lines.extend([
                    f'        {sub_var} = Text("{subtitle_text}", font_size=24, color=GRAY)',
                    f"        {sub_var}.next_to({title_var}, DOWN, buff=0.5)",
                    f"        self.play(FadeIn({sub_var}))",
                ])
        else:
            # Handle main text
            main_text = content.get("main_text", "")
            if main_text:
                lines = self._split_text_for_display(self._clean_text(main_text))
                for i, line in enumerate(lines[:6]):
                    line_var = f"{slide_id}_line_{i}"
                    code_lines.extend([
                        f'        {line_var} = Text("{line}", font_size=20, color={settings.get("text_color", "BLACK")})',
                        f"        {line_var}.next_to({title_var}, DOWN, buff={0.8 + i * 0.5})",
                        f"        self.play(FadeIn({line_var}))",
                    ])
                content_count = len(lines[:6])
            
            # Handle bullet points
            bullet_points = content.get("bullet_points", [])
            for i, point in enumerate(bullet_points[:5]):
                point_var = f"{slide_id}_bullet_{i}"
                point_text = self._clean_text(str(point))
                code_lines.extend([
                    f'        {point_var} = Text("* {point_text}", font_size=20, color={settings.get("text_color", "BLACK")})',
                    f"        {point_var}.next_to({title_var}, DOWN, buff={0.8 + content_count * 0.5 + i * 0.5})",
                    f"        self.play(FadeIn({point_var}, shift=RIGHT))",
                ])
            
            # Handle equations
            equations = content.get("equations", [])
            for i, eq in enumerate(equations[:3]):
                eq_var = f"{slide_id}_eq_{i}"
                eq_text = str(eq).replace("\\", "\\\\")
                code_lines.extend([
                    f'        {eq_var} = MathTex(r"{eq_text}")',
                    f"        {eq_var}.scale(0.8)",
                    f"        {eq_var}.next_to({title_var}, DOWN, buff=2)",
                    f"        self.play(Write({eq_var}))",
                ])
        
        # Apply animation rules if specified
        for rule in slide.get("animation_rules", []):
            narration = rule.get("narration", "")
            if narration:
                code_lines.append(f'        # Narration: {self._clean_text(narration)[:50]}...')
        
        # Wait and transition
        code_lines.append(f"        self.wait({duration})")
        code_lines.append(f"        self.play(*[FadeOut(mob) for mob in self.mobjects])")
        
        return code_lines

    # Legacy method for backward compatibility
    def generate_presentation(
        self,
        educational_script: Dict[str, Any],
        style_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete Manim presentation from educational script.
        
        DEPRECATED: Use process_content() with FDA input instead.
        This method is kept for backward compatibility.

        Args:
            educational_script: Structured educational content from pedagogy workflow
            style_options: Optional style customization

        Returns:
            Dictionary containing:
                - manim_code: Complete Python code for Manim presentation
                - slide_specs: Detailed specifications for each slide
                - metadata: Generation metadata
        """
        try:
            logger.info("Starting Manim presentation generation (legacy mode)")

            # Merge style options with defaults
            settings = {**self.default_settings, **(style_options or {})}

            # Step 1: Analyze educational script and plan slides
            slide_plan = self._plan_slides(educational_script)
            logger.info(f"Planned {len(slide_plan)} slides")

            # Step 2: Generate Manim code using the agent with full documentation context
            manim_code = self._generate_code_with_agent(
                educational_script, slide_plan, settings
            )

            # Step 3: Validate generated code
            validation_result = self._validate_manim_code(manim_code)

            if not validation_result["valid"]:
                logger.warning(
                    f"Generated code has issues: {validation_result['errors']}"
                )
                # Attempt to fix common issues
                manim_code = self._fix_common_issues(
                    manim_code, validation_result["errors"]
                )

            # Step 4: Estimate presentation duration
            duration = self._estimate_duration(manim_code)

            return {
                "manim_code": manim_code,
                "slide_specs": [s.to_dict() for s in slide_plan],
                "metadata": {
                    "total_slides": len(slide_plan),
                    "estimated_duration_seconds": duration,
                    "settings": settings,
                    "validation": validation_result,
                    "generation_timestamp": str(__import__("datetime").datetime.now()),
                },
            }

        except Exception as e:
            logger.error(f"Error generating Manim presentation: {str(e)}")
            raise AgentExecutionError(
                f"Failed to generate Manim presentation: {str(e)}",
                agent_type="manim_generation",
                original_error=e,
            )

    def _plan_slides(self, educational_script: Dict[str, Any]) -> List[SlideSpec]:
        """
        Plan the slide structure based on educational script content.

        The agent decides:
        - How many slides to create
        - What type each slide should be
        - What animations are appropriate
        - How to pace the content
        """
        slides = []

        # Title slide
        title = educational_script.get("title", "Educational Presentation")
        slides.append(
            SlideSpec(
                slide_type=SlideType.TITLE,
                title=title,
                content={"subtitle": "Educational Presentation", "author": ""},
                animations=["Write", "FadeIn"],
                duration=3.0,
                notes="Opening title slide with presentation title",
            )
        )

        # Learning objectives slide
        objectives = educational_script.get("learning_objectives", [])
        if objectives:
            slides.append(
                SlideSpec(
                    slide_type=SlideType.OBJECTIVES,
                    title="Learning Objectives",
                    content={"objectives": self._extract_objectives(objectives)},
                    animations=["Write", "LaggedStart", "FadeIn"],
                    duration=5.0,
                    notes="Display learning objectives with staggered animation",
                )
            )

        # Content slides from sections
        sections = educational_script.get("sections", [])
        for i, section in enumerate(sections):
            section_slides = self._plan_section_slides(section, i)
            slides.extend(section_slides)

        # Assessment slide if available
        assessments = educational_script.get("assessments", [])
        if assessments:
            slides.append(
                SlideSpec(
                    slide_type=SlideType.ASSESSMENT,
                    title="Knowledge Check",
                    content={"questions": assessments[:2]},  # Limit to 2 questions
                    animations=["Write", "FadeIn", "Indicate"],
                    duration=6.0,
                    notes="Interactive assessment questions",
                )
            )

        # Summary slide
        slides.append(
            SlideSpec(
                slide_type=SlideType.SUMMARY,
                title="Key Takeaways",
                content={"points": self._extract_key_points(educational_script)},
                animations=["Write", "LaggedStart"],
                duration=4.0,
                notes="Summarize main learning points",
            )
        )

        # Conclusion slide
        slides.append(
            SlideSpec(
                slide_type=SlideType.CONCLUSION,
                title="Thank You!",
                content={"message": "Questions?"},
                animations=["Write", "FadeIn"],
                duration=3.0,
                notes="Closing slide",
            )
        )

        return slides

    def _plan_section_slides(
        self, section: Dict[str, Any], index: int
    ) -> List[SlideSpec]:
        """Plan slides for a content section"""
        slides = []

        title = section.get("title", f"Section {index + 1}")
        content = section.get("content", "")
        key_concepts = section.get("key_concepts", [])
        section_type = section.get("section_type", "main_concept")

        # Determine slide type based on content analysis
        if "example" in title.lower() or "example" in section_type:
            slide_type = SlideType.EXAMPLE
            animations = ["Write", "Create", "Indicate"]
        elif "definition" in title.lower() or "definition" in section_type:
            slide_type = SlideType.DEFINITION
            animations = ["Write", "FadeIn", "Circumscribe"]
        elif any(
            math_term in content.lower()
            for math_term in ["equation", "formula", "=", "∑", "∫"]
        ):
            slide_type = SlideType.EQUATION
            animations = ["Write", "TransformMatchingTex", "Indicate"]
        elif "compare" in title.lower() or "vs" in title.lower():
            slide_type = SlideType.COMPARISON
            animations = ["Write", "FadeIn", "Transform"]
        else:
            slide_type = SlideType.CONCEPT
            animations = ["Write", "FadeIn", "LaggedStart"]

        # Main section slide
        slides.append(
            SlideSpec(
                slide_type=slide_type,
                title=title,
                content={
                    "text": content,
                    "key_concepts": key_concepts[:5],  # Limit concepts per slide
                },
                animations=animations,
                duration=self._estimate_content_duration(content),
                notes=f"Section {index + 1}: {title}",
            )
        )

        # Add sub-slides for long content
        if len(content) > 500:
            # Split into multiple slides
            subsections = section.get("subsections", [])
            for sub in subsections[:3]:  # Limit subsections
                slides.append(
                    SlideSpec(
                        slide_type=SlideType.CONCEPT,
                        title=sub.get("title", "Details"),
                        content={"text": sub.get("content", "")},
                        animations=["Write", "FadeIn"],
                        duration=self._estimate_content_duration(
                            sub.get("content", "")
                        ),
                        notes=f"Subsection of {title}",
                    )
                )

        return slides

    def _generate_code_with_agent(
        self,
        educational_script: Dict[str, Any],
        slide_plan: List[SlideSpec],
        settings: Dict[str, Any],
    ) -> str:
        """
        Use the AI agent to generate Manim code with full context.
        """
        # Prepare comprehensive prompt for the agent
        prompt = self._build_generation_prompt(educational_script, slide_plan, settings)

        try:
            # Call the agent with the prompt
            result = self.agent(prompt)

            # Extract code from result
            if hasattr(result, "message") and hasattr(result.message, "content"):
                response_text = ""
                for block in result.message.content:
                    if hasattr(block, "text"):
                        response_text += block.text

                # Extract Python code from response
                code = self._extract_code_from_response(response_text)
                if code:
                    return code

            # Fallback to string conversion
            response_str = str(result)
            code = self._extract_code_from_response(response_str)
            if code:
                return code

            # If no code extracted, generate fallback
            logger.warning("Could not extract code from agent response, using fallback")
            return self._generate_fallback_code(
                educational_script, slide_plan, settings
            )

        except Exception as e:
            logger.error(f"Agent code generation failed: {str(e)}")
            return self._generate_fallback_code(
                educational_script, slide_plan, settings
            )

    def _build_generation_prompt(
        self,
        educational_script: Dict[str, Any],
        slide_plan: List[SlideSpec],
        settings: Dict[str, Any],
    ) -> str:
        """Build comprehensive prompt for Manim code generation"""

        # Convert slide plan to readable format
        slide_descriptions = []
        for i, slide in enumerate(slide_plan):
            slide_descriptions.append(
                f"{i+1}. {slide.slide_type.value.upper()}: {slide.title}\n"
                f"   Content: {json.dumps(slide.content, indent=2)[:500]}\n"
                f"   Suggested animations: {', '.join(slide.animations)}\n"
                f"   Duration: {slide.duration}s"
            )

        prompt = f"""You are an expert Manim developer creating an educational presentation.

## MANIM DOCUMENTATION REFERENCE
{self.manim_docs}

## TASK
Generate complete, working Manim Python code for an educational presentation based on the following content and slide plan.

## PRESENTATION SETTINGS
- Background color: {settings['background_color']}
- Title font size: {settings['title_font_size']}
- Body font size: {settings['body_font_size']}
- Title color: {settings['title_color']}
- Text color: {settings['text_color']}
- Default wait time: {settings['default_wait']}s

## EDUCATIONAL CONTENT
Title: {educational_script.get('title', 'Educational Presentation')}

Learning Objectives:
{json.dumps(educational_script.get('learning_objectives', []), indent=2)[:1000]}

## SLIDE PLAN
{chr(10).join(slide_descriptions)}

## REQUIREMENTS
1. Generate a complete, self-contained Python file with proper Manim imports
2. Create a single Scene class named 'EducationalPresentation'
3. Use appropriate animations from the documentation for each slide type
4. Ensure smooth transitions between slides using FadeOut before new content
5. Use VGroup to organize related elements
6. Include self.wait() calls for pacing
7. Handle long text by splitting into multiple lines (max 60 chars per line)
8. Escape special characters in text strings
9. Use color constants from Manim (WHITE, BLACK, BLUE, RED, etc.)
10. The code must be syntactically correct and executable

## OUTPUT FORMAT
Return ONLY the Python code wrapped in ```python and ``` markers. No explanations needed.

Generate the complete Manim code now:"""

        return prompt

    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Extract Python code from agent response"""
        if not response or not isinstance(response, str):
            return None
            
        # Check if response looks like raw JSON/dict response (not code)
        if "'role':" in response or '"role":' in response:
            # This is likely a raw AI response structure, not code
            # Try to extract text content from it
            import json
            try:
                # Try to parse as JSON and extract text
                data = json.loads(response.replace("'", '"'))
                if isinstance(data, dict) and 'content' in data:
                    response = str(data['content'])
            except:
                pass
        
        # Try to find code blocks
        code_patterns = [
            r"```python\s*\n(.*?)```",
            r"```\s*\n(.*?)```",
            r"```python(.*?)```",
            r"```(.*?)```",
        ]

        for pattern in code_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                code = matches[0].strip()
                # Validate it looks like Manim code
                if "class" in code and ("construct" in code or "Scene" in code):
                    # Ensure it has the import
                    if "from manim import" not in code:
                        code = "from manim import *\n\n" + code
                    return code

        # Check if the response itself looks like code
        if (
            "from manim import" in response
            and "class" in response
            and "def construct" in response
        ):
            # Try to extract just the code portion
            start = response.find("from manim import")
            if start != -1:
                code = response[start:].strip()
                # Try to find where the code ends (before any closing ```)
                end_markers = ["```", "\n\n\n"]
                for marker in end_markers:
                    if marker in code:
                        code = code[:code.find(marker)]
                return code

        return None

    def _generate_fallback_code(
        self,
        educational_script: Dict[str, Any],
        slide_plan: List[SlideSpec],
        settings: Dict[str, Any],
    ) -> str:
        """Generate fallback Manim code if agent fails"""

        code_parts = [
            "from manim import *\n",
            "\n",
            "class EducationalPresentation(Scene):",
            '    """Generated educational presentation"""',
            "    ",
            "    def construct(self):",
            '        """Main presentation construction"""',
            f'        self.camera.background_color = {settings["background_color"]}',
            "        ",
        ]

        for i, slide in enumerate(slide_plan):
            code_parts.append(f"        # Slide {i+1}: {slide.title}")
            code_parts.extend(self._generate_slide_code(slide, settings, i))
            code_parts.append("        ")

        return "\n".join(code_parts)

    def _generate_slide_code(
        self, slide: SlideSpec, settings: Dict[str, Any], index: int
    ) -> List[str]:
        """Generate code for a single slide"""
        code_lines = []
        var_prefix = f"slide_{index}"

        title = self._clean_text(slide.title)

        if slide.slide_type == SlideType.TITLE:
            code_lines.extend(
                [
                    f'        {var_prefix}_title = Text("{title}", font_size={settings["title_font_size"]}, color={settings["title_color"]})',
                    f'        {var_prefix}_subtitle = Text("{self._clean_text(slide.content.get("subtitle", ""))}", font_size={settings["subtitle_font_size"]}, color=GRAY)',
                    f"        {var_prefix}_subtitle.next_to({var_prefix}_title, DOWN, buff=0.5)",
                    f"        ",
                    f"        self.play(Write({var_prefix}_title))",
                    f"        self.play(FadeIn({var_prefix}_subtitle))",
                    f"        self.wait({slide.duration})",
                    f"        self.play(FadeOut({var_prefix}_title), FadeOut({var_prefix}_subtitle))",
                ]
            )

        elif slide.slide_type == SlideType.OBJECTIVES:
            objectives = slide.content.get("objectives", [])[:5]
            code_lines.extend(
                [
                    f'        {var_prefix}_title = Text("{title}", font_size={settings["subtitle_font_size"]}, color={settings["title_color"]})',
                    f"        {var_prefix}_title.to_edge(UP)",
                    f"        self.play(Write({var_prefix}_title))",
                    f"        ",
                ]
            )

            for j, obj in enumerate(objectives):
                obj_text = self._clean_text(str(obj)[:80])
                code_lines.extend(
                    [
                        f'        {var_prefix}_obj_{j} = Text("• {obj_text}", font_size=24, color={settings["text_color"]})',
                        f"        {var_prefix}_obj_{j}.next_to({var_prefix}_title, DOWN, buff={0.8 + j * 0.6})",
                        f"        {var_prefix}_obj_{j}.align_to({var_prefix}_title, LEFT)",
                        f"        self.play(FadeIn({var_prefix}_obj_{j}, shift=RIGHT))",
                    ]
                )

            code_lines.extend(
                [
                    f"        self.wait({slide.duration})",
                    f"        self.play(*[FadeOut(mob) for mob in self.mobjects])",
                ]
            )

        elif slide.slide_type == SlideType.CONCLUSION:
            code_lines.extend(
                [
                    f'        {var_prefix}_text = Text("{title}", font_size={settings["title_font_size"]}, color={settings["title_color"]})',
                    f'        {var_prefix}_sub = Text("{self._clean_text(slide.content.get("message", ""))}", font_size={settings["subtitle_font_size"]}, color=GRAY)',
                    f"        {var_prefix}_sub.next_to({var_prefix}_text, DOWN, buff=0.5)",
                    f"        ",
                    f"        self.play(Write({var_prefix}_text))",
                    f"        self.play(FadeIn({var_prefix}_sub))",
                    f"        self.wait({slide.duration})",
                ]
            )

        else:
            # Generic slide type (CONCEPT, EXAMPLE, DEFINITION, etc.)
            content_text = self._clean_text(str(slide.content.get("text", ""))[:300])
            content_lines = self._split_text_for_display(content_text)

            code_lines.extend(
                [
                    f'        {var_prefix}_title = Text("{title}", font_size={settings["subtitle_font_size"]}, color={settings["title_color"]})',
                    f"        {var_prefix}_title.to_edge(UP)",
                    f"        self.play(Write({var_prefix}_title))",
                    f"        ",
                ]
            )

            for j, line in enumerate(content_lines[:5]):
                code_lines.extend(
                    [
                        f'        {var_prefix}_line_{j} = Text("{line}", font_size=20, color={settings["text_color"]})',
                        f"        {var_prefix}_line_{j}.next_to({var_prefix}_title, DOWN, buff={1.0 + j * 0.5})",
                        f"        {var_prefix}_line_{j}.align_to({var_prefix}_title, LEFT)",
                        f"        self.play(Write({var_prefix}_line_{j}))",
                    ]
                )

            # Add key concepts if available
            key_concepts = slide.content.get("key_concepts", [])[:3]
            if key_concepts:
                code_lines.append(f"        ")
                for k, concept in enumerate(key_concepts):
                    concept_text = self._clean_text(str(concept)[:50])
                    code_lines.extend(
                        [
                            f'        {var_prefix}_concept_{k} = Text("→ {concept_text}", font_size=18, color={settings["accent_color"]})',
                            f"        {var_prefix}_concept_{k}.to_edge(DOWN, buff={1.5 - k * 0.4})",
                            f"        self.play(FadeIn({var_prefix}_concept_{k}))",
                        ]
                    )

            code_lines.extend(
                [
                    f"        self.wait({slide.duration})",
                    f"        self.play(*[FadeOut(mob) for mob in self.mobjects])",
                ]
            )

        return code_lines

    def _validate_manim_code(self, code: str) -> Dict[str, Any]:
        """Validate generated Manim code"""
        errors = []
        warnings = []

        # Check for syntax errors
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")

        # Check for required elements
        required_elements = [
            ("from manim import", "Missing Manim import"),
            ("class", "Missing Scene class definition"),
            ("def construct", "Missing construct method"),
        ]

        for element, message in required_elements:
            if element not in code:
                errors.append(message)

        # Check for common issues
        if "self.play" not in code:
            warnings.append("No animations found - presentation may be static")

        if "self.wait" not in code:
            warnings.append("No wait statements - presentation may be too fast")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "line_count": len(code.split("\n")),
        }

    def _fix_common_issues(self, code: str, errors: List[str]) -> str:
        """Attempt to fix common code issues"""
        fixed_code = code

        # Add missing import
        if "Missing Manim import" in str(errors):
            if "from manim import" not in fixed_code:
                fixed_code = "from manim import *\n\n" + fixed_code

        # Fix unescaped quotes in strings
        fixed_code = re.sub(
            r'Text\("([^"]*)"([^"]*)"([^"]*)"\)',
            lambda m: f"Text(\"{m.group(1)}'{m.group(2)}'{m.group(3)}\")",
            fixed_code,
        )

        return fixed_code

    def _estimate_duration(self, code: str) -> int:
        """Estimate total presentation duration from code"""
        total = 0

        # Count wait statements
        wait_matches = re.findall(r"self\.wait\((\d+(?:\.\d+)?)\)", code)
        total += sum(float(w) for w in wait_matches)

        # Estimate animation time
        play_count = len(re.findall(r"self\.play\(", code))
        total += play_count * 1.0  # ~1 second per animation

        return int(total)

    def _extract_objectives(self, objectives: List[Any]) -> List[str]:
        """Extract objective strings from various formats"""
        result = []
        for obj in objectives[:5]:
            if isinstance(obj, dict):
                result.append(obj.get("objective", obj.get("text", str(obj))))
            else:
                result.append(str(obj))
        return result

    def _extract_key_points(self, educational_script: Dict[str, Any]) -> List[str]:
        """Extract key points for summary slide"""
        points = []

        # From learning objectives
        for obj in educational_script.get("learning_objectives", [])[:2]:
            if isinstance(obj, dict):
                points.append(obj.get("objective", str(obj)))
            else:
                points.append(str(obj))

        # From sections
        for section in educational_script.get("sections", [])[:3]:
            title = section.get("title", "")
            if title:
                points.append(title)

        return points[:5]

    def _estimate_content_duration(self, content: str) -> float:
        """Estimate reading time for content"""
        if not content:
            return 3.0

        word_count = len(content.split())
        # Average reading speed: ~150 words per minute for educational content
        # Plus time for animations
        return max(3.0, min(8.0, (word_count / 150) * 60 + 2))

    def _clean_text(self, text: str, max_length: int = 100) -> str:
        """Clean and prepare text for Manim code"""
        if not text:
            return ""

        # Remove or escape problematic characters
        text = text.replace('"', "'")
        text = text.replace("\\", "\\\\")
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        text = text.replace("\t", " ")
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        # Truncate if needed
        if len(text) > max_length:
            text = text[: max_length - 3] + "..."

        return text

    def _split_text_for_display(
        self, text: str, max_line_length: int = 60
    ) -> List[str]:
        """Split text into lines for slide display"""
        if not text:
            return [""]

        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_line_length:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines or [""]
