"""
Real Tests for Search Commands

This module tests all search commands using real database connections,
real embeddings, and actual search operations.
NO MOCKING - All tests use real components.
"""

import pytest
import json
from typer.testing import CliRunner
from arangodb.cli.main import app
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.arango_setup import connect_arango
from arangodb.core.utils.embedding_utils import get_embedding

runner = CliRunner()

@pytest.fixture(scope="session")
def setup_test_data():
    """Setup test data in real collections"""
    # Connect to real database
    db = get_db_connection()
    
    # Ensure collections exist
    collections = ["documents", "test_search_collection"]
    for collection_name in collections:
        if not db.has_collection(collection_name):
            db.create_collection(collection_name)
    
    # Create test documents with real embeddings
    documents = [
        {
            "_key": "test_doc_1",
            "content": "Machine learning and artificial intelligence are transforming technology",
            "type": "article",
            "tags": ["ml", "ai", "technology"]
        },
        {
            "_key": "test_doc_2", 
            "content": "Database systems require optimization for efficient query processing",
            "type": "tutorial",
            "tags": ["database", "optimization", "performance"]
        },
        {
            "_key": "test_doc_3",
            "content": "Neural networks are a key component of deep learning algorithms",
            "type": "research",
            "tags": ["ml", "neural-networks", "deep-learning"]
        },
        {
            "_key": "test_doc_4",
            "content": "ArangoDB is a multi-model database supporting graphs and documents",
            "type": "documentation",
            "tags": ["database", "arangodb", "graphs"]
        }
    ]
    
    # Clear existing test documents
    collection = db.collection("documents")
    for doc in documents:
        if collection.has(doc["_key"]):
            collection.delete(doc["_key"])
    
    # Create documents with embeddings using embedding utils
    
    for doc in documents:
        # Create embedding for content using real embedding model
        doc["embedding"] = get_embedding(doc["content"])
        collection.insert(doc)
    
    # Create test documents in custom collection
    test_collection = db.collection("test_search_collection")
    test_docs = [
        {
            "_key": "custom_doc_1",
            "content": "Python programming language is versatile and powerful",
            "category": "programming"
        },
        {
            "_key": "custom_doc_2",
            "content": "Graph databases excel at relationship queries",
            "category": "databases"
        }
    ]
    
    for doc in test_docs:
        if test_collection.has(doc["_key"]):
            test_collection.delete(doc["_key"])
        doc["embedding"] = get_embedding(doc["content"])
        test_collection.insert(doc)
    
    return db

class TestSearchCommands:
    """Test all search commands with real data"""
    
    def test_bm25_search_default(self, setup_test_data):
        """Test BM25 search with default parameters"""
        result = runner.invoke(app, [
            "search", "bm25",
            "--query", "database optimization",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "results" in data["data"]
        assert len(data["data"]["results"]) > 0
        
        # Verify results contain relevant documents
        results = data["data"]["results"]
        found_relevant = False
        for res in results:
            if "database" in res["doc"]["content"].lower():
                found_relevant = True
                break
        assert found_relevant
    
    def test_bm25_search_custom_collection(self, setup_test_data):
        """Test BM25 search on custom collection"""
        result = runner.invoke(app, [
            "search", "bm25",
            "--query", "programming", 
            "--collection", "test_search_collection",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["results"]) > 0
        
        # Verify we're searching in the correct collection
        first_result = data["data"]["results"][0]
        assert "Python programming" in first_result["doc"]["content"]
    
    def test_semantic_search_default(self, setup_test_data):
        """Test semantic search with real embeddings"""
        result = runner.invoke(app, [
            "search", "semantic",
            "--query", "artificial intelligence and deep learning",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["results"]) > 0
        
        # Check similarity scores exist
        first_result = data["data"]["results"][0]
        assert "score" in first_result
        assert first_result["score"] > 0.0
        
        # Verify semantic relevance
        found_ai_content = False
        for res in data["data"]["results"]:
            content = res["doc"]["content"].lower()
            if "learning" in content or "intelligence" in content:
                found_ai_content = True
                break
        assert found_ai_content
    
    def test_semantic_search_with_threshold(self, setup_test_data):
        """Test semantic search with similarity threshold"""
        result = runner.invoke(app, [
            "search", "semantic",
            "--query", "multi-model database features",
            "--threshold", "0.8",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # All results should meet threshold
        if data["data"]["results"]:
            for res in data["data"]["results"]:
                assert res["score"] >= 0.8
    
    def test_semantic_search_with_tags(self, setup_test_data):
        """Test semantic search with tag filtering"""
        result = runner.invoke(app, [
            "search", "semantic",
            "--query", "machine learning",
            "--tags", "ml,ai",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # Verify tag filtering
        for res in data["data"]["results"]:
            tags = res["doc"].get("tags", [])
            assert "ml" in tags or "ai" in tags
    
    def test_keyword_search(self, setup_test_data):
        """Test keyword search in specific field"""
        result = runner.invoke(app, [
            "search", "keyword",
            "--field", "type",
            "--keyword", "tutorial",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["results"]) > 0
        
        # Verify field match
        for res in data["data"]["results"]:
            assert res["doc"]["type"] == "tutorial"
    
    def test_tag_search_single_tag(self, setup_test_data):
        """Test tag search with single tag"""
        result = runner.invoke(app, [
            "search", "tag",
            "--tags", "database", 
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["results"]) > 0
        
        # Verify tag match
        for res in data["data"]["results"]:
            assert "database" in res["doc"]["tags"]
    
    def test_tag_search_multiple_tags_any(self, setup_test_data):
        """Test tag search with multiple tags (ANY mode)"""
        result = runner.invoke(app, [
            "search", "tag",
            "--tags", "ml,deep-learning",
            "--mode", "any",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # Verify at least one tag matches
        for res in data["data"]["results"]:
            tags = res["doc"]["tags"]
            assert "ml" in tags or "deep-learning" in tags
    
    def test_tag_search_multiple_tags_all(self, setup_test_data):
        """Test tag search with multiple tags (ALL mode)"""
        result = runner.invoke(app, [
            "search", "tag",
            "--tags", "ml,neural-networks",
            "--mode", "all",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # Verify all tags match
        if data["data"]["results"]:
            for res in data["data"]["results"]:
                tags = res["doc"]["tags"]
                assert "ml" in tags
                assert "neural-networks" in tags
    
    def test_graph_search(self, setup_test_data):
        """Test graph traversal search"""
        # First create a relationship
        db = setup_test_data
        
        # Import the edge collection creation
        from arangodb.core.arango_setup import ensure_edge_collections
        ensure_edge_collections(db)
        
        # Create a relationship
        edges_collection = db.collection("edges")
        edge_doc = {
            "_from": "documents/test_doc_1",
            "_to": "documents/test_doc_3",
            "relationship_type": "RELATED",
            "rationale": "Both discuss machine learning"
        }
        
        # Clear existing edge if present
        existing = edges_collection.find({"_from": edge_doc["_from"], "_to": edge_doc["_to"]})
        for e in existing:
            edges_collection.delete(e)
        
        edges_collection.insert(edge_doc)
        
        # Now test graph search
        result = runner.invoke(app, [
            "search", "graph",
            "--doc-id", "documents/test_doc_1",
            "--direction", "outbound",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["results"]) > 0
        
        # Verify we found the connected document
        found_connected = False
        for res in data["data"]["results"]:
            if res["doc"]["_key"] == "test_doc_3":
                found_connected = True
                break
        assert found_connected
    
    def test_search_with_limit(self, setup_test_data):
        """Test search with limit parameter"""
        result = runner.invoke(app, [
            "search", "bm25",
            "--query", "learning",
            "--limit", "2",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["results"]) <= 2
    
    def test_search_table_output(self, setup_test_data):
        """Test search with table output format"""
        result = runner.invoke(app, [
            "search", "semantic",
            "--query", "database systems",
            "--output", "table"
        ])
        
        assert result.exit_code == 0
        # Table output should contain formatted results
        assert "Score" in result.stdout
        assert "Content" in result.stdout
    
    def test_search_error_handling(self, setup_test_data):
        """Test search error handling"""
        # Test with non-existent collection
        result = runner.invoke(app, [
            "search", "bm25",
            "--query", "test",
            "--collection", "non_existent_collection",
            "--output", "json"
        ])
        
        # Should handle error gracefully
        assert result.exit_code != 0 or (result.exit_code == 0 and "error" in result.stdout)
    
    def test_search_empty_query(self, setup_test_data):
        """Test search with empty query"""
        result = runner.invoke(app, [
            "search", "semantic",
            "--query", "",
            "--output", "json"
        ])
        
        # Should require non-empty query
        assert result.exit_code != 0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-header"])