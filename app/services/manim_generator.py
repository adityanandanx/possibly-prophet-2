"""
Manim code generation service for creating educational presentations.

This service uses the ManimGenerationAgent which has access to Manim documentation
and intelligently designs slide structure and animations.
"""

from typing import Dict, Any, Optional
import logging
import re
from datetime import datetime

from agents.manim_generation_agent import ManimGenerationAgent

logger = logging.getLogger(__name__)


class ManimCodeGenerator:
    """
    Service for generating Manim code from educational scripts.
    
    Delegates to the ManimGenerationAgent which has deep knowledge of Manim's API
    and intelligently decides:
    - Slide structure and organization
    - Appropriate animations for different content types
    - Visual hierarchy and timing
    - Best practices for educational presentations
    """
    
    def __init__(self):
        """Initialize Manim code generator with the AI agent."""
        self._agent = ManimGenerationAgent()
        logger.info("Initialized ManimCodeGenerator with ManimGenerationAgent")
        
    def generate_manim_code(
        self,
        educational_script: Dict[str, Any],
        style_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Manim code from educational script.
        
        The AI agent analyzes the educational content and generates appropriate
        Manim code with:
        - Intelligent slide organization
        - Content-appropriate animations
        - Proper visual hierarchy
        - Educational pacing
        
        Args:
            educational_script: Structured educational content containing:
                - title: Presentation title
                - learning_objectives: List of learning objectives
                - sections: Content sections with titles and content
                - assessments: Optional assessment questions
            style_options: Optional style customization:
                - background_color: Scene background (default: WHITE)
                - title_color: Color for titles (default: BLUE)
                - text_color: Color for body text (default: BLACK)
            
        Returns:
            Complete Manim Python code as a string
        """
        logger.info("Generating Manim code from educational script")
        
        result = self._agent.generate_presentation(
            educational_script,
            style_options
        )
        
        code = result.get("manim_code", "")
        logger.info(f"Agent generated {result['metadata']['total_slides']} slides, "
                   f"estimated duration: {result['metadata']['estimated_duration_seconds']}s")
        
        return code
    
    def generate_presentation(
        self,
        educational_script: Dict[str, Any],
        style_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete presentation with metadata.
        
        Returns both the Manim code and detailed metadata about the generated
        presentation including slide specifications and timing.
        
        Args:
            educational_script: Structured educational content
            style_options: Optional style customization
            
        Returns:
            Dictionary containing:
                - manim_code: Complete Python code
                - slide_specs: Specifications for each slide
                - metadata: Generation metadata including duration estimates
        """
        return self._agent.generate_presentation(
            educational_script,
            style_options
        )

    def validate_manim_code(self, code: str) -> Dict[str, Any]:
        """
        Validate generated Manim code for basic syntax.
        
        Args:
            code: Generated Manim code
            
        Returns:
            Validation result with status and any errors
        """
        errors = []
        warnings = []
        
        # Check for syntax errors
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        
        # Check for required elements
        required_checks = [
            ('from manim import', 'Missing Manim import statement'),
            ('class ', 'Missing Scene class definition'),
            ('def construct(self)', 'Missing construct method'),
        ]
        
        for element, message in required_checks:
            if element not in code:
                errors.append(message)
        
        # Check for recommended elements
        if 'self.play' not in code:
            warnings.append("No animations found - presentation may be static")
        
        if 'self.wait' not in code:
            warnings.append("No wait statements - presentation may be too fast")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "line_count": len(code.split('\n')),
            "estimated_duration": self._estimate_duration(code)
        }
    
    def _estimate_duration(self, code: str) -> int:
        """Estimate presentation duration in seconds."""
        total = 0
        
        # Count wait statements
        wait_matches = re.findall(r'self\.wait\((\d+(?:\.\d+)?)\)', code)
        total += sum(float(w) for w in wait_matches)
        
        # Estimate animation time (~1.5s per animation)
        play_count = len(re.findall(r'self\.play\(', code))
        total += play_count * 1.5
        
        return int(total)
