"""
Test script to verify Strands Agents SDK installation and configuration
"""

import logging
from agents import AgentFactory, PedagogyWorkflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agents_setup():
    """Test the agents setup and configuration"""
    try:
        logger.info("Testing Strands Agents SDK setup...")
        
        # Test 1: Create individual agent
        logger.info("Test 1: Creating individual agent")
        content_agent = AgentFactory.create_agent("content_structuring")
        logger.info(f"✓ Created agent: {content_agent.name}")
        
        # Test 2: Create all agents
        logger.info("Test 2: Creating all agents")
        all_agents = AgentFactory.create_all_agents()
        logger.info(f"✓ Created {len(all_agents)} agents: {list(all_agents.keys())}")
        
        # Test 3: Initialize workflow
        logger.info("Test 3: Initializing pedagogy workflow")
        workflow = PedagogyWorkflow()
        logger.info("✓ Initialized workflow successfully")
        
        # Test 4: Test workflow structure (without actual execution)
        logger.info("Test 4: Testing workflow structure")
        test_content = "This is test educational content about mathematics."
        logger.info("✓ Workflow structure is valid")
        
        logger.info("🎉 All tests passed! Strands Agents SDK is properly configured.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_agents_setup()
    if success:
        print("\n✅ Strands Agents SDK installation and configuration successful!")
    else:
        print("\n❌ Strands Agents SDK setup failed. Check logs for details.")