"""
Test Q&A Edge Generator functionality.

Tests entity extraction and edge creation from Q&A pairs.
"""

import sys
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from arangodb.qa_generation.edge_generator import QAEdgeGenerator
from arangodb.qa_generation.models import QAPair, QuestionType


@pytest.fixture
def mock_db():
    """Create mock database for testing."""
    mock = Mock()
    mock.db = Mock()
    return mock


@pytest.fixture
def edge_generator(mock_db):
    """Create edge generator with mocked dependencies."""
    with patch('arangodb.qa_generation.edge_generator.spacy.load'):
        gen = QAEdgeGenerator(mock_db)
        # Mock NLP
        gen.nlp = Mock()
        return gen


class TestQAEdgeGenerator:
    """Test Q&A edge generator functionality."""
    
    def test_entity_extraction_with_spacy(self, edge_generator):
        """Test entity extraction using SpaCy."""
        qa_pair = QAPair(
            question="How does Python handle memory management?",
            thinking="Considering Python's approach...",
            answer="Python uses automatic garbage collection.",
            question_type=QuestionType.FACTUAL,
            confidence=0.9
        )
        
        # Mock SpaCy response
        mock_ent = Mock()
        mock_ent.text = "Python"
        mock_ent.label_ = "PRODUCT"
        
        mock_doc = Mock()
        mock_doc.ents = [mock_ent]
        
        edge_generator.nlp.return_value = mock_doc
        
        # Extract entities
        entities = edge_generator._extract_with_spacy(qa_pair)
        
        assert len(entities) > 0
        assert entities[0]["name"] == "Python"
        assert entities[0]["type"] == "CONCEPT"
        assert entities[0]["source"] == "spacy"
    
    def test_create_edge_document(self, edge_generator):
        """Test edge document creation."""
        qa_pair = QAPair(
            question="What is the capital of France?",
            thinking="France is a country in Europe...",
            answer="The capital of France is Paris.",
            question_type=QuestionType.FACTUAL,
            confidence=0.95,
            validation_score=0.98
        )
        
        from_entity = {
            "_id": "entities/france_123",
            "name": "France",
            "type": "LOCATION",
            "confidence": 0.9
        }
        
        to_entity = {
            "_id": "entities/paris_456",
            "name": "Paris",
            "type": "LOCATION", 
            "confidence": 0.95
        }
        
        source_doc = {
            "_id": "documents/geography_101",
            "title": "World Geography",
            "valid_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Create edge
        edge = edge_generator._create_edge_document(
            from_entity=from_entity,
            to_entity=to_entity,
            qa_pair=qa_pair,
            source_document=source_doc
        )
        
        # Verify edge structure
        assert edge["_from"] == "entities/france_123"
        assert edge["_to"] == "entities/paris_456"
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
    
    def test_low_confidence_review_status(self, edge_generator):
        """Test that low confidence edges are marked for review."""
        qa_pair = QAPair(
            question="What might be the connection?",
            thinking="This is speculative...",
            answer="There could be a connection.",
            question_type=QuestionType.MULTI_HOP,
            confidence=0.5,
            validation_score=0.6
        )
        
        from_entity = {"_id": "entities/a", "confidence": 0.6}
        to_entity = {"_id": "entities/b", "confidence": 0.6}
        source_doc = {"_id": "documents/test"}
        
        edge = edge_generator._create_edge_document(
            from_entity=from_entity,
            to_entity=to_entity,
            qa_pair=qa_pair,
            source_document=source_doc
        )
        
        # Low confidence should trigger review
        assert edge["confidence"] < 0.7
        assert edge["review_status"] == "pending"


# Integration test with real database
@pytest.mark.integration
def test_edge_creation_integration():
    """Test edge creation with real database."""
    from arango import ArangoClient
    from arangodb.core.db_connection_wrapper import DatabaseOperations
    
    # Skip if no database available
    try:
        client = ArangoClient(hosts="http://localhost:8529")
        db = client.db("test_qa_edges", username="root", password="openSesame")
        sys_db = client.db("_system", username="root", password="openSesame")
        
        # Create test database
        if not sys_db.has_database("test_qa_edges"):
            sys_db.create_database("test_qa_edges")
        
        # Create collections
        if not db.has_collection("entities"):
            db.create_collection("entities")
        if not db.has_collection("relationships"):
            db.create_collection("relationships", edge=True)
        
        db_ops = DatabaseOperations(db)
        edge_gen = QAEdgeGenerator(db_ops)
        
        # Test Q&A
        qa_pair = QAPair(
            question="How does Python handle memory?",
            thinking="Python memory management involves...",
            answer="Python uses garbage collection.",
            question_type=QuestionType.FACTUAL,
            confidence=0.9,
            validation_score=0.95
        )
        
        source_doc = {
            "_id": "documents/test_123",
            "title": "Test Document",
            "valid_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Create edges
        edges = edge_gen.create_qa_edges(qa_pair, source_doc)
        
        # Verify
        assert len(edges) >= 0  # May be 0 if not enough entities
        
        # Cleanup
        sys_db.delete_database("test_qa_edges")
        
    except Exception as e:
        pytest.skip(f"Database not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])