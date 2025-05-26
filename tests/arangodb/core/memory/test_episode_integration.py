#!/usr/bin/env python3
"""
Test script for Memory Agent with Episode Management integration.
"""

import sys
import time
from datetime import datetime, timezone
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO")

# Test integration
def test_memory_agent_with_episodes():
    """Test the Memory Agent with episode management."""
    from arangodb.core.arango_setup import connect_arango, ensure_database
    from arangodb.core.memory.memory_agent import MemoryAgent
    
    try:
        # Connect to database
        print("1. Connecting to ArangoDB...")
        client = connect_arango()
        db = ensure_database(client)
        
        # Create memory agent 
        print("2. Creating Memory Agent...")
        agent = MemoryAgent(db=db)
        
        # Start a new episode
        print("3. Starting new episode...")
        episode_id = agent.start_new_episode(
            name="Product Discussion Episode",
            description="Discussing our new product features",
            metadata={"topic": "product_development"}
        )
        
        if not episode_id:
            print("Error: Failed to create episode")
            return
            
        print(f"   Created episode: {episode_id}")
        
        # Simulate conversation
        print("4. Processing conversation...")
        user_msg = "What are the key features of our new product?"
        agent_response = "Our new product features include real-time collaboration, AI-powered insights, and seamless integration."
        
        result = agent.store_conversation(
            user_message=user_msg,
            agent_response=agent_response,
            reference_time=datetime.now(timezone.utc)
        )
        
        print(f"   Stored conversation: {result['conversation_id'][:8]}...")
        
        # Verify episode information
        print("5. Checking episode status...")
        current_episode = agent.get_current_episode()
        print(f"   Current episode: {current_episode}")
        
        # Check episode contents  
        from arangodb.core.memory.episode_manager import EpisodeManager
        episode_mgr = EpisodeManager(db=db)
        
        # Get episode details
        episode_info = episode_mgr.get_episode(episode_id)
        print(f"   Episode name: {episode_info['name']}")
        
        # Check linked entities
        entities = episode_mgr.get_episode_entities(episode_id)
        relationships = episode_mgr.get_episode_relationships(episode_id)
        
        print(f"   Linked entities: {len(entities)}")
        print(f"   Linked relationships: {len(relationships)}")
        
        # End the episode
        print("6. Ending episode...")
        agent.end_current_episode()
        print(f"   Episode ended, current: {agent.get_current_episode()}")
        
        print("\n✅ Episode integration test successful!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.exception("Detailed error:")
        sys.exit(1)

if __name__ == "__main__":
    test_memory_agent_with_episodes()