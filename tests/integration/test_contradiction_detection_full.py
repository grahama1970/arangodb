"""
Full integration test for automatic contradiction detection in Memory Agent.

Tests both manual edge creation and the Memory Agent's entity extraction.
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


def test_manual_contradiction_detection():
    """Test manual contradiction detection with direct edge creation."""
    try:
        # Connect to ArangoDB
        client = ArangoClient(hosts=HOST)
        sys_db = client.db("_system", username=USERNAME, password=PASSWORD)
        
        # Create test database if needed
        if not sys_db.has_database(DATABASE_NAME):
            sys_db.create_database(DATABASE_NAME)
        
        db = client.db(DATABASE_NAME, username=USERNAME, password=PASSWORD)
        
        # Import modules
        from arangodb.core.graph.contradiction_detection import detect_temporal_contradictions, resolve_contradiction
        from arangodb.core.memory.contradiction_logger import ContradictionLogger
        
        # Create test edge collections if missing
        if not db.has_collection("agent_entities"):
            db.create_collection("agent_entities")
        if not db.has_collection("agent_relationships"):
            db.create_collection("agent_relationships", edge=True)
            
        print("Creating test entities...")
        
        # Create entities
        john_entity = {
            "name": "John",
            "type": "Person"
        }
        john_doc = db.collection("agent_entities").insert(john_entity)
        john_id = f"agent_entities/{john_doc['_key']}"
        
        techcorp_entity = {
            "name": "TechCorp", 
            "type": "Organization"
        }
        techcorp_doc = db.collection("agent_entities").insert(techcorp_entity)
        techcorp_id = f"agent_entities/{techcorp_doc['_key']}"
        
        # Create initial relationship - John works for TechCorp
        print("\nCreating initial relationship: John works for TechCorp...")
        edge1 = {
            "_from": john_id,
            "_to": techcorp_id,
            "type": "WORKS_FOR",
            "attributes": {"role": "senior engineer"},
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "valid_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "invalid_at": None
        }
        
        # Insert first edge
        edge1_result = db.collection("agent_relationships").insert(edge1)
        edge1["_key"] = edge1_result["_key"]
        print(f"Inserted first edge: {edge1_result['_key']}")
        
        # Create a CONFLICTING relationship with the SAME type and entities
        # This is what creates a contradiction
        print("\nCreating conflicting relationship: John works for TechCorp but with different role...")
        edge2 = {
            "_from": john_id,
            "_to": techcorp_id,  # Same entities
            "type": "WORKS_FOR",  # Same type
            "attributes": {"role": "manager"},  # Different attributes
            "created_at": datetime.now(timezone.utc).isoformat(),
            "valid_at": datetime.now(timezone.utc).isoformat(),
            "invalid_at": None
        }
        
        # Check for contradictions
        contradictions = detect_temporal_contradictions(
            db=db,
            edge_collection="agent_relationships",
            edge_doc=edge2
        )
        
        print(f"\nContradictions detected: {len(contradictions)}")
        
        if contradictions:
            print("✓ Contradictions detected successfully!")
            
            # Log the contradictions
            logger = ContradictionLogger(db)
            
            for i, contradiction in enumerate(contradictions):
                print(f"\nContradiction {i+1}:")
                print(f"  Existing edge: {contradiction['_key']}")
                print(f"  Type: {contradiction['type']}")
                print(f"  Attributes: {contradiction.get('attributes', {})}")
                
                # Resolve the contradiction
                resolution = resolve_contradiction(
                    db=db,
                    edge_collection="agent_relationships",
                    new_edge=edge2,
                    contradicting_edge=contradiction,
                    strategy="newest_wins",
                    resolution_reason="Test contradiction resolution"
                )
                
                print(f"  Resolution: {resolution['action']}")
                print(f"  Success: {resolution['success']}")
                print(f"  Reason: {resolution['reason']}")
                
                # Log the contradiction
                logger.log_contradiction(
                    new_edge=edge2,
                    existing_edge=contradiction,
                    resolution=resolution,
                    context="manual_test"
                )
        else:
            print("✗ No contradictions detected - this is unexpected")
            
        # Get summary
        logger = ContradictionLogger(db)
        summary = logger.get_contradiction_summary()
        
        print(f"\nContradiction Log Summary:")
        print(f"  Total: {summary['total']}")
        print(f"  Resolved: {summary['resolved']}") 
        print(f"  Failed: {summary['failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1%}")
        
        # Clean up
        sys_db.delete_database(DATABASE_NAME)
        
        return len(contradictions) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_agent_contradiction():
    """Test contradiction detection through Memory Agent's entity extraction."""
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
        from arangodb.core.memory.contradiction_logger import ContradictionLogger
        
        # Create memory agent
        agent = MemoryAgent(db=db)
        
        print("\nTesting Memory Agent contradiction detection...")
        
        # Store initial conversation about John
        print("Storing first conversation...")
        result1 = agent.store_conversation(
            user_message="John is a senior engineer at TechCorp. He has been working there for 5 years.",
            agent_response="I understand that John is a senior engineer at TechCorp with 5 years of experience."
        )
        
        # Get initial contradiction count
        logger = ContradictionLogger(db)
        summary_before = logger.get_contradiction_summary()
        print(f"Contradictions before: {summary_before['total']}")
        
        # Store conflicting conversation
        print("\nStoring conflicting conversation...")
        result2 = agent.store_conversation(
            user_message="John recently left TechCorp and joined DataInc as a manager.",
            agent_response="I've updated my records - John is now a manager at DataInc, having left TechCorp."
        )
        
        # Get contradiction count after
        summary_after = logger.get_contradiction_summary()
        print(f"Contradictions after: {summary_after['total']}")
        
        new_contradictions = summary_after['total'] - summary_before['total']
        
        if new_contradictions > 0:
            print(f"✓ Successfully detected {new_contradictions} contradictions through Memory Agent")
            
            # Show recent contradictions
            logs = logger.get_contradictions(limit=5)
            for log in logs:
                print(f"\nContradiction in context '{log['context']}':")
                print(f"  Edge type: {log['new_edge']['type']}")
                print(f"  Resolution: {log['resolution']['action']}")
                print(f"  Status: {log['status']}")
        else:
            print("✗ No contradictions detected through Memory Agent")
            
        # Clean up
        sys_db.delete_database(DATABASE_NAME)
        
        return new_contradictions > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== Testing Manual Contradiction Detection ===")
    manual_success = test_manual_contradiction_detection()
    
    print("\n\n=== Testing Memory Agent Contradiction Detection ===")
    agent_success = test_memory_agent_contradiction()
    
    overall_success = manual_success and agent_success
    
    if overall_success:
        print("\n✅ VALIDATION PASSED - All contradiction detection tests passed")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED - Some tests failed")
        if not manual_success:
            print("  - Manual contradiction detection failed")
        if not agent_success:
            print("  - Memory Agent contradiction detection failed")
        sys.exit(1)