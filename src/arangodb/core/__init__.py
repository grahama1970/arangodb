"""
ArangoDB Core Module

This module provides the core business logic for ArangoDB operations, search functionality, 
memory agent, and graph traversal, independent of user interfaces.

Core components:
- Database setup and connection
- Document and relationship operations
- Search algorithms (BM25, semantic, hybrid)
- Memory agent functionality
- Graph traversal and management
- Utility functions
"""

# Version information
__version__ = "0.1.0"

# Note: The following imports will be activated as refactoring continues
"""
# Import core functionality to make it available at the package level
from arangodb.core.arango_setup import (
    connect_arango,
    ensure_database,
    ensure_collection,
    ensure_edge_collections,
    ensure_graph,
    ensure_arangosearch_view,
    ensure_memory_agent_collections,
)

from arangodb.core.db_operations import (
    create_document,
    get_document,
    update_document,
    delete_document,
    query_documents,
    create_relationship,
    delete_relationship_by_key,
    create_message,
    get_message,
    update_message,
    delete_message,
    get_conversation_messages,
    delete_conversation,
    link_message_to_document,
    get_documents_for_message,
    get_messages_for_document,
)

# Export constants
from arangodb.core.constants import (
    ARANGO_DB_NAME,
    COLLECTION_NAME,
    EDGE_COLLECTION_NAME,
    GRAPH_NAME,
    MESSAGES_COLLECTION_NAME,
    MEMORY_COLLECTION,
    MEMORY_EDGE_COLLECTION,
    MEMORY_GRAPH_NAME,
    MEMORY_VIEW_NAME,
    SEARCH_FIELDS,
)
"""
# Version information
__version__ = "0.1.0"