"""
Fixed Memory Agent Search with Vector Support

This module provides a fixed version of the memory agent search that uses
APPROX_NEAR_COSINE when possible and falls back to text search when needed.
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


def search_with_vector_support(
    memory_agent: Any,
    query: str,
    conversation_id: Optional[str] = None,
    n_results: int = 10,
    point_in_time: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Enhanced search that uses vector search when no filters are applied,
    otherwise falls back to text search.
    
    Args:
        memory_agent: The memory agent instance
        query: Search query text
        conversation_id: Optional filter by conversation ID
        n_results: Number of results to return
        point_in_time: Optional temporal filter
        
    Returns:
        List of matching message documents with scores
    """
    try:
        # Generate embedding for the query
        query_embedding = get_embedding(query)
        
        # Determine if we can use vector search (no filters)
        use_vector_search = (conversation_id is None and point_in_time is None)
        
        if use_vector_search:
            logger.info("Using APPROX_NEAR_COSINE vector search (no filters)")
            
            # Simple vector search without filters
            aql = f"""
            FOR doc IN {MEMORY_MESSAGE_COLLECTION}
                LET score = APPROX_NEAR_COSINE(doc.embedding, @query_embedding)
                SORT score DESC
                LIMIT @n_results
                RETURN MERGE(doc, {{
                    score: score
                }})
            """
            
            bind_vars = {
                "query_embedding": query_embedding,
                "n_results": n_results
            }
            
        else:
            logger.info("Using text search with BM25 (filters applied)")
            
            # Fall back to text search for complex queries with filters
            aql = f"""
            FOR doc IN {MEMORY_VIEW_NAME}
                SEARCH ANALYZER(doc.content IN TOKENS(@query, "text_en"), "text_en")
            """
            
            # Add filters
            bind_vars = {
                "query": query
            }
            
            filters = []
            if conversation_id:
                filters.append("doc.conversation_id == @conversation_id")
                bind_vars["conversation_id"] = conversation_id
                
            if point_in_time:
                filters.append("doc.timestamp <= @point_in_time")
                bind_vars["point_in_time"] = point_in_time.isoformat()
                
            if filters:
                aql += " FILTER " + " AND ".join(filters)
                
            # Sort by relevance and limit results
            aql += f"""
                SORT BM25(doc) DESC
                LIMIT @n_results
                RETURN MERGE(doc, {{
                    score: BM25(doc)
                }})
            """
            bind_vars["n_results"] = n_results
        
        # Execute query
        cursor = memory_agent.db.aql.execute(aql, bind_vars=bind_vars)
        results = list(cursor)
        
        # For vector search results, normalize scores to 0-1 range if needed
        if use_vector_search:
            for result in results:
                # APPROX_NEAR_COSINE returns values between -1 and 1
                # Normalize to 0-1 for consistency with text search scores
                result['score'] = (result['score'] + 1) / 2
        
        return results
        
    except Exception as e:
        if "ERR 1554" in str(e) and use_vector_search:
            # If vector search fails, fall back to text search
            logger.warning(f"Vector search failed, falling back to text search: {e}")
            return search_with_vector_support(
                memory_agent,
                query,
                conversation_id,
                n_results,
                point_in_time
            )
        else:
            logger.error(f"Error searching memories: {e}")
            raise


def fix_memory_agent_search():
    """
    Monkey patch the MemoryAgent search method to support vector search.
    """
    from arangodb.core.memory.memory_agent import MemoryAgent
    
    # Save the original method
    original_search = MemoryAgent.search
    
    def enhanced_search(self, query: str, conversation_id: Optional[str] = None,
                       n_results: int = 10, point_in_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Enhanced search with vector support"""
        return search_with_vector_support(self, query, conversation_id, n_results, point_in_time)
    
    # Replace the method
    MemoryAgent.search = enhanced_search
    logger.info("Memory agent search enhanced with vector support")


if __name__ == "__main__":
    """Test the enhanced search"""
    from arango import ArangoClient
    from arangodb.core.constants import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME
    from arangodb.core.memory.memory_agent import MemoryAgent
    
    # Connect to ArangoDB
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    # Apply the fix
    fix_memory_agent_search()
    
    # Initialize memory agent
    memory_agent = MemoryAgent(db=db)
    
    # Test vector search (no filters)
    print("\n1. Testing vector search (no filters)...")
    results = memory_agent.search("ArangoDB database", n_results=3)
    for result in results:
        print(f"- {result.get('content', '')[:50]}... (score: {result.get('score', 0):.4f})")
    
    # Test text search (with filters)
    print("\n2. Testing text search (with filters)...")
    results = memory_agent.search("Python", conversation_id="test", n_results=3)
    for result in results:
        print(f"- {result.get('content', '')[:50]}... (score: {result.get('score', 0):.4f})")