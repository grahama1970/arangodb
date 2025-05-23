"""
Semantic Search Module - Integrated with Embedding Validation

This module implements vector similarity search in ArangoDB using the APPROX_NEAR_COSINE
function correctly, with integrated embedding validation and vector utilities.
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

# Import embedding validation and vector utilities
from arangodb.core.utils.embedding_validator import (
    EmbeddingValidator,
    check_semantic_search_readiness,
    validate_embedding_before_insert
)
from arangodb.core.utils.vector_utils import (
    check_embedding_format,
    document_stats,
    fix_collection_embeddings,
    ensure_vector_index
)

# Define embedding field name
EMBEDDING_FIELD = "embedding"
EMBEDDING_METADATA_FIELD = "embedding_metadata"
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


def check_collection_readiness(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str = EMBEDDING_FIELD,
    metadata_field: str = EMBEDDING_METADATA_FIELD
) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a collection is ready for semantic search.
    
    Args:
        db: Database connection
        collection_name: Collection to check
        embedding_field: Field containing embeddings
        metadata_field: Field containing metadata
        
    Returns:
        Tuple of (is_ready, status_info)
    """
    # Use the embedding validator to check readiness
    validator = EmbeddingValidator(
        db=db,
        collection_name=collection_name,
        embedding_field=embedding_field,
        metadata_field=metadata_field,
        default_model="BAAI/bge-large-en-v1.5",
        default_dimensions=DEFAULT_EMBEDDING_DIMENSIONS
    )
    
    # Log the embedding status
    validator.log_embedding_status()
    
    # Get semantic search status
    status = validator.get_semantic_search_status()
    
    return status["can_search"], status


def prepare_collection_for_search(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str = EMBEDDING_FIELD,
    metadata_field: str = EMBEDDING_METADATA_FIELD,
    fix_embeddings: bool = True
) -> Tuple[bool, Dict[str, Any]]:
    """
    Prepare a collection for semantic search by fixing embeddings and ensuring indexes.
    
    Args:
        db: Database connection
        collection_name: Collection to prepare
        embedding_field: Field containing embeddings
        metadata_field: Field containing metadata
        fix_embeddings: Whether to fix missing/incorrect embeddings
        
    Returns:
        Tuple of (success, result_info)
    """
    result_info = {
        "collection": collection_name,
        "ready": False,
        "status": {},
        "fix_results": {},
        "index_results": {}
    }
    
    # First check current status
    is_ready, status = check_collection_readiness(db, collection_name, embedding_field, metadata_field)
    result_info["status"] = status
    
    if is_ready:
        logger.info(f"Collection {collection_name} is ready for semantic search")
        result_info["ready"] = True
        return True, result_info
    
    # Log the issues
    logger.warning(f"Collection {collection_name} has issues: {status['message']}")
    
    # Fix embeddings if requested and needed
    if fix_embeddings:
        # Get current stats
        stats = document_stats(db, collection_name, embedding_field, metadata_field)
        
        # Only fix if there are issues
        if stats["issues"]:
            logger.info(f"Attempting to fix embeddings for {collection_name}")
            fix_results = fix_collection_embeddings(
                db=db,
                collection_name=collection_name,
                embedding_field=embedding_field,
                metadata_field=metadata_field,
                dry_run=False
            )
            result_info["fix_results"] = fix_results
            
            # Check status again after fixing
            is_ready, status = check_collection_readiness(db, collection_name, embedding_field, metadata_field)
            result_info["status"] = status
    
    # Ensure vector index exists
    if is_ready or (status["embeddings_count"] >= 2 and status["consistent_dimensions"]):
        logger.info(f"Ensuring vector index for {collection_name}")
        index_results = ensure_vector_index(
            db=db,
            collection_name=collection_name,
            embedding_field=embedding_field
        )
        result_info["index_results"] = index_results
        
        if index_results["success"]:
            # Final readiness check
            is_ready, status = check_collection_readiness(db, collection_name, embedding_field, metadata_field)
            result_info["status"] = status
            result_info["ready"] = is_ready
    
    return result_info["ready"], result_info


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
    output_format: str = "table",
    validate_before_search: bool = True,
    auto_fix_embeddings: bool = False
) -> Dict[str, Any]:
    """
    Semantic search using ArangoDB's APPROX_NEAR_COSINE with proper validation.
    
    Args:
        db: ArangoDB database
        query: Search query text or embedding vector
        collections: Optional list of collections to search
        filter_expr: Optional AQL filter expression
        min_score: Minimum similarity score threshold (0-1)
        top_n: Maximum number of results to return
        tag_list: Optional list of tags to filter by
        output_format: Output format (table or json)
        validate_before_search: Whether to validate collection readiness before search
        auto_fix_embeddings: Whether to automatically fix embedding issues
        
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
    
    # Validate collection readiness if requested
    if validate_before_search:
        is_ready, status_info = prepare_collection_for_search(
            db=db,
            collection_name=collection_name,
            embedding_field=embedding_field,
            fix_embeddings=auto_fix_embeddings
        )
        
        if not is_ready:
            logger.error(f"Collection {collection_name} is not ready for semantic search: {status_info['status']['message']}")
            return {
                "results": [],
                "total": 0,
                "query": query if isinstance(query, str) else "Vector query",
                "time": time.time() - start_time,
                "search_engine": "failed",
                "error": status_info["status"]["message"],
                "collection_status": status_info
            }
    
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
    
    # Validate query embedding format
    is_valid, msg = check_embedding_format(query_embedding)
    if not is_valid:
        logger.error(f"Invalid query embedding: {msg}")
        return {
            "results": [],
            "total": 0,
            "query": query_text,
            "time": time.time() - start_time,
            "search_engine": "failed",
            "error": f"Invalid query embedding: {msg}"
        }
    
    # Check for valid embedding dimensions
    expected_dimension = DEFAULT_EMBEDDING_DIMENSIONS
    actual_dimension = len(query_embedding)
    if actual_dimension != expected_dimension:
        logger.warning(f"Query embedding dimension mismatch: expected {expected_dimension}, got {actual_dimension}")
    
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
        logger.error("This is likely because the vector index structure is incorrect or embeddings are inconsistent")
        results = []
        search_engine = "failed"
        
        # Provide helpful error message
        error_msg = str(e)
        if "ERR 1554" in error_msg:
            error_msg = "Vector search failed - check if all documents have proper embeddings and vector index exists"
    
    # Return results
    return {
        "results": results,
        "total": len(results),
        "query": query_text,
        "time": time.time() - start_time,
        "search_engine": search_engine,
        "error": error_msg if search_engine == "failed" else None
    }


def ensure_document_has_embedding(
    document: Dict[str, Any],
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str = EMBEDDING_FIELD,
    metadata_field: str = EMBEDDING_METADATA_FIELD,
    default_model: str = "BAAI/bge-large-en-v1.5"
) -> Dict[str, Any]:
    """
    Ensure a document has a valid embedding before insertion.
    
    Args:
        document: Document to check/fix
        db: Database connection
        collection_name: Target collection
        embedding_field: Field for embeddings
        metadata_field: Field for metadata
        default_model: Default embedding model
        
    Returns:
        Updated document with valid embedding
    """
    # Create validator for the collection
    validator = EmbeddingValidator(
        db=db,
        collection_name=collection_name,
        embedding_field=embedding_field,
        metadata_field=metadata_field,
        default_model=default_model,
        default_dimensions=DEFAULT_EMBEDDING_DIMENSIONS
    )
    
    # Validate the document
    validation = validator.validate_document_embedding(document)
    
    if validation["valid"]:
        return document
    
    # Fix the document if needed
    logger.warning(f"Document has embedding issues: {validation['issues']}")
    
    # Generate embedding if missing
    if embedding_field not in document or not isinstance(document[embedding_field], list):
        # Extract text to embed
        text_fields = ["content", "text", "summary", "title", "description"]
        text_to_embed = ""
        
        for field in text_fields:
            if field in document and document[field]:
                text_to_embed = document[field]
                break
        
        if not text_to_embed:
            # Try to construct text from title + content
            title = document.get("title", "")
            content = document.get("content", "")
            text_to_embed = f"{title} {content}".strip()
        
        if text_to_embed:
            logger.info(f"Generating embedding for document: {text_to_embed[:50]}...")
            embedding = get_embedding(text_to_embed)
            if embedding:
                document[embedding_field] = embedding
                document[metadata_field] = {
                    "model": default_model,
                    "dimensions": len(embedding),
                    "created_at": time.time()
                }
    
    return document


# Decorator for validating documents before insertion
@validate_embedding_before_insert(embedding_field=EMBEDDING_FIELD, metadata_field=EMBEDDING_METADATA_FIELD)
def insert_documents_with_validation(db: StandardDatabase, collection_name: str, documents: List[Dict[str, Any]]):
    """
    Insert documents with automatic embedding validation.
    
    This is a wrapper function that uses the validation decorator.
    """
    collection = db.collection(collection_name)
    return collection.insert_many(documents)


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
    
    # Check collection readiness
    print("\n=== Checking collection readiness ===")
    is_ready, status = check_collection_readiness(db, COLLECTION_NAME)
    print(f"Collection {COLLECTION_NAME} ready: {is_ready}")
    print(f"Status: {status['message']}")
    
    if status["issues"]:
        print("Issues found:")
        for issue in status["issues"]:
            print(f"  - {issue}")
    
    # Test document insertion with validation
    print("\n=== Testing document insertion with validation ===")
    test_doc = {
        "title": "Test Document",
        "content": "This is a test document for semantic search validation"
    }
    
    # Ensure document has embedding
    test_doc = ensure_document_has_embedding(test_doc, db, COLLECTION_NAME)
    print(f"Document has embedding: {EMBEDDING_FIELD in test_doc}")
    print(f"Embedding dimensions: {len(test_doc.get(EMBEDDING_FIELD, []))}")
    
    # Run a simple search
    print("\n=== Testing semantic search ===")
    query_text = "test validation"
    print(f"Query: '{query_text}'")
    
    result = semantic_search(
        db, 
        query_text, 
        min_score=0.3,
        validate_before_search=True,
        auto_fix_embeddings=True
    )
    
    # Print results
    print(f"Found {len(result['results'])} results")
    print(f"Search engine used: {result['search_engine']}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    
    if result["results"]:
        print("\nTop results:")
        for i, res in enumerate(result["results"][:3]):
            doc = res["doc"]
            score = res["similarity_score"]
            title = doc.get("title", "No title")
            print(f"  {i+1}. [{score:.4f}] {title}")