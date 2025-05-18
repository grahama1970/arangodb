"""
Test View Manager Optimization

Tests the optimized view management to ensure views are not recreated unnecessarily.
"""

import time
from unittest.mock import Mock, MagicMock, patch
import pytest
from arangodb.core.view_manager import (
    ensure_arangosearch_view_optimized,
    view_needs_update,
    clear_view_cache
)
from arangodb.core.view_config import ViewConfiguration, ViewUpdatePolicy


class TestViewManager:
    """Test view manager optimization."""
    
    def setup_method(self):
        """Clear cache before each test."""
        clear_view_cache()
    
    def test_view_needs_update_no_view(self):
        """Test when view doesn't exist."""
        db = Mock()
        db.has_view.return_value = False
        
        result = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result is True
        db.has_view.assert_called_once_with("test_view")
    
    def test_view_needs_update_same_config(self):
        """Test when view exists with same configuration."""
        db = Mock()
        db.has_view.return_value = True
        
        # Mock view with matching properties
        view = Mock()
        view.properties.return_value = {
            "links": {
                "test_collection": {
                    "analyzers": ["text_en"],
                    "includeAllFields": False,
                    "fields": {"field1": {}, "field2": {}}
                }
            }
        }
        db.view.return_value = view
        
        result = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result is False
    
    def test_view_needs_update_different_fields(self):
        """Test when view exists with different fields."""
        db = Mock()
        db.has_view.return_value = True
        
        # Mock view with different fields
        view = Mock()
        view.properties.return_value = {
            "links": {
                "test_collection": {
                    "analyzers": ["text_en"],
                    "includeAllFields": False,
                    "fields": {"field1": {}, "field3": {}}  # Different fields
                }
            }
        }
        db.view.return_value = view
        
        result = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result is True
    
    @patch('arangodb.core.view_manager.view_needs_update')
    def test_ensure_view_check_config_policy(self, mock_needs_update):
        """Test CHECK_CONFIG policy only recreates when needed."""
        db = Mock()
        db.has_view.return_value = True
        
        # View doesn't need update
        mock_needs_update.return_value = False
        
        config = ViewConfiguration(
            name="test_view",
            collection="test_collection",
            fields=["field1", "field2"],
            update_policy=ViewUpdatePolicy.CHECK_CONFIG
        )
        
        ensure_arangosearch_view_optimized(
            db, "test_view", "test_collection", ["field1", "field2"], 
            config=config
        )
        
        # Should not delete or create view
        db.delete_view.assert_not_called()
        db.create_arangosearch_view.assert_not_called()
    
    @patch('arangodb.core.view_manager.view_needs_update')
    def test_ensure_view_always_recreate_policy(self, mock_needs_update):
        """Test ALWAYS_RECREATE policy always recreates."""
        db = Mock()
        db.has_view.return_value = True
        
        config = ViewConfiguration(
            name="test_view",
            collection="test_collection",
            fields=["field1", "field2"],
            update_policy=ViewUpdatePolicy.ALWAYS_RECREATE
        )
        
        ensure_arangosearch_view_optimized(
            db, "test_view", "test_collection", ["field1", "field2"],
            config=config
        )
        
        # Should delete and recreate view
        db.delete_view.assert_called_once_with("test_view")
        db.create_arangosearch_view.assert_called_once()
    
    @patch('arangodb.core.view_manager.view_needs_update')
    def test_ensure_view_never_recreate_policy(self, mock_needs_update):
        """Test NEVER_RECREATE policy never recreates."""
        db = Mock()
        db.has_view.return_value = True
        
        # Even if view needs update
        mock_needs_update.return_value = True
        
        config = ViewConfiguration(
            name="test_view",
            collection="test_collection",
            fields=["field1", "field2"],
            update_policy=ViewUpdatePolicy.NEVER_RECREATE
        )
        
        ensure_arangosearch_view_optimized(
            db, "test_view", "test_collection", ["field1", "field2"],
            config=config
        )
        
        # Should not delete or create view
        db.delete_view.assert_not_called()
        db.create_arangosearch_view.assert_not_called()
    
    def test_ensure_view_force_recreate(self):
        """Test force_recreate bypasses all policies."""
        db = Mock()
        db.has_view.return_value = True
        
        config = ViewConfiguration(
            name="test_view",
            collection="test_collection",
            fields=["field1", "field2"],
            update_policy=ViewUpdatePolicy.NEVER_RECREATE  # Even with never recreate
        )
        
        ensure_arangosearch_view_optimized(
            db, "test_view", "test_collection", ["field1", "field2"],
            force_recreate=True,  # Force recreate
            config=config
        )
        
        # Should delete and recreate view
        db.delete_view.assert_called_once_with("test_view")
        db.create_arangosearch_view.assert_called_once()
    
    def test_cache_functionality(self):
        """Test that cache prevents redundant checks."""
        db = Mock()
        db.has_view.return_value = True
        db.db_name = "test_db"
        
        # Mock view with matching properties
        view = Mock()
        view.properties.return_value = {
            "links": {
                "test_collection": {
                    "analyzers": ["text_en"],
                    "includeAllFields": False,
                    "fields": {"field1": {}, "field2": {}}
                }
            }
        }
        db.view.return_value = view
        
        # First call should check properties
        result1 = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result1 is False
        assert db.view.call_count == 1
        
        # Second call should use cache
        result2 = view_needs_update(db, "test_view", "test_collection", ["field1", "field2"])
        assert result2 is False
        assert db.view.call_count == 1  # Still only called once


if __name__ == "__main__":
    # Run tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))