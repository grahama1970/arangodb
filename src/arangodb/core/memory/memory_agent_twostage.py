"""
Enhanced Memory Agent Search with Two-Stage Filtering

This module shows the correct approach: vector search first,
then Python filtering as a second stage.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from arangodb.core.constants import (
    MEMORY_MESSAGE_COLLECTION,
    MEMORY_VIEW_NAME
)
from arangodb.core.utils.embedding_utils import get_embedding


def search_with_twostage_filtering(
    memory_agent: Any,
    query: str,
    conversation_id: Optional[str] = None,
    n_results: int = 10,
    point_in_time: Optional[datetime] = None,
    expand_factor: int = 5
) -> List[Dict[str, Any]]:
    """
    Correct approach: Vector search without filters, then Python filtering.
    
    Args:
        memory_agent: The memory agent instance
        query: Search query text
        conversation_id: Optional filter by conversation ID
        n_results: Number of final results to return
        point_in_time: Optional temporal filter
        expand_factor: How many more results to fetch for filtering (default 5x)
        
    Returns:
        List of matching message documents with scores
    """
    try:
        # Generate embedding for the query
        query_embedding = get_embedding(query)
        
        # Stage 1: Pure vector search without ANY filters
        # Get more results than needed for post-filtering
        initial_limit = n_results * expand_factor
        
        logger.info(f"Stage 1: Vector search for {initial_limit} results")
        
        aql = f"""
        FOR doc IN {MEMORY_MESSAGE_COLLECTION}
            LET score = APPROX_NEAR_COSINE(doc.embedding, @query_embedding)
            SORT score DESC
            LIMIT @limit
            RETURN MERGE(doc, {{
                score: score
            }})
        """
        
        bind_vars = {
            "query_embedding": query_embedding,
            "limit": initial_limit
        }
        
        # Execute pure vector search
        cursor = memory_agent.db.aql.execute(aql, bind_vars=bind_vars)
        vector_results = list(cursor)
        
        logger.info(f"Vector search returned {len(vector_results)} results")
        
        # Stage 2: Python filtering
        logger.info("Stage 2: Python filtering")
        
        filtered_results = []
        for result in vector_results:
            # Apply conversation filter
            if conversation_id and result.get('conversation_id') != conversation_id:
                continue
                
            # Apply time filter
            if point_in_time:
                doc_time = result.get('timestamp')
                if doc_time:
                    # Parse timestamp and compare
                    if isinstance(doc_time, str):
                        doc_datetime = datetime.fromisoformat(doc_time.replace('Z', '+00:00'))
                    else:
                        doc_datetime = doc_time
                    
                    if doc_datetime > point_in_time:
                        continue
            
            # Document passes all filters
            filtered_results.append(result)
            
            # Check if we have enough results
            if len(filtered_results) >= n_results:
                break
        
        logger.info(f"Filtering complete: {len(filtered_results)} results match criteria")
        
        # Normalize scores from [-1, 1] to [0, 1] for consistency
        for result in filtered_results:
            result['score'] = (result['score'] + 1) / 2
        
        # Return top N results
        return filtered_results[:n_results]
        
    except Exception as e:
        if "ERR 1554" in str(e):
            logger.error(f"Vector search failed - this should not happen with pure APPROX_NEAR_COSINE: {e}")
            # Fall back to text search as emergency backup
            return fallback_text_search(memory_agent, query, conversation_id, n_results, point_in_time)
        else:
            logger.error(f"Error in two-stage search: {e}")
            raise


def fallback_text_search(
    memory_agent: Any,
    query: str,
    conversation_id: Optional[str] = None,
    n_results: int = 10,
    point_in_time: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Emergency fallback to text search if vector search fails."""
    
    logger.warning("Using text search fallback")
    
    aql = f"""
    FOR doc IN {MEMORY_VIEW_NAME}
        SEARCH ANALYZER(doc.content IN TOKENS(@query, "text_en"), "text_en")
    """
    
    bind_vars = {"query": query}
    filters = []
    
    if conversation_id:
        filters.append("doc.conversation_id == @conversation_id")
        bind_vars["conversation_id"] = conversation_id
        
    if point_in_time:
        filters.append("doc.timestamp <= @point_in_time")
        bind_vars["point_in_time"] = point_in_time.isoformat()
        
    if filters:
        aql += " FILTER " + " AND ".join(filters)
        
    aql += f"""
        SORT BM25(doc) DESC
        LIMIT @n_results
        RETURN MERGE(doc, {{
            score: BM25(doc)
        }})
    """
    bind_vars["n_results"] = n_results
    
    cursor = memory_agent.db.aql.execute(aql, bind_vars=bind_vars)
    return list(cursor)


def apply_fuzzy_filtering(results: List[Dict[str, Any]], 
                         search_term: str, 
                         field: str = 'content',
                         threshold: int = 80) -> List[Dict[str, Any]]:
    """
    Apply fuzzy string matching as an additional filter.
    
    Args:
        results: Vector search results
        search_term: Term to match
        field: Field to search in
        threshold: Fuzzy match threshold (0-100)
        
    Returns:
        Filtered results
    """
    try:
        from rapidfuzz import process, fuzz
    except ImportError:
        logger.warning("rapidfuzz not available, using exact matching")
        return [r for r in results if search_term.lower() in r.get(field, '').lower()]
    
    filtered = []
    for result in results:
        text = result.get(field, '')
        if not text:
            continue
            
        # Use token set ratio for flexible matching
        score = fuzz.token_set_ratio(search_term, text)
        
        if score >= threshold:
            result['fuzzy_score'] = score
            filtered.append(result)
    
    # Sort by fuzzy score descending
    filtered.sort(key=lambda x: x.get('fuzzy_score', 0), reverse=True)
    
    return filtered


if __name__ == "__main__":
    """Test the two-stage search approach"""
    from arango import ArangoClient
    from arangodb.core.constants import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME
    from arangodb.core.memory.memory_agent import MemoryAgent
    
    # Connect to ArangoDB
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    # Initialize memory agent
    memory_agent = MemoryAgent(db=db)
    
    # Test two-stage search
    print("\n=== Two-Stage Search Test ===")
    
    # Test 1: Pure vector search (should work)
    print("\n1. Pure vector search (no filters)...")
    results = search_with_twostage_filtering(memory_agent, "ArangoDB database", n_results=3)
    print(f"Found {len(results)} results")
    
    # Test 2: Vector search with Python filtering
    print("\n2. Vector search + Python filtering...")
    results = search_with_twostage_filtering(
        memory_agent, 
        "database", 
        conversation_id="test_conv_001",
        n_results=3
    )
    print(f"Found {len(results)} results after filtering")
    
    # Test 3: Additional fuzzy filtering
    print("\n3. Vector search + fuzzy filtering...")
    results = search_with_twostage_filtering(memory_agent, "memory", n_results=10)
    fuzzy_results = apply_fuzzy_filtering(results, "agent memory", field='content')
    print(f"Found {len(fuzzy_results)} results after fuzzy filtering")