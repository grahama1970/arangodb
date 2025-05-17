"""
ArangoDB MCP Layer

This module provides MCP (Machine-Collaborator Protocol) integration for ArangoDB operations,
built on top of the core business logic layer. MCP allows Claude to integrate with
ArangoDB through standardized interfaces.

Components:
- Search operations (BM25, semantic, hybrid, etc.)
- Document management (CRUD operations)
- Graph traversal and relationships
- Memory agent integration
- Type definitions for MCP
"""

# Import and expose search operations
from arangodb.mcp.search_operations import (
    mcp_bm25_search,
    mcp_semantic_search,
    mcp_hybrid_search,
    mcp_tag_search,
    mcp_keyword_search,
    mcp_graph_traverse
)

# Import and expose document operations
from arangodb.mcp.document_operations import (
    mcp_create_document,
    mcp_get_document,
    mcp_update_document,
    mcp_delete_document,
    mcp_create_relationship,
    mcp_delete_relationship
)

# Import and expose memory operations
from arangodb.mcp.memory_operations import (
    mcp_store_conversation,
    mcp_get_conversation_history,
    mcp_search_memory,
    mcp_detect_contradictions
)

# Exports
__all__ = [
    # Search operations
    'mcp_bm25_search',
    'mcp_semantic_search',
    'mcp_hybrid_search',
    'mcp_tag_search',
    'mcp_keyword_search',
    'mcp_graph_traverse',
    
    # Document operations
    'mcp_create_document',
    'mcp_get_document',
    'mcp_update_document',
    'mcp_delete_document',
    'mcp_create_relationship',
    'mcp_delete_relationship',
    
    # Memory operations
    'mcp_store_conversation',
    'mcp_get_conversation_history',
    'mcp_search_memory',
    'mcp_detect_contradictions'
]

__version__ = "0.1.0"