"""
Agent Factory for creating educational content generation agents
"""

from typing import Dict, Any
from .base_agent import BaseEducationalAgent
from .content_structuring_agent import EnhancedContentStructuringAgent
from .learning_objectives_agent import EnhancedLearningObjectivesAgent
from config.agents_config import PEDAGOGY_AGENTS
import logging

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory class for creating educational agents"""
    
    @staticmethod
    def create_agent(agent_type: str, **kwargs) -> BaseEducationalAgent:
        """
        Create an educational agent of the specified type
        
        Args:
            agent_type: Type of agent to create
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured educational agent instance
        """
        if agent_type not in PEDAGOGY_AGENTS:
            raise ValueError(f"Unknown agent type: {agent_type}. Available types: {list(PEDAGOGY_AGENTS.keys())}")
        
        logger.info(f"Creating {agent_type} agent")
        
        # Use enhanced agents for specific types
        if agent_type == "content_structuring":
            return EnhancedContentStructuringAgent(**kwargs)
        elif agent_type == "learning_objectives":
            return EnhancedLearningObjectivesAgent(**kwargs)
        else:
            # Use base agent for other types
            return BaseEducationalAgent(agent_type, **kwargs)
    
    @staticmethod
    def create_all_agents(**kwargs) -> Dict[str, BaseEducationalAgent]:
        """
        Create all pedagogy agents
        
        Args:
            **kwargs: Additional configuration parameters for all agents
            
        Returns:
            Dictionary mapping agent types to agent instances
        """
        agents = {}
        
        for agent_type in PEDAGOGY_AGENTS.keys():
            try:
                agents[agent_type] = AgentFactory.create_agent(agent_type, **kwargs)
                logger.info(f"Successfully created {agent_type} agent")
            except Exception as e:
                logger.error(f"Failed to create {agent_type} agent: {str(e)}")
                raise
        
        logger.info(f"Created {len(agents)} pedagogy agents")
        return agents
    
    @staticmethod
    def get_available_agent_types() -> list:
        """Get list of available agent types"""
        return list(PEDAGOGY_AGENTS.keys())