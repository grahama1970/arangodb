"""
Semantic Search Validator

This module provides utilities to ensure that semantic search can be 
performed safely and provides clear error messages when it cannot.

Usage:
    from arangodb.core.utils.semantic_search_validator import validate_before_semantic_search
    
    # Use as a decorator
    @validate_before_semantic_search
    def my_function_that_uses_semantic_search(db, query, ...):
        # Your semantic search code here
"""

from functools import wraps
from typing import Dict, Any, List, Optional, Union, Callable
from loguru import logger

from arango.database import StandardDatabase
from arangodb.core.search.semantic_search import safe_semantic_search


def validate_before_semantic_search(
    collection_param_name: str = "collection_name",
    collections_param_name: str = "collections",
    auto_fix: bool = True
):
    """
    Decorator that validates collections are ready for semantic search before executing a function.
    
    This decorator ensures that:
    1. The collection exists
    2. The collection has documents  
    3. Documents have embeddings
    4. There are enough documents for vector search (minimum 2)
    5. Embeddings have consistent dimensions
    6. A vector index exists
    
    Args:
        collection_param_name: Name of the collection parameter in the decorated function
        collections_param_name: Name of the collections array parameter in the decorated function
        auto_fix: Whether to automatically fix embedding issues if possible
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find the database parameter
            db = None
            if args and isinstance(args[0], StandardDatabase):
                db = args[0]
            elif args and hasattr(args[0], 'db') and isinstance(args[0].db, StandardDatabase):
                db = args[0].db
            else:
                for key, value in kwargs.items():
                    if key == 'db' and isinstance(value, StandardDatabase):
                        db = value
                        break
                    elif hasattr(value, 'db') and isinstance(value.db, StandardDatabase):
                        db = value.db
                        break
            
            if not db:
                logger.error("Could not find database connection in function parameters")
                raise ValueError("Database connection not found")
            
            # Find the collection(s) to validate
            collections = []
            
            # Check for single collection parameter
            if collection_param_name in kwargs:
                collections = [kwargs[collection_param_name]]
            else:
                # Check positional args
                func_code = func.__code__
                arg_names = func_code.co_varnames[:func_code.co_argcount]
                if collection_param_name in arg_names:
                    idx = arg_names.index(collection_param_name)
                    if idx < len(args):
                        collections = [args[idx]]
            
            # Check for collections array parameter
            if not collections and collections_param_name in kwargs:
                collections = kwargs[collections_param_name]
            else:
                # Check positional args for collections
                if not collections:
                    func_code = func.__code__
                    arg_names = func_code.co_varnames[:func_code.co_argcount]
                    if collections_param_name in arg_names:
                        idx = arg_names.index(collections_param_name)
                        if idx < len(args):
                            collections = args[idx]
            
            # Validate each collection
            for collection_name in collections:
                logger.info(f"Validating collection {collection_name} for semantic search")
                
                # Test with a simple query to trigger validation
                test_result = safe_semantic_search(
                    db=db,
                    query="test",
                    collections=[collection_name],
                    validate_before_search=True,
                    auto_fix_embeddings=auto_fix
                )
                
                if test_result.get("search_engine") == "failed":
                    error_msg = test_result.get("error", "Unknown error")
                    logger.error(f"Collection {collection_name} is not ready for semantic search: {error_msg}")
                    
                    # Return an error result instead of calling the function
                    return {
                        "results": [],
                        "total": 0,
                        "error": f"Collection validation failed: {error_msg}",
                        "search_engine": "validation-failed"
                    }
            
            # If validation passed, call the original function
            return func(*args, **kwargs)
            
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    """
    Demonstration of the semantic search validator
    """
    from arango import ArangoClient
    from arangodb.core.constants import (
        ARANGO_HOST, ARANGO_DB_NAME, ARANGO_USER, ARANGO_PASSWORD
    )
    
    # Connect to database
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    @validate_before_semantic_search(collection_param_name="collection")
    def example_semantic_search(db: StandardDatabase, query: str, collection: str):
        """Example function that uses semantic search"""
        from arangodb.core.search.semantic_search import semantic_search
        return semantic_search(db, query, collections=[collection])
    
    # Test with a valid collection
    print("Testing with valid collection:")
    result = example_semantic_search(db, "test query", "memory_documents")
    print(f"Result: {result['search_engine']}")
    
    # Test with invalid collection
    print("\nTesting with invalid collection:")
    result = example_semantic_search(db, "test query", "non_existent")
    print(f"Result: {result['search_engine']}")
    print(f"Error: {result.get('error', 'None')}")