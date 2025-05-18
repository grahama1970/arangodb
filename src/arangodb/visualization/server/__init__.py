"""D3.js visualization server package

This package provides FastAPI server for serving D3.js visualizations.
"""

from .visualization_server import app

__all__ = ["app"]