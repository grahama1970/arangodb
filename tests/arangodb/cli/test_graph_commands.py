"""
Real Tests for Graph Commands

This module tests all graph commands using real database connections
and actual graph operations.
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
def setup_graph_test_data():
    """Setup test graph data"""
    db = get_db_connection()
    
    # Ensure collections exist
    collections = ["documents", "test_nodes", "edges"]
    for collection_name in collections:
        if not db.has_collection(collection_name):
            db.create_collection(collection_name)
    
    # Ensure edge collections
    ensure_edge_collections(db)
    
    # Create test documents
    documents = db.collection("documents")
    test_docs = [
        {
            "_key": "graph_doc_1",
            "title": "Introduction to Graph Theory",
            "content": "Graph theory is the study of graphs and their properties.",
            "type": "tutorial"
        },
        {
            "_key": "graph_doc_2",
            "title": "Advanced Graph Algorithms", 
            "content": "Exploring complex algorithms for graph traversal and analysis.",
            "type": "advanced"
        },
        {
            "_key": "graph_doc_3",
            "title": "Real-world Graph Applications",
            "content": "How graphs are used in social networks and recommendation systems.",
            "type": "practical"
        },
        {
            "_key": "graph_doc_4",
            "title": "Graph Databases Overview",
            "content": "Understanding the benefits of graph databases like ArangoDB.",
            "type": "database"
        }
    ]
    
    # Clear and insert test documents
    for doc in test_docs:
        if documents.has(doc["_key"]):
            documents.delete(doc["_key"])
    
    for doc in test_docs:
        # Add embeddings
        doc["embedding"] = get_embedding(doc["content"])
        documents.insert(doc)
    
    # Create test relationships
    edges = db.collection("edges")
    test_edges = [
        {
            "_from": "documents/graph_doc_1",
            "_to": "documents/graph_doc_2",
            "relationship_type": "PREREQUISITE",
            "rationale": "Basic concepts needed for advanced topics"
        },
        {
            "_from": "documents/graph_doc_2",
            "_to": "documents/graph_doc_3",
            "relationship_type": "LEADS_TO",
            "rationale": "Advanced algorithms lead to practical applications"
        },
        {
            "_from": "documents/graph_doc_1",
            "_to": "documents/graph_doc_4",
            "relationship_type": "RELATED",
            "rationale": "Both cover fundamental graph concepts"
        },
        {
            "_from": "documents/graph_doc_3",
            "_to": "documents/graph_doc_4",
            "relationship_type": "USES",
            "rationale": "Applications often use graph databases"
        }
    ]
    
    # Clear existing edges
    for edge in test_edges:
        existing = edges.find({"_from": edge["_from"], "_to": edge["_to"]})
        for e in existing:
            edges.delete(e)
    
    # Insert test edges
    for edge in test_edges:
        edges.insert(edge)
    
    return db

class TestGraphCommands:
    """Test all graph commands with real data"""
    
    def test_graph_add_relationship(self, setup_graph_test_data):
        """Test adding a new relationship"""
        result = runner.invoke(app, [
            "graph", "add-relationship",
            "graph_doc_1", "graph_doc_3",  # Use keys, not full IDs
            "--type", "INSPIRES",
            "--rationale", "Theory inspires practical applications",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "_from" in data
        assert "_to" in data
        assert data["_from"].endswith("graph_doc_1")
        assert data["_to"].endswith("graph_doc_3")
        assert data["type"] == "INSPIRES"
    
    def test_graph_add_duplicate_relationship(self, setup_graph_test_data):
        """Test adding duplicate relationship (should update)"""
        # First add
        result1 = runner.invoke(app, [
            "graph", "add-relationship",
            "graph_doc_2", "graph_doc_4",  # Use keys, not full IDs
            "--type", "COMPLEMENTS",
            "--rationale", "Different perspectives on graphs",
            "--output", "json"
        ])
        
        # Second add with same nodes
        result2 = runner.invoke(app, [
            "graph", "add-relationship",
            "graph_doc_2", "graph_doc_4",  # Use keys, not full IDs
            "--type", "ENHANCES",
            "--rationale", "Updated relationship",
            "--output", "json"
        ])
        
        assert result2.exit_code == 0
        data2 = json.loads(result2.stdout)
        assert data2["type"] == "ENHANCES"
    
    def test_graph_traverse_outbound(self, setup_graph_test_data):
        """Test outbound graph traversal"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_1",  # Full ID required for traverse
            "--direction", "OUTBOUND",
            "--max-depth", "2",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "paths" in data
        assert len(data["paths"]) > 0
        
        # Should find connected documents in paths
        found_keys = []
        for path in data["paths"]:
            vertices = path.get("vertices", [])
            for vertex in vertices:
                if vertex.get("_key"):
                    found_keys.append(vertex["_key"])
        assert "graph_doc_2" in found_keys or "graph_doc_4" in found_keys
    
    def test_graph_traverse_inbound(self, setup_graph_test_data):
        """Test inbound graph traversal"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_3",  # Full ID required for traverse
            "--direction", "INBOUND",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "paths" in data
        
        # Should find documents pointing to doc_3
        found_keys = []
        for path in data["paths"]:
            vertices = path.get("vertices", [])
            for vertex in vertices:
                if vertex.get("_key"):
                    found_keys.append(vertex["_key"])
        assert "graph_doc_2" in found_keys or "graph_doc_1" in found_keys
    
    def test_graph_traverse_any_direction(self, setup_graph_test_data):
        """Test any direction graph traversal"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_2",  # Full ID required for traverse
            "--direction", "ANY",
            "--max-depth", "1",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "paths" in data
        
        # Should find both inbound and outbound connections
        found_keys = set()
        for path in data["paths"]:
            vertices = path.get("vertices", [])
            for vertex in vertices:
                if vertex.get("_key") and vertex["_key"] != "graph_doc_2":
                    found_keys.add(vertex["_key"])
        assert len(found_keys) >= 2
    
    def test_graph_traverse_with_limit(self, setup_graph_test_data):
        """Test graph traversal with limit"""
        result = runner.invoke(app, [
            "graph", "traverse", 
            "documents/graph_doc_1",  # Full ID required
            "--direction", "OUTBOUND",
            "--limit", "2",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "paths" in data
        assert len(data["paths"]) <= 2
    
    def test_graph_delete_relationship_by_key(self, setup_graph_test_data):
        """Test deleting a relationship by edge key"""
        # First create a relationship to get its key
        add_result = runner.invoke(app, [
            "graph", "add-relationship",
            "graph_doc_3", "graph_doc_4",  # Use keys
            "--type", "TEMPORARY",
            "--rationale", "Test edge to delete",
            "--output", "json"
        ])
        
        add_data = json.loads(add_result.stdout)
        edge_key = add_data["_key"]
        
        # Now delete it by key
        result = runner.invoke(app, [
            "graph", "delete-relationship",
            edge_key,  # Edge key as positional argument
            "--yes",  # Skip confirmation
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "success"
    
    def test_graph_add_relationship_with_attributes(self, setup_graph_test_data):
        """Test adding relationship with attributes"""
        result = runner.invoke(app, [
            "graph", "add-relationship",
            "graph_doc_1", "graph_doc_4",  # Use keys
            "--type", "COMPLEMENTS",
            "--rationale", "Complementary topics",
            "--attributes", '{"confidence": 0.95, "source": "manual"}',
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["type"] == "COMPLEMENTS"
        assert data.get("confidence") == 0.95
        assert data.get("source") == "manual"
    
    def test_graph_traverse_nonexistent_node(self, setup_graph_test_data):
        """Test traversing from non-existent node"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/nonexistent_doc",  # Full ID required
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "paths" in data
        assert data["paths"] == []  # No paths for non-existent node
    
    def test_graph_table_output(self, setup_graph_test_data):
        """Test graph commands with table output"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_1",  # Full ID required
            "--output", "table"
        ])
        
        assert result.exit_code == 0
        # Table should have traversal info
        assert "Path" in result.stdout or "Vertex" in result.stdout
    
    def test_graph_add_relationship_missing_rationale(self, setup_graph_test_data):
        """Test adding relationship without rationale"""
        result = runner.invoke(app, [
            "graph", "add-relationship",
            "graph_doc_1", "graph_doc_2",  # Use keys
            "--type", "RELATED"
            # Missing --rationale
        ])
        
        # Should require rationale
        assert result.exit_code != 0
    
    def test_graph_traverse_with_different_depths(self, setup_graph_test_data):
        """Test graph traversal with min and max depth"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_1",  # Full ID required
            "--min-depth", "1",
            "--max-depth", "3",
            "--direction", "OUTBOUND",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "paths" in data
        # Check that paths exist within specified depth range
        for path in data["paths"]:
            path_depth = len(path.get("edges", []))
            assert 1 <= path_depth <= 3
    
    def test_graph_traverse_csv_output(self, setup_graph_test_data):
        """Test graph traversal with CSV output"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_1",  # Full ID required
            "--direction", "OUTBOUND",
            "--output", "csv"
        ])
        
        assert result.exit_code == 0
        # CSV should have headers
        assert "Path" in result.stdout or "Vertices" in result.stdout

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-header"])