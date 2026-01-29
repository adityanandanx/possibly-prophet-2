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
        
        obj_1 = Text("• ing objectives based on content", font_size=24, color=BLACK)
        obj_1.next_to(objectives_title, DOWN, buff=0.8)
        obj_1.align_to(objectives_title, LEFT)
        self.play(Write(obj_1))
        
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        

        # Section 1: Main Content
        section_title = Text("Main Content", font_size=32, color=BLUE)
        section_title.to_edge(UP)
        self.play(Write(section_title))
        
        content_0_0 = Text("Machine learning is a subset of artificial intelligence", font_size=20, color=BLACK)
        content_0_0.next_to(section_title, DOWN, buff=1.0)
        content_0_0.align_to(section_title, LEFT)
        self.play(Write(content_0_0))
        
        content_0_1 = Text("that enables computers to learn and make decisions from data", font_size=20, color=BLACK)
        content_0_1.next_to(section_title, DOWN, buff=1.5)
        content_0_1.align_to(section_title, LEFT)
        self.play(Write(content_0_1))
        
        content_0_2 = Text("without being explicitly programmed. Key concepts include: -", font_size=20, color=BLACK)
        content_0_2.next_to(section_title, DOWN, buff=2.0)
        content_0_2.align_to(section_title, LEFT)
        self.play(Write(content_0_2))
        
        content_0_3 = Text("Supervised learning: Learning from labeled examples -", font_size=20, color=BLACK)
        content_0_3.next_to(section_title, DOWN, buff=2.5)
        content_0_3.align_to(section_title, LEFT)
        self.play(Write(content_0_3))
        
        content_0_4 = Text("Unsupervised learning: Finding patterns in unlabeled data -", font_size=20, color=BLACK)
        content_0_4.next_to(section_title, DOWN, buff=3.0)
        content_0_4.align_to(section_title, LEFT)
        self.play(Write(content_0_4))
        
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        

        # Conclusion Slide
        conclusion = Text("Thank You!", font_size=48, color=BLUE)
        subtitle = Text("Questions?", font_size=24, color=GRAY)
        subtitle.next_to(conclusion, DOWN, buff=0.5)
        
        self.play(Write(conclusion))
        self.play(Write(subtitle))
        self.wait(3)
