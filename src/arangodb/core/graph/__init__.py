"""
Graph Operations Core Module
Module: __init__.py
Description: Package initialization and exports

This module provides graph functionality for ArangoDB, including:
- Graph traversal 
- Relationship management
- Path finding
- Graph analysis
- Temporal relationships
- Enhanced relationship attributes

These functions support knowledge graph operations and querying.
"""

# Import and expose graph functions
from .enhanced_relationships import (
    create_temporal_relationship,
    create_edge_from_cli
)

# Import db_operations functions that are used for graph operations
from ..db_operations import (
    create_relationship,
    delete_relationship_by_key
)

# Import graph traverse from search module (it's actually in search)
from ..search.graph_traverse import graph_traverse

# Export named packages
__all__ = [
    "graph_traverse",
    "create_relationship",
    "delete_relationship_by_key",
    "create_temporal_relationship",
    "create_edge_from_cli",
]