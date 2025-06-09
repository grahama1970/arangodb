"""
Module: __init__.py
Description: ArangoDB package initialization and exports

External Dependencies:
- python-arango: https://docs.python-arango.com/
- litellm: https://docs.litellm.ai/

Sample Input:
>>> from arangodb import ArangoDBClient
>>> client = ArangoDBClient()
>>> client.connect()

Expected Output:
>>> # Returns StandardDatabase instance

Example Usage:
>>> from arangodb import ArangoDBClient, DatabaseOperations
>>> client = ArangoDBClient()
>>> db = client.connect()
>>> ops = DatabaseOperations(db)
>>> ops.query("FOR doc IN documents RETURN doc")
"""

__version__ = "0.1.0"

# Core database connections
from .core.arango_setup import connect_arango
from .core.utils.config_validator import ArangoConfig
from .core.db_connection_wrapper import DatabaseOperations
from .core.db_operations import (
    create_document,
    get_document,
    update_document,
    delete_document,
    query_documents,
    create_message,
    get_message,
    update_message,
    delete_message,
    get_conversation_messages,
    delete_conversation,
    link_message_to_document,
    get_documents_for_message,
    get_messages_for_document,
    create_relationship,
    delete_relationship_by_key
)

# Memory management
from .core.memory import (
    MemoryAgent,
    EpisodeManager,
    ContradictionLogger
)

# Search functionality
from .core.search import (
    semantic_search,
    hybrid_search,
    bm25_search,
    cross_encoder_rerank,
    tag_search,
    graph_traverse
)

# Graph operations
from .core.graph import (
    create_temporal_relationship,
    create_edge_from_cli,
    graph_traverse as graph_traverse_from_graph
)

# Models
from .core.models import (
    DocumentReference,
    SearchResult,
    TemporalEntity
)

# Q&A Generation
from .qa_generation import (
    QAGenerator,
    QAValidator,
    QAExporter
)

# Visualization
from .visualization import (
    D3VisualizationEngine,
    DataTransformer
)

# Dashboard
from .dashboard import DashboardManager

# MCP Server
from .mcp import (
    mcp_bm25_search,
    mcp_semantic_search,
    mcp_hybrid_search,
    mcp_create_document,
    mcp_get_document
)

# Create convenience client class
class ArangoDBClient:
    """Main client for ArangoDB operations"""
    
    def __init__(self, config: ArangoConfig = None):
        """Initialize ArangoDBClient
        
        Args:
            config: Optional ArangoConfig instance. If not provided, 
                    environment variables will be used by connect_arango()
        """
        self.config = config
        self._db = None
        
    def connect(self):
        """Connect to ArangoDB"""
        # connect_arango uses environment variables, not config parameter
        self._db = connect_arango()
        return self._db
        
    @property
    def db(self):
        """Get database connection"""
        if not self._db:
            self._db = self.connect()
        return self._db
        
    def get_operations(self):
        """Get DatabaseOperations instance"""
        return DatabaseOperations(self.db)

# Export main interfaces
__all__ = [
    # Version
    "__version__",
    
    # Client
    "ArangoDBClient",
    
    # Core
    "connect_arango",
    "ArangoConfig", 
    "DatabaseOperations",
    "create_document",
    "get_document",
    "update_document",
    "delete_document",
    "query_documents",
    "create_message",
    "get_message",
    "update_message",
    "delete_message",
    "get_conversation_messages",
    "delete_conversation",
    "link_message_to_document",
    "get_documents_for_message",
    "get_messages_for_document",
    "create_relationship",
    "delete_relationship_by_key",
    
    # Memory
    "MemoryAgent",
    "EpisodeManager",
    "ContradictionLogger",
    
    # Search
    "semantic_search",
    "hybrid_search",
    "bm25_search",
    "cross_encoder_rerank",
    "tag_search",
    "graph_traverse",
    
    # Graph
    "create_temporal_relationship",
    "create_edge_from_cli",
    
    # Models
    "DocumentReference",
    "SearchResult",
    "TemporalEntity",
    
    # Q&A
    "QAGenerator",
    "QAValidator",
    "QAExporter",
    
    # Visualization
    "D3VisualizationEngine",
    "DataTransformer",
    
    # Dashboard
    "DashboardManager",
    
    # MCP
    "mcp_bm25_search",
    "mcp_semantic_search",
    "mcp_hybrid_search",
    "mcp_create_document",
    "mcp_get_document"
]
