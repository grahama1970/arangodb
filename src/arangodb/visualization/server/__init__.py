"""D3.js visualization server package
Module: __init__.py
Description: Package initialization and exports

This package provides FastAPI server for serving D3.js visualizations.
"""

from .visualization_server import app

__all__ = ["app"]