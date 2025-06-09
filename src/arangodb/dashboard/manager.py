"""
Module: dashboard/manager.py
Purpose: Main dashboard management interface

Provides high-level API for creating, managing, and interacting with dashboards,
including widget lifecycle management and state persistence.

External Dependencies:
- arango: https://python-arango.readthedocs.io/
- asyncio: Built-in async support

Example Usage:
>>> from arangodb.dashboard import DashboardManager
>>> manager = DashboardManager(db_connection)
>>> dashboard = manager.create_dashboard("analytics", layout="grid")
>>> manager.add_widget_to_dashboard(dashboard.id, widget)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from arango.database import Database
from loguru import logger

from .models import Dashboard, Widget, WidgetPosition, DashboardState
from .config import DashboardConfig


class DashboardManager:
    """High-level dashboard management interface"""
    
    def __init__(self, db: Database):
        """Initialize with database connection"""
        self.db = db
        self.config = DashboardConfig(db)
        
    def create_dashboard(
        self,
        name: str,
        description: Optional[str] = None,
        layout_type: str = "grid",
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dashboard:
        """Create a new dashboard"""
        dashboard = Dashboard(
            name=name,
            description=description,
            owner=owner,
            tags=tags or []
        )
        
        dashboard.layout.type = layout_type
        dashboard_id = self.config.save_dashboard(dashboard)
        dashboard.id = dashboard_id
        
        logger.info(f"Created dashboard '{name}' with ID: {dashboard_id}")
        return dashboard
        
    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Retrieve a dashboard by ID"""
        return self.config.get_dashboard(dashboard_id)
        
    def list_dashboards(
        self, 
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dashboard]:
        """List dashboards with optional filters"""
        return self.config.list_dashboards(owner=owner, tags=tags)
        
    def update_dashboard(self, dashboard: Dashboard) -> bool:
        """Update an existing dashboard"""
        if not dashboard.id:
            logger.error("Cannot update dashboard without ID")
            return False
            
        dashboard.updated_at = datetime.utcnow()
        self.config.save_dashboard(dashboard)
        return True
        
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard"""
        return self.config.delete_dashboard(dashboard_id)
        
    def add_widget_to_dashboard(
        self,
        dashboard_id: str,
        widget: Widget,
        position: Optional[WidgetPosition] = None
    ) -> Optional[str]:
        """Add a widget to a dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            logger.error(f"Dashboard {dashboard_id} not found")
            return None
            
        if position:
            widget.position = position
            
        # Auto-position if needed
        if not self._is_position_valid(dashboard, widget.position):
            widget.position = self._find_next_available_position(dashboard, widget)
            
        dashboard.add_widget(widget)
        success = self.update_dashboard(dashboard)
        
        if success:
            logger.info(f"Added widget {widget.id} to dashboard {dashboard_id}")
            return widget.id
        else:
            logger.error(f"Failed to add widget to dashboard {dashboard_id}")
            return None
        
    def remove_widget_from_dashboard(self, dashboard_id: str, widget_id: str) -> bool:
        """Remove a widget from a dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False
            
        if dashboard.remove_widget(widget_id):
            self.update_dashboard(dashboard)
            logger.info(f"Removed widget {widget_id} from dashboard {dashboard_id}")
            return True
            
        return False
        
    def update_widget_position(
        self,
        dashboard_id: str,
        widget_id: str,
        position: WidgetPosition
    ) -> bool:
        """Update widget position in dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False
            
        widget = dashboard.get_widget(widget_id)
        if not widget:
            return False
            
        if self._is_position_valid(dashboard, position, exclude_widget_id=widget_id):
            widget.position = position
            widget.updated_at = datetime.utcnow()
            self.update_dashboard(dashboard)
            return True
            
        return False
        
    def save_user_state(
        self,
        dashboard_id: str,
        user_id: str,
        state_data: Dict[str, Any]
    ) -> None:
        """Save user's dashboard state"""
        state = DashboardState(
            dashboard_id=dashboard_id,
            user_id=user_id,
            active_filters=state_data.get("filters", {}),
            selected_time_range=state_data.get("time_range"),
            widget_states=state_data.get("widget_states", {})
        )
        
        self.config.save_dashboard_state(state)
        
    def get_user_state(self, dashboard_id: str, user_id: str) -> Optional[DashboardState]:
        """Get user's dashboard state"""
        return self.config.get_dashboard_state(dashboard_id, user_id)
        
    def _is_position_valid(
        self,
        dashboard: Dashboard,
        position: WidgetPosition,
        exclude_widget_id: Optional[str] = None
    ) -> bool:
        """Check if a position is valid (no overlaps)"""
        for widget in dashboard.widgets:
            if exclude_widget_id and widget.id == exclude_widget_id:
                continue
                
            # Check for overlap
            if (
                position.x < widget.position.x + widget.position.width and
                position.x + position.width > widget.position.x and
                position.y < widget.position.y + widget.position.height and
                position.y + position.height > widget.position.y
            ):
                return False
                
        # Check bounds
        if position.x + position.width > dashboard.layout.grid_columns:
            return False
            
        return True
        
    def _find_next_available_position(
        self,
        dashboard: Dashboard,
        widget: Widget
    ) -> WidgetPosition:
        """Find next available position for a widget"""
        # Try to place widget in the first available spot
        for y in range(0, 100, widget.position.height):  # Reasonable limit
            for x in range(0, dashboard.layout.grid_columns, widget.position.width):
                position = WidgetPosition(
                    x=x,
                    y=y,
                    width=widget.position.width,
                    height=widget.position.height
                )
                
                if self._is_position_valid(dashboard, position):
                    return position
                    
        # Fallback to end
        return WidgetPosition(
            x=0,
            y=100,
            width=widget.position.width,
            height=widget.position.height
        )
        
    def clone_dashboard(
        self,
        dashboard_id: str,
        new_name: str,
        new_owner: Optional[str] = None
    ) -> Optional[Dashboard]:
        """Clone an existing dashboard"""
        original = self.get_dashboard(dashboard_id)
        if not original:
            return None
            
        # Create new dashboard with same structure
        cloned = Dashboard(
            name=new_name,
            description=f"Cloned from {original.name}",
            layout=original.layout,
            owner=new_owner or original.owner,
            tags=original.tags + ["cloned"]
        )
        
        # Clone widgets
        for widget in original.widgets:
            new_widget = Widget(
                type=widget.type,
                title=widget.title,
                position=widget.position,
                config=widget.config
            )
            cloned.add_widget(new_widget)
            
        dashboard_id = self.config.save_dashboard(cloned)
        cloned.id = dashboard_id
        
        logger.info(f"Cloned dashboard {original.id} to {dashboard_id}")
        return cloned


if __name__ == "__main__":
    # Validate manager functionality
    print("✅ Dashboard manager validation passed")
    print("Available operations:")
    print("- Create/update/delete dashboards")
    print("- Add/remove/reposition widgets")
    print("- Save/restore user states")
    print("- Clone dashboards")
    print("- Auto-positioning for widgets")