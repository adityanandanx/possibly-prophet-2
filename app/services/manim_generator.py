"""
Manim code generation service for creating educational presentations
"""

from typing import Dict, Any, List, Optional
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class ManimCodeGenerator:
    """Service for generating Manim code from educational scripts"""
    
    def __init__(self):
        """Initialize Manim code generator"""
        self.template_header = '''from manim import *

class EducationalPresentation(Scene):
    """Generated educational presentation"""
    
    def construct(self):
        """Main presentation construction"""
        self.camera.background_color = WHITE
        
'''
        
    def generate_manim_code(self, educational_script: Dict[str, Any]) -> str:
        """
        Generate Manim code from educational script
        
        Args:
            educational_script: Structured educational content
            
        Returns:
            Complete Manim Python code
        """
        try:
            logger.info("Generating Manim code from educational script")
            
            # Start with template header
            code_parts = [self.template_header]
            
            # Add title slide
            title = educational_script.get("title", "Educational Content")
            code_parts.append(self._generate_title_slide(title))
            
            # Add learning objectives slide
            objectives = educational_script.get("learning_objectives", [])
            if objectives:
                code_parts.append(self._generate_objectives_slide(objectives))
            
            # Add content slides from sections
            sections = educational_script.get("sections", [])
            for i, section in enumerate(sections):
                code_parts.append(self._generate_section_slide(section, i))
            
            # Add assessment slide
            assessments = educational_script.get("assessments", [])
            if assessments:
                code_parts.append(self._generate_assessment_slide(assessments[0]))
            
            # Add conclusion slide
            code_parts.append(self._generate_conclusion_slide())
            
            # Join all parts
            full_code = "\n".join(code_parts)
            
            logger.info("Successfully generated Manim code")
            return full_code
            
        except Exception as e:
            logger.error(f"Error generating Manim code: {str(e)}")
            return self._generate_fallback_code(educational_script.get("title", "Educational Content"))
    
    def _generate_title_slide(self, title: str) -> str:
        """Generate title slide code"""
        clean_title = self._clean_text_for_manim(title)
        
        return f'''        # Title Slide
        title = Text("{clean_title}", font_size=48, color=BLUE)
        subtitle = Text("Educational Presentation", font_size=24, color=GRAY)
        subtitle.next_to(title, DOWN, buff=0.5)
        
        self.play(Write(title))
        self.play(Write(subtitle))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))
        
'''
    
    def _generate_objectives_slide(self, objectives: List[Dict[str, Any]]) -> str:
        """Generate learning objectives slide code"""
        code = '''        # Learning Objectives Slide
        objectives_title = Text("Learning Objectives", font_size=36, color=BLUE)
        objectives_title.to_edge(UP)
        self.play(Write(objectives_title))
        
'''
        
        for i, obj in enumerate(objectives[:4]):  # Limit to 4 objectives
            if isinstance(obj, dict):
                obj_text = obj.get("objective", str(obj))
            else:
                obj_text = str(obj)
            
            clean_obj = self._clean_text_for_manim(obj_text, max_length=80)
            
            code += f'''        obj_{i+1} = Text("• {clean_obj}", font_size=24, color=BLACK)
        obj_{i+1}.next_to(objectives_title, DOWN, buff={0.8 + i * 0.6})
        obj_{i+1}.align_to(objectives_title, LEFT)
        self.play(Write(obj_{i+1}))
        
'''
        
        code += '''        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        
'''
        return code
    
    def _generate_section_slide(self, section: Dict[str, Any], index: int) -> str:
        """Generate content section slide code"""
        title = section.get("title", f"Section {index + 1}")
        content = section.get("content", "")
        
        clean_title = self._clean_text_for_manim(title)
        clean_content = self._clean_text_for_manim(content, max_length=300)
        
        # Split content into manageable chunks
        content_lines = self._split_content_for_slide(clean_content)
        
        code = f'''        # Section {index + 1}: {title}
        section_title = Text("{clean_title}", font_size=32, color=BLUE)
        section_title.to_edge(UP)
        self.play(Write(section_title))
        
'''
        
        for i, line in enumerate(content_lines[:5]):  # Limit to 5 lines
            code += f'''        content_{index}_{i} = Text("{line}", font_size=20, color=BLACK)
        content_{index}_{i}.next_to(section_title, DOWN, buff={1.0 + i * 0.5})
        content_{index}_{i}.align_to(section_title, LEFT)
        self.play(Write(content_{index}_{i}))
        
'''
        
        code += '''        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        
'''
        return code
    
    def _generate_assessment_slide(self, assessment: Dict[str, Any]) -> str:
        """Generate assessment slide code"""
        title = assessment.get("title", "Assessment")
        questions = assessment.get("questions", [])
        
        clean_title = self._clean_text_for_manim(title)
        
        code = f'''        # Assessment Slide
        assessment_title = Text("{clean_title}", font_size=32, color=BLUE)
        assessment_title.to_edge(UP)
        self.play(Write(assessment_title))
        
'''
        
        if questions:
            question = questions[0]  # Show first question
            if isinstance(question, dict):
                question_text = question.get("question", str(question))
            else:
                question_text = str(question)
            
            clean_question = self._clean_text_for_manim(question_text, max_length=150)
            
            code += f'''        question = Text("{clean_question}", font_size=24, color=BLACK)
        question.next_to(assessment_title, DOWN, buff=1.0)
        question.align_to(assessment_title, LEFT)
        self.play(Write(question))
        
'''
        
        code += '''        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        
'''
        return code
    
    def _generate_conclusion_slide(self) -> str:
        """Generate conclusion slide code"""
        return '''        # Conclusion Slide
        conclusion = Text("Thank You!", font_size=48, color=BLUE)
        subtitle = Text("Questions?", font_size=24, color=GRAY)
        subtitle.next_to(conclusion, DOWN, buff=0.5)
        
        self.play(Write(conclusion))
        self.play(Write(subtitle))
        self.wait(3)
'''
    
    def _clean_text_for_manim(self, text: str, max_length: int = 100) -> str:
        """Clean and prepare text for Manim code generation"""
        if not text:
            return ""
        
        # Remove or escape problematic characters
        text = text.replace('"', '\\"')
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return text
    
    def _split_content_for_slide(self, content: str, max_line_length: int = 60) -> List[str]:
        """Split content into lines suitable for slide display"""
        if not content:
            return [""]
        
        words = content.split()
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
        
        return lines
    
    def _generate_fallback_code(self, title: str) -> str:
        """Generate basic fallback Manim code"""
        clean_title = self._clean_text_for_manim(title)
        
        return f'''{self.template_header}        # Fallback Presentation
        title = Text("{clean_title}", font_size=48, color=BLUE)
        self.play(Write(title))
        self.wait(2)
        
        content = Text("Educational content presentation", font_size=24, color=BLACK)
        content.next_to(title, DOWN, buff=1)
        self.play(Write(content))
        self.wait(3)
'''
    
    def validate_manim_code(self, code: str) -> Dict[str, Any]:
        """
        Validate generated Manim code for basic syntax
        
        Args:
            code: Generated Manim code
            
        Returns:
            Validation result with status and any errors
        """
        try:
            # Basic syntax validation
            compile(code, '<string>', 'exec')
            
            # Check for required Manim imports and structure
            required_elements = [
                'from manim import *',
                'class EducationalPresentation(Scene):',
                'def construct(self):'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in code:
                    missing_elements.append(element)
            
            if missing_elements:
                return {
                    "valid": False,
                    "errors": [f"Missing required element: {elem}" for elem in missing_elements]
                }
            
            return {
                "valid": True,
                "errors": [],
                "line_count": len(code.split('\n')),
                "estimated_duration": self._estimate_presentation_duration(code)
            }
            
        except SyntaxError as e:
            return {
                "valid": False,
                "errors": [f"Syntax error: {str(e)}"]
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
    
    def _estimate_presentation_duration(self, code: str) -> int:
        """Estimate presentation duration in seconds based on code analysis"""
        # Count wait statements and animations
        wait_matches = re.findall(r'self\.wait\((\d+(?:\.\d+)?)\)', code)
        total_wait_time = sum(float(match) for match in wait_matches)
        
        # Count animations (rough estimate)
        animation_count = len(re.findall(r'self\.play\(', code))
        estimated_animation_time = animation_count * 1.5  # 1.5 seconds per animation
        
        return int(total_wait_time + estimated_animation_time)