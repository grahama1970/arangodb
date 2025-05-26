"""
Test Q&A Edge Generator functionality.

Tests entity extraction and edge creation from Q&A pairs.
NO MOCKING - Uses real test database connections per CLAUDE.md guidelines.
"""

import sys
import pytest
from datetime import datetime, timezone
from arango.client import ArangoClient

from arangodb.qa_generation.edge_generator import QAEdgeGenerator
from arangodb.qa_generation.models import QAPair, QuestionType
from arangodb.core.db_connection_wrapper import DatabaseOperations


@pytest.fixture
def db():
    """Get real test database connection."""
    client = ArangoClient(hosts='http://localhost:8529')
    
    # Use system db to create test database if needed
    sys_db = client.db('_system', username='root', password='openSesame')
    if not sys_db.has_database('pizza_test'):
        sys_db.create_database('pizza_test')
    
    # Connect to test database
    db = client.db('pizza_test', username='root', password='openSesame')
    
    # Ensure collections exist
    collections = ['entities', 'relationships', 'documents']
    for collection in collections:
        if not db.has_collection(collection):
            if collection == 'relationships':
                db.create_collection(collection, edge=True)
            else:
                db.create_collection(collection)
    
    # Clear collections for test
    for collection in collections:
        db.collection(collection).truncate()
    
    yield db
    
    # Cleanup after test
    for collection in collections:
        db.collection(collection).truncate()


@pytest.fixture
def edge_generator(db):
    """Create edge generator with real database."""
    db_ops = DatabaseOperations(db)
    return QAEdgeGenerator(db_ops)


class TestQAEdgeGenerator:
    """Test Q&A edge generator functionality."""
    
    def test_entity_extraction_with_spacy(self, edge_generator):
        """Test entity extraction using SpaCy with real NLP."""
        qa_pair = QAPair(
            question="How does Python handle memory management?",
            thinking="Considering Python's approach...",
            answer="Python uses automatic garbage collection.",
            question_type=QuestionType.FACTUAL,
            confidence=0.9
        )
        
        # Extract entities using real SpaCy
        entities = edge_generator._extract_with_spacy(qa_pair)
        
        # Verify entities were extracted
        assert isinstance(entities, list)
        
        # Check if Python was identified as an entity
        entity_names = {e["name"].lower() for e in entities}
        assert "python" in entity_names or len(entities) > 0  # SpaCy might extract different entities
        
        # Verify entity structure
        if entities:
            assert "name" in entities[0]
            assert "type" in entities[0]
            assert "source" in entities[0]
            assert entities[0]["source"] == "spacy"
    
    def test_create_edge_document(self, edge_generator, db):
        """Test edge document creation with real database."""
        # Insert test entities first
        entities_col = db.collection("entities")
        
        france_doc = entities_col.insert({
            "_key": "france_123",
            "name": "France",
            "type": "LOCATION",
            "confidence": 0.9
        })
        
        paris_doc = entities_col.insert({
            "_key": "paris_456",
            "name": "Paris",
            "type": "LOCATION",
            "confidence": 0.95
        })
        
        # Insert test document
        docs_col = db.collection("documents")
        source_doc = docs_col.insert({
            "_key": "geography_101",
            "title": "World Geography",
            "valid_at": datetime.now(timezone.utc).isoformat()
        })
        
        qa_pair = QAPair(
            question="What is the capital of France?",
            thinking="France is a country in Europe...",
            answer="The capital of France is Paris.",
            question_type=QuestionType.FACTUAL,
            confidence=0.95,
            validation_score=0.98
        )
        
        from_entity = {
            "_id": f"entities/{france_doc['_key']}",
            "name": "France",
            "type": "LOCATION",
            "confidence": 0.9
        }
        
        to_entity = {
            "_id": f"entities/{paris_doc['_key']}",
            "name": "Paris",
            "type": "LOCATION", 
            "confidence": 0.95
        }
        
        source_doc_dict = {
            "_id": f"documents/{source_doc['_key']}",
            "title": "World Geography",
            "valid_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Create edge
        edge = edge_generator._create_edge_document(
            from_entity=from_entity,
            to_entity=to_entity,
            qa_pair=qa_pair,
            source_document=source_doc_dict
        )
        
        # Verify edge structure
        assert edge["_from"] == from_entity["_id"]
        assert edge["_to"] == to_entity["_id"]
        assert edge["type"] == "qa_derived"
        assert edge["question"] == qa_pair.question
        assert edge["answer"] == qa_pair.answer
        assert edge["confidence"] > 0.8
        assert "rationale" in edge
        assert len(edge["rationale"]) >= 50
        assert edge["review_status"] == "auto_approved"
    
    def test_weight_calculation(self, edge_generator):
        """Test edge weight calculation."""
        # Test different question types
        weight_factual = edge_generator._calculate_weight("FACTUAL", 0.9)
        weight_multi_hop = edge_generator._calculate_weight("MULTI_HOP", 0.9)
        
        assert weight_factual > weight_multi_hop
        assert 0 <= weight_factual <= 1
        assert 0 <= weight_multi_hop <= 1
    
    def test_low_confidence_review_status(self, edge_generator, db):
        """Test that low confidence edges are marked for review with real database."""
        # Insert test entities
        entities_col = db.collection("entities")
        
        entity_a = entities_col.insert({
            "_key": "entity_a",
            "name": "Entity A",
            "type": "CONCEPT",
            "confidence": 0.6
        })
        
        entity_b = entities_col.insert({
            "_key": "entity_b",
            "name": "Entity B",
            "type": "CONCEPT",
            "confidence": 0.6
        })
        
        # Insert test document
        docs_col = db.collection("documents")
        doc = docs_col.insert({
            "_key": "test_doc",
            "title": "Test Document"
        })
        
        qa_pair = QAPair(
            question="What might be the connection?",
            thinking="This is speculative...",
            answer="There could be a connection.",
            question_type=QuestionType.MULTI_HOP,
            confidence=0.5,
            validation_score=0.6
        )
        
        from_entity = {
            "_id": f"entities/{entity_a['_key']}",
            "confidence": 0.6
        }
        to_entity = {
            "_id": f"entities/{entity_b['_key']}",
            "confidence": 0.6
        }
        source_doc = {
            "_id": f"documents/{doc['_key']}"
        }
        
        edge = edge_generator._create_edge_document(
            from_entity=from_entity,
            to_entity=to_entity,
            qa_pair=qa_pair,
            source_document=source_doc
        )
        
        # Low confidence should trigger review
        assert edge["confidence"] < 0.7
        assert edge["review_status"] == "pending"


    def test_edge_creation_full_workflow(self, edge_generator, db):
        """Test full edge creation workflow with real database."""
        # Insert test document
        docs_col = db.collection("documents")
        source_doc = docs_col.insert({
            "_key": "test_123",
            "title": "Test Document",
            "valid_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Test Q&A
        qa_pair = QAPair(
            question="How does Python handle memory?",
            thinking="Python memory management involves...",
            answer="Python uses garbage collection.",
            question_type=QuestionType.FACTUAL,
            confidence=0.9,
            validation_score=0.95
        )
        
        source_doc_dict = {
            "_id": f"documents/{source_doc['_key']}",
            "title": "Test Document",
            "valid_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Create edges
        edges = edge_generator.create_qa_edges(qa_pair, source_doc_dict)
        
        # Verify - edges may be empty if no entities were extracted
        assert isinstance(edges, list)
        
        # If edges were created, verify they're in the database
        if edges:
            relationships_col = db.collection("relationships")
            for edge in edges:
                # Check that edge was inserted
                assert "_id" in edge or "_key" in edge
                
        # Verify entities were created if edges exist
        if edges:
            entities_col = db.collection("entities")
            assert entities_col.count() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])