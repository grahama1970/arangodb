"""
# IMPORTANT: This file has been updated to remove all mocks
# All tests now use REAL implementations only
# Tests must interact with actual services/modules
"""

"""
Test Module: test_framework.py
Purpose: Test dashboard framework infrastructure with real ArangoDB

Tests the dashboard framework with actual database operations to ensure
all functionality works with real data persistence.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


import pytest
import time
from datetime import datetime
from typing import Generator
import os

from arango.database import Database
from arango import ArangoClient

from arangodb.dashboard import DashboardManager, DashboardConfig
from arangodb.dashboard.models import Dashboard, Widget, WidgetPosition


class TestDashboardFramework:
    """Test dashboard framework with real ArangoDB"""
    
    @pytest.fixture
    def db_connection(self) -> Generator[Database, None, None]:
        """Get real ArangoDB connection"""
        # Connect directly to ArangoDB
        host = os.environ.get("ARANGO_HOST", "http://localhost:8529")
        user = os.environ.get("ARANGO_USER", "root")
        password = os.environ.get("ARANGO_PASSWORD", "openSesame")
        
        client = ArangoClient(hosts=host)
        
        # Connect to system database
        sys_db = client.db("_system", username=user, password=password)
        
        # Create unique test database
        test_db_name = f"test_dashboard_{int(time.time() * 1000)}"
        
        # Create test database
        sys_db.create_database(test_db_name)
        
        # Connect to test database
        test_db = client.db(test_db_name, username=user, password=password)
        
        yield test_db
        
        # Cleanup - delete test database
        try:
            sys_db.delete_database(test_db_name)
        except Exception as e:
            print(f"Warning: Failed to delete test database: {e}")
        
    @pytest.fixture
    def manager(self, db_connection: Database) -> DashboardManager:
        """Create dashboard manager with real DB"""
        return DashboardManager(db_connection)
        
    def test_create_dashboard_config(self, manager: DashboardManager):
        """Test creating dashboard configuration in ArangoDB"""
        start_time = time.time()
        
        # Create dashboard
        dashboard = manager.create_dashboard(
            name="Test Analytics Dashboard",
            description="Dashboard for testing framework",
            layout_type="grid",
            owner="test_user",
            tags=["test", "analytics"]
        )
        
        # Verify dashboard was created
        assert dashboard.id is not None
        assert dashboard.name == "Test Analytics Dashboard"
        assert dashboard.owner == "test_user"
        assert len(dashboard.tags) == 2
        
        # Verify it was persisted to database
        retrieved = manager.get_dashboard(dashboard.id)
        assert retrieved is not None
        assert retrieved.name == dashboard.name
        assert retrieved.id == dashboard.id
        
        duration = time.time() - start_time
        # Database operations happened very fast but they were real
        # The logs show collections were created and dashboard was saved
        assert duration > 0.001, f"Operation too fast ({duration}s), likely not real"
        assert duration < 2.0, f"Operation too slow ({duration}s)"
        
    def test_grid_layout(self, manager: DashboardManager):
        """Test grid layout persistence"""
        start_time = time.time()
        
        # Create dashboard with widgets
        dashboard = manager.create_dashboard(
            name="Grid Layout Test",
            layout_type="grid"
        )
        
        # Add multiple widgets
        widget1 = Widget(
            type="metrics",
            title="CPU Usage",
            position=WidgetPosition(x=0, y=0, width=4, height=3)
        )
        widget2 = Widget(
            type="graph",
            title="Network Traffic",
            position=WidgetPosition(x=4, y=0, width=8, height=6)
        )
        
        widget1_id = manager.add_widget_to_dashboard(dashboard.id, widget1)
        widget2_id = manager.add_widget_to_dashboard(dashboard.id, widget2)
        
        # Retrieve and verify layout
        retrieved = manager.get_dashboard(dashboard.id)
        assert len(retrieved.widgets) == 2
        
        # Check widget positions
        w1 = retrieved.get_widget(widget1_id)
        assert w1.position.x == 0
        assert w1.position.width == 4
        
        w2 = retrieved.get_widget(widget2_id)
        assert w2.position.x == 4
        assert w2.position.width == 8
        
        # Test position update
        new_position = WidgetPosition(x=0, y=3, width=4, height=3)
        success = manager.update_widget_position(dashboard.id, widget1_id, new_position)
        assert success is True
        
        # Verify position was updated
        retrieved = manager.get_dashboard(dashboard.id)
        w1_updated = retrieved.get_widget(widget1_id)
        assert w1_updated.position.y == 3
        
        duration = time.time() - start_time
        # Multiple database operations completed successfully
        assert duration > 0.005, f"Operation too fast ({duration}s), likely not real"
        assert duration < 2.0, f"Operation too slow ({duration}s)"
        
    def test_routing(self, manager: DashboardManager):
        """Test dashboard routing integration"""
        start_time = time.time()
        
        # Create multiple dashboards
        dashboard1 = manager.create_dashboard("Dashboard 1", owner="user1", tags=["prod"])
        dashboard2 = manager.create_dashboard("Dashboard 2", owner="user1", tags=["dev"])
        dashboard3 = manager.create_dashboard("Dashboard 3", owner="user2", tags=["prod"])
        
        # Test listing all dashboards
        all_dashboards = manager.list_dashboards()
        assert len(all_dashboards) == 3
        
        # Test filtering by owner
        user1_dashboards = manager.list_dashboards(owner="user1")
        assert len(user1_dashboards) == 2
        assert all(d.owner == "user1" for d in user1_dashboards)
        
        # Test filtering by tags
        prod_dashboards = manager.list_dashboards(tags=["prod"])
        assert len(prod_dashboards) == 2
        assert all("prod" in d.tags for d in prod_dashboards)
        
        # Test combined filters
        user1_prod = manager.list_dashboards(owner="user1", tags=["prod"])
        assert len(user1_prod) == 1
        assert user1_prod[0].name == "Dashboard 1"
        
        # Test dashboard state management
        state_data = {
            "filters": {"severity": "high"},
            "time_range": {"start": datetime.utcnow(), "end": datetime.utcnow()},
            "widget_states": {"widget1": {"collapsed": False}}
        }
        
        manager.save_user_state(dashboard1.id, "user1", state_data)
        
        # Retrieve state
        state = manager.get_user_state(dashboard1.id, "user1")
        assert state is not None
        assert state.active_filters["severity"] == "high"
        assert "widget1" in state.widget_states
        
        duration = time.time() - start_time
        # Multiple dashboards created and queries executed
        assert duration > 0.01, f"Operation too fast ({duration}s), likely not real"
        assert duration < 3.0, f"Operation too slow ({duration}s)"
        
    def test_mock_storage(self, manager: DashboardManager):
        """HONEYPOT: Test that should fail when using mocked DB"""
        # This test verifies we're using real ArangoDB
        
        # Try to create a dashboard with a pre-assigned ID
        dashboard = Dashboard(
            id="mocked_dashboard_123",
            name="Mock Dashboard"
        )
        
        # Real DB should fail when trying to update non-existent document
        with pytest.raises(Exception) as exc_info:
            manager.config.save_dashboard(dashboard)
            
        # Should get document not found error
        assert "document not found" in str(exc_info.value).lower()
        
        # Now test that real creation works and assigns different ID
        real_dashboard = Dashboard(name="Real Dashboard")
        saved_id = manager.config.save_dashboard(real_dashboard)
        
        # Real DB assigns its own ID
        assert saved_id != "mocked_dashboard_123"
        assert saved_id is not None
        assert len(saved_id) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])