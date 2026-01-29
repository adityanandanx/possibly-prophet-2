from manim import *

class EducationalPresentation(Scene):
    """Generated educational presentation"""
    
    def construct(self):
        """Main presentation construction"""
        self.camera.background_color = WHITE
        

        # Title Slide
        title = Text("Generated Educational Content", font_size=48, color=BLUE)
        subtitle = Text("Educational Presentation", font_size=24, color=GRAY)
        subtitle.next_to(title, DOWN, buff=0.5)
        
        self.play(Write(title))
        self.play(Write(subtitle))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))
        

        # Learning Objectives Slide
        objectives_title = Text("Learning Objectives", font_size=36, color=BLUE)
        objectives_title.to_edge(UP)
        self.play(Write(objectives_title))
        
        obj_1 = Text("• ing objectives based on the provided content, aligned with Bloom's Taxonomy a...", font_size=24, color=BLACK)
        obj_1.next_to(objectives_title, DOWN, buff=0.8)
        obj_1.align_to(objectives_title, LEFT)
        self.play(Write(obj_1))
        
        obj_2 = Text("• **: Define a 3D vector and list its components.", font_size=24, color=BLACK)
        obj_2.next_to(objectives_title, DOWN, buff=1.4)
        obj_2.align_to(objectives_title, LEFT)
        self.play(Write(obj_2))
        
        obj_3 = Text("• ensures students can recall basic information about vectors, which is foundat...", font_size=24, color=BLACK)
        obj_3.next_to(objectives_title, DOWN, buff=2.0)
        obj_3.align_to(objectives_title, LEFT)
        self.play(Write(obj_3))
        
        obj_4 = Text("• **: Explain the geometric interpretation of vector addition in 3D space using...", font_size=24, color=BLACK)
        obj_4.next_to(objectives_title, DOWN, buff=2.5999999999999996)
        obj_4.align_to(objectives_title, LEFT)
        self.play(Write(obj_4))
        
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        

        # Section 1: **Educational Content Structure: Vectors in 3D**
        section_title = Text("**Educational Content Structure: Vectors in 3D**", font_size=32, color=BLUE)
        section_title.to_edge(UP)
        self.play(Write(section_title))
        
        content_0_0 = Text("**Educational Content Structure: Vectors in 3D** **I.", font_size=20, color=BLACK)
        content_0_0.next_to(section_title, DOWN, buff=1.0)
        content_0_0.align_to(section_title, LEFT)
        self.play(Write(content_0_0))
        
        content_0_1 = Text("Introduction to 3D Vectors** - **Key Concepts**: Definition", font_size=20, color=BLACK)
        content_0_1.next_to(section_title, DOWN, buff=1.5)
        content_0_1.align_to(section_title, LEFT)
        self.play(Write(content_0_1))
        
        content_0_2 = Text("of vectors, components in 3D space - **Learning Outcomes**:", font_size=20, color=BLACK)
        content_0_2.next_to(section_title, DOWN, buff=2.0)
        content_0_2.align_to(section_title, LEFT)
        self.play(Write(content_0_2))
        
        content_0_3 = Text("Understand what vectors are and how they are represented in", font_size=20, color=BLACK)
        content_0_3.next_to(section_title, DOWN, buff=2.5)
        content_0_3.align_to(section_title, LEFT)
        self.play(Write(content_0_3))
        
        content_0_4 = Text("three dimensions - **Duration**: 2 minutes - **Content", font_size=20, color=BLACK)
        content_0_4.next_to(section_title, DOWN, buff=3.0)
        content_0_4.align_to(section_title, LEFT)
        self.play(Write(content_0_4))
        
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        

        # Section 2: **III
        section_title = Text("**III", font_size=32, color=BLUE)
        section_title.to_edge(UP)
        self.play(Write(section_title))
        
        content_1_0 = Text("**III. Vector Subtraction** - **Key Concepts**: Difference", font_size=20, color=BLACK)
        content_1_0.next_to(section_title, DOWN, buff=1.0)
        content_1_0.align_to(section_title, LEFT)
        self.play(Write(content_1_0))
        
        content_1_1 = Text("vector, component-wise subtraction - **Learning Outcomes**:", font_size=20, color=BLACK)
        content_1_1.next_to(section_title, DOWN, buff=1.5)
        content_1_1.align_to(section_title, LEFT)
        self.play(Write(content_1_1))
        
        content_1_2 = Text("Understand how to subtract one vector from another in 3D -", font_size=20, color=BLACK)
        content_1_2.next_to(section_title, DOWN, buff=2.0)
        content_1_2.align_to(section_title, LEFT)
        self.play(Write(content_1_2))
        
        content_1_3 = Text("**Duration**: 3 minutes - **Content Flow**: Describe", font_size=20, color=BLACK)
        content_1_3.next_to(section_title, DOWN, buff=2.5)
        content_1_3.align_to(section_title, LEFT)
        self.play(Write(content_1_3))
        
        content_1_4 = Text("subtracting vectors by subtracting their i, j, and k", font_size=20, color=BLACK)
        content_1_4.next_to(section_title, DOWN, buff=3.0)
        content_1_4.align_to(section_title, LEFT)
        self.play(Write(content_1_4))
        
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        

        # Section 3: Section 3
        section_title = Text("Section 3", font_size=32, color=BLUE)
        section_title.to_edge(UP)
        self.play(Write(section_title))
        
        content_2_0 = Text("**Prerequisites**: - Basic understanding of algebra and", font_size=20, color=BLACK)
        content_2_0.next_to(section_title, DOWN, buff=1.0)
        content_2_0.align_to(section_title, LEFT)
        self.play(Write(content_2_0))
        
        content_2_1 = Text("coordinate geometry - Familiarity with 2D vectors", font_size=20, color=BLACK)
        content_2_1.next_to(section_title, DOWN, buff=1.5)
        content_2_1.align_to(section_title, LEFT)
        self.play(Write(content_2_1))
        
        content_2_2 = Text("(recommended but not required) **Dependencies**: -", font_size=20, color=BLACK)
        content_2_2.next_to(section_title, DOWN, buff=2.0)
        content_2_2.align_to(section_title, LEFT)
        self.play(Write(content_2_2))
        
        content_2_3 = Text("Understanding vector addition is necessary before tackling", font_size=20, color=BLACK)
        content_2_3.next_to(section_title, DOWN, buff=2.5)
        content_2_3.align_to(section_title, LEFT)
        self.play(Write(content_2_3))
        
        content_2_4 = Text("vector subtraction - Practical applications rely on mastery", font_size=20, color=BLACK)
        content_2_4.next_to(section_title, DOWN, buff=3.0)
        content_2_4.align_to(section_title, LEFT)
        self.play(Write(content_2_4))
        
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        

        # Section 4: Section 4
        section_title = Text("Section 4", font_size=32, color=BLUE)
        section_title.to_edge(UP)
        self.play(Write(section_title))
        
        content_3_0 = Text("**Recommendations**: - Include interactive elements", font_size=20, color=BLACK)
        content_3_0.next_to(section_title, DOWN, buff=1.0)
        content_3_0.align_to(section_title, LEFT)
        self.play(Write(content_3_0))
        
        content_3_1 = Text("(quizzes, exercises) after each section to reinforce", font_size=20, color=BLACK)
        content_3_1.next_to(section_title, DOWN, buff=1.5)
        content_3_1.align_to(section_title, LEFT)
        self.play(Write(content_3_1))
        
        content_3_2 = Text("learning - Use visual aids (diagrams, animations) to support", font_size=20, color=BLACK)
        content_3_2.next_to(section_title, DOWN, buff=2.0)
        content_3_2.align_to(section_title, LEFT)
        self.play(Write(content_3_2))
        
        content_3_3 = Text("comprehension of 3D concepts - Provide additional resources", font_size=20, color=BLACK)
        content_3_3.next_to(section_title, DOWN, buff=2.5)
        content_3_3.align_to(section_title, LEFT)
        self.play(Write(content_3_3))
        
        content_3_4 = Text("for students needing more practice with algebraic operations", font_size=20, color=BLACK)
        content_3_4.next_to(section_title, DOWN, buff=3.0)
        content_3_4.align_to(section_title, LEFT)
        self.play(Write(content_3_4))
        
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        

        # Assessment Slide
        assessment_title = Text("Content Assessment", font_size=32, color=BLUE)
        assessment_title.to_edge(UP)
        self.play(Write(assessment_title))
        
        question = Text("ment Criteria", font_size=24, color=BLACK)
        question.next_to(assessment_title, DOWN, buff=1.0)
        question.align_to(assessment_title, LEFT)
        self.play(Write(question))
        
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        

        # Conclusion Slide
        conclusion = Text("Thank You!", font_size=48, color=BLUE)
        subtitle = Text("Questions?", font_size=24, color=GRAY)
        subtitle.next_to(conclusion, DOWN, buff=0.5)
        
        self.play(Write(conclusion))
        self.play(Write(subtitle))
        self.wait(3)
