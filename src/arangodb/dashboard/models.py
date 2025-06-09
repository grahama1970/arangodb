"""
Module: dashboard/models.py
Purpose: Pydantic models for dashboard data structures

Defines the data models for dashboards, widgets, and their configurations
that are persisted in ArangoDB.

External Dependencies:
- pydantic: https://docs.pydantic.dev/

Example Usage:
>>> from arangodb.dashboard.models import Dashboard, Widget
>>> dashboard = Dashboard(name="analytics", layout="grid", grid_columns=12)
>>> widget = Widget(type="metrics", title="Performance Metrics")
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, field_serializer


class WidgetPosition(BaseModel):
    """Position and size of a widget in the dashboard grid"""
    x: int = Field(ge=0, description="X coordinate in grid")
    y: int = Field(ge=0, description="Y coordinate in grid")
    width: int = Field(ge=1, le=12, description="Width in grid units")
    height: int = Field(ge=1, le=12, description="Height in grid units")
    

class WidgetConfig(BaseModel):
    """Configuration for a specific widget type"""
    refresh_interval: int = Field(default=5000, description="Refresh interval in milliseconds")
    data_source: Optional[str] = Field(default=None, description="AQL query or collection name")
    filters: Dict[str, Any] = Field(default_factory=dict)
    display_options: Dict[str, Any] = Field(default_factory=dict)


class Widget(BaseModel):
    """Individual widget definition"""
    model_config = ConfigDict(extra='allow')
    
    id: Optional[str] = Field(default=None, description="Widget unique identifier")
    type: Literal["metrics", "graph", "timeline", "table", "learning_curve"] = Field(
        description="Widget type"
    )
    title: str = Field(description="Widget display title")
    position: WidgetPosition = Field(default_factory=lambda: WidgetPosition(x=0, y=0, width=4, height=4))
    config: WidgetConfig = Field(default_factory=WidgetConfig)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO format string"""
        return dt.isoformat()
    

class DashboardLayout(BaseModel):
    """Dashboard layout configuration"""
    type: Literal["grid", "flex", "fixed"] = Field(default="grid")
    grid_columns: int = Field(default=12, ge=1, le=24)
    grid_row_height: int = Field(default=60, description="Height of each grid row in pixels")
    gap: int = Field(default=10, description="Gap between widgets in pixels")
    

class Dashboard(BaseModel):
    """Dashboard configuration model"""
    model_config = ConfigDict(extra='allow')
    
    id: Optional[str] = Field(default=None, description="Dashboard unique identifier")
    name: str = Field(description="Dashboard name")
    description: Optional[str] = Field(default=None)
    layout: DashboardLayout = Field(default_factory=DashboardLayout)
    widgets: List[Widget] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    owner: Optional[str] = Field(default=None, description="Dashboard owner username")
    shared_with: List[str] = Field(default_factory=list, description="Users with access")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO format string"""
        return dt.isoformat()
    
    def add_widget(self, widget: Widget) -> None:
        """Add a widget to the dashboard"""
        if not widget.id:
            widget.id = f"widget_{len(self.widgets)}_{int(datetime.utcnow().timestamp())}"
        self.widgets.append(widget)
        self.updated_at = datetime.utcnow()
        
    def remove_widget(self, widget_id: str) -> bool:
        """Remove a widget by ID"""
        initial_count = len(self.widgets)
        self.widgets = [w for w in self.widgets if w.id != widget_id]
        if len(self.widgets) < initial_count:
            self.updated_at = datetime.utcnow()
            return True
        return False
        
    def get_widget(self, widget_id: str) -> Optional[Widget]:
        """Get a widget by ID"""
        for widget in self.widgets:
            if widget.id == widget_id:
                return widget
        return None


class DashboardState(BaseModel):
    """Runtime state of a dashboard"""
    dashboard_id: str
    user_id: str
    active_filters: Dict[str, Any] = Field(default_factory=dict)
    selected_time_range: Optional[Dict[str, Union[datetime, str]]] = None
    widget_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    
    @field_serializer('last_accessed')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime to ISO format string"""
        return dt.isoformat()
        
    @field_serializer('selected_time_range')
    def serialize_time_range(self, time_range: Optional[Dict[str, Union[datetime, str]]]) -> Optional[Dict[str, str]]:
        """Serialize time range datetimes to ISO format strings"""
        if time_range is None:
            return None
        result = {}
        for key, value in time_range.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


if __name__ == "__main__":
    # Validate models with real data
    dashboard = Dashboard(
        name="RL Performance Dashboard",
        description="Monitor reinforcement learning metrics",
        layout=DashboardLayout(type="grid", grid_columns=12)
    )
    
    # Add a metrics widget
    metrics_widget = Widget(
        type="metrics",
        title="Model Accuracy",
        position=WidgetPosition(x=0, y=0, width=4, height=3),
        config=WidgetConfig(
            refresh_interval=2000,
            data_source="FOR m IN rl_metrics SORT m.timestamp DESC LIMIT 100 RETURN m"
        )
    )
    dashboard.add_widget(metrics_widget)
    
    # Add a learning curve widget
    curve_widget = Widget(
        type="learning_curve",
        title="Training Progress",
        position=WidgetPosition(x=4, y=0, width=8, height=6),
        config=WidgetConfig(
            data_source="FOR m IN rl_metrics COLLECT module = m.module INTO metrics RETURN {module, metrics}"
        )
    )
    dashboard.add_widget(curve_widget)
    
    print(f" Dashboard model validation passed")
    print(f"Dashboard: {dashboard.name}")
    print(f"Widgets: {len(dashboard.widgets)}")
    print(f"Layout: {dashboard.layout.type} with {dashboard.layout.grid_columns} columns")