"""
Integration test for automatic contradiction detection in Memory Agent.

Tests that the Memory Agent properly detects and resolves contradictions
when storing conversations that contain conflicting information.
"""

import sys
import json
from datetime import datetime, timezone, timedelta
from arango import ArangoClient

# Configure test database
HOST = "http://localhost:8529"
USERNAME = "root"
PASSWORD = "openSesame"
DATABASE_NAME = "agent_memory_test"


def test_contradiction_detection():
    """Test automatic contradiction detection during conversation storage."""
    try:
        # Connect to ArangoDB
        client = ArangoClient(hosts=HOST)
        sys_db = client.db("_system", username=USERNAME, password=PASSWORD)
        
        # Create test database if needed
        if not sys_db.has_database(DATABASE_NAME):
            sys_db.create_database(DATABASE_NAME)
        
        db = client.db(DATABASE_NAME, username=USERNAME, password=PASSWORD)
        
        # Import MemoryAgent
        from arangodb.core.memory.memory_agent import MemoryAgent
        
        # Create memory agent
        agent = MemoryAgent(db=db)
        
        # Test 1: Store initial conversation with relationships
        result1 = agent.store_conversation(
            user_message="John works for TechCorp as a senior engineer",
            agent_response="I understand that John is a senior engineer at TechCorp"
        )
        
        print(f"Stored first conversation: {result1['conversation_id']}")
        
        # Get contradiction summary before
        summary_before = agent.contradiction_logger.get_contradiction_summary()
        print(f"Contradictions before: {summary_before['total']}")
        
        # Test 2: Store conflicting information (should trigger contradiction detection)
        result2 = agent.store_conversation(
            user_message="Actually, John works for DataInc as a manager now",
            agent_response="I've updated my understanding - John is now a manager at DataInc"
        )
        
        print(f"Stored second conversation: {result2['conversation_id']}")
        
        # Get contradiction summary after
        summary_after = agent.contradiction_logger.get_contradiction_summary()
        print(f"Contradictions after: {summary_after['total']}")
        
        # Check that contradictions were detected
        new_contradictions = summary_after['total'] - summary_before['total']
        
        if new_contradictions > 0:
            print(f"✓ Successfully detected {new_contradictions} contradictions")
            
            # Get the contradiction logs
            logs = agent.contradiction_logger.get_contradictions(limit=10)
            
            for log in logs:
                print(f"\nContradiction detected:")
                print(f"  Edge type: {log['new_edge']['type']}")
                print(f"  Resolution: {log['resolution']['action']} ({log['resolution']['strategy']})")
                print(f"  Status: {log['status']}")
                print(f"  Context: {log['context']}")
        else:
            print("✗ No contradictions detected - this may be an error")
            return False
        
        # Test 3: Query to verify the latest information is being returned
        from arangodb.core.db_operations import get_entity_info
        
        # Get entity with name 'John'
        aql = f"""
        FOR e IN agent_entities
        FILTER e.name == "John"
        RETURN e
        """
        cursor = db.aql.execute(aql)
        john_entities = list(cursor)
        
        if john_entities:
            john = john_entities[0]
            print(f"\nJohn entity found: {john['_id']}")
            
            # Get current relationships for John
            aql = f"""
            FOR v, e IN 1..1 OUTBOUND @entity_id agent_relationships
            FILTER e.type == "WORKS_FOR"
            FILTER e.invalid_at == null
            RETURN {{edge: e, target: v}}
            """
            cursor = db.aql.execute(aql, bind_vars={"entity_id": john['_id']})
            current_relationships = list(cursor)
            
            print(f"Current relationships: {len(current_relationships)}")
            for rel in current_relationships:
                target_name = rel['target'].get('name', 'unknown')
                print(f"  - Works for: {target_name}")
        
        # Verify the contradiction was resolved correctly
        resolved_count = len([log for log in logs if log['status'] == 'resolved'])
        print(f"\nResolution success rate: {resolved_count}/{len(logs)}")
        
        # Clean up
        sys_db.delete_database(DATABASE_NAME)
        
        return new_contradictions > 0 and resolved_count == len(logs)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_contradiction_detection()
    
    if success:
        print("\n✅ VALIDATION PASSED - Contradiction detection working correctly")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED - Contradiction detection not working")
        sys.exit(1)