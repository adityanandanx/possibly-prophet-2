"""
Tests for Enhanced Content Structuring Agent
"""

import pytest
from unittest.mock import Mock, patch
from agents.content_structuring_agent import (
    EnhancedContentStructuringAgent,
    ContentType,
    SectionType,
    ContentSection,
    ContentAnalysis
)
from agents.exceptions import AgentExecutionError, AgentValidationError


class TestEnhancedContentStructuringAgent:
    """Test cases for Enhanced Content Structuring Agent"""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        with patch('agents.base_agent.Agent'):
            return EnhancedContentStructuringAgent()
    
    @pytest.fixture
    def sample_content(self):
        """Sample educational content for testing"""
        return """
        # Introduction to Machine Learning
        
        Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.
        
        ## What is Machine Learning?
        
        Machine learning algorithms build mathematical models based on training data to make predictions or decisions.
        
        ## Types of Machine Learning
        
        There are three main types of machine learning:
        
        1. Supervised Learning - uses labeled training data
        2. Unsupervised Learning - finds patterns in unlabeled data  
        3. Reinforcement Learning - learns through interaction with environment
        
        ## Applications
        
        Machine learning is used in many applications including:
        - Image recognition
        - Natural language processing
        - Recommendation systems
        - Autonomous vehicles
        
        ## Conclusion
        
        Machine learning is a powerful tool that continues to transform many industries.
        """
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.agent_type == "content_structuring"
        assert agent.name == "Enhanced Content Structuring Agent"
        assert len(agent.heading_patterns) > 0
        assert len(agent.topic_indicators) > 0
        assert len(agent.concept_patterns) > 0
    
    def test_identify_content_type(self, agent, sample_content):
        """Test content type identification"""
        content_type = agent._identify_content_type(sample_content)
        assert isinstance(content_type, ContentType)
        # Should identify as conceptual or technical content
        assert content_type in [ContentType.CONCEPTUAL, ContentType.TECHNICAL]
    
    def test_extract_main_topics(self, agent, sample_content):
        """Test main topic extraction"""
        topics = agent._extract_main_topics(sample_content)
        assert isinstance(topics, list)
        assert len(topics) > 0
        
        # Should extract topics from headings
        expected_topics = ["Introduction to Machine Learning", "What is Machine Learning", "Types of Machine Learning"]
        found_topics = [topic for topic in topics if any(expected in topic for expected in expected_topics)]
        assert len(found_topics) > 0
    
    def test_extract_key_concepts(self, agent, sample_content):
        """Test key concept extraction"""
        concepts = agent._extract_key_concepts(sample_content)
        assert isinstance(concepts, list)
        assert len(concepts) > 0
        
        # Should extract key ML concepts
        expected_concepts = ["machine learning", "artificial intelligence", "algorithms", "supervised learning"]
        found_concepts = [concept.lower() for concept in concepts]
        assert any(expected in found_concepts for expected in expected_concepts)
    
    def test_analyze_difficulty_level(self, agent):
        """Test difficulty level analysis"""
        # Simple content
        simple_content = "This is a simple explanation. It uses basic words. Anyone can understand it."
        difficulty = agent._analyze_difficulty_level(simple_content)
        assert difficulty in ["beginner", "intermediate", "advanced"]
        
        # Complex content
        complex_content = """
        The implementation of sophisticated machine learning methodologies requires comprehensive 
        understanding of mathematical optimization techniques, statistical inference procedures, 
        and computational complexity considerations in high-dimensional feature spaces.
        """
        difficulty = agent._analyze_difficulty_level(complex_content)
        assert difficulty in ["intermediate", "advanced"]
    
    def test_assess_structure_quality(self, agent, sample_content):
        """Test structure quality assessment"""
        quality = agent._assess_structure_quality(sample_content)
        assert isinstance(quality, float)
        assert 0.0 <= quality <= 1.0
        
        # Well-structured content should have higher quality score
        assert quality > 0.5  # Sample content has headings, lists, etc.
    
    def test_assess_coherence(self, agent, sample_content):
        """Test coherence assessment"""
        coherence = agent._assess_coherence(sample_content)
        assert isinstance(coherence, float)
        assert 0.0 <= coherence <= 1.0
    
    def test_create_initial_sections(self, agent, sample_content):
        """Test initial section creation"""
        sections = agent._create_initial_sections(sample_content)
        assert isinstance(sections, list)
        assert len(sections) > 0
        
        # Check section structure
        for section in sections:
            assert isinstance(section, ContentSection)
            assert section.title
            assert section.content
            assert isinstance(section.section_type, SectionType)
            assert section.level >= 1
            assert section.order >= 0
            assert isinstance(section.key_concepts, list)
            assert section.estimated_duration > 0
    
    def test_analyze_content_structure(self, agent, sample_content):
        """Test comprehensive content structure analysis"""
        analysis = agent._analyze_content_structure(sample_content)
        assert isinstance(analysis, ContentAnalysis)
        
        # Check analysis components
        assert isinstance(analysis.content_type, ContentType)
        assert isinstance(analysis.main_topics, list)
        assert isinstance(analysis.key_concepts, list)
        assert analysis.difficulty_level in ["beginner", "intermediate", "advanced"]
        assert analysis.estimated_reading_time > 0
        assert 0.0 <= analysis.structure_quality <= 1.0
        assert 0.0 <= analysis.coherence_score <= 1.0
        assert isinstance(analysis.sections, list)
        assert isinstance(analysis.content_flow, list)
    
    def test_generate_section_title(self, agent):
        """Test section title generation"""
        # Test with clear title content
        content_with_title = "Introduction to Neural Networks\n\nNeural networks are computational models..."
        title = agent._generate_section_title(content_with_title, 0)
        assert "Introduction" in title or "Neural Networks" in title
        
        # Test with generic content
        generic_content = "This section covers various topics related to the subject matter."
        title = agent._generate_section_title(generic_content, 1)
        assert title  # Should generate some title
    
    def test_determine_section_type(self, agent):
        """Test section type determination"""
        # Introduction content
        intro_content = "This introduction provides an overview of the topic."
        section_type = agent._determine_section_type(intro_content, 0, 5)
        assert section_type == SectionType.INTRODUCTION
        
        # Conclusion content
        conclusion_content = "In conclusion, we have covered the main concepts."
        section_type = agent._determine_section_type(conclusion_content, 4, 5)
        assert section_type == SectionType.CONCLUSION
        
        # Example content
        example_content = "For example, consider the following case study."
        section_type = agent._determine_section_type(example_content, 2, 5)
        assert section_type == SectionType.EXAMPLE
    
    def test_analyze_content_flow(self, agent):
        """Test content flow analysis"""
        content = "Introduction to the topic. Main concepts follow. Examples are provided. Conclusion summarizes."
        topics = ["Main Concepts", "Examples"]
        flow = agent._analyze_content_flow(content, topics)
        
        assert isinstance(flow, list)
        assert len(flow) > 0
        assert "Introduction" in flow
        assert "Conclusion" in flow or any("Conclusion" in item for item in flow)
    
    def test_is_section_boundary(self, agent):
        """Test section boundary detection"""
        current = "This is the current paragraph."
        
        # Next paragraph with heading
        next_heading = "# New Section\nThis starts a new section."
        assert agent._is_section_boundary(current, next_heading)
        
        # Next paragraph with transition
        next_transition = "Now let's move on to the next topic."
        assert agent._is_section_boundary(current, next_transition)
        
        # Regular continuation
        next_regular = "This continues the same topic with more details."
        # May or may not be boundary depending on content
        result = agent._is_section_boundary(current, next_regular)
        assert isinstance(result, bool)
    
    @patch('agents.base_agent.Agent')
    def test_process_content_integration(self, mock_agent_class):
        """Test full content processing integration"""
        # Mock the Strands Agent
        mock_agent = Mock()
        mock_agent.return_value = "Structured content analysis with sections and key concepts."
        mock_agent_class.return_value = mock_agent
        
        agent = EnhancedContentStructuringAgent()
        
        sample_content = """
        # Data Science Fundamentals
        
        Data science combines statistics, programming, and domain expertise.
        
        ## Key Skills
        - Statistical analysis
        - Programming (Python, R)
        - Data visualization
        - Machine learning
        
        ## Process
        1. Data collection
        2. Data cleaning
        3. Analysis
        4. Interpretation
        """
        
        context = {
            "topic": "Data Science",
            "difficulty_level": "intermediate",
            "target_audience": "students"
        }
        
        result = agent.process_content(sample_content, context)
        
        # Check result structure
        assert isinstance(result, dict)
        assert "agent_type" in result
        assert "processed_content" in result
        assert "structured_content" in result
        assert "metadata" in result
        
        assert result["agent_type"] == "content_structuring"
        assert "structured_content" in result
        
        # Verify agent was called
        mock_agent.assert_called_once()
    
    def test_validation_errors(self, agent):
        """Test validation error handling"""
        # Test empty structure validation
        with pytest.raises(AgentValidationError):
            agent._validate_content_structure({})
        
        # Test missing raw response
        with pytest.raises(AgentValidationError):
            agent._validate_content_structure({"some_key": "some_value"})
    
    def test_content_section_to_dict(self):
        """Test ContentSection to_dict conversion"""
        section = ContentSection(
            title="Test Section",
            content="Test content",
            section_type=SectionType.MAIN_CONCEPT,
            level=1,
            order=0,
            key_concepts=["concept1", "concept2"],
            estimated_duration=5,
            prerequisites=["prereq1"],
            learning_outcomes=["outcome1"],
            subsections=[]
        )
        
        section_dict = section.to_dict()
        assert isinstance(section_dict, dict)
        assert section_dict["title"] == "Test Section"
        assert section_dict["section_type"] == "main_concept"
        assert section_dict["key_concepts"] == ["concept1", "concept2"]
    
    def test_content_analysis_to_dict(self):
        """Test ContentAnalysis to_dict conversion"""
        analysis = ContentAnalysis(
            content_type=ContentType.TUTORIAL,
            main_topics=["topic1", "topic2"],
            key_concepts=["concept1"],
            difficulty_level="intermediate",
            estimated_reading_time=10,
            structure_quality=0.8,
            coherence_score=0.7,
            sections=[],
            content_flow=["intro", "main", "conclusion"]
        )
        
        analysis_dict = analysis.to_dict()
        assert isinstance(analysis_dict, dict)
        assert analysis_dict["content_type"] == "tutorial"
        assert analysis_dict["difficulty_level"] == "intermediate"
        assert analysis_dict["structure_quality"] == 0.8


class TestContentStructuringIntegration:
    """Integration tests for content structuring"""
    
    @pytest.fixture
    def complex_content(self):
        """Complex educational content for integration testing"""
        return """
        # Advanced Python Programming Concepts
        
        ## Introduction
        
        Python is a versatile programming language that supports multiple programming paradigms.
        This guide covers advanced concepts that every Python developer should understand.
        
        ## Object-Oriented Programming
        
        ### Classes and Objects
        
        Classes are blueprints for creating objects. Objects are instances of classes.
        
        ```python
        class Student:
            def __init__(self, name, age):
                self.name = name
                self.age = age
        ```
        
        ### Inheritance
        
        Inheritance allows classes to inherit attributes and methods from other classes.
        
        ## Functional Programming
        
        Python supports functional programming concepts like:
        - Higher-order functions
        - Lambda expressions
        - Map, filter, and reduce
        
        ### Example: Using Lambda Functions
        
        ```python
        square = lambda x: x ** 2
        numbers = [1, 2, 3, 4, 5]
        squared = list(map(square, numbers))
        ```
        
        ## Decorators
        
        Decorators are a powerful feature that allows modification of functions or classes.
        
        ### Function Decorators
        
        ```python
        def timer(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                end = time.time()
                print(f"Execution time: {end - start}")
                return result
            return wrapper
        ```
        
        ## Context Managers
        
        Context managers provide a way to allocate and release resources precisely.
        
        ## Conclusion
        
        These advanced concepts will help you write more efficient and maintainable Python code.
        Understanding these patterns is essential for professional Python development.
        """
    
    @patch('agents.base_agent.Agent')
    def test_complex_content_analysis(self, mock_agent_class, complex_content):
        """Test analysis of complex educational content"""
        mock_agent = Mock()
        mock_agent.return_value = "Comprehensive analysis of Python programming concepts with structured sections."
        mock_agent_class.return_value = mock_agent
        
        agent = EnhancedContentStructuringAgent()
        analysis = agent._analyze_content_structure(complex_content)
        
        # Should identify as technical content
        assert analysis.content_type == ContentType.TECHNICAL
        
        # Should extract multiple main topics
        assert len(analysis.main_topics) >= 3
        
        # Should identify key programming concepts
        programming_concepts = [concept.lower() for concept in analysis.key_concepts]
        expected_concepts = ["python", "programming", "classes", "objects", "inheritance"]
        assert any(expected in programming_concepts for expected in expected_concepts)
        
        # Should create multiple sections
        assert len(analysis.sections) >= 2
        
        # Should have reasonable reading time
        assert analysis.estimated_reading_time > 5
        
        # Should assess as intermediate/advanced difficulty
        assert analysis.difficulty_level in ["intermediate", "advanced"]
    
    def test_section_hierarchy_creation(self, complex_content):
        """Test creation of proper section hierarchies"""
        with patch('agents.base_agent.Agent'):
            agent = EnhancedContentStructuringAgent()
            sections = agent._create_initial_sections(complex_content)
            
            # Should create multiple sections
            assert len(sections) >= 3
            
            # Should have introduction and conclusion
            section_types = [section.section_type for section in sections]
            assert SectionType.INTRODUCTION in section_types
            
            # Sections should have proper ordering
            orders = [section.order for section in sections]
            assert orders == sorted(orders)  # Should be in ascending order
            
            # Each section should have content and concepts
            for section in sections:
                assert len(section.content) > 0
                assert section.estimated_duration > 0