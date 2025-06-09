"""
Module: dashboard/__init__.py
Purpose: Dashboard framework for ArangoDB visualization system

This module provides a comprehensive dashboard framework that extends the existing
visualization capabilities with real-time updates, widget management, and 
performance metrics tracking.

External Dependencies:
- fastapi: https://fastapi.tiangolo.com/
- arango: https://python-arango.readthedocs.io/
- pydantic: https://docs.pydantic.dev/

Example Usage:
>>> from arangodb.dashboard import DashboardManager
>>> manager = DashboardManager(db_connection)
>>> dashboard = manager.create_dashboard("analytics", layout="grid")
>>> dashboard.add_widget("metrics", position=(0, 0))
"""

from .manager import DashboardManager
from .config import DashboardConfig
from .models import Dashboard, Widget, WidgetPosition

__all__ = [
    "DashboardManager",
    "DashboardConfig", 
    "Dashboard",
    "Widget",
    "WidgetPosition"
]

__version__ = "0.1.0"