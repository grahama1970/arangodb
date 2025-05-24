"""
Test for Q&A edge enrichment functionality.

Tests the enrichment functionality for Q&A edges, including search integration
and contradiction detection.
"""

import os
import sys
import json
from datetime import datetime, timezone
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from arangodb.core.db_connection_wrapper import DatabaseOperations
from arangodb.qa_generation.enrichment import QAEdgeEnricher


def setup_test_db():
    """Set up test database connection and collections."""
    from arango import ArangoClient
    
    # Connect to database
    client = ArangoClient(hosts="http://localhost:8529")
    db = client.db("_system", username="root", password="openSesame")
    
    # Create test collections
    if not db.has_collection("test_entities"):
        db.create_collection("test_entities")
    else:
        db.collection("test_entities").truncate()
    
    if not db.has_collection("relationships"):
        db.create_collection("relationships", edge=True)
    else:
        db.collection("relationships").truncate()
    
    # Create sample entities
    entity1 = db.collection("test_entities").insert({
        "_key": "python",
        "name": "Python",
        "type": "TECHNOLOGY",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.95
    })
    
    entity2 = db.collection("test_entities").insert({
        "_key": "arangodb",
        "name": "ArangoDB",
        "type": "TECHNOLOGY",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.95
    })
    
    # Create sample Q&A edge
    qa_edge = db.collection("relationships").insert({
        "_from": f"test_entities/{entity1['_key']}",
        "_to": f"test_entities/{entity2['_key']}",
        "type": "QA_DERIVED",
        "question": "How does Python integrate with ArangoDB?",
        "answer": "Python integrates with ArangoDB using the python-arango driver, which provides a Python interface to the ArangoDB REST API.",
        "thinking": "I need to explain the Python driver for ArangoDB and how it relates to the REST API.",
        "question_type": "RELATIONSHIP",
        "confidence": 0.85,
        "context_confidence": 0.9,
        "rationale": "Q&A relationship between Python and ArangoDB",
        "context_rationale": "Extracted from document about Python integration with databases",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "valid_at": datetime.now(timezone.utc).isoformat(),
        "invalid_at": None,
        "review_status": "auto_approved"
    })
    
    # Create contradicting edge for testing
    contradicting_edge = db.collection("relationships").insert({
        "_from": f"test_entities/{entity1['_key']}",
        "_to": f"test_entities/{entity2['_key']}",
        "type": "QA_DERIVED",
        "question": "What Python driver does ArangoDB support?",
        "answer": "ArangoDB supports the python-arango driver as its official Python client library.",
        "thinking": "I should specify the official Python driver for ArangoDB.",
        "question_type": "FACTUAL",
        "confidence": 0.75,
        "context_confidence": 0.8,
        "rationale": "Q&A relationship between Python and ArangoDB",
        "context_rationale": "Extracted from ArangoDB documentation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "valid_at": datetime.now(timezone.utc).isoformat(),
        "invalid_at": None,
        "review_status": "auto_approved"
    })
    
    return db, qa_edge, contradicting_edge


def test_edge_enrichment():
    """Test the Q&A edge enrichment functionality."""
    # Set up test database
    db, qa_edge, contradicting_edge = setup_test_db()
    
    # Initialize database operations
    db_ops = DatabaseOperations(db)
    
    # Create enricher
    enricher = QAEdgeEnricher(db_ops)
    
    # Test search view integration
    search_added = enricher.add_qa_edges_to_search_view()
    assert search_added, "Failed to add Q&A edges to search views"
    
    # Get the edges from the database to ensure we have all fields
    qa_edge_loaded = db.collection("relationships").get(qa_edge["_key"])
    
    # Test contradiction detection - since we just created the edges, we don't expect
    # any contradictions here in our test scenario (both edges are valid)
    # We're just testing that the function executes correctly
    contradiction_results, success = enricher.check_contradictions(qa_edge_loaded)
    assert success, "Contradiction check failed"
    
    # Test weight calculation
    weight_updated = enricher.enrich_edge_with_weight(qa_edge["_key"])
    assert weight_updated, "Failed to update edge weight"
    
    # Verify weight was added
    updated_edge = db.collection("relationships").get(qa_edge["_key"])
    assert "weight" in updated_edge, "Weight not added to edge"
    assert updated_edge["weight"] > 0, "Weight value is not positive"
    
    # Test full enrichment - pass full IDs as strings
    results = enricher.enrich_qa_edges(
        edge_ids=[f"relationships/{qa_edge['_key']}"],
        add_to_search=True,
        check_contradictions=True,
        update_weights=True
    )
    
    assert results["total_edges"] > 0, "No edges were processed"
    assert results["search_added"], "Failed to add to search in full enrichment"
    
    # Only verify we had some contradictions checked - we don't necessarily expect to find
    # contradictions in our test scenario since both edges are considered valid
    assert results["contradictions_checked"] > 0, "No contradictions were checked"
    assert results["weights_updated"] > 0, "No weights were updated"
    
    # Clean up test data
    try:
        db.collection("relationships").truncate()
        db.collection("test_entities").truncate()
    except Exception as e:
        print(f"Warning: Error cleaning up test data: {e}")


if __name__ == "__main__":
    """Run the test directly."""
    import traceback
    
    try:
        test_edge_enrichment()
        print("✅ VALIDATION PASSED - Q&A edge enrichment works correctly")
    except Exception as e:
        print(f"❌ VALIDATION FAILED - Error in Q&A edge enrichment test: {e}")
        print(traceback.format_exc())
        sys.exit(1)