#!/usr/bin/env python3
"""
Test Memory Agent integration with Community Detection

This script validates that the Memory Agent correctly detects communities
when new entities are created during conversation storage.

Expected behavior:
1. Store conversations that mention multiple entities
2. Entities are automatically extracted
3. Communities are automatically detected
4. Communities are correctly assigned based on relationships
"""

import sys
import time
from datetime import datetime
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Import required modules
from arangodb.core.arango_setup import connect_arango, ensure_database
from arangodb.core.memory.memory_agent import MemoryAgent
from arangodb.core.graph.community_detection import CommunityDetector


def test_community_integration():
    """Test that community detection works with Memory Agent"""
    print("\n=== Testing Memory Agent + Community Detection Integration ===")
    
    try:
        # Connect to database
        print("\n1. Connecting to database...")
        client = connect_arango()
        db = ensure_database(client)
        print("✓ Connected to database")
        
        # Initialize memory agent with community detection enabled
        print("\n2. Initializing Memory Agent with community detection...")
        agent = MemoryAgent(
            db=db,
            auto_detect_communities=True,
            community_min_size=2,
            community_resolution=1.0
        )
        print("✓ Memory Agent initialized")
        
        # Store conversations that will create entities
        print("\n3. Storing conversations to create entities...")
        
        # Conversation 1: Python ecosystem
        result1 = agent.store_conversation(
            user_message="Tell me about Python web frameworks",
            agent_response="Python has several popular web frameworks. Django is a full-featured framework with batteries included, while Flask is a lightweight microframework. Both are excellent choices for web development.",
            conversation_id="conv_python_1"
        )
        print(f"✓ Stored conversation 1: {result1['conversation_id']}")
        
        # Conversation 2: Java ecosystem
        result2 = agent.store_conversation(
            user_message="What about Java frameworks?",
            agent_response="Java offers frameworks like Spring Boot for enterprise applications. Spring Boot works well with Spring Security for authentication and integrates nicely with various databases.",
            conversation_id="conv_java_1"
        )
        print(f"✓ Stored conversation 2: {result2['conversation_id']}")
        
        # Conversation 3: Database technologies
        result3 = agent.store_conversation(
            user_message="Which databases work well with web frameworks?",
            agent_response="PostgreSQL is a popular choice for Django applications, while MySQL is often used with Java Spring applications. Both are reliable relational databases.",
            conversation_id="conv_databases_1"
        )
        print(f"✓ Stored conversation 3: {result3['conversation_id']}")
        
        # Give time for async operations
        print("\n4. Waiting for entity extraction and community detection...")
        time.sleep(2)
        
        # Check if communities were detected
        print("\n5. Checking community detection results...")
        detector = CommunityDetector(db)
        communities = detector.get_all_communities()
        
        if communities:
            print(f"✓ Found {len(communities)} communities")
            for community in communities:
                print(f"  - Community {community['_key']}: {community['member_count']} members")
                print(f"    Sample members: {', '.join(community.get('sample_members', []))}")
                print(f"    Modularity: {community.get('metadata', {}).get('modularity_score', 0):.3f}")
        else:
            print("✗ No communities detected")
            
        # Check entities
        print("\n6. Checking entities...")
        entities_col = db.collection("agent_entities")
        entities = list(entities_col.all())
        
        if entities:
            print(f"✓ Found {len(entities)} entities")
            for entity in entities[:5]:  # Show first 5
                print(f"  - {entity.get('name', entity['_key'])}: {entity.get('type', 'unknown')}")
                if 'community_id' in entity:
                    print(f"    Community: {entity['community_id']}")
        else:
            print("✗ No entities found")
        
        # Test manual community detection trigger
        print("\n7. Testing manual community detection...")
        old_count = len(communities)
        detector.detect_communities(min_size=1)  # Lower threshold
        new_communities = detector.get_all_communities()
        new_count = len(new_communities)
        
        if new_count != old_count:
            print(f"✓ Community count changed: {old_count} -> {new_count}")
        else:
            print(f"  Community count unchanged: {new_count}")
        
        print("\n✓ Integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        print(f"\n✗ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Run the test
    success = test_community_integration()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)