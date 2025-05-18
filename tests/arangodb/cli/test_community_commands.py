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
            "--collection", "documents",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "communities" in data["data"]
        assert len(data["data"]["communities"]) > 0
        
        # Should detect at least 2 communities
        assert len(data["data"]["communities"]) >= 2
    
    def test_community_detect_with_algorithm(self, setup_community_test_data):
        """Test community detection with specific algorithm"""
        result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--algorithm", "modularity",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["algorithm"] == "modularity"
        assert len(data["data"]["communities"]) > 0
    
    def test_community_list(self, setup_community_test_data):
        """Test listing existing communities"""
        # First run detection to ensure communities exist
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--output", "json"
        ])
        
        # Now list communities
        result = runner.invoke(app, [
            "community", "list",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["communities"]) > 0
        
        # Verify community structure
        for community in data["data"]["communities"]:
            assert "_key" in community
            assert "name" in community
            assert "member_count" in community
    
    def test_community_show(self, setup_community_test_data):
        """Test showing specific community details"""
        # First detect communities
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--output", "json"
        ])
        
        detect_data = json.loads(detect_result.stdout)
        community_id = detect_data["data"]["communities"][0]["community_id"]
        
        # Show community details
        result = runner.invoke(app, [
            "community", "show",
            "--id", str(community_id),
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "members" in data["data"]
        assert len(data["data"]["members"]) > 0
    
    def test_community_members(self, setup_community_test_data):
        """Test listing community members"""
        # Detect communities first
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--output", "json"
        ])
        
        detect_data = json.loads(detect_result.stdout)
        community_id = detect_data["data"]["communities"][0]["community_id"]
        
        # List members
        result = runner.invoke(app, [
            "community", "members",
            "--id", str(community_id),
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["members"]) > 0
        
        # Verify members have expected structure
        for member in data["data"]["members"]:
            assert "_key" in member
            assert "title" in member
    
    def test_community_detect_with_resolution(self, setup_community_test_data):
        """Test community detection with different resolution"""
        # Lower resolution - fewer communities
        result_low = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--resolution", "0.5",
            "--output", "json"
        ])
        
        # Higher resolution - more communities
        result_high = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--resolution", "2.0",
            "--output", "json"
        ])
        
        assert result_low.exit_code == 0
        assert result_high.exit_code == 0
        
        data_low = json.loads(result_low.stdout)
        data_high = json.loads(result_high.stdout)
        
        # Different resolutions should generally produce different community counts
        assert data_low["success"] is True
        assert data_high["success"] is True
    
    def test_community_detect_with_min_size(self, setup_community_test_data):
        """Test community detection with minimum size filter"""
        result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--min-size", "3",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # All communities should meet minimum size
        for community in data["data"]["communities"]:
            assert community["size"] >= 3
    
    def test_community_stats(self, setup_community_test_data):
        """Test community statistics"""
        # First detect communities
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--output", "json"
        ])
        
        # Get statistics
        result = runner.invoke(app, [
            "community", "stats",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "total_communities" in data["data"]
        assert "average_size" in data["data"]
        assert "modularity_score" in data["data"]
    
    def test_community_merge(self, setup_community_test_data):
        """Test merging communities"""
        # First detect communities
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--output", "json"
        ])
        
        detect_data = json.loads(detect_result.stdout)
        if len(detect_data["data"]["communities"]) >= 2:
            comm1_id = detect_data["data"]["communities"][0]["community_id"]
            comm2_id = detect_data["data"]["communities"][1]["community_id"]
            
            # Merge communities
            result = runner.invoke(app, [
                "community", "merge",
                "--source", str(comm1_id),
                "--target", str(comm2_id),
                "--output", "json"
            ])
            
            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert data["success"] is True
    
    def test_community_table_output(self, setup_community_test_data):
        """Test community commands with table output"""
        result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--output", "table"
        ])
        
        assert result.exit_code == 0
        # Table should have headers
        assert "Community" in result.stdout or "ID" in result.stdout
    
    def test_community_export(self, setup_community_test_data):
        """Test exporting community data"""
        # First detect communities
        detect_result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--output", "json"
        ])
        
        # Export communities
        result = runner.invoke(app, [
            "community", "export",
            "--format", "json",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "export_data" in data["data"]
    
    def test_community_invalid_algorithm(self, setup_community_test_data):
        """Test community detection with invalid algorithm"""
        result = runner.invoke(app, [
            "community", "detect",
            "--collection", "documents",
            "--algorithm", "invalid_algorithm",
            "--output", "json"
        ])
        
        # Should handle error gracefully
        assert result.exit_code != 0 or (result.exit_code == 0 and "error" in result.stdout)
    
    def test_community_empty_collection(self, setup_community_test_data):
        """Test community detection on empty collection"""
        db = setup_community_test_data
        
        # Create empty collection
        if not db.has_collection("empty_collection"):
            db.create_collection("empty_collection")
        
        result = runner.invoke(app, [
            "community", "detect",
            "--collection", "empty_collection",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["communities"] == []

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-header"])