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
            "documents/graph_doc_1", "documents/graph_doc_3",
            "--type", "INSPIRES",
            "--rationale", "Theory inspires practical applications",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["_from"] == "documents/graph_doc_1"
        assert data["data"]["_to"] == "documents/graph_doc_3"
        assert data["data"]["relationship_type"] == "INSPIRES"
    
    def test_graph_add_duplicate_relationship(self, setup_graph_test_data):
        """Test adding duplicate relationship (should update)"""
        # First add
        result1 = runner.invoke(app, [
            "graph", "add-relationship",
            "documents/graph_doc_2", "documents/graph_doc_4",
            "--type", "COMPLEMENTS",
            "--rationale", "Different perspectives on graphs",
            "--output", "json"
        ])
        
        # Second add with same nodes
        result2 = runner.invoke(app, [
            "graph", "add-relationship",
            "documents/graph_doc_2", "documents/graph_doc_4",
            "--type", "ENHANCES",
            "--rationale", "Updated relationship",
            "--output", "json"
        ])
        
        assert result2.exit_code == 0
        data2 = json.loads(result2.stdout)
        assert data2["success"] is True
        assert data2["data"]["relationship_type"] == "ENHANCES"
    
    def test_graph_traverse_outbound(self, setup_graph_test_data):
        """Test outbound graph traversal"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_1",
            "--direction", "OUTBOUND",
            "--max-depth", "2",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["results"]) > 0
        
        # Should find connected documents
        found_keys = [res["doc"]["_key"] for res in data["data"]["results"]]
        assert "graph_doc_2" in found_keys or "graph_doc_4" in found_keys
    
    def test_graph_traverse_inbound(self, setup_graph_test_data):
        """Test inbound graph traversal"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_3",
            "--direction", "INBOUND",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # Should find documents pointing to doc_3
        found_keys = [res["doc"]["_key"] for res in data["data"]["results"]]
        assert "graph_doc_2" in found_keys
    
    def test_graph_traverse_any_direction(self, setup_graph_test_data):
        """Test any direction graph traversal"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_2",
            "--direction", "ANY",
            "--max-depth", "1",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # Should find both inbound and outbound connections
        found_keys = [res["doc"]["_key"] for res in data["data"]["results"]]
        assert len(found_keys) >= 2
    
    def test_graph_traverse_with_filter(self, setup_graph_test_data):
        """Test graph traversal with filter"""
        result = runner.invoke(app, [
            "graph", "traverse", 
            "documents/graph_doc_1",
            "--direction", "OUTBOUND",
            "--filter", "type:advanced",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # Should only find documents with type:advanced
        if data["data"]["results"]:
            for res in data["data"]["results"]:
                assert res["doc"]["type"] == "advanced"
    
    def test_graph_visualize(self, setup_graph_test_data):
        """Test graph visualization command"""
        result = runner.invoke(app, [
            "graph", "visualize",
            "--collection", "documents", 
            "--max-nodes", "5",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "nodes" in data["data"]
        assert "edges" in data["data"] 
        assert len(data["data"]["nodes"]) <= 5
    
    def test_graph_delete_relationship(self, setup_graph_test_data):
        """Test deleting a relationship"""
        # First create a relationship to delete
        add_result = runner.invoke(app, [
            "graph", "add-relationship",
            "documents/graph_doc_1", "documents/graph_doc_2",
            "--type", "TEMPORARY",
            "--output", "json"
        ])
        
        # Now delete it
        result = runner.invoke(app, [
            "graph", "delete-relationship",
            "documents/graph_doc_1", "documents/graph_doc_2",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # Verify it's deleted by trying to traverse
        traverse_result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_1",
            "--direction", "OUTBOUND",
            "--filter", "relationship_type:TEMPORARY",
            "--output", "json"
        ])
        
        traverse_data = json.loads(traverse_result.stdout)
        # Should not find the deleted relationship
        for res in traverse_data["data"]["results"]:
            if "relationship" in res:
                assert res["relationship"]["relationship_type"] != "TEMPORARY"
    
    def test_graph_traverse_nonexistent_node(self, setup_graph_test_data):
        """Test traversing from non-existent node"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/nonexistent_doc",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["results"] == []  # No results for non-existent node
    
    def test_graph_table_output(self, setup_graph_test_data):
        """Test graph commands with table output"""
        result = runner.invoke(app, [
            "graph", "traverse",
            "documents/graph_doc_1",
            "--output", "table"
        ])
        
        assert result.exit_code == 0
        # Table should have column headers
        assert "Document ID" in result.stdout or "Path" in result.stdout
    
    def test_graph_add_relationship_invalid_type(self, setup_graph_test_data):
        """Test adding relationship with empty type"""
        result = runner.invoke(app, [
            "graph", "add-relationship",
            "documents/graph_doc_1", "documents/graph_doc_2",
            "--type", "",
            "--output", "json"
        ])
        
        # Should require non-empty relationship type
        assert result.exit_code != 0 or (result.exit_code == 0 and "error" in result.stdout)
    
    def test_graph_stats(self, setup_graph_test_data):
        """Test graph statistics command"""
        result = runner.invoke(app, [
            "graph", "stats",
            "--collection", "documents",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "total_nodes" in data["data"]
        assert "total_edges" in data["data"]
        assert data["data"]["total_nodes"] >= 4
        assert data["data"]["total_edges"] >= 4
    
    def test_graph_subgraph(self, setup_graph_test_data):
        """Test extracting a subgraph"""
        result = runner.invoke(app, [
            "graph", "subgraph",
            "--center-node", "documents/graph_doc_2",
            "--radius", "1",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["nodes"]) >= 3  # Center + neighbors
        assert len(data["data"]["edges"]) >= 2  # Connected edges

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-header"])