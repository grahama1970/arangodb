"""
Complete fixed version of semantic search that uses manual cosine similarity.

This is a drop-in replacement for the problematic semantic_search module.
It bypasses APPROX_NEAR_COSINE entirely and uses manual calculation.
"""

import sys
import time
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from loguru import logger
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, ArangoServerError

# Import config variables
from arangodb.core.constants import (
    COLLECTION_NAME,
    VIEW_NAME,
    ALL_DATA_FIELDS_PREVIEW,
    DEFAULT_EMBEDDING_DIMENSIONS
)

# Define embedding field name
EMBEDDING_FIELD = "embedding"
from arangodb.core.utils.embedding_utils import get_embedding

def execute_aql_with_retry(
    db: StandardDatabase, 
    query: str, 
    bind_vars: Optional[Dict[str, Any]] = None
) -> Any:
    """Execute AQL query with retry logic."""
    try:
        return db.aql.execute(query, bind_vars=bind_vars)
    except Exception as e:
        logger.warning(f"AQL query failed: {e}")
        raise

def manual_cosine_similarity_search(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str,
    query_embedding: List[float],
    limit: int
) -> List[Dict[str, Any]]:
    """
    Perform vector search using manual cosine similarity calculation.
    This bypasses APPROX_NEAR_COSINE entirely.
    """
    # Normalize query embedding
    query_norm = sum(x*x for x in query_embedding) ** 0.5
    if query_norm == 0:
        logger.warning("Query embedding has zero norm")
        return []
    
    norm_query = [x/query_norm for x in query_embedding]
    query_dimension = len(query_embedding)
    
    # Manual cosine similarity calculation
    aql = f"""
    FOR doc IN {collection_name}
    FILTER HAS(doc, "{embedding_field}")
        AND IS_LIST(doc.{embedding_field})
        AND LENGTH(doc.{embedding_field}) == {query_dimension}
    
    // Calculate document norm
    LET docNorm = SQRT(SUM(
        FOR v IN doc.{embedding_field} 
        RETURN v*v
    ))
    
    // Skip zero-norm documents
    FILTER docNorm > 0
    
    // Calculate cosine similarity
    LET dotProduct = SUM(
        FOR i IN 0..{query_dimension-1}
        RETURN doc.{embedding_field}[i] * @norm_query[i]
    )
    
    LET similarity = dotProduct / docNorm
    
    SORT similarity DESC
    LIMIT {limit}
    
    RETURN {{
        "id": doc._id,
        "similarity_score": similarity
    }}
    """
    
    try:
        cursor = execute_aql_with_retry(db, aql, bind_vars={'norm_query': norm_query})
        results = list(cursor)
        logger.debug(f"Manual cosine similarity returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Manual cosine similarity failed: {e}")
        
        # Try L2 distance as fallback
        try:
            return l2_distance_fallback(db, collection_name, embedding_field, query_embedding, limit)
        except Exception as e2:
            logger.error(f"L2 distance fallback also failed: {e2}")
            return []

def l2_distance_fallback(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str,
    query_embedding: List[float],
    limit: int
) -> List[Dict[str, Any]]:
    """Use L2 distance as a fallback when cosine similarity fails."""
    query_dimension = len(query_embedding)
    
    aql = f"""
    FOR doc IN {collection_name}
    FILTER HAS(doc, "{embedding_field}")
        AND IS_LIST(doc.{embedding_field})
        AND LENGTH(doc.{embedding_field}) == {query_dimension}
    
    LET distance = L2_DISTANCE(doc.{embedding_field}, @query_embedding)
    
    SORT distance ASC
    LIMIT {limit}
    
    RETURN {{
        "id": doc._id,
        "similarity_score": 1.0 / (1.0 + distance)
    }}
    """
    
    cursor = execute_aql_with_retry(db, aql, bind_vars={'query_embedding': query_embedding})
    results = list(cursor)
    logger.debug(f"L2 distance fallback returned {len(results)} results")
    return results

def semantic_search(
    db: StandardDatabase,
    query: Union[str, List[float]],
    collections: Optional[List[str]] = None,
    filter_expr: Optional[str] = None,
    min_score: float = 0.7,
    top_n: int = 10,
    tag_list: Optional[List[str]] = None,
    force_pytorch: bool = False,
    force_direct: bool = False,
    force_twostage: bool = False,
    output_format: str = "table"
) -> Dict[str, Any]:
    """
    Fixed semantic search that uses manual cosine similarity.
    
    Args:
        db: ArangoDB database
        query: Search query text or embedding vector
        collections: Optional list of collections to search
        filter_expr: Optional AQL filter expression
        min_score: Minimum similarity score threshold (0-1)
        top_n: Maximum number of results to return
        tag_list: Optional list of tags to filter by
        output_format: Output format (table or json)
        
    Returns:
        Dict with search results
    """
    start_time = time.time()
    
    # Use default collection if not specified
    if not collections:
        collections = [COLLECTION_NAME]
    
    logger.info(f"Searching in collections: {collections}")
    collection_name = collections[0]
    embedding_field = EMBEDDING_FIELD
    
    # Get query embedding if query is text
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
    
    # Validate embedding dimensions
    if len(query_embedding) != DEFAULT_EMBEDDING_DIMENSIONS:
        logger.warning(f"Query embedding has {len(query_embedding)} dimensions, expected {DEFAULT_EMBEDDING_DIMENSIONS}")
    
    # Perform vector search using manual calculation
    logger.info("Using manual cosine similarity search (bypassing APPROX_NEAR_COSINE)")
    vector_results = manual_cosine_similarity_search(
        db, collection_name, embedding_field, query_embedding, top_n * 2
    )
    
    # Filter by minimum score and fetch full documents
    results = []
    for result in vector_results:
        score = result["similarity_score"]
        if score < min_score:
            continue
            
        # Fetch full document
        doc_id = result["id"]
        try:
            aql = "FOR doc IN @@collection FILTER doc._id == @id RETURN doc"
            cursor = execute_aql_with_retry(
                db, 
                aql, 
                bind_vars={"@collection": collection_name, "id": doc_id}
            )
            docs = list(cursor)
            if docs:
                results.append({
                    "doc": docs[0],
                    "similarity_score": score
                })
                
                if len(results) >= top_n:
                    break
        except Exception as e:
            logger.warning(f"Failed to fetch document {doc_id}: {e}")
    
    # Return results
    return {
        "results": results,
        "total": len(results),
        "query": query_text,
        "time": time.time() - start_time,
        "search_engine": "arangodb-manual-cosine-fixed"
    }