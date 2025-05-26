"""
Test View Manager Optimization

Tests the optimized view management to ensure views are not recreated unnecessarily.
NO MOCKING - Uses real test database connections per CLAUDE.md guidelines.
"""

import os
import pytest
from arango.client import ArangoClient
from arangodb.core.view_manager import (
    ensure_arangosearch_view_optimized,
    view_needs_update,
    clear_view_cache
)
from arangodb.core.view_config import ViewConfiguration, ViewUpdatePolicy

# Set test database
os.environ['ARANGO_DB_NAME'] = 'pizza_test'


class TestViewManager:
    """Test view manager optimization with real database."""
    
    @pytest.fixture
    def db(self):
        """Get real test database connection."""
        client = ArangoClient(hosts='http://localhost:8529')
        db = client.db('pizza_test', username='root', password='openSesame')
        
        # Ensure test collection exists
        if not db.has_collection('test_collection'):
            db.create_collection('test_collection')
        
        # Clean up any existing test views
        if db.has_view('test_view'):
            db.delete_view('test_view')
            
        yield db
        
        # Cleanup after test
        if db.has_view('test_view'):
            db.delete_view('test_view')
    
    def setup_method(self):
        """Clear cache before each test."""
        clear_view_cache()
    
    def test_view_needs_update_no_view(self, db):
        """Test when view doesn't exist using real database."""
        result = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result is True
    
    def test_view_needs_update_same_config(self, db):
        """Test when view exists with same configuration using real database."""
        # Create a view with specific configuration
        db.create_arangosearch_view(
            name="test_view",
            properties={
                "links": {
                    "test_collection": {
                        "analyzers": ["text_en"],
                        "includeAllFields": False,
                        "fields": {"field1": {}, "field2": {}}
                    }
                }
            }
        )
        
        # Check if view needs update with same fields
        result = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result is False
    
    def test_view_needs_update_different_fields(self, db):
        """Test when view exists with different fields using real database."""
        # Create a view with different fields
        db.create_arangosearch_view(
            name="test_view",
            properties={
                "links": {
                    "test_collection": {
                        "analyzers": ["text_en"],
                        "includeAllFields": False,
                        "fields": {"field1": {}, "field3": {}}  # Different fields
                    }
                }
            }
        )
        
        # Check if view needs update with different fields
        result = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result is True
    
    def test_ensure_view_check_config_policy(self, db):
        """Test CHECK_CONFIG policy only recreates when needed using real database."""
        # Create initial view
        db.create_arangosearch_view(
            name="test_view",
            properties={
                "links": {
                    "test_collection": {
                        "analyzers": ["text_en"],
                        "includeAllFields": False,
                        "fields": {"field1": {}, "field2": {}}
                    }
                }
            }
        )
        
        # Get initial view properties
        initial_view = db.view("test_view")
        initial_props = initial_view.properties()
        
        config = ViewConfiguration(
            name="test_view",
            collection="test_collection",
            fields=["field1", "field2"],
            update_policy=ViewUpdatePolicy.CHECK_CONFIG
        )
        
        # Ensure view with same config - should not recreate
        ensure_arangosearch_view_optimized(
            db, "test_view", "test_collection", ["field1", "field2"], 
            config=config
        )
        
        # Verify view still exists and wasn't recreated
        assert db.has_view("test_view")
        final_view = db.view("test_view")
        final_props = final_view.properties()
        
        # Properties should match (view wasn't recreated)
        assert initial_props["links"] == final_props["links"]
    
    def test_ensure_view_always_recreate_policy(self, db):
        """Test ALWAYS_RECREATE policy always recreates using real database."""
        # Create initial view
        db.create_arangosearch_view(
            name="test_view",
            properties={
                "links": {
                    "test_collection": {
                        "analyzers": ["text_en"],
                        "includeAllFields": False,
                        "fields": {"field1": {}}
                    }
                }
            }
        )
        
        config = ViewConfiguration(
            name="test_view",
            collection="test_collection",
            fields=["field1", "field2"],
            update_policy=ViewUpdatePolicy.ALWAYS_RECREATE
        )
        
        # Ensure view with ALWAYS_RECREATE policy
        ensure_arangosearch_view_optimized(
            db, "test_view", "test_collection", ["field1", "field2"],
            config=config
        )
        
        # Verify view was recreated with new fields
        assert db.has_view("test_view")
        view = db.view("test_view")
        props = view.properties()
        
        # Should have the new fields
        fields = props["links"]["test_collection"]["fields"]
        assert "field1" in fields
        assert "field2" in fields
    
    def test_ensure_view_never_recreate_policy(self, db):
        """Test NEVER_RECREATE policy never recreates using real database."""
        # Create initial view with different fields
        db.create_arangosearch_view(
            name="test_view",
            properties={
                "links": {
                    "test_collection": {
                        "analyzers": ["text_en"],
                        "includeAllFields": False,
                        "fields": {"field3": {}}  # Different field
                    }
                }
            }
        )
        
        config = ViewConfiguration(
            name="test_view",
            collection="test_collection",
            fields=["field1", "field2"],
            update_policy=ViewUpdatePolicy.NEVER_RECREATE
        )
        
        # Ensure view with NEVER_RECREATE policy
        ensure_arangosearch_view_optimized(
            db, "test_view", "test_collection", ["field1", "field2"],
            config=config
        )
        
        # Verify view was NOT recreated (still has old field)
        assert db.has_view("test_view")
        view = db.view("test_view")
        props = view.properties()
        
        # Should still have the old field only
        fields = props["links"]["test_collection"]["fields"]
        assert "field3" in fields
        assert "field1" not in fields
        assert "field2" not in fields
    
    def test_ensure_view_force_recreate(self, db):
        """Test force_recreate bypasses all policies using real database."""
        # Create initial view with different fields
        db.create_arangosearch_view(
            name="test_view",
            properties={
                "links": {
                    "test_collection": {
                        "analyzers": ["text_en"],
                        "includeAllFields": False,
                        "fields": {"field3": {}}  # Different field
                    }
                }
            }
        )
        
        config = ViewConfiguration(
            name="test_view",
            collection="test_collection",
            fields=["field1", "field2"],
            update_policy=ViewUpdatePolicy.NEVER_RECREATE  # Even with never recreate
        )
        
        # Ensure view with force_recreate=True
        ensure_arangosearch_view_optimized(
            db, "test_view", "test_collection", ["field1", "field2"],
            force_recreate=True,  # Force recreate
            config=config
        )
        
        # Verify view was recreated with new fields
        assert db.has_view("test_view")
        view = db.view("test_view")
        props = view.properties()
        
        # Should have the new fields (force_recreate overrides policy)
        fields = props["links"]["test_collection"]["fields"]
        assert "field1" in fields
        assert "field2" in fields
        assert "field3" not in fields
    
    def test_cache_functionality(self, db):
        """Test that cache prevents redundant checks using real database."""
        # Clear cache first
        clear_view_cache()
        
        # Create a view
        db.create_arangosearch_view(
            name="test_view",
            properties={
                "links": {
                    "test_collection": {
                        "analyzers": ["text_en"],
                        "includeAllFields": False,
                        "fields": {"field1": {}, "field2": {}}
                    }
                }
            }
        )
        
        # First call should check the database
        result1 = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result1 is False
        
        # Modify the view to make it different
        db.delete_view("test_view")
        db.create_arangosearch_view(
            name="test_view",
            properties={
                "links": {
                    "test_collection": {
                        "analyzers": ["text_en"],
                        "includeAllFields": False,
                        "fields": {"field3": {}}  # Different field
                    }
                }
            }
        )
        
        # Second call with same parameters should use cache and still return False
        result2 = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result2 is False  # Cache returns the old result
        
        # Clear cache and check again - should now detect the change
        clear_view_cache()
        result3 = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result3 is True  # Now detects the difference


if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))