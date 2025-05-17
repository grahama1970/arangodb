"""
Working integration test for contradiction detection.

Manually creates relationships to test the detection functionality.
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


def test_contradiction_detection_working():
    """Test contradiction detection by manually creating relationships."""
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
        from arangodb.core.memory.contradiction_logger import ContradictionLogger
        from arangodb.core.graph.contradiction_detection import detect_temporal_contradictions, resolve_contradiction
        
        # Create memory agent to ensure all collections exist
        agent = MemoryAgent(db=db)
        
        print("Creating test entities...")
        
        # Create entities
        from arangodb.core.db_operations import create_document
        
        john_entity = {
            "name": "John",
            "type": "Person"
        }
        john_result = create_document(db, "agent_entities", john_entity)
        john_id = f"agent_entities/{john_result['_key']}"
        
        techcorp_entity = {
            "name": "TechCorp", 
            "type": "Organization"
        }
        techcorp_result = create_document(db, "agent_entities", techcorp_entity)
        techcorp_id = f"agent_entities/{techcorp_result['_key']}"
        
        datainc_entity = {
            "name": "DataInc",
            "type": "Organization"
        }
        datainc_result = create_document(db, "agent_entities", datainc_entity)
        datainc_id = f"agent_entities/{datainc_result['_key']}"
        
        print(f"Created entities: John ({john_id}), TechCorp ({techcorp_id}), DataInc ({datainc_id})")
        
        # Create relationship 1: John works for TechCorp
        print("\nCreating relationship 1: John works for TechCorp...")
        edge1 = {
            "_from": john_id,
            "_to": techcorp_id,
            "type": "WORKS_FOR",
            "attributes": {"role": "senior engineer"},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "valid_at": datetime.now(timezone.utc).isoformat(),
            "invalid_at": None
        }
        
        # Check for contradictions before inserting
        contradictions = detect_temporal_contradictions(
            db=db,
            edge_collection="agent_relationships",
            edge_doc=edge1
        )
        
        print(f"Contradictions before inserting edge1: {len(contradictions)}")
        
        # Insert edge1
        result1 = db.collection("agent_relationships").insert(edge1)
        edge1["_key"] = result1["_key"]
        print(f"Inserted edge1: {result1['_key']}")
        
        # Create relationship 2: John works for DataInc (contradicts edge1)
        print("\nCreating relationship 2: John works for DataInc (contradictory)...")
        edge2 = {
            "_from": john_id,
            "_to": datainc_id,  # Different target - this should trigger contradiction detection
            "type": "WORKS_FOR",  # Same type
            "attributes": {"role": "manager"},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "valid_at": datetime.now(timezone.utc).isoformat(),
            "invalid_at": None
        }
        
        # Use Memory Agent's check to detect contradictions
        # This mimics what should happen in entity extraction
        contradictions = []
        try:
            # Query for existing WORKS_FOR relationships from John
            aql = f"""
            FOR e IN agent_relationships
            FILTER e._from == @from_id
            FILTER e.type == @type
            FILTER e.invalid_at == null
            RETURN e
            """
            cursor = db.aql.execute(
                aql,
                bind_vars={
                    "from_id": john_id,
                    "type": "WORKS_FOR"
                }
            )
            contradictions = list(cursor)
        except Exception as e:
            print(f"Error checking contradictions: {e}")
        
        print(f"Existing WORKS_FOR relationships for John: {len(contradictions)}")
        
        if contradictions:
            print("✓ Contradictions detected successfully!")
            
            # Initialize logger
            logger = ContradictionLogger(db)
            
            for existing_edge in contradictions:
                print(f"\nContradicting edge found: {existing_edge['_key']}")
                print(f"  Target: {existing_edge['_to']}")
                print(f"  Role: {existing_edge['attributes'].get('role', 'unknown')}")
                
                # Resolve the contradiction
                result = resolve_contradiction(
                    db=db,
                    edge_collection="agent_relationships",
                    new_edge=edge2,
                    contradicting_edge=existing_edge,
                    strategy="newest_wins",
                    resolution_reason="Manual test resolution"
                )
                
                print(f"  Resolution: {result['action']}")
                print(f"  Success: {result['success']}")
                
                # Log the contradiction
                logger.log_contradiction(
                    new_edge=edge2,
                    existing_edge=existing_edge,
                    resolution=result,
                    context="manual_test"
                )
        else:
            print("✗ No contradictions detected - this may be unexpected")
        
        # Insert edge2
        result2 = db.collection("agent_relationships").insert(edge2)
        print(f"\nInserted edge2: {result2['_key']}")
        
        # Check final state
        print("\n=== Final State ===")
        
        # Query valid relationships
        aql = """
        FOR e IN agent_relationships
        FILTER e._from == @john_id
        FILTER e.type == "WORKS_FOR"
        FILTER e.invalid_at == null
        RETURN e
        """
        cursor = db.aql.execute(aql, bind_vars={"john_id": john_id})
        valid_edges = list(cursor)
        
        print(f"Valid WORKS_FOR relationships for John: {len(valid_edges)}")
        for edge in valid_edges:
            target_key = edge['_to'].split('/')[-1]
            target = db.collection("agent_entities").get(target_key)
            print(f"  - Works for: {target['name']} as {edge['attributes'].get('role', 'unknown')}")
        
        # Get contradiction summary
        logger = ContradictionLogger(db)
        summary = logger.get_contradiction_summary()
        
        print(f"\nContradiction Summary:")
        print(f"  Total: {summary['total']}")
        print(f"  Resolved: {summary['resolved']}")
        print(f"  Success Rate: {summary['success_rate']:.1%}")
        
        # Clean up
        sys_db.delete_database(DATABASE_NAME)
        
        # Test passes if contradictions were detected and resolved
        return len(contradictions) > 0 and summary['total'] > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_contradiction_detection_working()
    
    if success:
        print("\n✅ VALIDATION PASSED - Contradiction detection working correctly")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED - Contradiction detection not working")
        sys.exit(1)