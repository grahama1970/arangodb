"""
Real Tests for Community Commands

This module tests all community detection commands using real database connections
and actual community detection algorithms.
NO MOCKING - All tests use real components.
"""

import pytest
import json
from typer.testing import CliRunner
from arangodb.cli.main import app
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.arango_setup import ensure_edge_collections
from arangodb.core.utils.embedding_utils import get_embedding

runner = CliRunner()

@pytest.fixture(scope="module")
def setup_community_test_data():
    """Setup test data for community detection"""
    db = get_db_connection()
    
    # Ensure collections exist
    collections = ["documents", "communities", "edges"]
    for collection_name in collections:
        if not db.has_collection(collection_name):
            db.create_collection(collection_name)
    
    # Ensure edge collections
    ensure_edge_collections(db)
    
    # Create test nodes that form clear communities
    documents = db.collection("documents")
    test_docs = [
        # Community 1: Machine Learning
        {
            "_key": "ml_doc_1",
            "title": "Introduction to Neural Networks",
            "content": "Neural networks are fundamental to deep learning.",
            "category": "ml",
            "topics": ["neural-networks", "deep-learning"]
        },
        {
            "_key": "ml_doc_2",
            "title": "Deep Learning Fundamentals",
            "content": "Deep learning uses multiple layers to learn representations.",
            "category": "ml",
            "topics": ["deep-learning", "ai"]
        },
        {
            "_key": "ml_doc_3",
            "title": "TensorFlow Tutorial",
            "content": "TensorFlow is a popular deep learning framework.",
            "category": "ml",
            "topics": ["tensorflow", "deep-learning", "frameworks"]
        },
        
        # Community 2: Databases
        {
            "_key": "db_doc_1",
            "title": "SQL Database Design",
            "content": "Relational databases use SQL for querying.",
            "category": "database",
            "topics": ["sql", "relational"]
        },
        {
            "_key": "db_doc_2",
            "title": "NoSQL Overview",
            "content": "NoSQL databases offer flexible schemas.",
            "category": "database", 
            "topics": ["nosql", "schema-less"]
        },
        {
            "_key": "db_doc_3",
            "title": "Graph Databases",
            "content": "Graph databases excel at relationship queries.",
            "category": "database",
            "topics": ["graphs", "nosql"]
        },
        
        # Bridge document
        {
            "_key": "bridge_doc",
            "title": "ML in Databases",
            "content": "Using machine learning for database optimization.",
            "category": "hybrid",
            "topics": ["ml", "database", "optimization"]
        }
    ]
    
    # Clear and insert documents
    for doc in test_docs:
        if documents.has(doc["_key"]):
            documents.delete(doc["_key"])
    
    for doc in test_docs:
        doc["embedding"] = get_embedding(doc["content"])
        documents.insert(doc)
    
    # Create edges to form communities
    edges = db.collection("edges")
    test_edges = [
        # Strong connections within ML community
        {"_from": "documents/ml_doc_1", "_to": "documents/ml_doc_2", "weight": 0.9},
        {"_from": "documents/ml_doc_2", "_to": "documents/ml_doc_3", "weight": 0.85},
        {"_from": "documents/ml_doc_1", "_to": "documents/ml_doc_3", "weight": 0.8},
        
        # Strong connections within DB community
        {"_from": "documents/db_doc_1", "_to": "documents/db_doc_2", "weight": 0.9},
        {"_from": "documents/db_doc_2", "_to": "documents/db_doc_3", "weight": 0.85},
        {"_from": "documents/db_doc_1", "_to": "documents/db_doc_3", "weight": 0.8},
        
        # Weak connections between communities (through bridge)
        {"_from": "documents/bridge_doc", "_to": "documents/ml_doc_2", "weight": 0.5},
        {"_from": "documents/bridge_doc", "_to": "documents/db_doc_2", "weight": 0.5}
    ]
    
    # Clear existing edges
    for edge in test_edges:
        existing = edges.find({"_from": edge["_from"], "_to": edge["_to"]})
        for e in existing:
            edges.delete(e)
        edge["relationship_type"] = "RELATED"
        edges.insert(edge)
    
    return db

class TestCommunityCommands:
    """Test all community detection commands with real data"""
    
    def test_community_detect_default(self, setup_community_test_data):
        """Test community detection with default parameters"""
        result = runner.invoke(app, [
            "community", "detect",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_communities" in data
        assert "communities" in data
        assert data["total_communities"] >= 0
        
        # If communities were detected, verify structure
        if data["total_communities"] > 0:
            assert len(data["communities"]) > 0
    
    def test_community_detect_with_resolution(self, setup_community_test_data):
        """Test community detection with different resolution parameters"""
        # Test with higher resolution
        result = runner.invoke(app, [
            "community", "detect",
            "--resolution", "2.0",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_communities" in data
        assert "communities" in data
        assert data["total_communities"] >= 0
    
    def test_community_list(self, setup_community_test_data):
        """Test listing existing communities"""
        # First run detection to ensure communities exist
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--output", "json"
        ])
        
        # Now list communities
        result = runner.invoke(app, [
            "community", "list",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total" in data
        assert "communities" in data
        assert data["total"] >= 0
        
        # Verify community structure if communities exist
        if data["total"] > 0:
            for community in data["communities"]:
                assert "id" in community
                assert "size" in community
                assert "sample_members" in community
    
    def test_community_show(self, setup_community_test_data):
        """Test showing specific community details"""
        # First detect communities
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--output", "json"
        ])
        
        detect_data = json.loads(detect_result.stdout)
        
        # Only test show if communities were detected
        if detect_data["total_communities"] > 0 and len(detect_data["communities"]) > 0:
            community_id = detect_data["communities"][0]["id"]
            
            # Show community details
            result = runner.invoke(app, [
                "community", "show",
                str(community_id),
                "--output", "json"
            ])
            
            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert "id" in data
            assert "member_count" in data
            assert "entities" in data
    
    
    def test_community_detect_multiple_resolutions(self, setup_community_test_data):
        """Test community detection with different resolution values"""
        # Lower resolution - fewer communities
        result_low = runner.invoke(app, [
            "community", "detect",
            "--resolution", "0.5",
            "--output", "json"
        ])
        
        # Higher resolution - more communities
        result_high = runner.invoke(app, [
            "community", "detect",
            "--resolution", "2.0",
            "--output", "json"
        ])
        
        assert result_low.exit_code == 0
        assert result_high.exit_code == 0
        
        data_low = json.loads(result_low.stdout)
        data_high = json.loads(result_high.stdout)
        
        # Both should have valid structure
        assert "total_communities" in data_low
        assert "total_communities" in data_high
    
    def test_community_detect_with_min_size(self, setup_community_test_data):
        """Test community detection with minimum size filter"""
        result = runner.invoke(app, [
            "community", "detect",
            "--min-size", "3",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_communities" in data
        assert "communities" in data
        
        # All communities should meet minimum size
        for community in data["communities"]:
            assert community["size"] >= 3
    
    
    def test_community_table_output(self, setup_community_test_data):
        """Test community commands with table output"""
        result = runner.invoke(app, [
            "community", "detect",
            "--output", "table"
        ])
        
        assert result.exit_code == 0
        # Table should have headers
        assert "Community" in result.stdout or "ID" in result.stdout
    
    def test_community_rebuild(self, setup_community_test_data):
        """Test community detection with rebuild flag"""
        # First detection without rebuild
        result1 = runner.invoke(app, [
            "community", "detect",
            "--output", "json"
        ])
        
        # Second detection with rebuild
        result2 = runner.invoke(app, [
            "community", "detect",
            "--rebuild",
            "--output", "json"
        ])
        
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        
        # Both should return valid data
        data1 = json.loads(result1.stdout)
        data2 = json.loads(result2.stdout)
        
        assert "total_communities" in data1
        assert "total_communities" in data2
    
    def test_community_list_with_filters(self, setup_community_test_data):
        """Test listing communities with filters"""
        # First detect communities to ensure they exist
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--output", "json"
        ])
        
        # List with minimum size filter
        result = runner.invoke(app, [
            "community", "list",
            "--min-size", "2",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total" in data
        assert "communities" in data
        
        # All listed communities should meet the minimum size
        for community in data["communities"]:
            assert community["size"] >= 2
    
    def test_community_list_sorting(self, setup_community_test_data):
        """Test listing communities with different sort options"""
        # First detect communities
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--output", "json"
        ])
        
        # Test sorting by size
        result = runner.invoke(app, [
            "community", "list",
            "--sort", "size",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "communities" in data
        
        # Verify descending order by size
        if len(data["communities"]) > 1:
            for i in range(len(data["communities"]) - 1):
                assert data["communities"][i]["size"] >= data["communities"][i+1]["size"]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-header"])