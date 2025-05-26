"""
Real Tests for CRUD Commands

This module tests all CRUD commands using real database connections
and actual data operations.
NO MOCKING - All tests use real components.
"""

import pytest
import json
from typer.testing import CliRunner
from arangodb.cli.main import app
from arangodb.cli.db_connection import get_db_connection
# MemoryAgent import not needed for CRUD tests

runner = CliRunner()

@pytest.fixture(scope="module")
def setup_crud_test_data():
    """Setup test collections for CRUD operations"""
    db = get_db_connection()
    
    # Create test collections
    test_collections = ["test_products", "test_users", "test_documents"]
    for collection_name in test_collections:
        if not db.has_collection(collection_name):
            db.create_collection(collection_name)
        else:
            # Clear existing data
            collection = db.collection(collection_name)
            collection.truncate()
    
    # Add some initial test data
    products = db.collection("test_products")
    products.insert({
        "_key": "prod_001",
        "name": "Widget Pro",
        "price": 29.99,
        "category": "tools",
        "tags": ["professional", "durable"]
    })
    products.insert({
        "_key": "prod_002", 
        "name": "Gadget Plus",
        "price": 49.99,
        "category": "electronics",
        "tags": ["smart", "wireless"]
    })
    
    users = db.collection("test_users")
    users.insert({
        "_key": "user_001",
        "username": "john_doe",
        "email": "john@example.com",
        "role": "admin"
    })
    
    return db

class TestCrudCommands:
    """Test all CRUD commands with real data"""
    
    def test_crud_create_basic(self, setup_crud_test_data):
        """Test creating a document with basic data"""
        result = runner.invoke(app, [
            "crud", "create", "test_products",
            '{"name": "Test Product", "price": 19.99}',
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["name"] == "Test Product"
        assert data["data"]["price"] == 19.99
        assert "_key" in data["data"]
        assert "_id" in data["data"]
    
    def test_crud_create_with_embedding(self, setup_crud_test_data):
        """Test creating a document with content that gets embedded"""
        result = runner.invoke(app, [
            "crud", "create", "test_documents",
            '{"title": "AI Tutorial", "content": "Machine learning is transforming technology industries worldwide"}',
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "embedding" in data["data"]  # Should have created embedding
        assert isinstance(data["data"]["embedding"], list)
        assert len(data["data"]["embedding"]) > 0
    
    def test_crud_read_by_key(self, setup_crud_test_data):
        """Test reading a document by key"""
        result = runner.invoke(app, [
            "crud", "read", "test_products", "prod_001",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["_key"] == "prod_001"
        assert data["data"]["name"] == "Widget Pro"
    
    def test_crud_read_not_found(self, setup_crud_test_data):
        """Test reading non-existent document"""
        result = runner.invoke(app, [
            "crud", "read", "test_products", "non_existent",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is False
        assert "not found" in data["error"].lower()
    
    def test_crud_update_document(self, setup_crud_test_data):
        """Test updating an existing document"""
        result = runner.invoke(app, [
            "crud", "update", "test_products", "prod_002",
            '{"price": 59.99, "on_sale": true}',
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["price"] == 59.99
        assert data["data"]["on_sale"] is True
        # Original fields should still exist
        assert data["data"]["name"] == "Gadget Plus"
    
    def test_crud_update_with_embedding(self, setup_crud_test_data):
        """Test updating content field regenerates embedding"""
        # First create a document
        create_result = runner.invoke(app, [
            "crud", "create", "test_documents",
            '{"title": "Original", "content": "Original content"}',
            "--output", "json"
        ])
        
        create_data = json.loads(create_result.stdout)
        doc_key = create_data["data"]["_key"]
        original_embedding = create_data["data"]["embedding"]
        
        # Now update the content
        result = runner.invoke(app, [
            "crud", "update", "test_documents", doc_key,
            '{"content": "Completely different content about quantum computing"}',
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["content"] == "Completely different content about quantum computing"
        # Embedding should be different
        assert data["data"]["embedding"] != original_embedding
    
    def test_crud_delete_document(self, setup_crud_test_data):
        """Test deleting a document"""
        # First create a document to delete
        create_result = runner.invoke(app, [
            "crud", "create", "test_products",
            '{"name": "Temp Product", "price": 9.99}',
            "--output", "json"
        ])
        
        create_data = json.loads(create_result.stdout)
        doc_key = create_data["data"]["_key"]
        
        # Now delete it (use --force to skip confirmation)
        result = runner.invoke(app, [
            "crud", "delete", "test_products", doc_key,
            "--force",  # Skip confirmation prompt in tests
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # Verify it's deleted
        read_result = runner.invoke(app, [
            "crud", "read", "test_products", doc_key,
            "--output", "json"
        ])
        
        read_data = json.loads(read_result.stdout)
        assert read_data["success"] is False
    
    def test_crud_list_default(self, setup_crud_test_data):
        """Test listing documents with default parameters"""
        result = runner.invoke(app, [
            "crud", "list", "test_products",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]) >= 2
        
        # Verify document structure
        docs = data["data"]
        assert all("_key" in doc for doc in docs)
        assert all("name" in doc for doc in docs)
    
    def test_crud_list_with_limit(self, setup_crud_test_data):
        """Test listing documents with limit"""
        result = runner.invoke(app, [
            "crud", "list", "test_products",
            "--limit", "1",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]) == 1
    
    def test_crud_list_with_filter(self, setup_crud_test_data):
        """Test listing documents with filter"""
        result = runner.invoke(app, [
            "crud", "list", "test_products",
            "--filter-field", "category",
            "--filter-value", "electronics",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # All results should match filter
        docs = data["data"]
        assert all(doc["category"] == "electronics" for doc in docs)
    
    def test_crud_list_empty_collection(self, setup_crud_test_data):
        """Test listing empty collection"""
        db = setup_crud_test_data
        # Create empty collection
        if not db.has_collection("empty_collection"):
            db.create_collection("empty_collection")
        
        result = runner.invoke(app, [
            "crud", "list", "empty_collection",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"] == []
    
    def test_crud_table_output(self, setup_crud_test_data):
        """Test CRUD commands with table output"""
        result = runner.invoke(app, [
            "crud", "list", "test_products",
            "--output", "table"
        ])
        
        assert result.exit_code == 0
        # Table should have column headers
        assert "Key" in result.stdout  # Table shows "Key" not "_key"
        assert "Widget Pro" in result.stdout
    
    def test_crud_create_invalid_json(self, setup_crud_test_data):
        """Test creating document with invalid JSON"""
        result = runner.invoke(app, [
            "crud", "create", "test_products",
            '{invalid json}',
            "--output", "json"
        ])
        
        # Should handle error gracefully
        assert result.exit_code != 0 or (result.exit_code == 0 and "error" in result.stdout)
    
    def test_crud_cross_collection(self, setup_crud_test_data):
        """Test CRUD operations work with any collection"""
        # Create in users collection
        result = runner.invoke(app, [
            "crud", "create", "test_users",
            '{"username": "jane_doe", "email": "jane@example.com"}',
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["username"] == "jane_doe"
        
        # List users
        list_result = runner.invoke(app, [
            "crud", "list", "test_users",
            "--output", "json"
        ])
        
        list_data = json.loads(list_result.stdout)
        assert len(list_data["data"]) >= 2
    
    def test_crud_update_nonexistent(self, setup_crud_test_data):
        """Test updating non-existent document"""
        result = runner.invoke(app, [
            "crud", "update", "test_products", "nonexistent_key",
            '{"price": 100}',
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is False
        assert "not found" in data["error"].lower()
    
    def test_crud_create_with_special_chars(self, setup_crud_test_data):
        """Test creating document with special characters"""
        # Use proper JSON escaping for the quotes
        json_data = json.dumps({
            "title": "Test & Demo",
            "content": "Content with 'quotes' and \"double quotes\""
        })
        
        result = runner.invoke(app, [
            "crud", "create", "test_documents",
            json_data,
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["title"] == "Test & Demo"
        assert data["data"]["content"] == "Content with 'quotes' and \"double quotes\""

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-header"])