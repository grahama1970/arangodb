"""
Patch for semantic_search.py to use manual cosine similarity directly.

This patch modifies the get_cached_vector_results function to skip APPROX_NEAR_COSINE
and use manual cosine similarity calculation directly since APPROX_NEAR_COSINE
consistently fails with HTTP 500 errors.
"""

def apply_semantic_search_patch():
    """Apply patch to semantic_search module to fix APPROX_NEAR_COSINE issue."""
    
    # Import the module correctly
    from arangodb.core.search import semantic_search as semantic_search_module
    
    # Store original function
    original_get_cached_vector_results = semantic_search_module.get_cached_vector_results
    
    def patched_get_cached_vector_results(
        db,
        collection_name: str,
        embedding_field: str,
        query_embedding,
        limit: int
    ):
        """
        Patched version that skips APPROX_NEAR_COSINE and uses manual calculation.
        """
        # Log that we're using the patched version
        from loguru import logger
        logger.info("Using patched vector search (manual cosine similarity)")
        
        # Convert to list if tuple
        if isinstance(query_embedding, tuple):
            query_embedding = list(query_embedding)
        
        # Skip straight to fallback
        return semantic_search_module.fallback_vector_search(
            db, collection_name, embedding_field, query_embedding, limit
        )
    
    # Replace the function
    semantic_search_module.get_cached_vector_results = patched_get_cached_vector_results
    
    # Also patch _perform_manual_vector_search to ensure it works correctly
    original_perform_manual = semantic_search_module._perform_manual_vector_search
    
    def patched_perform_manual_vector_search(
        db,
        collection_name: str,
        embedding_field: str,
        query_embedding,
        limit: int,
        bind_vars
    ):
        """
        Patched version with improved manual calculation.
        """
        from loguru import logger
        
        # Normalize query embedding
        query_norm = sum(x*x for x in query_embedding) ** 0.5
        if query_norm == 0:
            return []
        
        norm_query = [x/query_norm for x in query_embedding]
        query_dimension = len(query_embedding)
        
        # Use simplified but working query
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
        
        # Use clean bind vars
        clean_bind_vars = {"norm_query": norm_query}
        
        try:
            cursor = db.aql.execute(aql, bind_vars=clean_bind_vars)
            results = list(cursor)
            logger.debug(f"Patched manual search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Patched manual search failed: {e}")
            
            # Try L2 distance as last resort
            try:
                l2_aql = f"""
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
                
                cursor = db.aql.execute(l2_aql, bind_vars={"query_embedding": query_embedding})
                results = list(cursor)
                logger.debug(f"L2 distance fallback returned {len(results)} results")
                return results
            except Exception as e2:
                logger.error(f"L2 distance fallback also failed: {e2}")
                return []
    
    # Replace the manual search function
    semantic_search_module._perform_manual_vector_search = patched_perform_manual_vector_search
    
    return True


# Auto-apply patch when imported
if __name__ != "__main__":
    apply_semantic_search_patch()