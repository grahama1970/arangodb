"""
Semantic Search Module - Fixed APPROX_NEAR_COSINE Implementation

This module implements vector similarity search in ArangoDB using the APPROX_NEAR_COSINE
function correctly, with improved index validation.
"""

import sys
import time
import json
import inspect
from typing import Dict, Any, List, Optional, Union, Tuple

from loguru import logger
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, ArangoServerError

# Import config variables from proper location
from arangodb.core.constants import (
    COLLECTION_NAME,
    VIEW_NAME,
    ALL_DATA_FIELDS_PREVIEW,
    DEFAULT_EMBEDDING_DIMENSIONS
)

# Define embedding field name
EMBEDDING_FIELD = "embedding"
from arangodb.core.utils.embedding_utils import get_embedding


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
def execute_aql_with_retry(
    db: StandardDatabase, 
    query: str, 
    bind_vars: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Execute AQL query with retry logic for transient errors.
    
    Args:
        db: ArangoDB database
        query: AQL query string
        bind_vars: Query bind variables
        
    Returns:
        Query cursor
        
    Raises:
        Exception: Re-raises the last exception after retries are exhausted
    """
    try:
        return db.aql.execute(query, bind_vars=bind_vars)
    except (AQLQueryExecuteError, ArangoServerError) as e:
        # Log the error before retry
        logger.warning(f"ArangoDB query failed, retrying: {str(e)}")
        # Re-raise to let @retry handle it
        raise


def validate_vector_index(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str
) -> bool:
    """
    Validate that a proper vector index exists for the collection.
    
    Note: Due to ArangoDB client limitations, the 'params' field may not
    be included in the index info when retrieved via collection.indexes().
    We check if a vector index exists on the field, and if queries work.
    
    Args:
        db: Database connection
        collection_name: Collection to check
        embedding_field: Field containing embeddings
        
    Returns:
        True if a valid vector index exists, False otherwise
    """
    try:
        collection = db.collection(collection_name)
        indexes = collection.indexes()
        
        # Check for vector index on the correct field
        has_vector_index = False
        for index in indexes:
            if index.get("type") == "vector" and embedding_field in index.get("fields", []):
                has_vector_index = True
                logger.info(f"Found vector index for {collection_name}.{embedding_field}")
                break
        
        if not has_vector_index:
            logger.warning(f"No vector index found for {collection_name}.{embedding_field}")
            return False
        
        # Test if the index works by running a simple query
        try:
            test_aql = f"""
            FOR doc IN {collection_name}
            LIMIT 1
            LET score = APPROX_NEAR_COSINE(doc.{embedding_field}, doc.{embedding_field})
            RETURN score
            """
            cursor = db.aql.execute(test_aql)
            list(cursor)  # Execute the query
            logger.info(f"Vector index is functional for {collection_name}.{embedding_field}")
            return True
        except Exception as e:
            logger.warning(f"Vector index test query failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error validating vector index: {e}")
        return False


def create_proper_vector_index(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str,
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
) -> bool:
    """
    Create a proper vector index for APPROX_NEAR_COSINE compatibility.
    
    Args:
        db: Database instance
        collection_name: Name of the collection
        embedding_field: Name of the embedding field
        dimensions: Dimensions of the embeddings
        
    Returns:
        True if index created or already exists, False otherwise
    """
    try:
        collection = db.collection(collection_name)
        
        # Check if we already have a valid index
        if validate_vector_index(db, collection_name, embedding_field):
            return True
        
        # Delete any existing vector indexes on this field
        indexes = collection.indexes()
        for index in indexes:
            if index.get("type") == "vector" and embedding_field in index.get("fields", []):
                index_id = index.get("id")
                logger.info(f"Removing existing vector index {index_id}")
                collection.delete_index(index_id)
        
        # Check if collection has enough documents with proper embeddings
        count_query = f"""
        RETURN LENGTH(
            FOR doc IN {collection_name}
            FILTER HAS(doc, "{embedding_field}") 
                AND IS_LIST(doc.{embedding_field})
                AND LENGTH(doc.{embedding_field}) > 0
            RETURN 1
        )
        """
        cursor = execute_aql_with_retry(db, count_query)
        doc_count = list(cursor)[0]
        
        if doc_count < 2:
            logger.warning(f"Collection {collection_name} has only {doc_count} documents with valid embeddings.")
            logger.warning("Need at least 2 documents with embeddings to create a vector index.")
            return False
        
        # Determine appropriate nLists value based on collection size
        n_lists = 2  # Default for small collections
        
        # Ensure nLists is not larger than document count
        if n_lists > doc_count:
            n_lists = doc_count
            logger.warning(f"Adjusted nLists to {n_lists} (cannot exceed document count)")
        
        # Create vector index with proper structure
        logger.info(f"Creating vector index for {collection_name}.{embedding_field}")
        
        # Use PROPER STRUCTURE - params as sub-object
        index_config = {
            "type": "vector",
            "fields": [embedding_field],
            "params": {  # params MUST be a sub-object
                "dimension": dimensions,
                "metric": "cosine",
                "nLists": n_lists  # Use appropriate size based on collection
            }
        }
        
        result = collection.add_index(index_config)
        logger.info(f"Vector index created: {result}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create vector index for {collection_name}.{embedding_field}: {e}")
        return False


def check_and_fix_vector_index(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str = EMBEDDING_FIELD,
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
) -> bool:
    """
    Check and fix the vector index if needed.
    
    Args:
        db: Database connection
        collection_name: Collection to check and fix
        embedding_field: Field containing embeddings
        dimensions: Expected embedding dimensions
        
    Returns:
        True if the index is valid or was fixed, False otherwise
    """
    # First validate the index
    if validate_vector_index(db, collection_name, embedding_field):
        return True
        
    # If not valid, try to create a proper index
    return create_proper_vector_index(db, collection_name, embedding_field, dimensions)


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
    Semantic search using ArangoDB's APPROX_NEAR_COSINE with proper vector index.
    
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
    
    # Check for valid embedding dimensions
    expected_dimension = DEFAULT_EMBEDDING_DIMENSIONS
    actual_dimension = len(query_embedding)
    if actual_dimension != expected_dimension:
        logger.warning(f"Query embedding dimension mismatch: expected {expected_dimension}, got {actual_dimension}")
    
    # Verify and fix the vector index if needed
    index_valid = check_and_fix_vector_index(db, collection_name, embedding_field, actual_dimension)
    
    if not index_valid:
        logger.warning(f"Unable to create or validate a proper vector index for {collection_name}.{embedding_field}")
        logger.info("Ensure all documents have proper list embeddings with same dimensions before creating the index")
        logger.info("Use vector_utils.py to fix embedding formats and create proper indexes")
    
    # Try to use APPROX_NEAR_COSINE (primary implementation)
    vector_query = f"""
    FOR doc IN {collection_name}
    LET score = APPROX_NEAR_COSINE(doc.{embedding_field}, @query_embedding)
    SORT score DESC
    LIMIT {top_n * 2}
    RETURN {{
        "id": doc._id,
        "similarity_score": score
    }}
    """
    
    # Add tag filtering if needed
    if tag_list and len(tag_list) > 0:
        tag_conditions = []
        bind_vars = {"query_embedding": query_embedding}
        
        for i, tag in enumerate(tag_list):
            bind_var_name = f"tag_{i}"
            bind_vars[bind_var_name] = tag
            tag_conditions.append(f'@{bind_var_name} IN doc.tags')
        
        vector_query = f"""
        FOR doc IN {collection_name}
        FILTER {' AND '.join(tag_conditions)}
        LET score = APPROX_NEAR_COSINE(doc.{embedding_field}, @query_embedding)
        SORT score DESC
        LIMIT {top_n * 2}
        RETURN {{
            "id": doc._id,
            "similarity_score": score
        }}
        """
    else:
        bind_vars = {"query_embedding": query_embedding}
    
    results = []
    try:
        cursor = execute_aql_with_retry(db, vector_query, bind_vars=bind_vars)
        vector_results = list(cursor)
        logger.info(f"APPROX_NEAR_COSINE returned {len(vector_results)} results successfully")
        
        # Filter by minimum score and fetch full documents
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
        
        search_engine = "arangodb-approx-near-cosine"
        
    except Exception as e:
        logger.error(f"APPROX_NEAR_COSINE search failed: {e}")
        logger.error("This is likely because the vector index structure is incorrect")
        logger.error("Use vector_utils.py to fix embedding formats and create proper indexes")
        logger.error("Ensure vector indexes are created with 'params' as a sub-object")
        results = []
        search_engine = "failed"
    
    # Return results
    return {
        "results": results,
        "total": len(results),
        "query": query_text,
        "time": time.time() - start_time,
        "search_engine": search_engine
    }


if __name__ == "__main__":
    """
    Simple usage function to verify the module works with real data.
    """
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:HH:mm:ss} | {level:<7} | {message}"
    )
    
    # Set up database connection
    from arango import ArangoClient
    from arangodb.core.constants import ARANGO_HOST, ARANGO_DB_NAME, ARANGO_USER, ARANGO_PASSWORD
    
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    # Test vector index validation
    print("Testing vector index validation...")
    is_valid = validate_vector_index(db, COLLECTION_NAME, EMBEDDING_FIELD)
    print(f"Vector index valid: {is_valid}")
    
    # Run a simple search
    query_text = "test query"
    print(f"Testing semantic search with query: '{query_text}'")
    result = semantic_search(db, query_text, min_score=0.3)
    
    # Print results
    print(f"Found {len(result['results'])} results")
    print(f"Search engine used: {result['search_engine']}")