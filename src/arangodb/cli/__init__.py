"""
ArangoDB CLI Package
Module: __init__.py
Description: Package initialization and exports

Provides consistent command-line interface following stellar template.
"""

from arangodb.cli.main import app

__all__ = ["app"]
