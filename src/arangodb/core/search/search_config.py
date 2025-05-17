"""
Search Configuration Module

Provides configuration options for different search methods and strategies.
Allows customization of search behavior per query type.

Example usage:
    config = SearchConfig(
        preferred_method=SearchMethod.SEMANTIC,
        enable_reranking=True,
        result_limit=20
    )
    
    results = hybrid_search.search_with_config(query, config)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class SearchMethod(Enum):
    """Available search methods."""
    BM25 = "bm25"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"
    TAG = "tag"
    GRAPH = "graph"


class RerankerType(Enum):
    """Available reranking methods."""
    NONE = "none"
    CROSS_ENCODER = "cross_encoder"
    CUSTOM = "custom"


@dataclass
class SearchConfig:
    """Configuration for search operations."""
    
    # Primary search method
    preferred_method: SearchMethod = SearchMethod.HYBRID
    
    # Hybrid search weights (if using hybrid)
    bm25_weight: float = 0.5
    semantic_weight: float = 0.5
    
    # Result configuration
    result_limit: int = 20
    min_score: Optional[float] = None
    
    # Reranking configuration
    enable_reranking: bool = False
    reranker_type: RerankerType = RerankerType.CROSS_ENCODER
    rerank_top_k: int = 50
    
    # Filter configuration
    tags: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    time_range: Optional[tuple] = None  # (start_time, end_time)
    
    # Advanced options
    include_graph_context: bool = False
    graph_depth: int = 2
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    
    # Performance options
    enable_caching: bool = True
    timeout_ms: int = 5000


@dataclass
class QueryTypeConfig:
    """Pre-configured search settings for different query types."""
    
    # Factual questions (prefer BM25)
    FACTUAL = SearchConfig(
        preferred_method=SearchMethod.BM25,
        enable_reranking=True,
        result_limit=10
    )
    
    # Conceptual/semantic questions (prefer semantic)
    CONCEPTUAL = SearchConfig(
        preferred_method=SearchMethod.SEMANTIC,
        enable_reranking=True,
        result_limit=15
    )
    
    # Exploratory questions (use hybrid)
    EXPLORATORY = SearchConfig(
        preferred_method=SearchMethod.HYBRID,
        bm25_weight=0.4,
        semantic_weight=0.6,
        enable_reranking=True,
        result_limit=25
    )
    
    # Recent context queries (time-filtered hybrid)
    RECENT_CONTEXT = SearchConfig(
        preferred_method=SearchMethod.HYBRID,
        result_limit=30,
        time_range=None  # Will be set dynamically
    )
    
    # Tag-based queries
    TAG_BASED = SearchConfig(
        preferred_method=SearchMethod.TAG,
        result_limit=20
    )
    
    # Graph exploration
    GRAPH_EXPLORATION = SearchConfig(
        preferred_method=SearchMethod.GRAPH,
        include_graph_context=True,
        graph_depth=3,
        result_limit=15
    )


class SearchConfigManager:
    """Manages search configurations and provides query routing."""
    
    def __init__(self):
        self.custom_configs = {}
        self.default_config = SearchConfig()
    
    def get_config_for_query(self, query: str, query_type: Optional[str] = None) -> SearchConfig:
        """
        Get appropriate search configuration based on query and type.
        
        Args:
            query: The search query text
            query_type: Optional explicit query type
            
        Returns:
            SearchConfig: Appropriate configuration for the query
        """
        # If explicit type provided, use predefined config
        if query_type:
            query_type_upper = query_type.upper()
            if hasattr(QueryTypeConfig, query_type_upper):
                return getattr(QueryTypeConfig, query_type_upper)
        
        # Heuristic-based routing
        query_lower = query.lower()
        
        # Tag-based queries (check first as most specific)
        if "tag:" in query_lower or "#" in query:
            return QueryTypeConfig.TAG_BASED
        
        # Graph exploration (check before factual to catch "what's related")
        if any(word in query_lower for word in ["related", "connected", "linked", "graph"]):
            return QueryTypeConfig.GRAPH_EXPLORATION
        
        # Factual indicators
        if any(word in query_lower for word in ["what", "when", "where", "how many", "how much"]):
            return QueryTypeConfig.FACTUAL
        
        # Conceptual indicators  
        if any(word in query_lower for word in ["why", "explain", "understand", "theory"]):
            return QueryTypeConfig.CONCEPTUAL
        
        # Recent/temporal queries
        if any(word in query_lower for word in ["recent", "latest", "today", "yesterday", "last"]):
            config = QueryTypeConfig.RECENT_CONTEXT
            # Set dynamic time range (e.g., last 7 days)
            import datetime
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(days=7)
            config.time_range = (start_time.isoformat(), end_time.isoformat())
            return config
        
        # Default to exploratory/hybrid
        return QueryTypeConfig.EXPLORATORY
    
    def register_custom_config(self, name: str, config: SearchConfig):
        """Register a custom search configuration."""
        self.custom_configs[name] = config
    
    def get_custom_config(self, name: str) -> Optional[SearchConfig]:
        """Get a registered custom configuration."""
        return self.custom_configs.get(name)


if __name__ == "__main__":
    """Validate search configuration functionality."""
    
    # Test basic config creation
    basic_config = SearchConfig()
    print(f"Default config: {basic_config.preferred_method.value}")
    
    # Test query type configs
    manager = SearchConfigManager()
    
    test_queries = [
        ("What is Python?", "FACTUAL"),
        ("Why is recursion important?", "CONCEPTUAL"),
        ("Show me recent updates", "RECENT"),
        ("Find documents with tag:python", "TAG"),
        ("What's related to databases?", "GRAPH"),
        ("General information about coding", "EXPLORATORY")
    ]
    
    for query, expected_type in test_queries:
        config = manager.get_config_for_query(query)
        print(f"Query: '{query}' -> Method: {config.preferred_method.value}")
    
    # Test custom config
    custom = SearchConfig(
        preferred_method=SearchMethod.SEMANTIC,
        enable_reranking=True,
        result_limit=50
    )
    manager.register_custom_config("semantic_heavy", custom)
    retrieved = manager.get_custom_config("semantic_heavy")
    print(f"Custom config retrieved: {retrieved.result_limit} results")
    
    print("✅ Search configuration validation passed!")