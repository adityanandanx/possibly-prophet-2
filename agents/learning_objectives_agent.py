"""
Enhanced Learning Objectives Agent for Educational Content Generator

This agent specializes in generating educational goals and learning objectives
from content, with alignment to pedagogical frameworks like Bloom's Taxonomy.
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


class BloomLevel(Enum):
    """Bloom's Taxonomy cognitive levels"""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class LearningDomain(Enum):
    """Learning domains"""
    COGNITIVE = "cognitive"
    AFFECTIVE = "affective"
    PSYCHOMOTOR = "psychomotor"


@dataclass
class LearningObjective:
    """Represents a structured learning objective"""
    text: str
    bloom_level: BloomLevel
    domain: LearningDomain
    action_verb: str
    content_area: str
    condition: str
    criteria: str
    measurable: bool
    specific: bool
    achievable: bool
    relevant: bool
    time_bound: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "text": self.text,
            "bloom_level": self.bloom_level.value,
            "domain": self.domain.value,
            "action_verb": self.action_verb,
            "content_area": self.content_area,
            "condition": self.condition,
            "criteria": self.criteria,
            "measurable": self.measurable,
            "specific": self.specific,
            "achievable": self.achievable,
            "relevant": self.relevant,
            "time_bound": self.time_bound,
            "smart_score": self._calculate_smart_score()
        }
    
    def _calculate_smart_score(self) -> float:
        """Calculate SMART criteria score (0.0 to 1.0)"""
        criteria = [
            self.specific,
            self.measurable,
            self.achievable,
            self.relevant,
            self.time_bound
        ]
        return sum(criteria) / len(criteria)


@dataclass
class ObjectiveAnalysis:
    """Results of learning objectives analysis"""
    objectives: List[LearningObjective]
    bloom_distribution: Dict[str, int]
    domain_distribution: Dict[str, int]
    complexity_level: str
    alignment_score: float
    coverage_score: float
    quality_metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "objectives": [obj.to_dict() for obj in self.objectives],
            "bloom_distribution": self.bloom_distribution,
            "domain_distribution": self.domain_distribution,
            "complexity_level": self.complexity_level,
            "alignment_score": self.alignment_score,
            "coverage_score": self.coverage_score,
            "quality_metrics": self.quality_metrics
        }


class EnhancedLearningObjectivesAgent(BaseEducationalAgent):
    """
    Enhanced Learning Objectives Agent with pedagogical framework alignment
    """
    
    def __init__(self, **kwargs):
        """Initialize the enhanced learning objectives agent"""
        super().__init__("learning_objectives", **kwargs)
        
        # Bloom's Taxonomy action verbs by level
        self.bloom_verbs = {
            BloomLevel.REMEMBER: [
                'define', 'describe', 'identify', 'list', 'name', 'recall', 'recognize',
                'retrieve', 'state', 'tell', 'match', 'select', 'choose', 'find'
            ],
            BloomLevel.UNDERSTAND: [
                'explain', 'interpret', 'summarize', 'paraphrase', 'classify', 'compare',
                'contrast', 'demonstrate', 'illustrate', 'translate', 'rewrite', 'discuss'
            ],
            BloomLevel.APPLY: [
                'apply', 'execute', 'implement', 'solve', 'use', 'demonstrate', 'operate',
                'schedule', 'sketch', 'employ', 'practice', 'calculate', 'show'
            ],
            BloomLevel.ANALYZE: [
                'analyze', 'break down', 'compare', 'contrast', 'differentiate', 'discriminate',
                'distinguish', 'examine', 'experiment', 'question', 'test', 'investigate'
            ],
            BloomLevel.EVALUATE: [
                'evaluate', 'assess', 'critique', 'judge', 'justify', 'argue', 'defend',
                'validate', 'support', 'rate', 'prioritize', 'recommend', 'conclude'
            ],
            BloomLevel.CREATE: [
                'create', 'design', 'develop', 'compose', 'construct', 'formulate', 'generate',
                'plan', 'produce', 'build', 'invent', 'make', 'originate', 'synthesize'
            ]
        }
        
        # Content type to Bloom level mapping
        self.content_bloom_mapping = {
            'definition': [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND],
            'concept': [BloomLevel.UNDERSTAND, BloomLevel.APPLY],
            'procedure': [BloomLevel.APPLY, BloomLevel.ANALYZE],
            'analysis': [BloomLevel.ANALYZE, BloomLevel.EVALUATE],
            'synthesis': [BloomLevel.EVALUATE, BloomLevel.CREATE],
            'application': [BloomLevel.APPLY, BloomLevel.CREATE]
        }
        
        # Learning domain indicators
        self.domain_indicators = {
            LearningDomain.COGNITIVE: [
                'understand', 'analyze', 'remember', 'apply', 'knowledge', 'comprehension',
                'thinking', 'reasoning', 'problem solving', 'critical thinking'
            ],
            LearningDomain.AFFECTIVE: [
                'appreciate', 'value', 'attitude', 'belief', 'feeling', 'emotion',
                'motivation', 'interest', 'respect', 'empathy'
            ],
            LearningDomain.PSYCHOMOTOR: [
                'perform', 'demonstrate', 'execute', 'manipulate', 'coordinate',
                'skill', 'technique', 'physical', 'motor', 'dexterity'
            ]
        }
        
        logger.info("Enhanced Learning Objectives Agent initialized")
    
    def _prepare_prompt(self, content: str, context: Dict[str, Any]) -> str:
        """Prepare enhanced prompt for learning objectives generation"""
        
        # Analyze content for objective generation context
        content_analysis = self._analyze_content_for_objectives(content)
        
        # Build context-aware prompt
        prompt_parts = [
            "You are an expert educational learning objectives agent. Your task is to generate specific, measurable, and pedagogically sound learning objectives from educational content.",
            "",
            "CONTENT TO ANALYZE:",
            content,
            "",
            "CONTENT ANALYSIS:",
            f"- Content Type: {content_analysis['content_type']}",
            f"- Key Concepts: {', '.join(content_analysis['key_concepts'])}",
            f"- Difficulty Level: {content_analysis['difficulty_level']}",
            f"- Suggested Bloom Levels: {', '.join([level.value for level in content_analysis['suggested_bloom_levels']])}",
            f"- Learning Domain: {content_analysis['primary_domain'].value}",
            "",
            "LEARNING OBJECTIVES REQUIREMENTS:",
            "1. Create 3-6 specific, measurable learning objectives",
            "2. Use appropriate Bloom's Taxonomy action verbs",
            "3. Ensure objectives span multiple cognitive levels",
            "4. Make objectives SMART (Specific, Measurable, Achievable, Relevant, Time-bound)",
            "5. Align objectives with content complexity and scope",
            "6. Include conditions and criteria where appropriate",
            "",
            "BLOOM'S TAXONOMY LEVELS TO CONSIDER:",
            "- Remember: Define, identify, list, recall",
            "- Understand: Explain, interpret, summarize, compare",
            "- Apply: Apply, execute, implement, solve",
            "- Analyze: Analyze, examine, differentiate, investigate",
            "- Evaluate: Evaluate, critique, judge, justify",
            "- Create: Create, design, develop, compose",
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
            "Please generate learning objectives that:",
            "- Start with measurable action verbs",
            "- Specify what learners will be able to do",
            "- Include conditions and criteria when relevant",
            "- Progress from lower to higher cognitive levels",
            "- Are aligned with the content's educational goals",
            "",
            "Format each objective clearly and provide rationale for Bloom level selection."
        ])
        
        return "\n".join(prompt_parts)
    
    def _analyze_content_for_objectives(self, content: str) -> Dict[str, Any]:
        """
        Analyze content to inform learning objectives generation
        
        Args:
            content: Educational content to analyze
            
        Returns:
            Analysis results for objective generation
        """
        analysis = {
            'content_type': self._identify_content_type_for_objectives(content),
            'key_concepts': self._extract_key_concepts_for_objectives(content),
            'difficulty_level': self._assess_content_difficulty(content),
            'suggested_bloom_levels': self._suggest_bloom_levels(content),
            'primary_domain': self._identify_primary_learning_domain(content),
            'content_scope': self._assess_content_scope(content)
        }
        
        return analysis
    
    def _identify_content_type_for_objectives(self, content: str) -> str:
        """Identify content type for objective generation"""
        content_lower = content.lower()
        
        # Content type patterns with weights
        type_patterns = {
            'definition': [
                (r'\b(?:definition|define|means|refers to|is defined as)\b', 3),
                (r'\b\w+\s+(?:is|are)\s+', 2),
                (r':\s*[A-Z]', 1)  # Definition format
            ],
            'concept': [
                (r'\b(?:concept|principle|theory|idea|notion)\b', 3),
                (r'\b(?:understanding|comprehension|grasp)\b', 2),
                (r'\b(?:fundamental|basic|core|essential)\b', 1)
            ],
            'procedure': [
                (r'\b(?:step|procedure|method|process|algorithm)\b', 3),
                (r'\b(?:how to|instructions|guide|tutorial)\b', 2),
                (r'^\s*\d+\.\s', 2)  # Numbered steps
            ],
            'analysis': [
                (r'\b(?:analysis|analyze|examination|investigation)\b', 3),
                (r'\b(?:compare|contrast|evaluate|assess)\b', 2),
                (r'\b(?:relationship|correlation|pattern)\b', 1)
            ],
            'synthesis': [
                (r'\b(?:synthesis|combine|integrate|merge)\b', 3),
                (r'\b(?:relationship|connection|link)\b', 2),
                (r'\b(?:overall|comprehensive|holistic)\b', 1)
            ],
            'application': [
                (r'\b(?:application|apply|use|implement)\b', 3),
                (r'\b(?:example|case study|scenario|practice)\b', 2),
                (r'\b(?:real.world|practical|hands.on)\b', 1)
            ]
        }
        
        # Calculate scores for each type
        type_scores = {}
        for content_type, patterns in type_patterns.items():
            score = 0
            for pattern, weight in patterns:
                matches = len(re.findall(pattern, content_lower, re.MULTILINE))
                score += matches * weight
            type_scores[content_type] = score
        
        # Return type with highest score
        best_type = max(type_scores.items(), key=lambda x: x[1])
        return best_type[0] if best_type[1] > 0 else 'concept'
    
    def _extract_key_concepts_for_objectives(self, content: str) -> List[str]:
        """Extract key concepts specifically for objective generation"""
        concepts = []
        
        # Extract from headings (high priority for objectives)
        heading_patterns = [
            r'^#{1,6}\s+(.+)$',
            r'^(.+)\n[=-]{3,}$',
            r'^\d+\.\s+(.+)$'
        ]
        
        for pattern in heading_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            concepts.extend([match.strip() for match in matches if len(match.strip()) > 2])
        
        # Extract from emphasis (important for objectives)
        emphasis_patterns = [
            r'\*\*([^*]+)\*\*',  # Bold
            r'\*([^*]+)\*',      # Italic
            r'_([^_]+)_',        # Underlined
            r'`([^`]+)`'         # Code/technical terms
        ]
        
        for pattern in emphasis_patterns:
            matches = re.findall(pattern, content)
            concepts.extend([match.strip() for match in matches if len(match.strip()) > 2])
        
        # Extract from definition patterns
        definition_patterns = [
            r'(\w+(?:\s+\w+)*)\s+(?:is|are|means|refers to)',
            r'(?:define|definition of)\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s*:\s*[A-Z]'
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts.extend([match.strip() for match in matches])
        
        # Clean and deduplicate
        cleaned_concepts = []
        seen = set()
        
        for concept in concepts:
            # Clean concept
            concept = re.sub(r'[^\w\s-]', '', concept).strip()
            concept = re.sub(r'\s+', ' ', concept)
            
            # Skip if too short or already seen
            if len(concept) < 3 or concept.lower() in seen:
                continue
            
            seen.add(concept.lower())
            cleaned_concepts.append(concept)
        
        return cleaned_concepts[:10]  # Limit to most relevant
    
    def _assess_content_difficulty(self, content: str) -> str:
        """Assess content difficulty for objective alignment"""
        score = 0
        
        # Vocabulary complexity
        words = content.split()
        if words:
            long_words = [w for w in words if len(w) > 8]
            complexity_ratio = len(long_words) / len(words)
            
            if complexity_ratio > 0.15:
                score += 3
            elif complexity_ratio > 0.10:
                score += 2
            elif complexity_ratio > 0.05:
                score += 1
        
        # Technical terminology
        technical_patterns = [
            r'\b\w+(?:tion|sion|ment|ness|ity|ism)\b',
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b(?:algorithm|methodology|implementation)\b'
        ]
        
        technical_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                            for pattern in technical_patterns)
        
        if technical_count > 20:
            score += 3
        elif technical_count > 10:
            score += 2
        elif technical_count > 5:
            score += 1
        
        # Sentence complexity
        sentences = re.split(r'[.!?]+', content)
        if sentences:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_length > 25:
                score += 2
            elif avg_length > 15:
                score += 1
        
        # Determine difficulty level
        if score >= 6:
            return "advanced"
        elif score >= 3:
            return "intermediate"
        else:
            return "beginner"
    
    def _suggest_bloom_levels(self, content: str) -> List[BloomLevel]:
        """Suggest appropriate Bloom levels based on content analysis"""
        content_type = self._identify_content_type_for_objectives(content)
        difficulty = self._assess_content_difficulty(content)
        
        # Base levels from content type
        suggested_levels = self.content_bloom_mapping.get(content_type, [BloomLevel.UNDERSTAND])
        
        # Adjust based on difficulty
        if difficulty == "beginner":
            # Focus on lower levels
            if BloomLevel.ANALYZE in suggested_levels:
                suggested_levels.remove(BloomLevel.ANALYZE)
            if BloomLevel.EVALUATE in suggested_levels:
                suggested_levels.remove(BloomLevel.EVALUATE)
            if BloomLevel.CREATE in suggested_levels:
                suggested_levels.remove(BloomLevel.CREATE)
            
            # Ensure basic levels are included
            if BloomLevel.REMEMBER not in suggested_levels:
                suggested_levels.insert(0, BloomLevel.REMEMBER)
        
        elif difficulty == "advanced":
            # Include higher levels
            if BloomLevel.ANALYZE not in suggested_levels:
                suggested_levels.append(BloomLevel.ANALYZE)
            if len(suggested_levels) < 3:
                suggested_levels.append(BloomLevel.EVALUATE)
        
        # Ensure we have at least 2 levels
        if len(suggested_levels) < 2:
            suggested_levels.append(BloomLevel.UNDERSTAND)
        
        return suggested_levels[:4]  # Limit to 4 levels
    
    def _identify_primary_learning_domain(self, content: str) -> LearningDomain:
        """Identify the primary learning domain"""
        content_lower = content.lower()
        
        domain_scores = {}
        for domain, indicators in self.domain_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            domain_scores[domain] = score
        
        # Return domain with highest score
        best_domain = max(domain_scores.items(), key=lambda x: x[1])
        return best_domain[0] if best_domain[1] > 0 else LearningDomain.COGNITIVE
    
    def _assess_content_scope(self, content: str) -> str:
        """Assess the scope of content for objective planning"""
        word_count = len(content.split())
        concept_count = len(self._extract_key_concepts_for_objectives(content))
        
        if word_count > 2000 or concept_count > 8:
            return "broad"
        elif word_count > 500 or concept_count > 4:
            return "moderate"
        else:
            return "narrow"
    
    def _process_response(self, response: str) -> Dict[str, Any]:
        """Process agent response with enhanced learning objectives analysis, Bloom alignment, and measurability"""
        try:
            # First try to parse objectives from response
            objectives = self._parse_objectives_from_response(response)
            
            # If no good objectives found, create measurable learning outcomes
            if not objectives or len(objectives) < 2:
                logger.info("Creating measurable learning outcomes from content analysis")
                objectives = self._generate_measurable_learning_outcomes(response, {})
            else:
                # Enhance existing objectives for measurability
                logger.info("Enhancing parsed objectives for measurability")
                objectives = self._enhance_objective_measurability(objectives)
            
            # Analyze objectives quality and alignment
            analysis = self._analyze_objectives_quality(objectives)
            
            # Create detailed Bloom taxonomy report
            bloom_report = self._create_bloom_taxonomy_report(analysis)
            
            # Validate measurability
            measurability_report = self._validate_objective_measurability(objectives)
            
            # Validate objectives
            self._validate_objectives(analysis)
            
            return {
                "agent_type": self.agent_type,
                "processed_content": response,
                "learning_objectives": analysis.to_dict(),
                "bloom_taxonomy_report": bloom_report,
                "measurability_report": measurability_report,
                "metadata": {
                    "agent_name": self.name,
                    "processing_timestamp": datetime.now().isoformat(),
                    "objectives_version": "4.0",
                    "analysis_method": "enhanced_measurable_bloom_alignment",
                    "total_objectives": len(objectives),
                    "bloom_coverage": len(analysis.bloom_distribution),
                    "quality_score": analysis.alignment_score,
                    "measurability_score": measurability_report['overall_measurability_score'],
                    "bloom_progression": bloom_report['cognitive_progression']['is_progressive'],
                    "verb_appropriateness": bloom_report['verb_appropriateness']['appropriateness_score'],
                    "avg_smart_score": sum(obj._calculate_smart_score() for obj in objectives) / len(objectives) if objectives else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing learning objectives response: {str(e)}")
            raise AgentExecutionError(
                "Failed to process learning objectives response",
                agent_type=self.agent_type,
                original_error=e
            )
    
    def _parse_objectives_from_response(self, response: str) -> List[LearningObjective]:
        """Parse learning objectives from agent response"""
        objectives = []
        
        # Look for objective patterns in the response
        objective_patterns = [
            r'(?:^|\n)\s*(?:\d+\.|\-|\*)\s*(.+?)(?=\n|$)',  # Numbered or bulleted
            r'(?:^|\n)(.+?(?:will be able to|can|should).+?)(?=\n|$)',  # Objective format
            r'(?:^|\n)((?:Students?|Learners?).+?)(?=\n|$)'  # Student-focused
        ]
        
        potential_objectives = []
        for pattern in objective_patterns:
            matches = re.findall(pattern, response, re.MULTILINE | re.IGNORECASE)
            potential_objectives.extend(matches)
        
        # Process each potential objective
        for obj_text in potential_objectives:
            obj_text = obj_text.strip()
            
            # Skip if too short or doesn't look like an objective
            if len(obj_text) < 10 or not self._looks_like_objective(obj_text):
                continue
            
            # Analyze the objective
            objective = self._analyze_single_objective(obj_text)
            if objective:
                objectives.append(objective)
        
        # If no objectives found, create from content analysis
        if not objectives:
            objectives = self._generate_fallback_objectives(response)
        
        return objectives[:6]  # Limit to 6 objectives
    
    def _looks_like_objective(self, text: str) -> bool:
        """Check if text looks like a learning objective"""
        text_lower = text.lower()
        
        # Check for action verbs
        all_verbs = []
        for verbs in self.bloom_verbs.values():
            all_verbs.extend(verbs)
        
        has_action_verb = any(verb in text_lower for verb in all_verbs)
        
        # Check for objective indicators
        objective_indicators = [
            'will be able to', 'can', 'should', 'students', 'learners',
            'understand', 'explain', 'demonstrate', 'apply', 'analyze'
        ]
        
        has_indicator = any(indicator in text_lower for indicator in objective_indicators)
        
        return has_action_verb or has_indicator
    
    def _analyze_single_objective(self, obj_text: str) -> Optional[LearningObjective]:
        """Analyze a single objective text"""
        try:
            # Extract action verb
            action_verb = self._extract_action_verb(obj_text)
            if not action_verb:
                return None
            
            # Determine Bloom level
            bloom_level = self._determine_bloom_level(action_verb)
            
            # Extract content area
            content_area = self._extract_content_area(obj_text)
            
            # Extract condition and criteria
            condition = self._extract_condition(obj_text)
            criteria = self._extract_criteria(obj_text)
            
            # Determine learning domain
            domain = self._determine_learning_domain(obj_text)
            
            # Assess SMART criteria
            smart_assessment = self._assess_smart_criteria(obj_text)
            
            return LearningObjective(
                text=obj_text,
                bloom_level=bloom_level,
                domain=domain,
                action_verb=action_verb,
                content_area=content_area,
                condition=condition,
                criteria=criteria,
                **smart_assessment
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing objective '{obj_text}': {e}")
            return None
    
    def _extract_action_verb(self, obj_text: str) -> str:
        """Extract the main action verb from objective text"""
        obj_lower = obj_text.lower()
        
        # Look for Bloom taxonomy verbs
        for level, verbs in self.bloom_verbs.items():
            for verb in verbs:
                if verb in obj_lower:
                    return verb
        
        # Look for common action verbs
        common_verbs = ['understand', 'know', 'learn', 'master', 'complete']
        for verb in common_verbs:
            if verb in obj_lower:
                return verb
        
        return ""
    
    def _determine_bloom_level(self, action_verb: str) -> BloomLevel:
        """Determine Bloom level from action verb"""
        verb_lower = action_verb.lower()
        
        for level, verbs in self.bloom_verbs.items():
            if verb_lower in verbs:
                return level
        
        # Default to understand
        return BloomLevel.UNDERSTAND
    
    def _extract_content_area(self, obj_text: str) -> str:
        """Extract the content area from objective text"""
        # Simple extraction - look for noun phrases after action verbs
        words = obj_text.split()
        
        # Find action verb position
        verb_pos = -1
        for i, word in enumerate(words):
            if word.lower() in [verb for verbs in self.bloom_verbs.values() for verb in verbs]:
                verb_pos = i
                break
        
        if verb_pos >= 0 and verb_pos < len(words) - 1:
            # Take next few words as content area
            content_words = words[verb_pos + 1:verb_pos + 5]
            return ' '.join(content_words).rstrip('.,!?')
        
        return obj_text[:50]  # Fallback to first part of objective
    
    def _extract_condition(self, obj_text: str) -> str:
        """Extract condition from objective text"""
        condition_patterns = [
            r'(?:given|provided|using|with|after|when)\s+([^,]+)',
            r'(?:in the context of|during|while)\s+([^,]+)'
        ]
        
        for pattern in condition_patterns:
            match = re.search(pattern, obj_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_criteria(self, obj_text: str) -> str:
        """Extract success criteria from objective text"""
        criteria_patterns = [
            r'(?:with|at|to)\s+(\d+%|\d+/\d+|accuracy|precision)',
            r'(?:correctly|accurately|successfully)\s+([^,]+)',
            r'(?:within|in)\s+(\d+\s+(?:minutes?|hours?|days?))'
        ]
        
        for pattern in criteria_patterns:
            match = re.search(pattern, obj_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _determine_learning_domain(self, obj_text: str) -> LearningDomain:
        """Determine learning domain from objective text"""
        obj_lower = obj_text.lower()
        
        domain_scores = {}
        for domain, indicators in self.domain_indicators.items():
            score = sum(1 for indicator in indicators if indicator in obj_lower)
            domain_scores[domain] = score
        
        best_domain = max(domain_scores.items(), key=lambda x: x[1])
        return best_domain[0] if best_domain[1] > 0 else LearningDomain.COGNITIVE
    
    def _assess_smart_criteria(self, obj_text: str) -> Dict[str, bool]:
        """Assess SMART criteria for the objective"""
        obj_lower = obj_text.lower()
        
        # Specific: Has clear action verb and content area
        specific = bool(self._extract_action_verb(obj_text) and len(obj_text.split()) > 3)
        
        # Measurable: Has criteria or measurable outcomes
        measurable = bool(
            self._extract_criteria(obj_text) or
            any(word in obj_lower for word in ['demonstrate', 'identify', 'list', 'calculate'])
        )
        
        # Achievable: Not overly complex (heuristic)
        achievable = len(obj_text.split()) < 25 and not any(
            word in obj_lower for word in ['master all', 'completely understand', 'perfectly']
        )
        
        # Relevant: Contains educational content (heuristic)
        relevant = len(self._extract_content_area(obj_text)) > 0
        
        # Time-bound: Has time indicators
        time_bound = bool(re.search(r'\b(?:by|within|in|after)\s+\d+', obj_text, re.IGNORECASE))
        
        return {
            'specific': specific,
            'measurable': measurable,
            'achievable': achievable,
            'relevant': relevant,
            'time_bound': time_bound
        }
    
    def _generate_fallback_objectives(self, content: str) -> List[LearningObjective]:
        """Generate fallback objectives when parsing fails"""
        objectives = []
        
        # Extract key concepts for objective generation
        key_concepts = self._extract_key_concepts_for_objectives(content)[:3]
        
        # Generate basic objectives for each concept
        for i, concept in enumerate(key_concepts):
            if i == 0:
                # Remember level for first concept
                obj_text = f"Define and recall key aspects of {concept}"
                bloom_level = BloomLevel.REMEMBER
            elif i == 1:
                # Understand level for second concept
                obj_text = f"Explain the main principles of {concept}"
                bloom_level = BloomLevel.UNDERSTAND
            else:
                # Apply level for third concept
                obj_text = f"Apply knowledge of {concept} to solve problems"
                bloom_level = BloomLevel.APPLY
            
            objective = LearningObjective(
                text=obj_text,
                bloom_level=bloom_level,
                domain=LearningDomain.COGNITIVE,
                action_verb=obj_text.split()[0].lower(),
                content_area=concept,
                condition="",
                criteria="",
                specific=True,
                measurable=True,
                achievable=True,
                relevant=True,
                time_bound=False
            )
            
            objectives.append(objective)
        
        return objectives
    
    def _analyze_objectives_quality(self, objectives: List[LearningObjective]) -> ObjectiveAnalysis:
        """Analyze the quality and alignment of learning objectives"""
        
        # Calculate Bloom distribution
        bloom_distribution = {}
        for level in BloomLevel:
            count = sum(1 for obj in objectives if obj.bloom_level == level)
            if count > 0:
                bloom_distribution[level.value] = count
        
        # Calculate domain distribution
        domain_distribution = {}
        for domain in LearningDomain:
            count = sum(1 for obj in objectives if obj.domain == domain)
            if count > 0:
                domain_distribution[domain.value] = count
        
        # Assess complexity level
        complexity_level = self._assess_objectives_complexity(objectives)
        
        # Calculate alignment score
        alignment_score = self._calculate_alignment_score(objectives)
        
        # Calculate coverage score
        coverage_score = self._calculate_coverage_score(objectives)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(objectives)
        
        return ObjectiveAnalysis(
            objectives=objectives,
            bloom_distribution=bloom_distribution,
            domain_distribution=domain_distribution,
            complexity_level=complexity_level,
            alignment_score=alignment_score,
            coverage_score=coverage_score,
            quality_metrics=quality_metrics
        )
    
    def _assess_objectives_complexity(self, objectives: List[LearningObjective]) -> str:
        """Assess overall complexity of objectives"""
        if not objectives:
            return "basic"
        
        # Count higher-order thinking objectives
        higher_order_count = sum(1 for obj in objectives 
                               if obj.bloom_level in [BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE])
        
        higher_order_ratio = higher_order_count / len(objectives)
        
        if higher_order_ratio > 0.5:
            return "advanced"
        elif higher_order_ratio > 0.2:
            return "intermediate"
        else:
            return "basic"
    
    def _calculate_alignment_score(self, objectives: List[LearningObjective]) -> float:
        """Calculate how well objectives align with pedagogical principles"""
        if not objectives:
            return 0.0
        
        score = 0.0
        
        # Bloom level progression (bonus for having multiple levels)
        unique_levels = len(set(obj.bloom_level for obj in objectives))
        score += min(0.3, unique_levels * 0.1)
        
        # SMART criteria compliance
        smart_scores = [obj._calculate_smart_score() for obj in objectives]
        avg_smart_score = sum(smart_scores) / len(smart_scores)
        score += avg_smart_score * 0.4
        
        # Appropriate verb usage
        appropriate_verbs = sum(1 for obj in objectives if obj.action_verb in 
                              self.bloom_verbs.get(obj.bloom_level, []))
        verb_score = appropriate_verbs / len(objectives)
        score += verb_score * 0.3
        
        return min(1.0, score)
    
    def _calculate_coverage_score(self, objectives: List[LearningObjective]) -> float:
        """Calculate how well objectives cover the content"""
        if not objectives:
            return 0.0
        
        # Check for progression through Bloom levels
        levels_present = set(obj.bloom_level for obj in objectives)
        level_coverage = len(levels_present) / len(BloomLevel)
        
        # Check for content area diversity
        content_areas = set(obj.content_area for obj in objectives)
        content_diversity = min(1.0, len(content_areas) / max(len(objectives), 1))
        
        # Combine scores
        coverage_score = (level_coverage * 0.6) + (content_diversity * 0.4)
        
        return coverage_score
    
    def _calculate_quality_metrics(self, objectives: List[LearningObjective]) -> Dict[str, float]:
        """Calculate various quality metrics"""
        if not objectives:
            return {}
        
        metrics = {}
        
        # Average SMART score
        smart_scores = [obj._calculate_smart_score() for obj in objectives]
        metrics['avg_smart_score'] = sum(smart_scores) / len(smart_scores)
        
        # Specificity score (objectives with clear action verbs)
        specific_count = sum(1 for obj in objectives if obj.specific)
        metrics['specificity_score'] = specific_count / len(objectives)
        
        # Measurability score
        measurable_count = sum(1 for obj in objectives if obj.measurable)
        metrics['measurability_score'] = measurable_count / len(objectives)
        
        # Bloom level distribution balance
        bloom_counts = [sum(1 for obj in objectives if obj.bloom_level == level) 
                       for level in BloomLevel]
        max_count = max(bloom_counts) if bloom_counts else 1
        min_count = min([count for count in bloom_counts if count > 0]) if any(bloom_counts) else 0
        metrics['bloom_balance'] = min_count / max_count if max_count > 0 else 0
        
        return metrics
    
    def _validate_objectives(self, analysis: ObjectiveAnalysis) -> None:
        """Validate the learning objectives analysis"""
        if not analysis.objectives:
            raise AgentValidationError(
                "No learning objectives generated",
                agent_type=self.agent_type
            )
        
        if len(analysis.objectives) > 10:
            raise AgentValidationError(
                f"Too many objectives generated: {len(analysis.objectives)} (max 10)",
                agent_type=self.agent_type
            )
        
        if analysis.alignment_score < 0.3:
            logger.warning(f"Low alignment score: {analysis.alignment_score}")
        
        logger.info("Learning objectives validation passed")
    def _create_bloom_aligned_objectives(self, content: str, context: Dict[str, Any]) -> List[LearningObjective]:
        """
        Create learning objectives with explicit Bloom's Taxonomy alignment
        
        Args:
            content: Educational content
            context: Additional context for objective creation
            
        Returns:
            List of Bloom-aligned learning objectives
        """
        # Analyze content for Bloom alignment
        content_analysis = self._analyze_content_for_objectives(content)
        suggested_levels = content_analysis['suggested_bloom_levels']
        key_concepts = content_analysis['key_concepts']
        difficulty = content_analysis['difficulty_level']
        
        objectives = []
        
        # Create objectives for each suggested Bloom level
        for i, bloom_level in enumerate(suggested_levels):
            if i < len(key_concepts):
                concept = key_concepts[i]
                
                # Select appropriate verb for this Bloom level
                verbs = self.bloom_verbs[bloom_level]
                selected_verb = self._select_best_verb_for_concept(verbs, concept, content)
                
                # Create objective text with proper structure
                obj_text = self._construct_bloom_objective(
                    bloom_level, selected_verb, concept, difficulty, context
                )
                
                # Create learning objective with full analysis
                objective = self._create_detailed_objective(
                    obj_text, bloom_level, selected_verb, concept, content
                )
                
                if objective:
                    objectives.append(objective)
        
        # Ensure we have a good progression through Bloom levels
        objectives = self._ensure_bloom_progression(objectives, content_analysis)
        
        return objectives
    
    def _select_best_verb_for_concept(self, verbs: List[str], concept: str, content: str) -> str:
        """Select the most appropriate verb for a concept based on content context"""
        concept_lower = concept.lower()
        content_lower = content.lower()
        
        # Score verbs based on context relevance
        verb_scores = {}
        
        for verb in verbs:
            score = 0
            
            # Check if verb appears in content (indicates relevance)
            if verb in content_lower:
                score += 3
            
            # Check concept-verb compatibility
            if self._is_verb_concept_compatible(verb, concept_lower):
                score += 2
            
            # Check content type compatibility
            if self._is_verb_content_type_compatible(verb, content_lower):
                score += 1
            
            verb_scores[verb] = score
        
        # Return verb with highest score, or first verb as fallback
        best_verb = max(verb_scores.items(), key=lambda x: x[1])
        return best_verb[0] if best_verb[1] > 0 else verbs[0]
    
    def _is_verb_concept_compatible(self, verb: str, concept: str) -> bool:
        """Check if a verb is compatible with a concept"""
        # Define verb-concept compatibility patterns
        compatibility_patterns = {
            'define': ['definition', 'concept', 'term', 'principle'],
            'explain': ['process', 'method', 'theory', 'principle'],
            'demonstrate': ['skill', 'technique', 'procedure', 'method'],
            'analyze': ['relationship', 'pattern', 'structure', 'system'],
            'evaluate': ['quality', 'effectiveness', 'value', 'merit'],
            'create': ['solution', 'design', 'plan', 'model']
        }
        
        patterns = compatibility_patterns.get(verb, [])
        return any(pattern in concept for pattern in patterns)
    
    def _is_verb_content_type_compatible(self, verb: str, content: str) -> bool:
        """Check if a verb is compatible with content type"""
        # Define verb-content type compatibility
        if verb in ['define', 'identify', 'list'] and 'definition' in content:
            return True
        elif verb in ['explain', 'describe', 'interpret'] and any(word in content for word in ['concept', 'theory', 'principle']):
            return True
        elif verb in ['apply', 'use', 'implement'] and any(word in content for word in ['method', 'procedure', 'technique']):
            return True
        elif verb in ['analyze', 'examine', 'compare'] and any(word in content for word in ['analysis', 'comparison', 'relationship']):
            return True
        elif verb in ['evaluate', 'assess', 'critique'] and any(word in content for word in ['evaluation', 'assessment', 'quality']):
            return True
        elif verb in ['create', 'design', 'develop'] and any(word in content for word in ['creation', 'design', 'development']):
            return True
        
        return False
    
    def _construct_bloom_objective(self, bloom_level: BloomLevel, verb: str, concept: str, 
                                 difficulty: str, context: Dict[str, Any]) -> str:
        """Construct a well-formed objective following Bloom's Taxonomy principles"""
        
        # Base objective structure: [Condition] + Learner + Action Verb + Content + [Criteria]
        learner = "Students will be able to"
        
        # Adjust verb form for objective structure
        action_verb = verb
        
        # Create content specification based on Bloom level
        if bloom_level == BloomLevel.REMEMBER:
            content_spec = f"the key definitions and facts about {concept}"
        elif bloom_level == BloomLevel.UNDERSTAND:
            content_spec = f"the main principles and concepts of {concept}"
        elif bloom_level == BloomLevel.APPLY:
            content_spec = f"{concept} in practical situations and real-world scenarios"
        elif bloom_level == BloomLevel.ANALYZE:
            content_spec = f"the components and relationships within {concept}"
        elif bloom_level == BloomLevel.EVALUATE:
            content_spec = f"the effectiveness and value of different approaches to {concept}"
        elif bloom_level == BloomLevel.CREATE:
            content_spec = f"new solutions and approaches using {concept}"
        else:
            content_spec = concept
        
        # Add condition based on difficulty and context
        condition = ""
        if difficulty == "advanced":
            condition = "Given complex scenarios, "
        elif difficulty == "intermediate":
            condition = "Using provided resources, "
        elif context.get('has_examples'):
            condition = "Based on the examples provided, "
        
        # Add criteria based on Bloom level and difficulty
        criteria = ""
        if bloom_level in [BloomLevel.APPLY, BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE]:
            if difficulty == "advanced":
                criteria = " with 85% accuracy"
            elif difficulty == "intermediate":
                criteria = " with appropriate justification"
            else:
                criteria = " correctly"
        
        # Construct final objective
        objective = f"{condition}{learner} {action_verb} {content_spec}{criteria}".strip()
        
        # Clean up grammar and formatting
        objective = re.sub(r'\s+', ' ', objective)  # Remove extra spaces
        objective = objective[0].upper() + objective[1:] if objective else ""  # Capitalize first letter
        
        return objective
    
    def _create_detailed_objective(self, obj_text: str, bloom_level: BloomLevel, 
                                 verb: str, concept: str, content: str) -> LearningObjective:
        """Create a detailed learning objective with full analysis"""
        
        # Extract components
        condition = self._extract_condition(obj_text)
        criteria = self._extract_criteria(obj_text)
        domain = self._determine_learning_domain(obj_text)
        
        # Enhanced SMART assessment
        smart_assessment = self._enhanced_smart_assessment(obj_text, bloom_level, concept)
        
        return LearningObjective(
            text=obj_text,
            bloom_level=bloom_level,
            domain=domain,
            action_verb=verb,
            content_area=concept,
            condition=condition,
            criteria=criteria,
            **smart_assessment
        )
    
    def _enhanced_smart_assessment(self, obj_text: str, bloom_level: BloomLevel, concept: str) -> Dict[str, bool]:
        """Enhanced SMART criteria assessment with Bloom level consideration"""
        obj_lower = obj_text.lower()
        
        # Specific: Clear action verb and well-defined content area
        specific = (
            bool(re.search(r'\b(?:students?|learners?)\s+will\s+be\s+able\s+to\b', obj_lower)) and
            len(concept) > 2 and
            any(verb in obj_lower for verb in self.bloom_verbs[bloom_level])
        )
        
        # Measurable: Observable action verbs and clear outcomes
        measurable_verbs = [
            'define', 'identify', 'list', 'describe', 'explain', 'demonstrate',
            'apply', 'solve', 'analyze', 'compare', 'evaluate', 'create'
        ]
        measurable = (
            any(verb in obj_lower for verb in measurable_verbs) and
            not any(vague_word in obj_lower for vague_word in ['understand', 'know', 'learn', 'appreciate'])
        )
        
        # Achievable: Appropriate for Bloom level and not overly ambitious
        achievable = (
            len(obj_text.split()) < 30 and  # Not too complex
            not any(word in obj_lower for word in ['master all', 'completely', 'perfectly', 'everything']) and
            self._is_bloom_level_appropriate(bloom_level, obj_text)
        )
        
        # Relevant: Contains meaningful educational content
        relevant = (
            len(concept) > 2 and
            not any(generic in concept.lower() for generic in ['thing', 'stuff', 'item', 'content']) and
            bool(re.search(r'\b(?:principle|concept|method|technique|theory|application)\b', obj_lower))
        )
        
        # Time-bound: Has explicit or implicit time constraints
        time_bound = (
            bool(re.search(r'\b(?:by|within|in|after|during)\s+(?:the\s+)?(?:end\s+of\s+)?(?:this\s+)?(?:lesson|unit|course|session)', obj_lower)) or
            bool(re.search(r'\b(?:by|within|in)\s+\d+\s+(?:minutes?|hours?|days?|weeks?)', obj_lower)) or
            'end of' in obj_lower
        )
        
        return {
            'specific': specific,
            'measurable': measurable,
            'achievable': achievable,
            'relevant': relevant,
            'time_bound': time_bound
        }
    
    def _is_bloom_level_appropriate(self, bloom_level: BloomLevel, obj_text: str) -> bool:
        """Check if the Bloom level is appropriate for the objective complexity"""
        obj_lower = obj_text.lower()
        
        # Check for complexity indicators
        complexity_indicators = {
            BloomLevel.REMEMBER: ['basic', 'simple', 'fundamental', 'key facts'],
            BloomLevel.UNDERSTAND: ['explain', 'interpret', 'main ideas', 'concepts'],
            BloomLevel.APPLY: ['use', 'apply', 'practical', 'real-world', 'scenarios'],
            BloomLevel.ANALYZE: ['analyze', 'examine', 'compare', 'relationships', 'components'],
            BloomLevel.EVALUATE: ['evaluate', 'assess', 'judge', 'critique', 'effectiveness'],
            BloomLevel.CREATE: ['create', 'design', 'develop', 'new', 'original', 'innovative']
        }
        
        indicators = complexity_indicators.get(bloom_level, [])
        return any(indicator in obj_lower for indicator in indicators)
    
    def _ensure_bloom_progression(self, objectives: List[LearningObjective], 
                                content_analysis: Dict[str, Any]) -> List[LearningObjective]:
        """Ensure objectives follow a logical Bloom taxonomy progression"""
        
        if len(objectives) < 2:
            return objectives
        
        # Sort objectives by Bloom level hierarchy
        bloom_order = [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND, BloomLevel.APPLY, 
                      BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE]
        
        # Group objectives by Bloom level
        level_groups = {}
        for obj in objectives:
            if obj.bloom_level not in level_groups:
                level_groups[obj.bloom_level] = []
            level_groups[obj.bloom_level].append(obj)
        
        # Ensure we have foundational levels for advanced content
        difficulty = content_analysis.get('difficulty_level', 'intermediate')
        
        if difficulty in ['intermediate', 'advanced']:
            # Ensure we have Remember or Understand level
            foundational_levels = [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND]
            has_foundational = any(level in level_groups for level in foundational_levels)
            
            if not has_foundational and len(objectives) > 0:
                # Add a foundational objective
                first_concept = content_analysis.get('key_concepts', ['the main concepts'])[0]
                foundational_obj = self._create_detailed_objective(
                    f"Students will be able to define the key terms and concepts of {first_concept}",
                    BloomLevel.REMEMBER,
                    'define',
                    first_concept,
                    ""
                )
                objectives.insert(0, foundational_obj)
        
        # Reorder objectives by Bloom progression
        ordered_objectives = []
        for level in bloom_order:
            if level in level_groups:
                ordered_objectives.extend(level_groups[level])
        
        return ordered_objectives
    
    def _create_bloom_taxonomy_report(self, analysis: ObjectiveAnalysis) -> Dict[str, Any]:
        """Create a detailed Bloom's Taxonomy alignment report"""
        
        report = {
            'bloom_coverage': self._analyze_bloom_coverage(analysis),
            'cognitive_progression': self._analyze_cognitive_progression(analysis),
            'verb_appropriateness': self._analyze_verb_appropriateness(analysis),
            'level_balance': self._analyze_level_balance(analysis),
            'recommendations': self._generate_bloom_recommendations(analysis)
        }
        
        return report
    
    def _analyze_bloom_coverage(self, analysis: ObjectiveAnalysis) -> Dict[str, Any]:
        """Analyze how well objectives cover Bloom's taxonomy levels"""
        
        total_levels = len(BloomLevel)
        covered_levels = len(analysis.bloom_distribution)
        coverage_percentage = (covered_levels / total_levels) * 100
        
        # Identify missing levels
        present_levels = set(BloomLevel(level) for level in analysis.bloom_distribution.keys())
        all_levels = set(BloomLevel)
        missing_levels = [level.value for level in all_levels - present_levels]
        
        return {
            'coverage_percentage': coverage_percentage,
            'covered_levels': covered_levels,
            'total_levels': total_levels,
            'missing_levels': missing_levels,
            'distribution': analysis.bloom_distribution
        }
    
    def _analyze_cognitive_progression(self, analysis: ObjectiveAnalysis) -> Dict[str, Any]:
        """Analyze the cognitive progression of objectives"""
        
        bloom_order = [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND, BloomLevel.APPLY, 
                      BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE]
        
        # Check if objectives follow logical progression
        objective_levels = [obj.bloom_level for obj in analysis.objectives]
        level_indices = [bloom_order.index(level) for level in objective_levels]
        
        # Calculate progression score
        is_progressive = all(level_indices[i] <= level_indices[i+1] for i in range(len(level_indices)-1))
        
        # Calculate complexity progression
        avg_complexity_by_position = []
        for i, level_idx in enumerate(level_indices):
            avg_complexity_by_position.append(level_idx)
        
        progression_trend = 'increasing' if len(avg_complexity_by_position) > 1 and avg_complexity_by_position[-1] > avg_complexity_by_position[0] else 'mixed'
        
        return {
            'is_progressive': is_progressive,
            'progression_trend': progression_trend,
            'level_sequence': [level.value for level in objective_levels],
            'complexity_range': {
                'lowest': min(level_indices),
                'highest': max(level_indices),
                'span': max(level_indices) - min(level_indices)
            }
        }
    
    def _analyze_verb_appropriateness(self, analysis: ObjectiveAnalysis) -> Dict[str, Any]:
        """Analyze how appropriate the action verbs are for their Bloom levels"""
        
        appropriate_count = 0
        total_count = len(analysis.objectives)
        verb_analysis = []
        
        for obj in analysis.objectives:
            is_appropriate = obj.action_verb in self.bloom_verbs.get(obj.bloom_level, [])
            appropriate_count += 1 if is_appropriate else 0
            
            verb_analysis.append({
                'objective': obj.text[:50] + "..." if len(obj.text) > 50 else obj.text,
                'verb': obj.action_verb,
                'bloom_level': obj.bloom_level.value,
                'is_appropriate': is_appropriate,
                'suggested_verbs': self.bloom_verbs.get(obj.bloom_level, [])[:3]
            })
        
        appropriateness_score = appropriate_count / total_count if total_count > 0 else 0
        
        return {
            'appropriateness_score': appropriateness_score,
            'appropriate_count': appropriate_count,
            'total_count': total_count,
            'verb_analysis': verb_analysis
        }
    
    def _analyze_level_balance(self, analysis: ObjectiveAnalysis) -> Dict[str, Any]:
        """Analyze the balance of objectives across Bloom levels"""
        
        if not analysis.bloom_distribution:
            return {'balance_score': 0, 'is_balanced': False}
        
        counts = list(analysis.bloom_distribution.values())
        total_objectives = sum(counts)
        
        # Calculate balance score (lower variance = better balance)
        mean_count = total_objectives / len(counts)
        variance = sum((count - mean_count) ** 2 for count in counts) / len(counts)
        balance_score = max(0, 1 - (variance / (mean_count ** 2))) if mean_count > 0 else 0
        
        # Determine if distribution is balanced (no level has more than 50% of objectives)
        max_percentage = max(count / total_objectives for count in counts) * 100
        is_balanced = max_percentage <= 50
        
        return {
            'balance_score': balance_score,
            'is_balanced': is_balanced,
            'max_percentage': max_percentage,
            'distribution_analysis': {
                level: {
                    'count': count,
                    'percentage': (count / total_objectives) * 100
                }
                for level, count in analysis.bloom_distribution.items()
            }
        }
    
    def _generate_bloom_recommendations(self, analysis: ObjectiveAnalysis) -> List[str]:
        """Generate recommendations for improving Bloom taxonomy alignment"""
        
        recommendations = []
        
        # Coverage recommendations
        bloom_coverage = self._analyze_bloom_coverage(analysis)
        if bloom_coverage['coverage_percentage'] < 50:
            recommendations.append(
                f"Consider adding objectives for missing Bloom levels: {', '.join(bloom_coverage['missing_levels'])}"
            )
        
        # Progression recommendations
        progression = self._analyze_cognitive_progression(analysis)
        if not progression['is_progressive']:
            recommendations.append(
                "Reorder objectives to follow a logical cognitive progression from lower to higher Bloom levels"
            )
        
        # Verb appropriateness recommendations
        verb_analysis = self._analyze_verb_appropriateness(analysis)
        if verb_analysis['appropriateness_score'] < 0.8:
            recommendations.append(
                "Review action verbs to ensure they align with their intended Bloom taxonomy levels"
            )
        
        # Balance recommendations
        balance = self._analyze_level_balance(analysis)
        if not balance['is_balanced']:
            recommendations.append(
                "Distribute objectives more evenly across Bloom taxonomy levels to ensure comprehensive coverage"
            )
        
        # Complexity recommendations
        if analysis.complexity_level == 'basic' and len(analysis.objectives) > 3:
            recommendations.append(
                "Consider adding higher-order thinking objectives (Analyze, Evaluate, Create) to increase cognitive challenge"
            )
        
        return recommendations if recommendations else ["Objectives show good Bloom taxonomy alignment"]
    def _enhance_objective_measurability(self, objectives: List[LearningObjective]) -> List[LearningObjective]:
        """
        Enhance objectives to make them more measurable and specific
        
        Args:
            objectives: List of learning objectives to enhance
            
        Returns:
            Enhanced objectives with improved measurability
        """
        enhanced_objectives = []
        
        for obj in objectives:
            enhanced_obj = self._make_objective_more_measurable(obj)
            enhanced_objectives.append(enhanced_obj)
        
        return enhanced_objectives
    
    def _make_objective_more_measurable(self, objective: LearningObjective) -> LearningObjective:
        """Make a single objective more measurable and specific"""
        
        # Analyze current measurability
        measurability_issues = self._identify_measurability_issues(objective)
        
        # Enhance the objective text
        enhanced_text = objective.text
        
        # Fix vague verbs
        if 'vague_verb' in measurability_issues:
            enhanced_text = self._replace_vague_verb(enhanced_text, objective.bloom_level)
        
        # Add specific criteria if missing
        if 'missing_criteria' in measurability_issues:
            enhanced_text = self._add_performance_criteria(enhanced_text, objective.bloom_level)
        
        # Add conditions if missing
        if 'missing_conditions' in measurability_issues:
            enhanced_text = self._add_performance_conditions(enhanced_text, objective.bloom_level)
        
        # Make content area more specific
        if 'vague_content' in measurability_issues:
            enhanced_text = self._specify_content_area(enhanced_text, objective.content_area)
        
        # Create enhanced objective
        enhanced_objective = LearningObjective(
            text=enhanced_text,
            bloom_level=objective.bloom_level,
            domain=objective.domain,
            action_verb=self._extract_action_verb(enhanced_text),
            content_area=self._extract_content_area(enhanced_text),
            condition=self._extract_condition(enhanced_text),
            criteria=self._extract_criteria(enhanced_text),
            **self._enhanced_smart_assessment(enhanced_text, objective.bloom_level, objective.content_area)
        )
        
        return enhanced_objective
    
    def _identify_measurability_issues(self, objective: LearningObjective) -> List[str]:
        """Identify issues that make an objective less measurable"""
        issues = []
        
        # Check for vague verbs
        vague_verbs = ['understand', 'know', 'learn', 'appreciate', 'be aware of', 'realize', 'grasp']
        if any(vague_verb in objective.text.lower() for vague_verb in vague_verbs):
            issues.append('vague_verb')
        
        # Check for missing criteria
        if not objective.criteria or len(objective.criteria.strip()) == 0:
            if objective.bloom_level in [BloomLevel.APPLY, BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE]:
                issues.append('missing_criteria')
        
        # Check for missing conditions
        if not objective.condition or len(objective.condition.strip()) == 0:
            if objective.bloom_level in [BloomLevel.APPLY, BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE]:
                issues.append('missing_conditions')
        
        # Check for vague content area
        vague_content_indicators = ['things', 'concepts', 'ideas', 'material', 'content', 'information']
        if any(vague in objective.content_area.lower() for vague in vague_content_indicators):
            issues.append('vague_content')
        
        return issues
    
    def _replace_vague_verb(self, obj_text: str, bloom_level: BloomLevel) -> str:
        """Replace vague verbs with specific, measurable ones"""
        
        # Mapping of vague verbs to specific alternatives by Bloom level
        verb_replacements = {
            BloomLevel.REMEMBER: {
                'understand': 'define',
                'know': 'identify',
                'learn': 'list',
                'appreciate': 'recognize',
                'be aware of': 'recall',
                'realize': 'state'
            },
            BloomLevel.UNDERSTAND: {
                'understand': 'explain',
                'know': 'describe',
                'learn': 'interpret',
                'appreciate': 'summarize',
                'be aware of': 'discuss',
                'realize': 'illustrate'
            },
            BloomLevel.APPLY: {
                'understand': 'apply',
                'know': 'use',
                'learn': 'implement',
                'appreciate': 'demonstrate',
                'be aware of': 'execute',
                'realize': 'solve'
            },
            BloomLevel.ANALYZE: {
                'understand': 'analyze',
                'know': 'examine',
                'learn': 'investigate',
                'appreciate': 'compare',
                'be aware of': 'differentiate',
                'realize': 'break down'
            },
            BloomLevel.EVALUATE: {
                'understand': 'evaluate',
                'know': 'assess',
                'learn': 'critique',
                'appreciate': 'judge',
                'be aware of': 'validate',
                'realize': 'justify'
            },
            BloomLevel.CREATE: {
                'understand': 'create',
                'know': 'design',
                'learn': 'develop',
                'appreciate': 'compose',
                'be aware of': 'construct',
                'realize': 'generate'
            }
        }
        
        replacements = verb_replacements.get(bloom_level, {})
        enhanced_text = obj_text
        
        for vague_verb, specific_verb in replacements.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(vague_verb), re.IGNORECASE)
            enhanced_text = pattern.sub(specific_verb, enhanced_text)
        
        return enhanced_text
    
    def _add_performance_criteria(self, obj_text: str, bloom_level: BloomLevel) -> str:
        """Add specific performance criteria to make objectives measurable"""
        
        # Define criteria templates by Bloom level
        criteria_templates = {
            BloomLevel.REMEMBER: [
                "with 90% accuracy",
                "correctly identifying at least 8 out of 10 items",
                "without reference materials"
            ],
            BloomLevel.UNDERSTAND: [
                "using their own words",
                "with clear examples",
                "demonstrating comprehension through explanation"
            ],
            BloomLevel.APPLY: [
                "with 85% accuracy",
                "in at least 3 different scenarios",
                "following proper procedures"
            ],
            BloomLevel.ANALYZE: [
                "identifying at least 3 key components",
                "with supporting evidence",
                "using appropriate analytical frameworks"
            ],
            BloomLevel.EVALUATE: [
                "using established criteria",
                "with justified reasoning",
                "considering multiple perspectives"
            ],
            BloomLevel.CREATE: [
                "meeting specified requirements",
                "demonstrating originality",
                "within given constraints"
            ]
        }
        
        # Select appropriate criteria
        available_criteria = criteria_templates.get(bloom_level, ["successfully"])
        selected_criteria = available_criteria[0]  # Use first as default
        
        # Add criteria to objective if not already present
        if not any(criterion in obj_text.lower() for criterion in ['with', 'using', 'demonstrating', 'meeting']):
            # Insert criteria before the period or at the end
            if obj_text.endswith('.'):
                enhanced_text = obj_text[:-1] + f" {selected_criteria}."
            else:
                enhanced_text = obj_text + f" {selected_criteria}"
        else:
            enhanced_text = obj_text
        
        return enhanced_text
    
    def _add_performance_conditions(self, obj_text: str, bloom_level: BloomLevel) -> str:
        """Add specific conditions to make objectives more measurable"""
        
        # Define condition templates by Bloom level
        condition_templates = {
            BloomLevel.REMEMBER: [
                "Given a list of terms",
                "Without reference materials",
                "Within 10 minutes"
            ],
            BloomLevel.UNDERSTAND: [
                "Given examples and non-examples",
                "Using provided resources",
                "In their own words"
            ],
            BloomLevel.APPLY: [
                "Given real-world scenarios",
                "Using appropriate tools",
                "In practical situations"
            ],
            BloomLevel.ANALYZE: [
                "Given complex data sets",
                "Using analytical frameworks",
                "With supporting evidence"
            ],
            BloomLevel.EVALUATE: [
                "Given multiple options",
                "Using established criteria",
                "With justified reasoning"
            ],
            BloomLevel.CREATE: [
                "Given specific requirements",
                "Using available resources",
                "Within project constraints"
            ]
        }
        
        # Check if objective already has conditions
        has_conditions = any(indicator in obj_text.lower() for indicator in 
                           ['given', 'using', 'with', 'when', 'after', 'during'])
        
        if not has_conditions:
            available_conditions = condition_templates.get(bloom_level, ["When required"])
            selected_condition = available_conditions[0]
            
            # Add condition at the beginning
            enhanced_text = f"{selected_condition}, {obj_text.lower()}"
            # Capitalize first letter after comma
            enhanced_text = enhanced_text[:len(selected_condition) + 2] + enhanced_text[len(selected_condition) + 2:].capitalize()
        else:
            enhanced_text = obj_text
        
        return enhanced_text
    
    def _specify_content_area(self, obj_text: str, content_area: str) -> str:
        """Make content area more specific and measurable"""
        
        # Define specific content area replacements
        content_replacements = {
            'concepts': 'key principles and definitions',
            'ideas': 'main theories and applications',
            'material': 'core content and examples',
            'content': 'fundamental concepts and procedures',
            'information': 'essential facts and relationships',
            'things': 'specific elements and components'
        }
        
        enhanced_text = obj_text
        
        for vague_term, specific_term in content_replacements.items():
            if vague_term in content_area.lower():
                enhanced_text = enhanced_text.replace(vague_term, specific_term)
        
        return enhanced_text
    
    def _generate_measurable_learning_outcomes(self, content: str, context: Dict[str, Any]) -> List[LearningObjective]:
        """
        Generate highly measurable and specific learning outcomes
        
        Args:
            content: Educational content
            context: Additional context
            
        Returns:
            List of measurable learning objectives
        """
        # Create initial Bloom-aligned objectives
        initial_objectives = self._create_bloom_aligned_objectives(content, context)
        
        # Enhance for measurability
        measurable_objectives = self._enhance_objective_measurability(initial_objectives)
        
        # Add assessment methods to each objective
        final_objectives = []
        for obj in measurable_objectives:
            enhanced_obj = self._add_assessment_method(obj)
            final_objectives.append(enhanced_obj)
        
        return final_objectives
    
    def _add_assessment_method(self, objective: LearningObjective) -> LearningObjective:
        """Add suggested assessment method to make objective more measurable"""
        
        # Define assessment methods by Bloom level
        assessment_methods = {
            BloomLevel.REMEMBER: [
                "multiple choice quiz",
                "matching exercise",
                "fill-in-the-blank test",
                "definition quiz"
            ],
            BloomLevel.UNDERSTAND: [
                "short answer questions",
                "concept mapping",
                "explanation essay",
                "paraphrasing exercise"
            ],
            BloomLevel.APPLY: [
                "problem-solving tasks",
                "case study analysis",
                "practical demonstration",
                "simulation exercise"
            ],
            BloomLevel.ANALYZE: [
                "comparative analysis",
                "data interpretation",
                "component identification",
                "relationship mapping"
            ],
            BloomLevel.EVALUATE: [
                "criteria-based assessment",
                "peer review",
                "critical essay",
                "decision matrix"
            ],
            BloomLevel.CREATE: [
                "project portfolio",
                "design challenge",
                "original composition",
                "prototype development"
            ]
        }
        
        # Select appropriate assessment method
        methods = assessment_methods.get(objective.bloom_level, ["performance assessment"])
        suggested_method = methods[0]
        
        # Add assessment method to metadata (not to the objective text itself)
        # This would be used by the system to suggest assessment approaches
        enhanced_objective = LearningObjective(
            text=objective.text,
            bloom_level=objective.bloom_level,
            domain=objective.domain,
            action_verb=objective.action_verb,
            content_area=objective.content_area,
            condition=objective.condition,
            criteria=objective.criteria,
            measurable=objective.measurable,
            specific=objective.specific,
            achievable=objective.achievable,
            relevant=objective.relevant,
            time_bound=objective.time_bound
        )
        
        # Add assessment method as additional attribute
        enhanced_objective.suggested_assessment = suggested_method
        
        return enhanced_objective
    
    def _validate_objective_measurability(self, objectives: List[LearningObjective]) -> Dict[str, Any]:
        """
        Validate that objectives are sufficiently measurable and specific
        
        Args:
            objectives: List of objectives to validate
            
        Returns:
            Validation report with measurability metrics
        """
        validation_report = {
            'overall_measurability_score': 0.0,
            'objectives_analysis': [],
            'measurability_issues': [],
            'improvement_suggestions': []
        }
        
        total_measurability = 0.0
        
        for i, obj in enumerate(objectives):
            # Calculate measurability score for this objective
            measurability_score = self._calculate_objective_measurability_score(obj)
            total_measurability += measurability_score
            
            # Analyze specific issues
            issues = self._identify_measurability_issues(obj)
            
            obj_analysis = {
                'objective_number': i + 1,
                'text': obj.text,
                'measurability_score': measurability_score,
                'smart_score': obj._calculate_smart_score(),
                'issues': issues,
                'has_specific_verb': obj.action_verb in [verb for verbs in self.bloom_verbs.values() for verb in verbs],
                'has_criteria': bool(obj.criteria),
                'has_conditions': bool(obj.condition)
            }
            
            validation_report['objectives_analysis'].append(obj_analysis)
            
            # Collect issues
            if issues:
                validation_report['measurability_issues'].extend([
                    f"Objective {i+1}: {issue}" for issue in issues
                ])
        
        # Calculate overall score
        validation_report['overall_measurability_score'] = total_measurability / len(objectives) if objectives else 0.0
        
        # Generate improvement suggestions
        validation_report['improvement_suggestions'] = self._generate_measurability_suggestions(validation_report)
        
        return validation_report
    
    def _calculate_objective_measurability_score(self, objective: LearningObjective) -> float:
        """Calculate measurability score for a single objective"""
        score = 0.0
        
        # Specific action verb (0.3 points)
        if objective.action_verb in [verb for verbs in self.bloom_verbs.values() for verb in verbs]:
            score += 0.3
        
        # Has performance criteria (0.25 points)
        if objective.criteria and len(objective.criteria.strip()) > 0:
            score += 0.25
        
        # Has conditions (0.2 points)
        if objective.condition and len(objective.condition.strip()) > 0:
            score += 0.2
        
        # Specific content area (0.15 points)
        if objective.content_area and len(objective.content_area) > 3:
            vague_indicators = ['things', 'concepts', 'ideas', 'material', 'content']
            if not any(vague in objective.content_area.lower() for vague in vague_indicators):
                score += 0.15
        
        # Observable behavior (0.1 points)
        observable_verbs = [
            'define', 'identify', 'list', 'describe', 'explain', 'demonstrate',
            'apply', 'solve', 'analyze', 'compare', 'evaluate', 'create'
        ]
        if any(verb in objective.text.lower() for verb in observable_verbs):
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_measurability_suggestions(self, validation_report: Dict[str, Any]) -> List[str]:
        """Generate suggestions for improving objective measurability"""
        suggestions = []
        
        # Overall score suggestions
        overall_score = validation_report['overall_measurability_score']
        if overall_score < 0.7:
            suggestions.append("Consider revising objectives to include more specific action verbs and performance criteria")
        
        # Specific issue suggestions
        issues = validation_report['measurability_issues']
        
        if any('vague_verb' in issue for issue in issues):
            suggestions.append("Replace vague verbs (understand, know, learn) with specific, observable action verbs")
        
        if any('missing_criteria' in issue for issue in issues):
            suggestions.append("Add performance criteria (accuracy levels, quality standards, time limits) to higher-order objectives")
        
        if any('missing_conditions' in issue for issue in issues):
            suggestions.append("Specify conditions under which performance will be demonstrated (given materials, tools, scenarios)")
        
        if any('vague_content' in issue for issue in issues):
            suggestions.append("Make content areas more specific by identifying particular concepts, skills, or knowledge areas")
        
        # Analysis-based suggestions
        objectives_analysis = validation_report['objectives_analysis']
        
        # Check for missing SMART elements
        low_smart_objectives = [obj for obj in objectives_analysis if obj['smart_score'] < 0.6]
        if low_smart_objectives:
            suggestions.append(f"Improve SMART criteria compliance for {len(low_smart_objectives)} objectives")
        
        # Check for missing assessment alignment
        no_criteria_count = sum(1 for obj in objectives_analysis if not obj['has_criteria'])
        if no_criteria_count > 0:
            suggestions.append(f"Add performance criteria to {no_criteria_count} objectives to enable proper assessment")
        
        return suggestions if suggestions else ["Objectives demonstrate good measurability and specificity"]