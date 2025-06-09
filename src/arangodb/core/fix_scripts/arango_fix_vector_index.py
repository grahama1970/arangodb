"""
Fix for vector index creation in ArangoDB
Module: arango_fix_vector_index.py
Description: Functions for arango fix vector index operations

This module provides a fix for creating proper vector indexes in ArangoDB
to enable APPROX_NEAR_COSINE functionality.
"""

import os
from loguru import logger
from arango.database import StandardDatabase
from arango.exceptions import IndexCreateError

from arangodb.core.constants import (
    MEMORY_MESSAGE_COLLECTION,
    EMBEDDING_FIELD,
    DEFAULT_EMBEDDING_DIMENSIONS,
    COMPACTED_SUMMARIES_COLLECTION
)


def create_proper_vector_index(
    db: StandardDatabase,
    collection_name: str,
    field_name: str = EMBEDDING_FIELD,
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
) -> None:
    """
    Create a proper vector index for APPROX_NEAR_COSINE compatibility.
    
    Args:
        db: Database instance
        collection_name: Name of the collection
        field_name: Name of the embedding field
        dimensions: Dimensions of the embeddings
    """
    try:
        collection = db.collection(collection_name)
        
        # Check existing indexes
        existing_indexes = collection.indexes()
        
        # Check if vector index already exists
        for index in existing_indexes:
            if (index.get("type") == "vector" and 
                field_name in index.get("fields", [])):
                logger.info(f"Vector index already exists for {collection_name}.{field_name}")
                logger.debug(f"Index details: {index}")
                return
        
        # Create vector index with proper structure
        logger.info(f"Creating vector index for {collection_name}.{field_name}")
        
        # Use PROPER STRUCTURE - params as sub-object
        index_config = {
            "type": "vector",
            "fields": [field_name],
            "params": {  # params MUST be a sub-object
                "dimension": dimensions,
                "metric": "cosine",
                "nLists": 2  # Use 2 for small datasets
            }
        }
        
        result = collection.add_index(index_config)
        logger.info(f"Vector index created: {result}")
        
    except IndexCreateError as e:
        logger.error(f"Failed to create vector index for {collection_name}.{field_name}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error creating vector index: {e}")
        raise


def fix_memory_agent_indexes(db: StandardDatabase) -> None:
    """
    Fix vector indexes for memory agent collections.
    
    Args:
        db: Database instance
    """
    # Collections that need vector indexes
    collections_to_fix = [
        MEMORY_MESSAGE_COLLECTION,
        COMPACTED_SUMMARIES_COLLECTION,
        "memory_documents"  # If documents have embeddings
    ]
    
    for collection_name in collections_to_fix:
        if db.has_collection(collection_name):
            try:
                create_proper_vector_index(db, collection_name)
            except Exception as e:
                logger.error(f"Failed to fix index for {collection_name}: {e}")
                # Continue with other collections
        else:
            logger.warning(f"Collection {collection_name} doesn't exist, skipping index creation")


if __name__ == "__main__":
    """Test the vector index fix"""
    import sys
    from arangodb.core.arango_setup import connect_arango, ensure_database
    
    print("Testing vector index fix...")
    
    try:
        # Connect to ArangoDB
        client = connect_arango()
        db = ensure_database(client)
        
        # Fix indexes
        fix_memory_agent_indexes(db)
        
        # Verify indexes
        for collection_name in [MEMORY_MESSAGE_COLLECTION, COMPACTED_SUMMARIES_COLLECTION]:
            if db.has_collection(collection_name):
                collection = db.collection(collection_name)
                indexes = collection.indexes()
                
                print(f"\nIndexes for {collection_name}:")
                for index in indexes:
                    if index.get("type") == "vector":
                        print(f"  Vector index: {index}")
                        params = index.get("params", {})
                        print(f"    Dimensions: {params.get('dimension', 'N/A')}")
                        print(f"    Metric: {params.get('metric', 'N/A')}")
                        print(f"    nLists: {params.get('nLists', 'N/A')}")
        
        print("\n✅ Vector index fix complete")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)