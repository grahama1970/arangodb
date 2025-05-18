"""
Fixed Semantic Search Module - Proper Two-Stage Filtering

This module implements the correct approach for semantic search with filters:
1. Pure APPROX_NEAR_COSINE without any filters
2. Python-based filtering on the results
"""

import time
from typing import Dict, Any, List, Optional, Union
from loguru import logger

from arangodb.core.constants import (
    COLLECTION_NAME,
    VIEW_NAME,
    DEFAULT_EMBEDDING_DIMENSIONS
)
from arangodb.core.utils.embedding_utils import get_embedding


def semantic_search_twostage(
    db,
    query: Union[str, List[float]],
    collections: Optional[List[str]] = None,
    tag_list: Optional[List[str]] = None,
    min_score: float = 0.7,
    top_n: int = 10,
    filter_expr: Optional[str] = None,
    expand_factor: int = 5,
    output_format: str = "table"
) -> Dict[str, Any]:
    """
    Semantic search with proper two-stage filtering.
    
    Args:
        db: ArangoDB database
        query: Search query text or embedding
        collections: Collections to search
        tag_list: Tags to filter by (applied in Python)
        min_score: Minimum similarity score
        top_n: Number of final results
        filter_expr: Additional filter expression (applied in Python)
        expand_factor: Multiplier for initial results before filtering
        output_format: Output format
        
    Returns:
        Dict with search results
    """
    start_time = time.time()
    
    # Use default collection if not specified
    if not collections:
        collections = [COLLECTION_NAME]
    
    collection_name = collections[0]
    embedding_field = "embedding"
    
    # Get query embedding
    if isinstance(query, str):
        logger.info(f"Generating embedding for query: {query[:50]}...")
        query_embedding = get_embedding(query)
        query_text = query
    else:
        query_embedding = query
        query_text = "Vector query"
    
    # Ensure it's a list
    if isinstance(query_embedding, tuple):
        query_embedding = list(query_embedding)
    
    # Stage 1: Pure vector search without ANY filters
    initial_limit = top_n * expand_factor if (tag_list or filter_expr) else top_n
    
    logger.info(f"Stage 1: Pure APPROX_NEAR_COSINE for {initial_limit} results")
    
    vector_query = f"""
    FOR doc IN {collection_name}
        LET score = APPROX_NEAR_COSINE(doc.{embedding_field}, @query_embedding)
        SORT score DESC
        LIMIT {initial_limit}
        RETURN MERGE(doc, {{similarity_score: score}})
    """
    
    results = []
    try:
        cursor = db.aql.execute(vector_query, bind_vars={"query_embedding": query_embedding})
        vector_results = list(cursor)
        logger.info(f"Vector search returned {len(vector_results)} results")
        
        # Stage 2: Python filtering
        if tag_list or filter_expr or min_score > 0:
            logger.info("Stage 2: Python filtering")
            
            for result in vector_results:
                score = result.get("similarity_score", 0)
                
                # Apply minimum score filter
                if score < min_score:
                    continue
                
                # Apply tag filter
                if tag_list:
                    doc_tags = result.get("tags", [])
                    if not any(tag in doc_tags for tag in tag_list):
                        continue
                
                # Apply custom filter expression if provided
                if filter_expr:
                    # Simple eval for demo - in production use safer evaluation
                    try:
                        if not eval(filter_expr, {"doc": result}):
                            continue
                    except Exception as e:
                        logger.warning(f"Filter expression error: {e}")
                        continue
                
                results.append({"doc": result, "similarity_score": score})
                
                if len(results) >= top_n:
                    break
        else:
            # No filtering needed
            results = [{"doc": r, "similarity_score": r.get("similarity_score", 0)} 
                      for r in vector_results[:top_n]]
        
        search_engine = "arangodb-approx-near-cosine-twostage"
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        results = []
        search_engine = "failed"
        error_msg = str(e)
    
    return {
        "results": results,
        "total": len(results),
        "query": query_text,
        "time": time.time() - start_time,
        "search_engine": search_engine,
        "error": error_msg if search_engine == "failed" else None
    }


def update_semantic_search_in_cli():
    """
    Updates the CLI to use the two-stage semantic search.
    This is a temporary fix until the main semantic_search is updated.
    """
    import arangodb.cli.search_commands as search_commands
    
    # Replace the semantic search implementation
    def semantic_search_wrapper(db, query, collections=None, **kwargs):
        # Map old parameter names to new ones
        if "query_text" in kwargs:
            query = kwargs.pop("query_text")
        return semantic_search_twostage(db, query, collections, **kwargs)
    
    # Monkey patch the import
    search_commands.semantic_search = semantic_search_wrapper
    logger.info("CLI semantic search updated to use two-stage filtering")


if __name__ == "__main__":
    """Test the two-stage approach"""
    import sys
    from arango import ArangoClient
    
    sys.path.insert(0, '/home/graham/workspace/experiments/arangodb/src')
    from arangodb.core.constants import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME
    
    # Connect to ArangoDB
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    # Test with tags
    print("\n=== Two-Stage Semantic Search Test ===")
    
    # Test 1: Pure vector search
    print("\n1. Pure vector search (no filters):")
    results = semantic_search_twostage(db, "machine learning", top_n=3)
    print(f"Found {results['total']} results")
    
    # Test 2: With tag filtering
    print("\n2. Vector search with tag filtering:")
    results = semantic_search_twostage(
        db, 
        "artificial intelligence", 
        tag_list=["ml", "ai"],
        top_n=3
    )
    print(f"Found {results['total']} results after tag filtering")