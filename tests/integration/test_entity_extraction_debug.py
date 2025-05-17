"""
Debug test for entity extraction in Memory Agent.

Checks why relationships are not being created from conversations.
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


def test_entity_extraction():
    """Test entity extraction to see why relationships aren't being created."""
    try:
        # Connect to ArangoDB
        client = ArangoClient(hosts=HOST)
        sys_db = client.db("_system", username=USERNAME, password=PASSWORD)
        
        # Create test database if needed
        if not sys_db.has_database(DATABASE_NAME):
            sys_db.create_database(DATABASE_NAME)
        
        db = client.db(DATABASE_NAME, username=USERNAME, password=PASSWORD)
        
        # Import modules
        from arangodb.core.memory.memory_agent import MemoryAgent
        
        # Create memory agent
        agent = MemoryAgent(db=db)
        
        # Test text for entity extraction
        test_text = "John works for TechCorp as a senior engineer. He has been there for 5 years."
        
        print("Testing entity extraction directly...")
        
        # Try to call the internal extraction method
        memory_key = "test_memory"
        reference_time = datetime.now(timezone.utc)
        
        # Store a conversation to trigger extraction
        print("\nStoring conversation to trigger entity extraction...")
        result = agent.store_conversation(
            user_message=test_text,
            agent_response="I understand John is a senior engineer at TechCorp."
        )
        
        print(f"Conversation stored: {result['conversation_id']}")
        
        # Query to see what entities were created
        print("\nQuerying entities created...")
        aql = """
        FOR e IN agent_entities
        RETURN e
        """
        cursor = db.aql.execute(aql)
        entities = list(cursor)
        
        print(f"Total entities: {len(entities)}")
        for entity in entities:
            print(f"  - {entity['name']} ({entity['type']})")
        
        # Query to see what relationships were created
        print("\nQuerying relationships created...")
        aql = """
        FOR r IN agent_relationships
        RETURN r
        """
        cursor = db.aql.execute(aql)
        relationships = list(cursor)
        
        print(f"Total relationships: {len(relationships)}")
        for rel in relationships:
            print(f"  - Type: {rel['type']}")
            print(f"    From: {rel['_from']}")
            print(f"    To: {rel['_to']}")
            if 'attributes' in rel:
                print(f"    Attributes: {rel['attributes']}")
        
        # Check the memory agent's extraction log
        print("\nChecking extraction errors...")
        aql = """
        FOR m IN agent_memories
        RETURN m
        """
        cursor = db.aql.execute(aql)
        memories = list(cursor)
        
        print(f"Total memories: {len(memories)}")
        
        # Also test direct extraction if possible
        try:
            print("\nTesting direct extraction method...")
            # Create a mock memory doc
            mock_memory = {
                "_key": "test_key",
                "content": test_text
            }
            
            # Try calling the extraction method directly (may fail if it's private)
            entity_keys, rel_keys = agent._extract_and_store_entities(
                test_text, "test_key", reference_time
            )
            
            print(f"Direct extraction - Entities: {len(entity_keys)}, Relationships: {len(rel_keys)}")
            
        except Exception as e:
            print(f"Direct extraction failed: {e}")
        
        # Clean up
        sys_db.delete_database(DATABASE_NAME)
        
        # Success if at least entities were created
        return len(entities) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_entity_extraction()
    
    if success:
        print("\n✅ Entity extraction test passed")
        sys.exit(0)
    else:
        print("\n❌ Entity extraction test failed")
        sys.exit(1)