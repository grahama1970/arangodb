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
        
        # Create test edge collections if missing
        if not db.has_collection("agent_relationships"):
            db.create_collection("agent_relationships", edge=True)
            
        # First, let's manually create entities and relationships to test contradiction detection
        print("Creating test entities and relationships...")
        
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
        
        datainc_entity = {
            "name": "DataInc",
            "type": "Organization"
        }
        datainc_doc = db.collection("agent_entities").insert(datainc_entity)
        datainc_id = f"agent_entities/{datainc_doc['_key']}"
        
        # Create initial relationship
        print("Creating initial relationship: John works for TechCorp...")
        edge1 = {
            "_from": john_id,
            "_to": techcorp_id,
            "type": "WORKS_FOR",
            "attributes": {"role": "senior engineer"},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "valid_at": datetime.now(timezone.utc).isoformat(),
            "invalid_at": None
        }
        
        # Use the contradiction detection module
        from arangodb.core.graph.contradiction_detection import detect_temporal_contradictions, resolve_contradiction
        
        # Check for contradictions before inserting
        contradictions = detect_temporal_contradictions(
            db=db,
            edge_collection="agent_relationships",
            edge_doc=edge1
        )
        
        print(f"Contradictions before inserting first edge: {len(contradictions)}")
        
        # Insert first edge
        edge1_result = db.collection("agent_relationships").insert(edge1)
        print(f"Inserted first edge: {edge1_result['_key']}")
        
        # Create conflicting relationship
        print("\nCreating conflicting relationship: John works for DataInc...")
        edge2 = {
            "_from": john_id,
            "_to": datainc_id,
            "type": "WORKS_FOR",
            "attributes": {"role": "manager"},
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
        
        print(f"Contradictions detected: {len(contradictions)}")
        
        if contradictions:
            print("\n✓ Contradictions detected successfully!")
            
            for i, contradiction in enumerate(contradictions):
                print(f"\nContradiction {i+1}:")
                print(f"  Existing edge: {contradiction['_key']}")
                print(f"  Type: {contradiction['type']}")
                print(f"  From: {contradiction['_from']} To: {contradiction['_to']}")
                
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
                from arangodb.core.memory.contradiction_logger import ContradictionLogger
                logger = ContradictionLogger(db)
                logger.log_contradiction(
                    new_edge=edge2,
                    existing_edge=contradiction,
                    resolution=resolution,
                    context="test_contradiction_detection"
                )
        else:
            print("\n✗ No contradictions detected - check configuration")
            
        # Insert second edge
        edge2_result = db.collection("agent_relationships").insert(edge2)
        print(f"\nInserted second edge: {edge2_result['_key']}")
        
        # Query the contradiction log
        logger = ContradictionLogger(db)
        summary = logger.get_contradiction_summary()
        
        print(f"\nContradiction Log Summary:")
        print(f"  Total: {summary['total']}")
        print(f"  Resolved: {summary['resolved']}") 
        print(f"  Failed: {summary['failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1%}")
        
        # Verify the latest state
        print("\nCurrent valid relationships for John:")
        aql = """
        FOR e IN agent_relationships
        FILTER e._from == @john_id
        FILTER e.type == "WORKS_FOR"
        FILTER e.invalid_at == null
        RETURN e
        """
        cursor = db.aql.execute(aql, bind_vars={"john_id": john_id})
        current_edges = list(cursor)
        
        for edge in current_edges:
            to_entity = db.collection("agent_entities").get(edge['_to'].split('/')[-1])
            print(f"  - Works for: {to_entity['name']} as {edge['attributes'].get('role', 'unknown')}")
        
        # Clean up
        sys_db.delete_database(DATABASE_NAME)
        
        success = len(contradictions) > 0 and summary['total'] > 0
        return success
        
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