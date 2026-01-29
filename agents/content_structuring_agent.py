"""
Enhanced Content Structuring Agent for Educational Content Generator

This agent specializes in analyzing and organizing educational content into
logical sections with clear hierarchies, improved content flow, and structured
learning progressions.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseEducationalAgent
from .exceptions import AgentExecutionError, AgentValidationError

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of educational content"""
    ACADEMIC = "academic"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    NARRATIVE = "narrative"
    TECHNICAL = "technical"
    CONCEPTUAL = "conceptual"


class SectionType(Enum):
    """Types of content sections"""
    INTRODUCTION = "introduction"
    OVERVIEW = "overview"
    MAIN_CONCEPT = "main_concept"
    EXAMPLE = "example"
    EXPLANATION = "explanation"
    PROCEDURE = "procedure"
    SUMMARY = "summary"
    CONCLUSION = "conclusion"
    EXERCISE = "exercise"
    REFERENCE = "reference"


@dataclass
class ContentSection:
    """Represents a structured content section"""
    title: str
    content: str
    section_type: SectionType
    level: int  # Hierarchy level (1 = top level, 2 = subsection, etc.)
    order: int  # Order within the same level
    key_concepts: List[str]
    estimated_duration: int  # In minutes
    prerequisites: List[str]
    learning_outcomes: List[str]
    subsections: List['ContentSection']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "title": self.title,
            "content": self.content,
            "section_type": self.section_type.value,
            "level": self.level,
            "order": self.order,
            "key_concepts": self.key_concepts,
            "estimated_duration": self.estimated_duration,
            "prerequisites": self.prerequisites,
            "learning_outcomes": self.learning_outcomes,
            "subsections": [sub.to_dict() for sub in self.subsections]
        }


@dataclass
class ContentAnalysis:
    """Results of content analysis"""
    content_type: ContentType
    main_topics: List[str]
    key_concepts: List[str]
    difficulty_level: str
    estimated_reading_time: int
    structure_quality: float  # 0.0 to 1.0
    coherence_score: float   # 0.0 to 1.0
    sections: List[ContentSection]
    content_flow: List[str]  # Logical progression of topics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "content_type": self.content_type.value,
            "main_topics": self.main_topics,
            "key_concepts": self.key_concepts,
            "difficulty_level": self.difficulty_level,
            "estimated_reading_time": self.estimated_reading_time,
            "structure_quality": self.structure_quality,
            "coherence_score": self.coherence_score,
            "sections": [section.to_dict() for section in self.sections],
            "content_flow": self.content_flow
        }


class EnhancedContentStructuringAgent(BaseEducationalAgent):
    """
    Enhanced Content Structuring Agent with advanced content analysis and organization
    """
    
    def __init__(self, **kwargs):
        """Initialize the enhanced content structuring agent"""
        super().__init__("content_structuring", **kwargs)
        
        # Enhanced content analysis patterns with more sophisticated detection
        self.heading_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headings
            r'^(.+)\n[=-]{3,}$',  # Underlined headings
            r'^\d+\.\s+(.+)$',   # Numbered headings
            r'^[A-Z][A-Z\s]{2,}$',  # ALL CAPS headings
            r'^(.{1,50}):$',     # Colon-terminated headings
            r'^\*\*(.+)\*\*$',   # Bold headings (markdown)
            r'^__(.+)__$',       # Bold headings (alternative markdown)
            r'^\s*([A-Z][^.!?]*?)\s*\n\s*$',  # Standalone capitalized lines
        ]
        
        # Enhanced topic identification patterns with semantic understanding
        self.topic_indicators = [
            r'(?:introduction|overview|background|context|getting started)',
            r'(?:definition|concept|principle|theory|fundamental|basic)',
            r'(?:example|illustration|case study|scenario|demonstration)',
            r'(?:method|procedure|process|algorithm|steps|approach)',
            r'(?:analysis|evaluation|comparison|contrast|assessment)',
            r'(?:conclusion|summary|results|findings|outcomes)',
            r'(?:application|implementation|practice|usage|deployment)',
            r'(?:exercise|problem|question|task|assignment|challenge)',
            r'(?:discussion|explanation|interpretation|understanding)',
            r'(?:review|recap|synthesis|integration|consolidation)',
        ]
        
        # Advanced concept extraction patterns with context awareness
        self.concept_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Proper nouns
            r'\b(\w+(?:\s+\w+){0,2})\s+(?:is|are|means|refers to)',  # Definitions
            r'(?:the concept of|the principle of|the theory of)\s+(\w+(?:\s+\w+)*)',
            r'\*\*([^*]+)\*\*',  # Bold text (markdown)
            r'\*([^*]+)\*',      # Italic text (markdown)
            r'_([^_]+)_',        # Underlined text
            r'`([^`]+)`',        # Code/technical terms
            r'"([^"]+)"',        # Quoted important terms
            r'(?:key|important|essential|critical|fundamental)\s+(\w+(?:\s+\w+)*)',
        ]
        
        # Section boundary detection patterns
        self.section_boundary_patterns = [
            r'^\s*(?:section|chapter|part)\s*\d*[:\-\s]*',
            r'^\s*(?:now|next|moving on|let\'s|another)',
            r'^\s*(?:in this|this section|here we)',
            r'^\s*(?:furthermore|moreover|additionally|however)',
        ]
        
        # Topic transition indicators for better section identification
        self.transition_indicators = [
            'now let us', 'next we will', 'moving on to', 'another important',
            'in addition to', 'furthermore', 'however', 'on the other hand',
            'meanwhile', 'subsequently', 'consequently', 'therefore',
            'in contrast', 'similarly', 'alternatively', 'specifically'
        ]
        
        logger.info("Enhanced Content Structuring Agent initialized")
    
    def _prepare_prompt(self, content: str, context: Dict[str, Any]) -> str:
        """Prepare enhanced prompt for content structuring"""
        
        # Perform initial content analysis
        analysis = self._analyze_content_structure(content)
        
        # Build context-aware prompt
        prompt_parts = [
            "You are an expert educational content structuring agent. Your task is to analyze and organize educational content into logical, hierarchical sections that enhance learning.",
            "",
            "CONTENT TO STRUCTURE:",
            content,
            "",
            "ANALYSIS CONTEXT:",
            f"- Content Type: {analysis.content_type.value}",
            f"- Main Topics: {', '.join(analysis.main_topics)}",
            f"- Key Concepts: {', '.join(analysis.key_concepts)}",
            f"- Difficulty Level: {analysis.difficulty_level}",
            f"- Estimated Reading Time: {analysis.estimated_reading_time} minutes",
            "",
            "STRUCTURING REQUIREMENTS:",
            "1. Create a clear hierarchical structure with logical section progression",
            "2. Identify and extract key concepts for each section",
            "3. Ensure each section has clear learning outcomes",
            "4. Organize content to support progressive learning",
            "5. Maintain coherent flow between sections",
            "6. Estimate appropriate duration for each section",
            "",
            "ADDITIONAL CONTEXT:",
        ]
        
        # Add context information
        if context:
            for key, value in context.items():
                if key not in ['original_content', 'previous_results']:
                    prompt_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        prompt_parts.extend([
            "",
            "Please provide a structured analysis with:",
            "- Clear section titles and hierarchies",
            "- Key concepts for each section",
            "- Learning outcomes for each section",
            "- Logical content flow and progression",
            "- Estimated duration for each section",
            "",
            "Format your response as a detailed educational content structure."
        ])
        
        return "\n".join(prompt_parts)
    
    def _process_response(self, response: str) -> Dict[str, Any]:
        """Process agent response with enhanced content structuring and hierarchical analysis"""
        try:
            # Parse the agent's response to extract structured information
            structured_content = self._parse_agent_response(response)
            
            # Generate comprehensive hierarchical structure
            hierarchical_structure = self._generate_hierarchical_content_structure(response)
            
            # Enhance with additional analysis
            enhanced_structure = self._enhance_content_structure(structured_content)
            
            # Combine all structural information
            enhanced_structure['hierarchical_structure'] = hierarchical_structure
            
            # Validate the structure
            self._validate_content_structure(enhanced_structure)
            
            return {
                "agent_type": self.agent_type,
                "processed_content": response,
                "structured_content": enhanced_structure,
                "metadata": {
                    "agent_name": self.name,
                    "processing_timestamp": datetime.now().isoformat(),
                    "structure_version": "3.0",
                    "analysis_method": "enhanced_hierarchical_analysis",
                    "hierarchy_depth": hierarchical_structure['metadata']['total_levels'],
                    "complexity_score": hierarchical_structure['metadata']['complexity_score'],
                    "coherence_metrics": hierarchical_structure['metadata']['coherence_metrics']
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing content structuring response: {str(e)}")
            raise AgentExecutionError(
                "Failed to process content structuring response",
                agent_type=self.agent_type,
                original_error=e
            )
    
    def _analyze_content_structure(self, content: str) -> ContentAnalysis:
        """
        Perform comprehensive content structure analysis with enhanced logic
        
        Args:
            content: Raw educational content
            
        Returns:
            ContentAnalysis with detailed structure information
        """
        try:
            # Enhanced content metrics
            word_count = len(content.split())
            sentence_count = len(re.findall(r'[.!?]+', content))
            paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
            estimated_reading_time = max(1, word_count // 200)  # ~200 words per minute
            
            # Advanced content type identification
            content_type = self._identify_content_type_enhanced(content)
            
            # Enhanced topic and concept extraction
            main_topics = self._extract_main_topics_enhanced(content)
            key_concepts = self._extract_key_concepts_enhanced(content)
            
            # Advanced difficulty analysis
            difficulty_level = self._analyze_difficulty_level_enhanced(content)
            
            # Enhanced structure quality assessment
            structure_quality = self._assess_structure_quality_enhanced(content)
            coherence_score = self._assess_coherence_enhanced(content)
            
            # Create enhanced sections with better organization
            sections = self._create_enhanced_sections(content)
            
            # Determine optimal content flow
            content_flow = self._analyze_content_flow_enhanced(content, main_topics, sections)
            
            # Add content organization metrics
            organization_metrics = self._calculate_organization_metrics(content, sections)
            
            analysis = ContentAnalysis(
                content_type=content_type,
                main_topics=main_topics,
                key_concepts=key_concepts,
                difficulty_level=difficulty_level,
                estimated_reading_time=estimated_reading_time,
                structure_quality=structure_quality,
                coherence_score=coherence_score,
                sections=sections,
                content_flow=content_flow
            )
            
            # Add enhanced metadata
            analysis.word_count = word_count
            analysis.sentence_count = sentence_count
            analysis.paragraph_count = paragraph_count
            analysis.organization_metrics = organization_metrics
            
            logger.info(f"Enhanced content analysis completed: {len(sections)} sections, "
                       f"{len(main_topics)} topics, {len(key_concepts)} concepts")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content structure: {str(e)}")
            # Return enhanced fallback analysis
            return self._create_fallback_analysis(content)
    
    def _identify_content_type_enhanced(self, content: str) -> ContentType:
        """Enhanced content type identification with better pattern matching"""
        content_lower = content.lower()
        word_count = len(content.split())
        
        # Calculate weighted scores for each content type
        type_scores = {
            ContentType.ACADEMIC: 0,
            ContentType.TUTORIAL: 0,
            ContentType.TECHNICAL: 0,
            ContentType.REFERENCE: 0,
            ContentType.NARRATIVE: 0,
            ContentType.CONCEPTUAL: 0
        }
        
        # Academic indicators with weights
        academic_patterns = {
            r'\b(?:research|study|analysis|methodology|hypothesis|conclusion|findings|results)\b': 2,
            r'\b(?:abstract|literature review|methodology|discussion|references)\b': 3,
            r'\b(?:peer.?reviewed|journal|publication|citation|bibliography)\b': 3,
            r'\b(?:statistical|empirical|quantitative|qualitative)\b': 2,
            r'\b(?:experiment|survey|interview|data collection)\b': 2
        }
        
        # Tutorial indicators with weights
        tutorial_patterns = {
            r'\b(?:step|how to|tutorial|guide|instructions|follow|learn)\b': 2,
            r'\b(?:first|second|third|next|then|finally)\b': 1,
            r'\b(?:click|select|choose|enter|type|press)\b': 2,
            r'\b(?:beginner|getting started|introduction to)\b': 3,
            r'^\s*\d+\.\s': 2  # Numbered steps
        }
        
        # Technical indicators with weights
        technical_patterns = {
            r'\b(?:algorithm|implementation|code|system|technical|specification)\b': 2,
            r'\b(?:function|method|class|variable|parameter|return)\b': 3,
            r'\b(?:API|SDK|framework|library|database|server)\b': 2,
            r'\b(?:configuration|deployment|architecture|design pattern)\b': 2,
            r'```|`[^`]+`': 3  # Code blocks
        }
        
        # Reference indicators with weights
        reference_patterns = {
            r'\b(?:definition|reference|glossary|index|appendix|dictionary)\b': 3,
            r'\b(?:see also|refer to|as defined|terminology)\b': 2,
            r'^\s*\*\s*\w+:': 2,  # Definition lists
            r'\b\w+\s*:\s*[A-Z]': 1  # Term: Definition format
        }
        
        # Narrative indicators with weights
        narrative_patterns = {
            r'\b(?:story|narrative|example|case study|scenario|situation)\b': 2,
            r'\b(?:once upon|imagine|consider|suppose|let\'s say)\b': 3,
            r'\b(?:character|plot|setting|conflict|resolution)\b': 2,
            r'\b(?:for example|for instance|such as)\b': 1
        }
        
        # Conceptual indicators with weights
        conceptual_patterns = {
            r'\b(?:concept|principle|theory|idea|notion|understanding)\b': 2,
            r'\b(?:explain|understand|comprehend|grasp|realize)\b': 1,
            r'\b(?:fundamental|basic|essential|core|key)\b': 1,
            r'\b(?:relationship|connection|association|correlation)\b': 2
        }
        
        # Calculate scores for each type
        pattern_groups = [
            (ContentType.ACADEMIC, academic_patterns),
            (ContentType.TUTORIAL, tutorial_patterns),
            (ContentType.TECHNICAL, technical_patterns),
            (ContentType.REFERENCE, reference_patterns),
            (ContentType.NARRATIVE, narrative_patterns),
            (ContentType.CONCEPTUAL, conceptual_patterns)
        ]
        
        for content_type, patterns in pattern_groups:
            for pattern, weight in patterns.items():
                matches = len(re.findall(pattern, content_lower, re.MULTILINE))
                type_scores[content_type] += matches * weight
        
        # Normalize scores by content length
        for content_type in type_scores:
            type_scores[content_type] = type_scores[content_type] / max(word_count / 100, 1)
        
        # Return type with highest score, or conceptual as default
        best_type = max(type_scores.items(), key=lambda x: x[1])
        return best_type[0] if best_type[1] > 0.1 else ContentType.CONCEPTUAL
    
    def _extract_main_topics_enhanced(self, content: str) -> List[str]:
        """Enhanced main topic extraction with better NLP techniques"""
        topics = []
        
        # Extract from various sources with confidence scoring
        topic_sources = []
        
        # 1. Extract from headings (high confidence)
        heading_topics = []
        for pattern in self.heading_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                clean_topic = self._clean_topic_text(match)
                if clean_topic and len(clean_topic) > 2:
                    heading_topics.append((clean_topic, 0.9))  # High confidence
        
        # 2. Extract from first sentences of paragraphs (medium confidence)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        paragraph_topics = []
        for paragraph in paragraphs:
            first_sentence = paragraph.split('.')[0].strip()
            if len(first_sentence) > 10 and len(first_sentence) < 100:
                # Check if it looks like a topic sentence
                if self._is_topic_sentence(first_sentence):
                    clean_topic = self._extract_topic_from_sentence(first_sentence)
                    if clean_topic:
                        paragraph_topics.append((clean_topic, 0.6))  # Medium confidence
        
        # 3. Extract from topic indicators (medium confidence)
        indicator_topics = []
        for pattern in self.topic_indicators:
            matches = re.findall(f'{pattern}[:\\s]+([^.!?]+)', content, re.IGNORECASE)
            for match in matches:
                clean_topic = self._clean_topic_text(match)
                if clean_topic and len(clean_topic) > 5:
                    indicator_topics.append((clean_topic, 0.7))
        
        # 4. Extract using noun phrase patterns (lower confidence)
        noun_phrase_topics = []
        noun_patterns = [
            r'\b(?:the|a|an)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "the Concept"
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|are|involves|includes)\b',  # "Topic is"
            r'\b(?:understanding|learning|studying)\s+([a-z][a-z\s]+)\b',  # "understanding topic"
        ]
        
        for pattern in noun_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                clean_topic = self._clean_topic_text(match)
                if clean_topic and len(clean_topic) > 3:
                    noun_phrase_topics.append((clean_topic, 0.4))  # Lower confidence
        
        # Combine all topics with their confidence scores
        all_topics = heading_topics + paragraph_topics + indicator_topics + noun_phrase_topics
        
        # Remove duplicates and rank by confidence and frequency
        topic_scores = {}
        for topic, confidence in all_topics:
            topic_lower = topic.lower()
            if topic_lower not in topic_scores:
                topic_scores[topic_lower] = {'text': topic, 'score': 0, 'count': 0}
            topic_scores[topic_lower]['score'] += confidence
            topic_scores[topic_lower]['count'] += 1
        
        # Calculate final scores (confidence * frequency)
        for topic_data in topic_scores.values():
            topic_data['final_score'] = topic_data['score'] * topic_data['count']
        
        # Sort by final score and return top topics
        sorted_topics = sorted(topic_scores.values(), key=lambda x: x['final_score'], reverse=True)
        
        return [topic['text'] for topic in sorted_topics[:10]]
    
    def _clean_topic_text(self, text: str) -> str:
        """Clean and normalize topic text"""
        if not text:
            return ""
        
        # Remove extra whitespace and punctuation
        text = re.sub(r'[^\w\s-]', '', text).strip()
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common stop words from beginning/end
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = text.split()
        
        # Remove stop words from beginning
        while words and words[0].lower() in stop_words:
            words.pop(0)
        
        # Remove stop words from end
        while words and words[-1].lower() in stop_words:
            words.pop()
        
        return ' '.join(words)
    
    def _is_topic_sentence(self, sentence: str) -> bool:
        """Determine if a sentence is likely a topic sentence"""
        sentence_lower = sentence.lower()
        
        # Topic sentence indicators
        topic_indicators = [
            'this section', 'this chapter', 'we will', 'let us', 'consider',
            'the main', 'the primary', 'the key', 'important', 'essential',
            'fundamental', 'basic', 'core', 'central'
        ]
        
        return any(indicator in sentence_lower for indicator in topic_indicators)
    
    def _extract_topic_from_sentence(self, sentence: str) -> str:
        """Extract the main topic from a topic sentence"""
        # Simple extraction - look for noun phrases after common patterns
        patterns = [
            r'(?:this section|this chapter|we will|let us)\s+(?:discuss|explore|examine|cover|learn about)\s+([^.!?]+)',
            r'(?:the main|the primary|the key)\s+([^.!?]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|are)\s+(?:important|essential|fundamental)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return self._clean_topic_text(match.group(1))
        
        # Fallback: return cleaned first part of sentence
        words = sentence.split()[:6]  # First 6 words
        return self._clean_topic_text(' '.join(words))
    
    def _extract_key_concepts_enhanced(self, content: str) -> List[str]:
        """Enhanced key concept extraction with better pattern matching and scoring"""
        concepts = []
        
        # 1. Extract from definition patterns (high confidence)
        definition_patterns = [
            (r'(\w+(?:\s+\w+)*)\s+(?:is|are|means|refers to|defined as)\s+([^.!?]+)', 0.9),
            (r'(?:define|definition of)\s+(\w+(?:\s+\w+)*)', 0.8),
            (r'(\w+(?:\s+\w+)*)\s*:\s*[A-Z][^.!?]+', 0.8),  # Term: Definition format
            (r'(?:the concept of|the principle of|the theory of)\s+(\w+(?:\s+\w+)*)', 0.9),
        ]
        
        for pattern, confidence in definition_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    concept = match[0]
                else:
                    concept = match
                clean_concept = self._clean_concept_text(concept)
                if clean_concept:
                    concepts.append((clean_concept, confidence))
        
        # 2. Extract from emphasis patterns (medium confidence)
        emphasis_patterns = [
            (r'\*\*([^*]+)\*\*', 0.7),  # Bold text (markdown)
            (r'\*([^*]+)\*', 0.6),      # Italic text (markdown)
            (r'_([^_]+)_', 0.6),        # Underlined text
            (r'`([^`]+)`', 0.5),        # Code/technical terms
            (r'"([^"]+)"', 0.4),        # Quoted terms
        ]
        
        for pattern, confidence in emphasis_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                clean_concept = self._clean_concept_text(match)
                if clean_concept and self._is_valid_concept(clean_concept):
                    concepts.append((clean_concept, confidence))
        
        # 3. Extract proper nouns and technical terms (medium confidence)
        proper_noun_patterns = [
            (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', 0.5),  # Proper nouns
            (r'\b([A-Z]{2,})\b', 0.6),  # Acronyms
            (r'\b(\w+(?:tion|sion|ment|ness|ity|ism))\b', 0.4),  # Abstract suffixes
        ]
        
        for pattern, confidence in proper_noun_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                clean_concept = self._clean_concept_text(match)
                if clean_concept and self._is_valid_concept(clean_concept):
                    concepts.append((clean_concept, confidence))
        
        # 4. Extract from contextual patterns (lower confidence)
        contextual_patterns = [
            (r'(?:important|key|essential|fundamental|critical)\s+(\w+(?:\s+\w+)*)', 0.6),
            (r'(?:understand|learn|study|master)\s+(\w+(?:\s+\w+)*)', 0.4),
            (r'(?:concept|principle|theory|idea)\s+of\s+(\w+(?:\s+\w+)*)', 0.7),
        ]
        
        for pattern, confidence in contextual_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                clean_concept = self._clean_concept_text(match)
                if clean_concept and self._is_valid_concept(clean_concept):
                    concepts.append((clean_concept, confidence))
        
        # Score and rank concepts
        concept_scores = {}
        for concept, confidence in concepts:
            concept_lower = concept.lower()
            if concept_lower not in concept_scores:
                concept_scores[concept_lower] = {
                    'text': concept,
                    'score': 0,
                    'count': 0,
                    'max_confidence': 0
                }
            
            concept_scores[concept_lower]['score'] += confidence
            concept_scores[concept_lower]['count'] += 1
            concept_scores[concept_lower]['max_confidence'] = max(
                concept_scores[concept_lower]['max_confidence'], confidence
            )
        
        # Calculate final scores (weighted by frequency and confidence)
        for concept_data in concept_scores.values():
            frequency_weight = min(concept_data['count'] / 3.0, 1.0)  # Cap frequency impact
            concept_data['final_score'] = (
                concept_data['max_confidence'] * 0.7 + 
                frequency_weight * 0.3
            )
        
        # Filter and sort concepts
        valid_concepts = [
            data for data in concept_scores.values()
            if data['final_score'] > 0.3 and self._is_educational_concept(data['text'])
        ]
        
        sorted_concepts = sorted(valid_concepts, key=lambda x: x['final_score'], reverse=True)
        
        return [concept['text'] for concept in sorted_concepts[:15]]
    
    def _clean_concept_text(self, text: str) -> str:
        """Clean and normalize concept text"""
        if not text:
            return ""
        
        # Remove extra whitespace and some punctuation
        text = re.sub(r'[^\w\s-]', '', text).strip()
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common articles and prepositions
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = text.split()
        
        # Remove stop words from beginning
        while words and words[0].lower() in stop_words:
            words.pop(0)
        
        return ' '.join(words)
    
    def _is_valid_concept(self, concept: str) -> bool:
        """Check if a concept is valid for educational content"""
        if not concept or len(concept) < 2 or len(concept) > 50:
            return False
        
        # Skip very common words
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'this', 'that', 'these', 'those', 'here', 'there', 'when', 'where', 'how', 'why',
            'what', 'who', 'which', 'can', 'will', 'would', 'should', 'could', 'may', 'might'
        }
        
        if concept.lower() in common_words:
            return False
        
        # Skip single letters or numbers
        if len(concept) == 1 or concept.isdigit():
            return False
        
        return True
    
    def _is_educational_concept(self, concept: str) -> bool:
        """Check if a concept is relevant for educational content"""
        concept_lower = concept.lower()
        
        # Skip very generic terms
        generic_terms = {
            'content', 'information', 'data', 'text', 'section', 'chapter',
            'example', 'case', 'study', 'research', 'analysis', 'method'
        }
        
        if concept_lower in generic_terms:
            return False
        
        # Prefer concepts that look educational
        educational_indicators = [
            r'\b\w+(?:tion|sion|ment|ness|ity|ism)\b',  # Abstract concepts
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',      # Proper nouns/terms
            r'\b\w{6,}\b',  # Longer words tend to be more specific
        ]
        
        return any(re.search(pattern, concept) for pattern in educational_indicators)
    
    def _analyze_difficulty_level_enhanced(self, content: str) -> str:
        """Enhanced difficulty level analysis with multiple factors"""
        score = 0
        
        # 1. Sentence complexity analysis
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            
            if avg_sentence_length > 30:
                score += 3
            elif avg_sentence_length > 20:
                score += 2
            elif avg_sentence_length > 15:
                score += 1
        
        # 2. Vocabulary complexity
        words = content.split()
        if words:
            # Long words (complexity indicator)
            long_words = [w for w in words if len(w) > 8]
            long_word_ratio = len(long_words) / len(words)
            
            if long_word_ratio > 0.15:
                score += 3
            elif long_word_ratio > 0.10:
                score += 2
            elif long_word_ratio > 0.05:
                score += 1
            
            # Syllable complexity (approximation)
            complex_syllable_words = [w for w in words if self._estimate_syllables(w) > 3]
            syllable_ratio = len(complex_syllable_words) / len(words)
            
            if syllable_ratio > 0.20:
                score += 2
            elif syllable_ratio > 0.10:
                score += 1
        
        # 3. Technical terminology density
        technical_patterns = [
            r'\b\w+(?:tion|sion|ment|ness|ity|ism|ology|graphy)\b',  # Abstract/technical suffixes
            r'\b(?:algorithm|methodology|implementation|specification|architecture)\b',
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\w+[-_]\w+\b',  # Hyphenated/compound technical terms
        ]
        
        technical_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                            for pattern in technical_patterns)
        technical_density = technical_count / max(len(words), 1)
        
        if technical_density > 0.15:
            score += 3
        elif technical_density > 0.08:
            score += 2
        elif technical_density > 0.04:
            score += 1
        
        # 4. Conceptual complexity indicators
        complex_concepts = [
            'abstract', 'theoretical', 'conceptual', 'philosophical', 'analytical',
            'synthesis', 'evaluation', 'interpretation', 'inference', 'hypothesis'
        ]
        
        concept_count = sum(1 for concept in complex_concepts if concept in content.lower())
        if concept_count > 5:
            score += 2
        elif concept_count > 2:
            score += 1
        
        # 5. Mathematical/scientific complexity
        math_science_patterns = [
            r'\b(?:equation|formula|theorem|proof|hypothesis|variable)\b',
            r'\b(?:statistical|empirical|quantitative|qualitative|experimental)\b',
            r'[∑∏∫∂∇αβγδεζηθλμπρσφψω]',  # Mathematical symbols
            r'\$[^$]+\$',  # LaTeX math
        ]
        
        math_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                        for pattern in math_science_patterns)
        if math_count > 10:
            score += 3
        elif math_count > 5:
            score += 2
        elif math_count > 2:
            score += 1
        
        # 6. Prerequisite knowledge indicators
        prerequisite_patterns = [
            r'(?:assuming|given that|prerequisite|requires knowledge of)',
            r'(?:as we learned|as discussed|previously mentioned)',
            r'(?:advanced|intermediate|complex|sophisticated)'
        ]
        
        prereq_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                          for pattern in prerequisite_patterns)
        if prereq_count > 3:
            score += 2
        elif prereq_count > 1:
            score += 1
        
        # Determine difficulty level based on total score
        if score >= 10:
            return "expert"
        elif score >= 7:
            return "advanced"
        elif score >= 4:
            return "intermediate"
        elif score >= 2:
            return "beginner"
        else:
            return "introductory"
    
    def _estimate_syllables(self, word: str) -> int:
        """Estimate syllable count for a word (simple heuristic)"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _assess_structure_quality(self, content: str) -> float:
        """Assess the structural quality of content (0.0 to 1.0)"""
        score = 0.0
        
        # Check for headings
        heading_count = sum(len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)) 
                          for pattern in self.heading_patterns)
        if heading_count > 0:
            score += 0.3
        
        # Check for paragraphs
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 2:
            score += 0.2
        
        # Check for lists or enumeration
        list_patterns = [r'^\s*[-*+]\s', r'^\s*\d+\.\s', r'^\s*[a-zA-Z]\.\s']
        has_lists = any(re.search(pattern, content, re.MULTILINE) for pattern in list_patterns)
        if has_lists:
            score += 0.2
        
        # Check for transitions
        transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently', 'additionally']
        transition_count = sum(1 for word in transition_words if word in content.lower())
        if transition_count > 2:
            score += 0.2
        
        # Check for examples
        example_indicators = ['example', 'for instance', 'such as', 'e.g.', 'i.e.']
        has_examples = any(indicator in content.lower() for indicator in example_indicators)
        if has_examples:
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_coherence(self, content: str) -> float:
        """Assess content coherence (0.0 to 1.0)"""
        # Simple coherence assessment based on text features
        score = 0.5  # Base score
        
        # Check for logical flow indicators
        flow_indicators = [
            'first', 'second', 'third', 'finally', 'next', 'then', 'after',
            'before', 'during', 'meanwhile', 'subsequently', 'previously'
        ]
        
        flow_count = sum(1 for indicator in flow_indicators if indicator in content.lower())
        score += min(0.3, flow_count * 0.05)
        
        # Check for coherence markers
        coherence_markers = [
            'as a result', 'in conclusion', 'to summarize', 'in other words',
            'on the other hand', 'in contrast', 'similarly', 'likewise'
        ]
        
        coherence_count = sum(1 for marker in coherence_markers if marker in content.lower())
        score += min(0.2, coherence_count * 0.1)
        
        return min(1.0, score)
    
    def _create_initial_sections(self, content: str) -> List[ContentSection]:
        """Create initial content sections based on structure analysis"""
        sections = []
        
        # Split content into potential sections
        # This is a simplified approach - in practice, this would be more sophisticated
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            return sections
        
        # Create sections based on content length and structure
        current_section_content = []
        section_count = 0
        
        for i, paragraph in enumerate(paragraphs):
            current_section_content.append(paragraph)
            
            # Determine if this should be a section break
            should_break = (
                len(current_section_content) >= 3 or  # Minimum content
                i == len(paragraphs) - 1 or  # Last paragraph
                self._is_section_boundary(paragraph, paragraphs[i+1] if i+1 < len(paragraphs) else "")
            )
            
            if should_break:
                section_content = '\n\n'.join(current_section_content)
                section_title = self._generate_section_title(section_content, section_count)
                section_type = self._determine_section_type(section_content, section_count, len(paragraphs))
                
                section = ContentSection(
                    title=section_title,
                    content=section_content,
                    section_type=section_type,
                    level=1,
                    order=section_count,
                    key_concepts=self._extract_key_concepts(section_content)[:5],
                    estimated_duration=max(1, len(section_content.split()) // 150),
                    prerequisites=[],
                    learning_outcomes=[],
                    subsections=[]
                )
                
                sections.append(section)
                current_section_content = []
                section_count += 1
        
        return sections
    
    def _is_section_boundary(self, current_paragraph: str, next_paragraph: str) -> bool:
        """Determine if there should be a section boundary"""
        # Check for heading patterns in next paragraph
        for pattern in self.heading_patterns:
            if re.match(pattern, next_paragraph, re.IGNORECASE):
                return True
        
        # Check for topic transition indicators
        transition_indicators = [
            'now let', 'next', 'moving on', 'another', 'in addition',
            'furthermore', 'however', 'on the other hand'
        ]
        
        next_lower = next_paragraph.lower()
        return any(next_lower.startswith(indicator) for indicator in transition_indicators)
    
    def _generate_section_title(self, content: str, section_index: int) -> str:
        """Generate an appropriate title for a content section"""
        # Try to extract title from first sentence or heading
        first_sentence = content.split('.')[0].strip()
        
        # Check if first sentence looks like a title
        if len(first_sentence) < 100 and ':' not in first_sentence:
            # Clean up potential title
            title = re.sub(r'^[^\w]*', '', first_sentence)
            title = re.sub(r'[^\w\s-]$', '', title)
            if len(title) > 5 and len(title) < 80:
                return title
        
        # Generate generic title based on position
        if section_index == 0:
            return "Introduction"
        elif section_index == 1:
            return "Main Concepts"
        else:
            return f"Section {section_index + 1}"
    
    def _determine_section_type(self, content: str, section_index: int, total_sections: int) -> SectionType:
        """Determine the type of a content section"""
        content_lower = content.lower()
        
        # Introduction indicators
        intro_indicators = ['introduction', 'overview', 'background', 'context', 'begin']
        if section_index == 0 or any(indicator in content_lower for indicator in intro_indicators):
            return SectionType.INTRODUCTION
        
        # Conclusion indicators
        conclusion_indicators = ['conclusion', 'summary', 'in summary', 'to conclude', 'finally']
        if section_index == total_sections - 1 or any(indicator in content_lower for indicator in conclusion_indicators):
            return SectionType.CONCLUSION
        
        # Example indicators
        example_indicators = ['example', 'for instance', 'case study', 'illustration']
        if any(indicator in content_lower for indicator in example_indicators):
            return SectionType.EXAMPLE
        
        # Procedure indicators
        procedure_indicators = ['step', 'procedure', 'method', 'process', 'algorithm']
        if any(indicator in content_lower for indicator in procedure_indicators):
            return SectionType.PROCEDURE
        
        # Default to main concept
        return SectionType.MAIN_CONCEPT
    
    def _analyze_content_flow(self, content: str, main_topics: List[str]) -> List[str]:
        """Analyze the logical flow of content"""
        # Simple flow analysis based on topic order and transitions
        flow = []
        
        # Add introduction if content suggests it
        intro_indicators = ['introduction', 'overview', 'background']
        if any(indicator in content.lower() for indicator in intro_indicators):
            flow.append("Introduction")
        
        # Add main topics in order of appearance
        for topic in main_topics[:5]:  # Limit to 5 main topics
            flow.append(topic)
        
        # Add conclusion if content suggests it
        conclusion_indicators = ['conclusion', 'summary', 'in conclusion']
        if any(indicator in content.lower() for indicator in conclusion_indicators):
            flow.append("Conclusion")
        
        return flow if flow else ["Introduction", "Main Content", "Conclusion"]
    
    def _parse_agent_response(self, response: str) -> Dict[str, Any]:
        """Parse the agent's structured response"""
        # This is a simplified parser - in practice, this would be more sophisticated
        # and might use structured output formats like JSON
        
        return {
            "raw_response": response,
            "sections_identified": True,
            "structure_enhanced": True,
            "parsing_method": "text_analysis"
        }
    
    def _enhance_content_structure(self, structured_content: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance the content structure with additional analysis"""
        # Add enhancement metadata
        structured_content["enhancement_applied"] = True
        structured_content["enhancement_timestamp"] = datetime.now().isoformat()
        structured_content["enhancement_version"] = "2.0"
        
        return structured_content
    
    def _validate_content_structure(self, structure: Dict[str, Any]) -> None:
        """Validate the enhanced content structure"""
        if not structure:
            raise AgentValidationError(
                "Content structure is empty",
                agent_type=self.agent_type
            )
        
        if "raw_response" not in structure:
            raise AgentValidationError(
                "Content structure missing raw response",
                agent_type=self.agent_type
            )
        
        logger.info("Content structure validation passed")
    def _assess_structure_quality_enhanced(self, content: str) -> float:
        """Enhanced assessment of structural quality (0.0 to 1.0)"""
        score = 0.0
        
        # 1. Heading structure analysis (0.3 max)
        heading_count = sum(len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)) 
                          for pattern in self.heading_patterns)
        
        if heading_count > 0:
            # Check for hierarchical structure
            markdown_headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
            if markdown_headings:
                levels = [len(match[0]) for match in markdown_headings]
                if len(set(levels)) > 1:  # Multiple heading levels
                    score += 0.3
                else:
                    score += 0.2
            else:
                score += 0.15
        
        # 2. Paragraph structure (0.2 max)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            if 50 <= avg_paragraph_length <= 150:  # Optimal paragraph length
                score += 0.2
            elif 30 <= avg_paragraph_length <= 200:
                score += 0.15
            else:
                score += 0.1
        
        # 3. List and enumeration structure (0.15 max)
        list_patterns = [
            r'^\s*[-*+]\s+',  # Bullet lists
            r'^\s*\d+\.\s+',  # Numbered lists
            r'^\s*[a-zA-Z]\.\s+',  # Lettered lists
        ]
        
        list_count = sum(len(re.findall(pattern, content, re.MULTILINE)) 
                        for pattern in list_patterns)
        if list_count > 0:
            score += min(0.15, list_count * 0.03)
        
        # 4. Transition and flow indicators (0.15 max)
        transition_patterns = [
            r'\b(?:however|therefore|furthermore|moreover|consequently|additionally)\b',
            r'\b(?:first|second|third|finally|next|then|after|before)\b',
            r'\b(?:in conclusion|to summarize|in summary|as a result)\b',
            r'\b(?:for example|for instance|such as|namely)\b',
        ]
        
        transition_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                             for pattern in transition_patterns)
        if transition_count > 0:
            score += min(0.15, transition_count * 0.02)
        
        # 5. Content organization indicators (0.1 max)
        organization_patterns = [
            r'\b(?:introduction|overview|background|conclusion|summary)\b',
            r'\b(?:definition|example|explanation|analysis|discussion)\b',
        ]
        
        org_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                       for pattern in organization_patterns)
        if org_count > 0:
            score += min(0.1, org_count * 0.02)
        
        # 6. Visual structure elements (0.1 max)
        visual_elements = [
            r'```[^`]*```',  # Code blocks
            r'\|[^|]*\|',    # Tables
            r'!\[[^\]]*\]\([^)]*\)',  # Images
            r'\*\*[^*]+\*\*',  # Bold text
            r'\*[^*]+\*',      # Italic text
        ]
        
        visual_count = sum(len(re.findall(pattern, content, re.MULTILINE)) 
                          for pattern in visual_elements)
        if visual_count > 0:
            score += min(0.1, visual_count * 0.02)
        
        return min(1.0, score)
    
    def _assess_coherence_enhanced(self, content: str) -> float:
        """Enhanced coherence assessment (0.0 to 1.0)"""
        score = 0.3  # Base score
        
        # 1. Logical flow indicators (0.25 max)
        flow_indicators = [
            r'\b(?:first|firstly|initially|to begin)\b',
            r'\b(?:second|secondly|next|then|after|following)\b',
            r'\b(?:third|thirdly|furthermore|moreover|additionally)\b',
            r'\b(?:finally|lastly|in conclusion|to conclude)\b',
        ]
        
        flow_matches = []
        for pattern in flow_indicators:
            matches = re.findall(pattern, content, re.IGNORECASE)
            flow_matches.extend(matches)
        
        if len(flow_matches) >= 3:
            score += 0.25
        elif len(flow_matches) >= 2:
            score += 0.15
        elif len(flow_matches) >= 1:
            score += 0.1
        
        # 2. Coherence and cohesion markers (0.2 max)
        coherence_markers = [
            r'\b(?:as a result|consequently|therefore|thus|hence)\b',
            r'\b(?:however|nevertheless|nonetheless|on the other hand)\b',
            r'\b(?:similarly|likewise|in the same way|correspondingly)\b',
            r'\b(?:in contrast|conversely|on the contrary|whereas)\b',
            r'\b(?:in other words|that is|namely|specifically)\b',
        ]
        
        coherence_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                            for pattern in coherence_markers)
        score += min(0.2, coherence_count * 0.03)
        
        # 3. Reference and connection patterns (0.15 max)
        reference_patterns = [
            r'\b(?:as mentioned|as discussed|as shown|as seen)\b',
            r'\b(?:this|these|that|those)\s+(?:concept|idea|principle|method)\b',
            r'\b(?:the above|the following|the previous|the next)\b',
            r'\b(?:refer to|see also|compare with|in relation to)\b',
        ]
        
        reference_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                            for pattern in reference_patterns)
        score += min(0.15, reference_count * 0.03)
        
        # 4. Topic consistency (0.1 max)
        # Check if key topics are mentioned throughout the content
        main_topics = self._extract_main_topics_enhanced(content)[:3]
        if main_topics:
            topic_distribution = []
            content_parts = [content[i:i+len(content)//3] for i in range(0, len(content), len(content)//3)]
            
            for topic in main_topics:
                parts_with_topic = sum(1 for part in content_parts if topic.lower() in part.lower())
                topic_distribution.append(parts_with_topic / len(content_parts))
            
            avg_distribution = sum(topic_distribution) / len(topic_distribution)
            score += min(0.1, avg_distribution * 0.2)
        
        return min(1.0, score)
    
    def _create_enhanced_sections(self, content: str) -> List[ContentSection]:
        """Create enhanced content sections with better organization"""
        sections = []
        
        # First, try advanced hierarchical section creation
        try:
            hierarchical_sections = self._create_advanced_sections_with_hierarchy(content)
            if hierarchical_sections and len(hierarchical_sections) > 1:
                logger.info(f"Created {len(hierarchical_sections)} sections using hierarchical analysis")
                return hierarchical_sections
        except Exception as e:
            logger.warning(f"Hierarchical section creation failed: {e}, falling back to heading-based")
        
        # Second, try to identify sections using headings
        heading_sections = self._extract_sections_from_headings(content)
        if heading_sections:
            logger.info(f"Created {len(heading_sections)} sections using heading analysis")
            return heading_sections
        
        # Third, use paragraph-based sectioning with advanced grouping
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if not paragraphs:
            return sections
        
        # Analyze paragraph relationships and group them using advanced techniques
        paragraph_groups = self._group_related_paragraphs_advanced(paragraphs)
        
        for i, group in enumerate(paragraph_groups):
            section_content = '\n\n'.join(group)
            section_title = self._generate_enhanced_section_title(section_content, i, len(paragraph_groups))
            section_type = self._determine_enhanced_section_type(section_content, i, len(paragraph_groups))
            
            # Extract section-specific information using enhanced methods
            key_concepts = self._extract_key_concepts_enhanced(section_content)[:5]
            learning_outcomes = self._generate_learning_outcomes(section_content, key_concepts)
            prerequisites = self._identify_prerequisites(section_content)
            
            section = ContentSection(
                title=section_title,
                content=section_content,
                section_type=section_type,
                level=1,
                order=i,
                key_concepts=key_concepts,
                estimated_duration=max(1, len(section_content.split()) // 150),
                prerequisites=prerequisites,
                learning_outcomes=learning_outcomes,
                subsections=[]
            )
            
            sections.append(section)
        
        logger.info(f"Created {len(sections)} sections using paragraph-based analysis")
        return sections
    
    def _extract_sections_from_headings(self, content: str) -> List[ContentSection]:
        """Extract sections based on heading structure"""
        sections = []
        
        # Find all headings with their positions
        headings = []
        for pattern in self.heading_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                heading_text = match.group(1) if match.groups() else match.group(0)
                headings.append({
                    'text': heading_text.strip(),
                    'start': match.start(),
                    'end': match.end(),
                    'level': self._determine_heading_level(match.group(0))
                })
        
        if not headings:
            return []
        
        # Sort headings by position
        headings.sort(key=lambda x: x['start'])
        
        # Create sections from headings
        for i, heading in enumerate(headings):
            # Determine section content
            content_start = heading['end']
            content_end = headings[i + 1]['start'] if i + 1 < len(headings) else len(content)
            section_content = content[content_start:content_end].strip()
            
            if section_content:  # Only create section if there's content
                section_type = self._determine_section_type_from_title(heading['text'])
                key_concepts = self._extract_key_concepts_enhanced(section_content)[:5]
                
                section = ContentSection(
                    title=heading['text'],
                    content=section_content,
                    section_type=section_type,
                    level=heading['level'],
                    order=i,
                    key_concepts=key_concepts,
                    estimated_duration=max(1, len(section_content.split()) // 150),
                    prerequisites=[],
                    learning_outcomes=self._generate_learning_outcomes(section_content, key_concepts),
                    subsections=[]
                )
                
                sections.append(section)
        
        return sections
    
    def _determine_heading_level(self, heading_text: str) -> int:
        """Determine the hierarchical level of a heading"""
        # Check for markdown-style headings
        if heading_text.startswith('#'):
            return len(heading_text) - len(heading_text.lstrip('#'))
        
        # Default to level 1 for other heading types
        return 1
    
    def _determine_section_type_from_title(self, title: str) -> SectionType:
        """Determine section type from title text"""
        title_lower = title.lower()
        
        # Map title patterns to section types
        type_patterns = {
            SectionType.INTRODUCTION: ['introduction', 'intro', 'overview', 'background', 'getting started'],
            SectionType.CONCLUSION: ['conclusion', 'summary', 'wrap up', 'final', 'ending'],
            SectionType.EXAMPLE: ['example', 'case study', 'illustration', 'demo', 'sample'],
            SectionType.PROCEDURE: ['steps', 'procedure', 'method', 'process', 'how to', 'tutorial'],
            SectionType.EXPLANATION: ['explanation', 'theory', 'concept', 'understanding', 'why'],
            SectionType.REFERENCE: ['reference', 'appendix', 'glossary', 'resources', 'further reading'],
        }
        
        for section_type, patterns in type_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                return section_type
        
        return SectionType.MAIN_CONCEPT
    
    def _group_related_paragraphs(self, paragraphs: List[str]) -> List[List[str]]:
        """Group related paragraphs into logical sections"""
        if len(paragraphs) <= 3:
            return [paragraphs]
        
        groups = []
        current_group = []
        
        for i, paragraph in enumerate(paragraphs):
            current_group.append(paragraph)
            
            # Determine if this should end a group
            should_end_group = (
                len(current_group) >= 3 or  # Minimum group size
                i == len(paragraphs) - 1 or  # Last paragraph
                self._is_topic_transition(paragraph, paragraphs[i + 1] if i + 1 < len(paragraphs) else "")
            )
            
            if should_end_group:
                groups.append(current_group)
                current_group = []
        
        # Handle any remaining paragraphs
        if current_group:
            if groups:
                groups[-1].extend(current_group)
            else:
                groups.append(current_group)
        
        return groups
    
    def _is_topic_transition(self, current_paragraph: str, next_paragraph: str) -> bool:
        """Determine if there's a topic transition between paragraphs"""
        # Check for explicit transition indicators
        transition_indicators = [
            'now let', 'next', 'moving on', 'another', 'in addition',
            'furthermore', 'however', 'on the other hand', 'meanwhile',
            'in contrast', 'similarly', 'alternatively'
        ]
        
        next_lower = next_paragraph.lower()
        if any(next_lower.startswith(indicator) for indicator in transition_indicators):
            return True
        
        # Check for topic shift based on key terms
        current_topics = set(self._extract_key_concepts_enhanced(current_paragraph)[:3])
        next_topics = set(self._extract_key_concepts_enhanced(next_paragraph)[:3])
        
        # If there's little overlap in key concepts, it might be a transition
        if current_topics and next_topics:
            overlap = len(current_topics.intersection(next_topics))
            return overlap == 0
        
        return False
    
    def _generate_enhanced_section_title(self, content: str, section_index: int, total_sections: int) -> str:
        """Generate an enhanced title for a content section"""
        # Try to extract a meaningful title from the content
        first_sentence = content.split('.')[0].strip()
        
        # Check if first sentence could be a title
        if len(first_sentence) < 100 and not first_sentence.endswith('?'):
            # Look for title-like patterns
            title_patterns = [
                r'^([A-Z][^.!?]*?)(?:\s+is\s+|\s+are\s+|\s+involves\s+)',  # "Topic is..."
                r'^(Understanding|Learning|Exploring|Analyzing)\s+([^.!?]+)',  # "Understanding Topic"
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:',  # "Topic:"
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, first_sentence)
                if match:
                    title = match.group(1).strip()
                    if 5 < len(title) < 80:
                        return title
        
        # Extract key concepts and create title
        key_concepts = self._extract_key_concepts_enhanced(content)[:2]
        if key_concepts:
            if len(key_concepts) == 1:
                return key_concepts[0]
            else:
                return f"{key_concepts[0]} and {key_concepts[1]}"
        
        # Generate positional title
        if section_index == 0:
            return "Introduction"
        elif section_index == total_sections - 1:
            return "Conclusion"
        else:
            return f"Section {section_index + 1}"
    
    def _determine_enhanced_section_type(self, content: str, section_index: int, total_sections: int) -> SectionType:
        """Enhanced section type determination"""
        content_lower = content.lower()
        
        # Weighted scoring for different section types
        type_scores = {
            SectionType.INTRODUCTION: 0,
            SectionType.MAIN_CONCEPT: 0,
            SectionType.EXAMPLE: 0,
            SectionType.EXPLANATION: 0,
            SectionType.PROCEDURE: 0,
            SectionType.CONCLUSION: 0,
        }
        
        # Position-based scoring
        if section_index == 0:
            type_scores[SectionType.INTRODUCTION] += 3
        elif section_index == total_sections - 1:
            type_scores[SectionType.CONCLUSION] += 3
        
        # Content-based scoring
        content_patterns = {
            SectionType.INTRODUCTION: [
                (r'\b(?:introduction|overview|background|context|begin)\b', 2),
                (r'\b(?:this (?:section|chapter|article) will|we will (?:explore|discuss|examine))\b', 3),
            ],
            SectionType.EXAMPLE: [
                (r'\b(?:example|for instance|case study|illustration|consider)\b', 2),
                (r'\b(?:imagine|suppose|let\'s say|scenario)\b', 2),
            ],
            SectionType.PROCEDURE: [
                (r'\b(?:step|procedure|method|process|algorithm|instructions)\b', 2),
                (r'^\s*\d+\.\s', 3),  # Numbered steps
                (r'\b(?:first|second|third|next|then|finally)\b', 1),
            ],
            SectionType.EXPLANATION: [
                (r'\b(?:explanation|theory|concept|principle|why|how|because)\b', 2),
                (r'\b(?:understand|comprehend|realize|recognize)\b', 1),
            ],
            SectionType.CONCLUSION: [
                (r'\b(?:conclusion|summary|in summary|to conclude|finally)\b', 3),
                (r'\b(?:in conclusion|to summarize|wrap up|overall)\b', 2),
            ],
        }
        
        # Calculate scores
        for section_type, patterns in content_patterns.items():
            for pattern, weight in patterns:
                matches = len(re.findall(pattern, content_lower, re.MULTILINE))
                type_scores[section_type] += matches * weight
        
        # Default scoring for main concept
        type_scores[SectionType.MAIN_CONCEPT] += 1
        
        # Return type with highest score
        best_type = max(type_scores.items(), key=lambda x: x[1])
        return best_type[0]
    
    def _generate_learning_outcomes(self, content: str, key_concepts: List[str]) -> List[str]:
        """Generate learning outcomes for a section"""
        outcomes = []
        
        # Generate outcomes based on content type and key concepts
        content_lower = content.lower()
        
        # Basic outcome templates
        if 'definition' in content_lower or 'concept' in content_lower:
            if key_concepts:
                outcomes.append(f"Define and explain {key_concepts[0]}")
        
        if 'example' in content_lower or 'illustration' in content_lower:
            outcomes.append("Identify examples and applications")
        
        if 'method' in content_lower or 'procedure' in content_lower:
            outcomes.append("Apply the described methods and procedures")
        
        if 'analysis' in content_lower or 'evaluation' in content_lower:
            outcomes.append("Analyze and evaluate the presented information")
        
        # Add concept-specific outcomes
        for concept in key_concepts[:2]:
            outcomes.append(f"Understand the significance of {concept}")
        
        return outcomes[:3]  # Limit to 3 outcomes
    
    def _identify_prerequisites(self, content: str) -> List[str]:
        """Identify prerequisites mentioned in the content"""
        prerequisites = []
        content_lower = content.lower()
        
        # Look for explicit prerequisite mentions
        prereq_patterns = [
            r'(?:prerequisite|requires?|assumes?|given that|provided that)\s+([^.!?]+)',
            r'(?:before|prior to|first)\s+(?:understanding|learning|knowing)\s+([^.!?]+)',
            r'(?:familiarity with|knowledge of|understanding of)\s+([^.!?]+)',
        ]
        
        for pattern in prereq_patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                clean_prereq = self._clean_concept_text(match)
                if clean_prereq and len(clean_prereq) > 3:
                    prerequisites.append(clean_prereq)
        
        return prerequisites[:3]  # Limit to 3 prerequisites
    
    def _analyze_content_flow_enhanced(self, content: str, main_topics: List[str], sections: List[ContentSection]) -> List[str]:
        """Enhanced analysis of logical content flow"""
        flow = []
        
        # If we have sections, use their titles for flow
        if sections:
            flow = [section.title for section in sections]
        else:
            # Fallback to topic-based flow
            # Add introduction if content suggests it
            intro_indicators = ['introduction', 'overview', 'background', 'begin']
            if any(indicator in content.lower() for indicator in intro_indicators):
                flow.append("Introduction")
            
            # Add main topics in logical order
            for topic in main_topics[:5]:
                flow.append(topic)
            
            # Add conclusion if content suggests it
            conclusion_indicators = ['conclusion', 'summary', 'in conclusion', 'finally']
            if any(indicator in content.lower() for indicator in conclusion_indicators):
                flow.append("Conclusion")
        
        return flow if flow else ["Introduction", "Main Content", "Conclusion"]
    
    def _calculate_organization_metrics(self, content: str, sections: List[ContentSection]) -> Dict[str, float]:
        """Calculate various organization quality metrics"""
        metrics = {}
        
        # Section balance (how evenly distributed are sections)
        if sections:
            section_lengths = [len(section.content.split()) for section in sections]
            if section_lengths:
                avg_length = sum(section_lengths) / len(section_lengths)
                variance = sum((length - avg_length) ** 2 for length in section_lengths) / len(section_lengths)
                balance_score = max(0, 1 - (variance / (avg_length ** 2)))
                metrics['section_balance'] = balance_score
        
        # Concept distribution (how well are key concepts distributed)
        key_concepts = self._extract_key_concepts_enhanced(content)[:5]
        if key_concepts and sections:
            concept_distribution = []
            for concept in key_concepts:
                sections_with_concept = sum(1 for section in sections 
                                          if concept.lower() in section.content.lower())
                distribution = sections_with_concept / len(sections)
                concept_distribution.append(distribution)
            
            metrics['concept_distribution'] = sum(concept_distribution) / len(concept_distribution)
        
        # Flow consistency (presence of transition elements)
        transition_count = len(re.findall(
            r'\b(?:however|therefore|furthermore|moreover|consequently|next|then)\b',
            content, re.IGNORECASE
        ))
        word_count = len(content.split())
        metrics['flow_consistency'] = min(1.0, transition_count / max(word_count / 100, 1))
        
        return metrics
    
    def _create_fallback_analysis(self, content: str) -> ContentAnalysis:
        """Create a fallback analysis when enhanced analysis fails"""
        word_count = len(content.split())
        
        return ContentAnalysis(
            content_type=ContentType.CONCEPTUAL,
            main_topics=["Main Content"],
            key_concepts=[],
            difficulty_level="intermediate",
            estimated_reading_time=max(1, word_count // 200),
            structure_quality=0.5,
            coherence_score=0.5,
            sections=[ContentSection(
                title="Main Content",
                content=content,
                section_type=SectionType.MAIN_CONCEPT,
                level=1,
                order=0,
                key_concepts=[],
                estimated_duration=max(1, word_count // 150),
                prerequisites=[],
                learning_outcomes=["Understand the main concepts"],
                subsections=[]
            )],
            content_flow=["Introduction", "Main Content", "Conclusion"]
        )
    def _identify_section_boundaries_advanced(self, content: str) -> List[Dict[str, Any]]:
        """
        Advanced section boundary identification using multiple techniques
        
        Returns:
            List of section boundaries with metadata
        """
        boundaries = []
        lines = content.split('\n')
        
        # 1. Heading-based boundaries (highest confidence)
        for i, line in enumerate(lines):
            for pattern in self.heading_patterns:
                match = re.match(pattern, line.strip(), re.IGNORECASE)
                if match:
                    heading_text = match.group(1) if match.groups() else line.strip()
                    boundaries.append({
                        'line_number': i,
                        'type': 'heading',
                        'text': heading_text,
                        'confidence': 0.9,
                        'level': self._determine_heading_level_advanced(line)
                    })
                    break
        
        # 2. Paragraph-based boundaries (medium confidence)
        paragraphs = content.split('\n\n')
        current_line = 0
        
        for para_idx, paragraph in enumerate(paragraphs):
            para_lines = paragraph.count('\n') + 1
            
            # Check if paragraph starts with topic indicators
            first_sentence = paragraph.strip().split('.')[0]
            if self._is_topic_boundary_sentence(first_sentence):
                boundaries.append({
                    'line_number': current_line,
                    'type': 'topic_boundary',
                    'text': first_sentence,
                    'confidence': 0.7,
                    'level': 1
                })
            
            current_line += para_lines + 1  # +1 for the empty line
        
        # 3. Transition-based boundaries (lower confidence)
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            for indicator in self.transition_indicators:
                if line_lower.startswith(indicator):
                    boundaries.append({
                        'line_number': i,
                        'type': 'transition',
                        'text': line.strip(),
                        'confidence': 0.5,
                        'level': 2
                    })
                    break
        
        # Sort boundaries by line number and remove duplicates
        boundaries.sort(key=lambda x: x['line_number'])
        
        # Remove boundaries that are too close to each other
        filtered_boundaries = []
        for boundary in boundaries:
            if not filtered_boundaries or boundary['line_number'] - filtered_boundaries[-1]['line_number'] > 2:
                filtered_boundaries.append(boundary)
        
        return filtered_boundaries
    
    def _determine_heading_level_advanced(self, heading_text: str) -> int:
        """Advanced heading level determination"""
        # Markdown-style headings
        if heading_text.startswith('#'):
            return len(heading_text) - len(heading_text.lstrip('#'))
        
        # Check for formatting indicators
        if heading_text.isupper():
            return 1  # ALL CAPS usually indicates top level
        
        if heading_text.startswith(('1.', '2.', '3.')):
            return 1  # Numbered top-level sections
        
        if heading_text.startswith(('a.', 'b.', 'c.', 'i.', 'ii.', 'iii.')):
            return 2  # Lettered/roman subsections
        
        # Default level based on content
        return 1
    
    def _is_topic_boundary_sentence(self, sentence: str) -> bool:
        """Determine if a sentence indicates a topic boundary"""
        sentence_lower = sentence.lower().strip()
        
        # Strong topic boundary indicators
        strong_indicators = [
            'this section', 'this chapter', 'this part',
            'we will now', 'let us now', 'next we',
            'another important', 'the next topic',
            'moving on to', 'turning to'
        ]
        
        for indicator in strong_indicators:
            if indicator in sentence_lower:
                return True
        
        # Weak topic boundary indicators (need additional context)
        weak_indicators = [
            'now', 'next', 'another', 'furthermore',
            'however', 'meanwhile', 'in addition'
        ]
        
        starts_with_weak = any(sentence_lower.startswith(indicator) for indicator in weak_indicators)
        if starts_with_weak and len(sentence) > 20:  # Longer sentences more likely to be boundaries
            return True
        
        return False
    
    def _extract_hierarchical_topics(self, content: str) -> Dict[str, Any]:
        """
        Extract topics in a hierarchical structure
        
        Returns:
            Hierarchical topic structure with levels and relationships
        """
        # Get section boundaries
        boundaries = self._identify_section_boundaries_advanced(content)
        
        # Build hierarchical structure
        hierarchy = {
            'main_topics': [],
            'subtopics': {},
            'topic_relationships': []
        }
        
        # Extract content between boundaries
        lines = content.split('\n')
        
        for i, boundary in enumerate(boundaries):
            start_line = boundary['line_number']
            end_line = boundaries[i + 1]['line_number'] if i + 1 < len(boundaries) else len(lines)
            
            # Extract section content
            section_lines = lines[start_line:end_line]
            section_content = '\n'.join(section_lines)
            
            # Extract topics from this section
            section_topics = self._extract_section_topics(section_content, boundary['level'])
            
            # Add to hierarchy
            if boundary['level'] == 1:
                topic_entry = {
                    'title': boundary['text'],
                    'topics': section_topics,
                    'level': boundary['level'],
                    'type': boundary['type']
                }
                hierarchy['main_topics'].append(topic_entry)
            else:
                # Add as subtopic to the most recent main topic
                if hierarchy['main_topics']:
                    parent_topic = hierarchy['main_topics'][-1]['title']
                    if parent_topic not in hierarchy['subtopics']:
                        hierarchy['subtopics'][parent_topic] = []
                    
                    hierarchy['subtopics'][parent_topic].append({
                        'title': boundary['text'],
                        'topics': section_topics,
                        'level': boundary['level']
                    })
        
        # Identify topic relationships
        hierarchy['topic_relationships'] = self._identify_topic_relationships(hierarchy)
        
        return hierarchy
    
    def _extract_section_topics(self, section_content: str, level: int) -> List[str]:
        """Extract topics from a specific section"""
        topics = []
        
        # Use different extraction strategies based on section level
        if level == 1:
            # Main sections - look for broader topics
            topics.extend(self._extract_main_topics_enhanced(section_content)[:3])
        else:
            # Subsections - look for specific concepts
            topics.extend(self._extract_key_concepts_enhanced(section_content)[:5])
        
        return topics
    
    def _identify_topic_relationships(self, hierarchy: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify relationships between topics"""
        relationships = []
        
        # Sequential relationships (topics that follow each other)
        main_topics = hierarchy['main_topics']
        for i in range(len(main_topics) - 1):
            relationships.append({
                'type': 'sequential',
                'from': main_topics[i]['title'],
                'to': main_topics[i + 1]['title'],
                'relationship': 'follows'
            })
        
        # Hierarchical relationships (parent-child)
        for parent, subtopics in hierarchy['subtopics'].items():
            for subtopic in subtopics:
                relationships.append({
                    'type': 'hierarchical',
                    'from': parent,
                    'to': subtopic['title'],
                    'relationship': 'contains'
                })
        
        # Conceptual relationships (topics that share concepts)
        for i, topic1 in enumerate(main_topics):
            for j, topic2 in enumerate(main_topics[i + 1:], i + 1):
                shared_concepts = set(topic1['topics']).intersection(set(topic2['topics']))
                if shared_concepts:
                    relationships.append({
                        'type': 'conceptual',
                        'from': topic1['title'],
                        'to': topic2['title'],
                        'relationship': 'shares_concepts',
                        'shared_concepts': list(shared_concepts)
                    })
        
        return relationships
    
    def _create_advanced_sections_with_hierarchy(self, content: str) -> List[ContentSection]:
        """Create sections with advanced hierarchical understanding"""
        # Get hierarchical topic structure
        topic_hierarchy = self._extract_hierarchical_topics(content)
        
        sections = []
        
        # Create sections from main topics
        for i, main_topic in enumerate(topic_hierarchy['main_topics']):
            # Extract content for this main topic
            section_content = self._extract_content_for_topic(content, main_topic, topic_hierarchy)
            
            # Create main section
            main_section = ContentSection(
                title=main_topic['title'],
                content=section_content,
                section_type=self._determine_section_type_from_hierarchy(main_topic),
                level=1,
                order=i,
                key_concepts=main_topic['topics'],
                estimated_duration=max(1, len(section_content.split()) // 150),
                prerequisites=self._identify_prerequisites_from_hierarchy(main_topic, topic_hierarchy),
                learning_outcomes=self._generate_learning_outcomes_from_hierarchy(main_topic),
                subsections=[]
            )
            
            # Add subsections if they exist
            if main_topic['title'] in topic_hierarchy['subtopics']:
                for j, subtopic in enumerate(topic_hierarchy['subtopics'][main_topic['title']]):
                    subsection_content = self._extract_content_for_topic(content, subtopic, topic_hierarchy)
                    
                    subsection = ContentSection(
                        title=subtopic['title'],
                        content=subsection_content,
                        section_type=self._determine_section_type_from_hierarchy(subtopic),
                        level=2,
                        order=j,
                        key_concepts=subtopic['topics'],
                        estimated_duration=max(1, len(subsection_content.split()) // 200),
                        prerequisites=[],
                        learning_outcomes=self._generate_learning_outcomes_from_hierarchy(subtopic),
                        subsections=[]
                    )
                    
                    main_section.subsections.append(subsection)
            
            sections.append(main_section)
        
        return sections
    
    def _extract_content_for_topic(self, content: str, topic: Dict[str, Any], hierarchy: Dict[str, Any]) -> str:
        """Extract content relevant to a specific topic"""
        # This is a simplified implementation
        # In practice, this would use more sophisticated content extraction
        
        # Find content sections that mention the topic
        topic_title = topic['title'].lower()
        paragraphs = content.split('\n\n')
        
        relevant_paragraphs = []
        for paragraph in paragraphs:
            # Check if paragraph is relevant to this topic
            if (topic_title in paragraph.lower() or 
                any(concept.lower() in paragraph.lower() for concept in topic['topics'])):
                relevant_paragraphs.append(paragraph)
        
        return '\n\n'.join(relevant_paragraphs) if relevant_paragraphs else content[:500]
    
    def _determine_section_type_from_hierarchy(self, topic: Dict[str, Any]) -> SectionType:
        """Determine section type based on hierarchical position and content"""
        title_lower = topic['title'].lower()
        
        # Check topic type from boundary detection
        if topic.get('type') == 'heading':
            # Analyze heading content for type indicators
            type_indicators = {
                SectionType.INTRODUCTION: ['introduction', 'intro', 'overview', 'background'],
                SectionType.CONCLUSION: ['conclusion', 'summary', 'wrap up', 'final'],
                SectionType.EXAMPLE: ['example', 'case study', 'illustration', 'demo'],
                SectionType.PROCEDURE: ['steps', 'procedure', 'method', 'how to'],
                SectionType.EXPLANATION: ['explanation', 'theory', 'concept', 'understanding'],
            }
            
            for section_type, indicators in type_indicators.items():
                if any(indicator in title_lower for indicator in indicators):
                    return section_type
        
        # Default based on level and position
        if topic.get('level', 1) == 1:
            return SectionType.MAIN_CONCEPT
        else:
            return SectionType.EXPLANATION
    
    def _identify_prerequisites_from_hierarchy(self, topic: Dict[str, Any], hierarchy: Dict[str, Any]) -> List[str]:
        """Identify prerequisites based on topic hierarchy and relationships"""
        prerequisites = []
        
        # Look for sequential relationships where this topic follows others
        for relationship in hierarchy['topic_relationships']:
            if (relationship['type'] == 'sequential' and 
                relationship['to'] == topic['title']):
                prerequisites.append(relationship['from'])
        
        # Look for conceptual dependencies
        for relationship in hierarchy['topic_relationships']:
            if (relationship['type'] == 'conceptual' and 
                relationship['to'] == topic['title'] and
                'shared_concepts' in relationship):
                prerequisites.extend(relationship['shared_concepts'][:2])
        
        return prerequisites[:3]  # Limit to 3 prerequisites
    
    def _generate_learning_outcomes_from_hierarchy(self, topic: Dict[str, Any]) -> List[str]:
        """Generate learning outcomes based on hierarchical topic structure"""
        outcomes = []
        
        # Generate outcomes based on topic level and content
        if topic.get('level', 1) == 1:
            # Main topic outcomes
            outcomes.append(f"Understand the main concepts of {topic['title']}")
            if topic['topics']:
                outcomes.append(f"Explain key aspects including {', '.join(topic['topics'][:2])}")
        else:
            # Subtopic outcomes
            outcomes.append(f"Apply knowledge of {topic['title']}")
            if topic['topics']:
                outcomes.append(f"Demonstrate understanding of {topic['topics'][0]}")
        
        # Add analysis outcome for complex topics
        if len(topic['topics']) > 3:
            outcomes.append(f"Analyze relationships between different aspects of {topic['title']}")
        
        return outcomes[:3]  # Limit to 3 outcomes
    def _group_related_paragraphs_advanced(self, paragraphs: List[str]) -> List[List[str]]:
        """Advanced paragraph grouping using semantic similarity and topic coherence"""
        if len(paragraphs) <= 3:
            return [paragraphs]
        
        # Calculate paragraph features for grouping
        paragraph_features = []
        for paragraph in paragraphs:
            features = {
                'text': paragraph,
                'key_concepts': set(self._extract_key_concepts_enhanced(paragraph)[:3]),
                'topics': set(self._extract_main_topics_enhanced(paragraph)[:2]),
                'length': len(paragraph.split()),
                'has_transition': self._has_transition_indicators(paragraph),
                'is_topic_sentence': self._is_topic_sentence(paragraph.split('.')[0]),
            }
            paragraph_features.append(features)
        
        # Group paragraphs based on similarity and coherence
        groups = []
        current_group = []
        
        for i, para_features in enumerate(paragraph_features):
            current_group.append(para_features['text'])
            
            # Determine if this should end a group
            should_end_group = False
            
            # Check group size limits
            if len(current_group) >= 4:  # Maximum group size
                should_end_group = True
            
            # Check for topic transitions
            elif i < len(paragraph_features) - 1:
                next_para = paragraph_features[i + 1]
                
                # Strong transition indicators
                if next_para['has_transition'] or next_para['is_topic_sentence']:
                    should_end_group = True
                
                # Concept similarity check
                elif para_features['key_concepts'] and next_para['key_concepts']:
                    concept_overlap = len(para_features['key_concepts'].intersection(next_para['key_concepts']))
                    concept_total = len(para_features['key_concepts'].union(next_para['key_concepts']))
                    
                    if concept_total > 0:
                        similarity = concept_overlap / concept_total
                        if similarity < 0.2:  # Low similarity indicates topic change
                            should_end_group = True
            
            # Always end group at last paragraph
            elif i == len(paragraph_features) - 1:
                should_end_group = True
            
            if should_end_group:
                if current_group:
                    groups.append(current_group)
                    current_group = []
        
        # Handle any remaining paragraphs
        if current_group:
            if groups:
                groups[-1].extend(current_group)
            else:
                groups.append(current_group)
        
        # Ensure minimum group sizes
        final_groups = []
        for group in groups:
            if len(group) >= 2 or not final_groups:
                final_groups.append(group)
            else:
                # Merge small groups with previous group
                final_groups[-1].extend(group)
        
        return final_groups if final_groups else [paragraphs]
    
    def _has_transition_indicators(self, paragraph: str) -> bool:
        """Check if paragraph contains transition indicators"""
        paragraph_lower = paragraph.lower()
        
        # Strong transition indicators at the beginning
        strong_transitions = [
            'however', 'therefore', 'furthermore', 'moreover', 'consequently',
            'nevertheless', 'nonetheless', 'meanwhile', 'subsequently',
            'in contrast', 'on the other hand', 'alternatively', 'specifically'
        ]
        
        for transition in strong_transitions:
            if paragraph_lower.startswith(transition):
                return True
        
        # Weaker transition indicators
        weak_transitions = [
            'now', 'next', 'then', 'after', 'before', 'during',
            'another', 'additionally', 'also', 'similarly'
        ]
        
        first_sentence = paragraph_lower.split('.')[0]
        for transition in weak_transitions:
            if first_sentence.startswith(transition + ' '):
                return True
        
        return False
    def _generate_hierarchical_content_structure(self, content: str) -> Dict[str, Any]:
        """
        Generate a comprehensive hierarchical content structure
        
        Returns:
            Complete hierarchical structure with multiple levels and relationships
        """
        # Get the basic hierarchical topics
        topic_hierarchy = self._extract_hierarchical_topics(content)
        
        # Enhance with additional structural elements
        enhanced_structure = {
            'document_structure': self._analyze_document_structure(content),
            'content_hierarchy': topic_hierarchy,
            'learning_progression': self._create_learning_progression(topic_hierarchy),
            'concept_map': self._build_concept_map(content, topic_hierarchy),
            'navigation_structure': self._create_navigation_structure(topic_hierarchy),
            'metadata': {
                'total_levels': self._calculate_hierarchy_depth(topic_hierarchy),
                'complexity_score': self._calculate_structural_complexity(topic_hierarchy),
                'coherence_metrics': self._calculate_hierarchy_coherence(topic_hierarchy)
            }
        }
        
        return enhanced_structure
    
    def _analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analyze the overall document structure"""
        structure = {
            'has_title': False,
            'has_introduction': False,
            'has_conclusion': False,
            'has_sections': False,
            'has_subsections': False,
            'section_count': 0,
            'subsection_count': 0,
            'heading_levels': [],
            'structural_elements': []
        }
        
        lines = content.split('\n')
        
        # Analyze headings and structure
        for line in lines:
            line_stripped = line.strip()
            
            # Check for markdown headings
            if line_stripped.startswith('#'):
                level = len(line_stripped) - len(line_stripped.lstrip('#'))
                structure['heading_levels'].append(level)
                
                if level == 1:
                    structure['section_count'] += 1
                    structure['has_sections'] = True
                    
                    # Check for introduction/conclusion
                    heading_text = line_stripped.lstrip('#').strip().lower()
                    if 'introduction' in heading_text or 'intro' in heading_text:
                        structure['has_introduction'] = True
                    elif 'conclusion' in heading_text or 'summary' in heading_text:
                        structure['has_conclusion'] = True
                
                elif level == 2:
                    structure['subsection_count'] += 1
                    structure['has_subsections'] = True
        
        # Detect other structural elements
        if re.search(r'^\s*[-*+]\s', content, re.MULTILINE):
            structure['structural_elements'].append('bullet_lists')
        
        if re.search(r'^\s*\d+\.\s', content, re.MULTILINE):
            structure['structural_elements'].append('numbered_lists')
        
        if re.search(r'\|[^|]*\|', content):
            structure['structural_elements'].append('tables')
        
        if re.search(r'```[^`]*```', content, re.DOTALL):
            structure['structural_elements'].append('code_blocks')
        
        # Determine if document has a title (first heading or prominent text)
        first_lines = content.split('\n')[:5]
        for line in first_lines:
            if line.strip() and (line.startswith('#') or len(line.strip()) < 100):
                structure['has_title'] = True
                break
        
        return structure
    
    def _create_learning_progression(self, hierarchy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a learning progression based on topic hierarchy"""
        progression = []
        
        # Start with introduction if available
        intro_topics = [topic for topic in hierarchy['main_topics'] 
                       if 'introduction' in topic['title'].lower() or 'intro' in topic['title'].lower()]
        
        if intro_topics:
            progression.append({
                'stage': 'introduction',
                'title': intro_topics[0]['title'],
                'learning_goals': ['Orient to the topic', 'Understand basic context'],
                'cognitive_load': 'low',
                'prerequisites': []
            })
        
        # Add main content topics in logical order
        main_content_topics = [topic for topic in hierarchy['main_topics'] 
                              if topic not in intro_topics and 
                              'conclusion' not in topic['title'].lower()]
        
        for i, topic in enumerate(main_content_topics):
            # Determine cognitive load based on topic complexity
            cognitive_load = 'low'
            if len(topic['topics']) > 5:
                cognitive_load = 'high'
            elif len(topic['topics']) > 2:
                cognitive_load = 'medium'
            
            # Identify prerequisites from previous topics
            prerequisites = []
            if i > 0:
                prerequisites.append(main_content_topics[i-1]['title'])
            
            progression.append({
                'stage': 'main_content',
                'title': topic['title'],
                'learning_goals': [f"Master {concept}" for concept in topic['topics'][:3]],
                'cognitive_load': cognitive_load,
                'prerequisites': prerequisites
            })
        
        # Add conclusion if available
        conclusion_topics = [topic for topic in hierarchy['main_topics'] 
                           if 'conclusion' in topic['title'].lower() or 'summary' in topic['title'].lower()]
        
        if conclusion_topics:
            progression.append({
                'stage': 'conclusion',
                'title': conclusion_topics[0]['title'],
                'learning_goals': ['Synthesize knowledge', 'Reflect on learning'],
                'cognitive_load': 'medium',
                'prerequisites': [topic['title'] for topic in main_content_topics]
            })
        
        return progression
    
    def _build_concept_map(self, content: str, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Build a concept map showing relationships between concepts"""
        # Extract all concepts from the content
        all_concepts = self._extract_key_concepts_enhanced(content)
        
        # Create concept nodes
        concept_nodes = {}
        for concept in all_concepts:
            concept_nodes[concept] = {
                'id': concept,
                'type': self._classify_concept_type(concept, content),
                'importance': self._calculate_concept_importance(concept, content),
                'related_topics': []
            }
        
        # Find which topics each concept belongs to
        for topic in hierarchy['main_topics']:
            for concept in topic['topics']:
                if concept in concept_nodes:
                    concept_nodes[concept]['related_topics'].append(topic['title'])
        
        # Create concept relationships
        concept_relationships = []
        for i, concept1 in enumerate(all_concepts):
            for concept2 in all_concepts[i+1:]:
                relationship_strength = self._calculate_concept_relationship(concept1, concept2, content)
                if relationship_strength > 0.3:  # Threshold for significant relationships
                    concept_relationships.append({
                        'from': concept1,
                        'to': concept2,
                        'strength': relationship_strength,
                        'type': self._determine_relationship_type(concept1, concept2, content)
                    })
        
        return {
            'nodes': concept_nodes,
            'relationships': concept_relationships,
            'central_concepts': self._identify_central_concepts(concept_nodes, concept_relationships)
        }
    
    def _classify_concept_type(self, concept: str, content: str) -> str:
        """Classify the type of concept"""
        concept_lower = concept.lower()
        
        # Definition-based concepts
        if re.search(f'{re.escape(concept_lower)}\\s+(?:is|are|means|refers to)', content, re.IGNORECASE):
            return 'definition'
        
        # Process or method concepts
        if any(word in concept_lower for word in ['method', 'process', 'algorithm', 'procedure', 'technique']):
            return 'process'
        
        # Theory or principle concepts
        if any(word in concept_lower for word in ['theory', 'principle', 'law', 'rule', 'concept']):
            return 'theory'
        
        # Application or example concepts
        if any(word in concept_lower for word in ['application', 'example', 'case', 'instance', 'use']):
            return 'application'
        
        # Tool or technology concepts
        if any(word in concept_lower for word in ['tool', 'system', 'technology', 'software', 'platform']):
            return 'tool'
        
        return 'general'
    
    def _calculate_concept_importance(self, concept: str, content: str) -> float:
        """Calculate the importance of a concept based on frequency and context"""
        concept_lower = concept.lower()
        
        # Count occurrences
        occurrences = len(re.findall(re.escape(concept_lower), content.lower()))
        
        # Weight by context (headings, emphasis, definitions)
        importance_score = occurrences * 0.1
        
        # Bonus for appearing in headings
        if re.search(f'#{1,6}.*{re.escape(concept_lower)}', content, re.IGNORECASE):
            importance_score += 0.5
        
        # Bonus for being emphasized (bold, italic)
        if re.search(f'\\*\\*[^*]*{re.escape(concept_lower)}[^*]*\\*\\*', content, re.IGNORECASE):
            importance_score += 0.3
        
        # Bonus for being defined
        if re.search(f'{re.escape(concept_lower)}\\s+(?:is|are|means)', content, re.IGNORECASE):
            importance_score += 0.4
        
        return min(1.0, importance_score)
    
    def _calculate_concept_relationship(self, concept1: str, concept2: str, content: str) -> float:
        """Calculate relationship strength between two concepts"""
        # Find sentences containing both concepts
        sentences = re.split(r'[.!?]+', content)
        co_occurrence_count = 0
        
        for sentence in sentences:
            if (concept1.lower() in sentence.lower() and 
                concept2.lower() in sentence.lower()):
                co_occurrence_count += 1
        
        # Calculate relationship strength based on co-occurrence
        total_sentences = len(sentences)
        if total_sentences == 0:
            return 0.0
        
        relationship_strength = co_occurrence_count / total_sentences
        
        # Bonus for appearing in the same paragraph
        paragraphs = content.split('\n\n')
        paragraph_co_occurrence = 0
        
        for paragraph in paragraphs:
            if (concept1.lower() in paragraph.lower() and 
                concept2.lower() in paragraph.lower()):
                paragraph_co_occurrence += 1
        
        if len(paragraphs) > 0:
            relationship_strength += (paragraph_co_occurrence / len(paragraphs)) * 0.5
        
        return min(1.0, relationship_strength)
    
    def _determine_relationship_type(self, concept1: str, concept2: str, content: str) -> str:
        """Determine the type of relationship between concepts"""
        # Look for explicit relationship indicators
        relationship_patterns = {
            'causal': [f'{concept1}.*(?:causes?|leads? to|results? in).*{concept2}',
                      f'{concept2}.*(?:caused by|results? from).*{concept1}'],
            'hierarchical': [f'{concept1}.*(?:includes?|contains?).*{concept2}',
                           f'{concept2}.*(?:part of|component of).*{concept1}'],
            'sequential': [f'{concept1}.*(?:before|prior to|followed by).*{concept2}',
                          f'{concept2}.*(?:after|following).*{concept1}'],
            'comparative': [f'{concept1}.*(?:similar to|like|compared to).*{concept2}',
                           f'{concept2}.*(?:similar to|like|compared to).*{concept1}'],
            'oppositional': [f'{concept1}.*(?:unlike|different from|opposite).*{concept2}',
                            f'{concept2}.*(?:unlike|different from|opposite).*{concept1}']
        }
        
        for rel_type, patterns in relationship_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return rel_type
        
        return 'associative'  # Default relationship type
    
    def _identify_central_concepts(self, concept_nodes: Dict[str, Any], relationships: List[Dict[str, Any]]) -> List[str]:
        """Identify the most central concepts in the concept map"""
        # Calculate centrality based on number of relationships
        centrality_scores = {}
        
        for concept in concept_nodes:
            centrality_scores[concept] = 0
        
        # Count relationships for each concept
        for relationship in relationships:
            centrality_scores[relationship['from']] += relationship['strength']
            centrality_scores[relationship['to']] += relationship['strength']
        
        # Also factor in concept importance
        for concept, node_data in concept_nodes.items():
            centrality_scores[concept] += node_data['importance'] * 0.5
        
        # Sort by centrality and return top concepts
        sorted_concepts = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [concept for concept, score in sorted_concepts[:5]]
    
    def _create_navigation_structure(self, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Create a navigation structure for the content"""
        navigation = {
            'main_sections': [],
            'breadcrumb_paths': {},
            'cross_references': [],
            'suggested_reading_order': []
        }
        
        # Create main sections for navigation
        for i, topic in enumerate(hierarchy['main_topics']):
            section = {
                'id': f"section_{i}",
                'title': topic['title'],
                'level': topic.get('level', 1),
                'subsections': []
            }
            
            # Add subsections if they exist
            if topic['title'] in hierarchy['subtopics']:
                for j, subtopic in enumerate(hierarchy['subtopics'][topic['title']]):
                    subsection = {
                        'id': f"section_{i}_sub_{j}",
                        'title': subtopic['title'],
                        'level': subtopic.get('level', 2)
                    }
                    section['subsections'].append(subsection)
            
            navigation['main_sections'].append(section)
        
        # Create breadcrumb paths
        for section in navigation['main_sections']:
            navigation['breadcrumb_paths'][section['id']] = [section['title']]
            
            for subsection in section['subsections']:
                navigation['breadcrumb_paths'][subsection['id']] = [
                    section['title'], subsection['title']
                ]
        
        # Create cross-references based on topic relationships
        for relationship in hierarchy['topic_relationships']:
            if relationship['type'] in ['conceptual', 'sequential']:
                navigation['cross_references'].append({
                    'from': relationship['from'],
                    'to': relationship['to'],
                    'type': relationship['type'],
                    'description': f"See also: {relationship['to']}"
                })
        
        # Suggest reading order
        navigation['suggested_reading_order'] = [
            topic['title'] for topic in hierarchy['main_topics']
        ]
        
        return navigation
    
    def _calculate_hierarchy_depth(self, hierarchy: Dict[str, Any]) -> int:
        """Calculate the maximum depth of the hierarchy"""
        max_depth = 1  # At least main topics
        
        for topic in hierarchy['main_topics']:
            current_depth = topic.get('level', 1)
            max_depth = max(max_depth, current_depth)
        
        # Check subtopics
        for subtopics in hierarchy['subtopics'].values():
            for subtopic in subtopics:
                current_depth = subtopic.get('level', 2)
                max_depth = max(max_depth, current_depth)
        
        return max_depth
    
    def _calculate_structural_complexity(self, hierarchy: Dict[str, Any]) -> float:
        """Calculate the structural complexity of the hierarchy"""
        # Factors: number of topics, subtopics, relationships, depth
        
        main_topic_count = len(hierarchy['main_topics'])
        subtopic_count = sum(len(subtopics) for subtopics in hierarchy['subtopics'].values())
        relationship_count = len(hierarchy['topic_relationships'])
        depth = self._calculate_hierarchy_depth(hierarchy)
        
        # Normalize and combine factors
        complexity_score = (
            (main_topic_count / 10.0) * 0.3 +  # Main topics (normalized to 10)
            (subtopic_count / 20.0) * 0.2 +    # Subtopics (normalized to 20)
            (relationship_count / 15.0) * 0.3 + # Relationships (normalized to 15)
            (depth / 5.0) * 0.2                 # Depth (normalized to 5)
        )
        
        return min(1.0, complexity_score)
    
    def _calculate_hierarchy_coherence(self, hierarchy: Dict[str, Any]) -> Dict[str, float]:
        """Calculate coherence metrics for the hierarchy"""
        metrics = {
            'topic_coherence': 0.0,
            'relationship_coherence': 0.0,
            'structural_coherence': 0.0
        }
        
        # Topic coherence: how well topics relate to each other
        if hierarchy['main_topics']:
            topic_overlap_scores = []
            
            for i, topic1 in enumerate(hierarchy['main_topics']):
                for topic2 in hierarchy['main_topics'][i+1:]:
                    # Calculate topic overlap based on shared concepts
                    shared_concepts = set(topic1['topics']).intersection(set(topic2['topics']))
                    total_concepts = set(topic1['topics']).union(set(topic2['topics']))
                    
                    if total_concepts:
                        overlap_score = len(shared_concepts) / len(total_concepts)
                        topic_overlap_scores.append(overlap_score)
            
            if topic_overlap_scores:
                metrics['topic_coherence'] = sum(topic_overlap_scores) / len(topic_overlap_scores)
        
        # Relationship coherence: quality of identified relationships
        if hierarchy['topic_relationships']:
            relationship_types = [rel['type'] for rel in hierarchy['topic_relationships']]
            type_diversity = len(set(relationship_types)) / len(relationship_types)
            metrics['relationship_coherence'] = 1.0 - type_diversity  # More diverse = less coherent
        
        # Structural coherence: balance of hierarchy
        if hierarchy['main_topics']:
            topic_sizes = [len(topic['topics']) for topic in hierarchy['main_topics']]
            if topic_sizes:
                avg_size = sum(topic_sizes) / len(topic_sizes)
                size_variance = sum((size - avg_size) ** 2 for size in topic_sizes) / len(topic_sizes)
                metrics['structural_coherence'] = max(0.0, 1.0 - (size_variance / (avg_size ** 2)))
        
        return metrics