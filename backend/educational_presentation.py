from manim import *


class EducationalPresentation(Scene):
    def construct(self):
        # Set background color
        self.camera.background_color = WHITE

        # Title Slide
        title = Text("Generated Educational Content", font_size=48, color=BLUE)
        subtitle = Text("Educational Presentation", font_size=32, color=BLACK)
        VGroup(title, subtitle).arrange(DOWN, buff=0.5).to_edge(UP)

        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(subtitle, shift=UP), run_time=1.0)
        self.wait(3.0)
        self.play(FadeOut(title, subtitle))

        # Objectives Slide
        objectives = [
            "Define and differentiate between supervised/unsupervised learning",
            "Apply supervised learning for 85%+ classification accuracy",
            "Analyze overfitting/underfitting impact on performance",
            "Examine relationships between variables in model evaluation",
        ]
        bullets = VGroup(*[Tex(obj, font_size=24, color=BLACK) for obj in objectives])
        bullets.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        title = Text("Learning Objectives", font_size=36, color=BLUE)
        title.to_edge(UP)

        self.play(Write(title), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(b, shift=UP) for b in bullets], lag_ratio=0.2))
        self.wait(5.0)
        self.play(FadeOut(title, bullets))

        # Content Structure Slide
        content = [
            "**Educational Content Structure: Machine Learning**",
            "I. Overview (1 min, Intermediate)",
            "- AI subset, pattern recognition",
            "II. Core Concepts (5 min, Intermediate)",
            "- Supervised/Unsupervised learning",
            "III. Advanced Concepts (6 min, Advanced)",
            "- Neural Networks, Model Training",
        ]
        content_text = VGroup(
            *[Tex(line, font_size=24, color=BLACK) for line in content]
        )
        content_text.arrange(DOWN, aligned_edge=LEFT, buff=0.2)

        self.play(LaggedStart(*[Write(line) for line in content_text], lag_ratio=0.3))
        self.wait(8.0)
        self.play(FadeOut(content_text))

        # Prerequisites Slide
        prereq = [
            "**Prerequisites:**",
            "- Data/algorithms basics",
            "- Statistical concepts familiarity",
            "**Dependencies:**",
            "- III builds on I+II",
            "- IV requires model training (III.B)",
        ]
        prereq_text = VGroup(*[Tex(line, font_size=24, color=BLACK) for line in prereq])
        prereq_text.arrange(DOWN, aligned_edge=LEFT, buff=0.2)

        self.play(
            LaggedStart(
                *[FadeIn(line, shift=UP) for line in prereq_text], lag_ratio=0.2
            )
        )
        self.wait(8.0)
        self.play(FadeOut(prereq_text))

        # Assessment Slide
        quiz_title = Text("Content Assessment", font_size=36, color=BLUE)
        questions = [
            "Define key ML concepts (10 pts)",
            "Apply classification techniques (10 pts)",
            "Analyze performance metrics (10 pts)",
        ]
        quiz_items = VGroup(*[Tex(q, font_size=24, color=BLACK) for q in questions])
        quiz_items.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        quiz = VGroup(quiz_title, quiz_items).arrange(DOWN, buff=0.5)

        self.play(Write(quiz_title), run_time=1.0)
        self.play(
            LaggedStart(*[FadeIn(q, shift=UP) for q in quiz_items], lag_ratio=0.2)
        )
        self.wait(6.0)
        self.play(FadeOut(quiz))

        # Summary Slide
        summary_points = [
            "Supervised vs Unsupervised learning",
            "Classification accuracy application",
            "Content structure overview",
            "Advanced concepts exploration",
        ]
        summary = VGroup(*[Tex(p, font_size=24, color=BLACK) for p in summary_points])
        summary.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        title = Text("Key Takeaways", font_size=36, color=BLUE)
        title.to_edge(UP)

        self.play(Write(title), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(p, shift=UP) for p in summary], lag_ratio=0.2))
        self.wait(4.0)
        self.play(FadeOut(title, summary))

        # Conclusion Slide
        thanks = Text("Thank You!", font_size=48, color=BLUE)
        questions = Text("Questions?", font_size=32, color=BLACK)
        questions.next_to(thanks, DOWN, buff=0.5)

        self.play(Write(thanks), run_time=1.5)
        self.play(FadeIn(questions, shift=UP), run_time=1.0)
        self.wait(3.0)
