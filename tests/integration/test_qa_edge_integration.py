"""
Test Q&A Edge Integration with Graph Database

This module tests the integration between Q&A generation and the graph database,
ensuring that Q&A pairs are properly converted to edge documents.
"""

import sys
import os
import json
from datetime import datetime, timezone
import pytest
from loguru import logger
import importlib.util

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from arangodb.core.db_connection_wrapper import DatabaseOperations
from arangodb.qa_generation.models import QAPair, QuestionType
from arangodb.qa_generation.edge_generator import QAEdgeGenerator
from arangodb.core.graph.relationship_extraction import EntityExtractor


def setup_test_db():
    """Set up test database connection."""
    from arango import ArangoClient
    
    # Connect to database
    client = ArangoClient(hosts="http://localhost:8529")
    db = client.db("_system", username="root", password="openSesame")
    
    # Create test collections
    if not db.has_collection("test_entities"):
        db.create_collection("test_entities")
    else:
        db.collection("test_entities").truncate()
    
    if not db.has_collection("test_relationships"):
        db.create_collection("test_relationships", edge=True)
    else:
        db.collection("test_relationships").truncate()
        
    if not db.has_collection("relationships"):
        db.create_collection("relationships", edge=True)
    else:
        db.collection("relationships").truncate()
    
    if not db.has_collection("entities"):
        db.create_collection("entities")
    else:
        db.collection("entities").truncate()
    
    # Create sample entities
    db.collection("entities").insert({
        "_key": "python",
        "name": "Python",
        "type": "TECHNOLOGY",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.95
    })
    
    db.collection("entities").insert({
        "_key": "arangodb",
        "name": "ArangoDB",
        "type": "TECHNOLOGY",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.95
    })
    
    return db


def test_entity_extractor():
    """Test standalone entity extraction."""
    entity_extractor = EntityExtractor()
    
    test_text = """
    Python is a popular programming language used in conjunction with ArangoDB.
    Graph databases like ArangoDB allow for flexible data modeling with edges and vertices.
    Google Cloud Platform and Amazon Web Services both support deploying ArangoDB.
    """
    
    entities = entity_extractor.extract_entities(test_text)
    
    # Verify entities were extracted
    assert len(entities) > 0, "No entities were extracted"
    
    # Check for specific entities
    entity_names = [e["name"].lower() for e in entities]
    assert any("python" in name for name in entity_names), "Python not found in entities"
    assert any("arangodb" in name for name in entity_names), "ArangoDB not found in entities"
    
    # Check entity types
    entity_types = [e["type"] for e in entities]
    assert "TECHNOLOGY" in entity_types, "No TECHNOLOGY entities found"


def test_qa_edge_generation():
    """Test generating edges from Q&A pairs."""
    # Check if spaCy is available
    spacy_available = importlib.util.find_spec("spacy") is not None
    if not spacy_available:
        logger.warning("Spacy not available, skipping full test")
    
    # Set up test database
    db = setup_test_db()
    db_ops = DatabaseOperations(db)
    
    # Create edge generator
    edge_generator = QAEdgeGenerator(db_ops)
    
    # Create test Q&A pair
    qa_pair = QAPair(
        question="How does Python integrate with ArangoDB?",
        answer="Python integrates with ArangoDB using the python-arango driver, which provides a Python interface to the ArangoDB REST API.",
        thinking="I need to explain the Python driver for ArangoDB and how it relates to the REST API.",
        question_type=QuestionType.RELATIONSHIP,
        confidence=0.95,
        validation_score=0.9,
        source_section="test_section_123",
        source_hash="abc123hash456",
        temperature_used=0.2
    )
    
    # Create test source document with hierarchical structure
    source_doc = {
        "_id": "test_docs/python_arango_123",
        "title": "Python ArangoDB Integration Guide",
        "content": "This guide explains how to use Python with ArangoDB...",
        "valid_at": datetime.now(timezone.utc).isoformat(),
        "section_title": "Python Driver API",
        "parent_id": "test_docs/python_arango_main",
        "parent_title": "ArangoDB Python Integration",
        "section_path": "/docs/python/driver/api",
        "level": 2,
        "heading_level": 3
    }
    
    # Generate edges
    edges = edge_generator.create_qa_edges(qa_pair, source_doc, batch_id="test_batch_001")
    
    # Verify edges were created
    assert len(edges) > 0, "No edges were created from Q&A pair"
    
    # Verify edge properties
    edge = edges[0]
    assert edge["type"] == "qa_derived", "Incorrect edge type"
    assert "question" in edge, "Edge missing question field"
    assert "answer" in edge, "Edge missing answer field"
    assert "confidence" in edge, "Edge missing confidence field"
    assert "rationale" in edge, "Edge missing rationale field"
    assert edge["confidence"] > 0.5, "Edge confidence too low"
    assert "valid_at" in edge, "Edge missing temporal metadata"
    
    # Verify review status
    assert "review_status" in edge, "Edge missing review status"
    
    # Verify new context fields
    assert "context_confidence" in edge, "Edge missing context confidence"
    assert "context_rationale" in edge, "Edge missing context rationale"
    assert len(edge["context_rationale"]) >= 50, "Context rationale too short"
    
    # Verify hierarchical context
    assert "hierarchical_context" in edge, "Edge missing hierarchical context"
    hierarchy = edge["hierarchical_context"]
    assert "document_title" in hierarchy, "Hierarchical context missing document title"
    assert "section_title" in hierarchy, "Hierarchical context missing section title"
    assert "path" in hierarchy, "Hierarchical context missing path"
    assert hierarchy["level"] == 2, "Incorrect hierarchy level"
    
    # Clean up test data
    try:
        db.collection("test_relationships").truncate()
        db.collection("test_entities").truncate()
    except Exception as e:
        logger.warning(f"Error cleaning up test data: {e}")


def test_qa_edge_integration_end_to_end():
    """Test full end-to-end integration of Q&A edges with graph database."""
    # This would include:
    # 1. Generating Q&A pairs from a document
    # 2. Creating entities and edges from those pairs
    # 3. Querying the graph to verify integration
    # 4. Testing the view integration
    # Placeholder for now, to be implemented when more components are ready
    pass


if __name__ == "__main__":
    """Run tests directly."""
    # Setup logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Track failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Entity Extraction
    total_tests += 1
    try:
        test_entity_extractor()
        logger.info("Entity extraction test passed")
    except Exception as e:
        all_validation_failures.append(f"Entity extraction test failed: {e}")
    
    # Test 2: Q&A Edge Generation
    total_tests += 1
    try:
        test_qa_edge_generation()
        logger.info("Q&A edge generation test passed")
    except Exception as e:
        all_validation_failures.append(f"Q&A edge generation test failed: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Q&A edge integration is functional and ready for use")
        sys.exit(0)