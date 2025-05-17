"""
Fixed Semantic Search Module

This module provides a working implementation of vector similarity search using ArangoDB.
Since APPROX_NEAR_COSINE fails with HTTP 500 errors, we use manual cosine similarity
calculation or L2_DISTANCE as alternatives.
"""

import time
from typing import Dict, Any, List, Optional, Union
from loguru import logger
from arango.database import StandardDatabase
from arangodb.core.constants import DEFAULT_EMBEDDING_DIMENSIONS
from arangodb.core.utils.embedding_utils import get_embedding

def get_vector_search_results(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str,
    query_embedding: List[float],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform vector search using manual cosine similarity.
    
    This is a fallback for when APPROX_NEAR_COSINE doesn't work.
    """
    # Normalize query embedding
    query_norm = sum(x*x for x in query_embedding) ** 0.5
    if query_norm == 0:
        logger.warning("Query embedding has zero norm")
        return []
    
    norm_query = [x/query_norm for x in query_embedding]
    
    # Use manual cosine similarity calculation
    aql = f"""
    FOR doc IN {collection_name}
    FILTER HAS(doc, "{embedding_field}")
        AND IS_LIST(doc.{embedding_field})
        AND LENGTH(doc.{embedding_field}) == {len(query_embedding)}
    
    // Calculate document norm
    LET docNorm = SQRT(SUM(
        FOR v IN doc.{embedding_field} 
        RETURN v*v
    ))
    
    // Skip zero-norm documents
    FILTER docNorm > 0
    
    // Normalize document embedding
    LET normDoc = (
        FOR v IN doc.{embedding_field} 
        RETURN v / docNorm
    )
    
    // Calculate cosine similarity
    LET dotProduct = SUM(
        FOR i IN 0..{len(query_embedding)-1}
        RETURN normDoc[i] * @norm_query[i]
    )
    
    SORT dotProduct DESC
    LIMIT {limit}
    
    RETURN {{
        "id": doc._id,
        "similarity_score": dotProduct
    }}
    """
    
    try:
        cursor = db.aql.execute(aql, bind_vars={'norm_query': norm_query})
        results = list(cursor)
        logger.debug(f"Manual cosine similarity returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Manual vector search failed: {e}")
        return []

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
        collections = ["memory_documents"]
    
    collection_name = collections[0]
    embedding_field = "embedding"
    
    # Get query embedding if query is text
    if isinstance(query, str):
        logger.info(f"Generating embedding for query: {query[:50]}...")
        query_embedding = get_embedding(query)
        query_text = query
    else:
        query_embedding = query
        query_text = "Vector query"
    
    # Validate embedding dimensions
    if len(query_embedding) != DEFAULT_EMBEDDING_DIMENSIONS:
        logger.warning(f"Query embedding has {len(query_embedding)} dimensions, expected {DEFAULT_EMBEDDING_DIMENSIONS}")
    
    # Get vector search results using manual calculation
    vector_results = get_vector_search_results(
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
            cursor = db.aql.execute(
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
        "search_engine": "arangodb-manual-cosine"
    }

# Additional helper functions for different distance metrics

def l2_distance_search(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str,
    query_embedding: List[float],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform vector search using L2 distance.
    
    Note: Lower distance = more similar
    """
    aql = f"""
    FOR doc IN {collection_name}
    FILTER HAS(doc, "{embedding_field}")
        AND IS_LIST(doc.{embedding_field})
        AND LENGTH(doc.{embedding_field}) == {len(query_embedding)}
    
    LET distance = L2_DISTANCE(doc.{embedding_field}, @query_embedding)
    
    SORT distance ASC
    LIMIT {limit}
    
    RETURN {{
        "id": doc._id,
        "distance": distance,
        "similarity_score": 1.0 / (1.0 + distance)  // Convert to similarity
    }}
    """
    
    try:
        cursor = db.aql.execute(aql, bind_vars={'query_embedding': query_embedding})
        results = list(cursor)
        logger.debug(f"L2 distance search returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"L2 distance search failed: {e}")
        return []