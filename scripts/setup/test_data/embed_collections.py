"""
Module: embed_collections.py

External Dependencies:
- loguru: https://loguru.readthedocs.io/
- arango: https://docs.python-arango.com/

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

#!/usr/bin/env python3
"""
Utility to generate embeddings for all documents in specified collections.

This function uses the local BGE embedder from embedding_utils.py to create
embeddings for searchable text fields in documents.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger
from arango import ArangoClient

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from arangodb.core.utils.embedding_utils import get_embedding
from arangodb.core.constants import (
    ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD,
    DEFAULT_EMBEDDING_DIMENSIONS
)

logger.add("embed_collections.log", rotation="10 MB")

def embed_document(doc: Dict[str, Any], embedding_fields: List[str]) -> Optional[List[float]]:
    """
    Generate embedding for a document by combining specified fields.
    
    Args:
        doc: Document to embed
        embedding_fields: List of field names to include in embedding
        
    Returns:
        Embedding vector or None if generation fails
    """
    # Collect text from all embedding fields
    text_parts = []
    
    for field in embedding_fields:
        # Handle nested fields (e.g., "metadata.context")
        value = doc
        for part in field.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                value = None
                break
        
        if value is not None:
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                # Join list items (e.g., tags)
                text_parts.extend(str(item) for item in value if item)
    
    if not text_parts:
        logger.warning(f"No text found in document {doc.get('_key', 'unknown')} for embedding")
        return None
    
    # Combine all text parts
    combined_text = " ".join(text_parts)
    logger.debug(f"Embedding text for {doc.get('_key', 'unknown')}: {combined_text[:100]}...")
    
    # Generate embedding
    embedding = get_embedding(combined_text)
    
    if embedding and len(embedding) == DEFAULT_EMBEDDING_DIMENSIONS:
        return embedding
    else:
        logger.error(f"Invalid embedding generated for document {doc.get('_key', 'unknown')}")
        return None

def embed_collection(
    db_name: str,
    collection_name: str,
    embedding_fields: List[str],
    embedding_field_name: str = "embedding",
    batch_size: int = 100,
    skip_existing: bool = True
) -> Dict[str, Any]:
    """
    Generate embeddings for all documents in a collection.
    
    Args:
        db_name: Name of the database
        collection_name: Name of the collection to embed
        embedding_fields: List of fields to use for embedding generation
        embedding_field_name: Name of field to store embedding (default: "embedding")
        batch_size: Number of documents to process at once
        skip_existing: Skip documents that already have embeddings
        
    Returns:
        Statistics about the embedding process
    """
    stats = {
        "total_documents": 0,
        "documents_embedded": 0,
        "documents_skipped": 0,
        "documents_failed": 0,
        "collection": collection_name
    }
    
    try:
        # Connect to ArangoDB
        client = ArangoClient(hosts=ARANGO_HOST)
        db = client.db(db_name, username=ARANGO_USER, password=ARANGO_PASSWORD)
        
        if not db.has_collection(collection_name):
            logger.error(f"Collection {collection_name} does not exist in database {db_name}")
            return stats
        
        collection = db.collection(collection_name)
        
        # Get total document count
        stats["total_documents"] = collection.count()
        logger.info(f"Processing {stats['total_documents']} documents in {collection_name}")
        
        # Process documents in batches
        cursor = collection.all(batch_size=batch_size)
        
        for doc in cursor:
            try:
                # Check if document already has embedding
                if skip_existing and embedding_field_name in doc and doc[embedding_field_name]:
                    stats["documents_skipped"] += 1
                    continue
                
                # Generate embedding
                embedding = embed_document(doc, embedding_fields)
                
                if embedding:
                    # Update document with embedding
                    collection.update({
                        "_key": doc["_key"],
                        embedding_field_name: embedding
                    })
                    stats["documents_embedded"] += 1
                    
                    if stats["documents_embedded"] % 10 == 0:
                        logger.info(f"Embedded {stats['documents_embedded']} documents...")
                else:
                    stats["documents_failed"] += 1
                    logger.warning(f"Failed to embed document {doc['_key']}")
                    
            except Exception as e:
                stats["documents_failed"] += 1
                logger.error(f"Error processing document {doc.get('_key', 'unknown')}: {e}")
        
        logger.info(f"Embedding complete for {collection_name}: {stats}")
        
    except Exception as e:
        logger.error(f"Error embedding collection {collection_name}: {e}")
    
    return stats

def embed_multiple_collections(
    db_name: str,
    collection_configs: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Embed multiple collections with different configurations.
    
    Args:
        db_name: Name of the database
        collection_configs: List of configurations, each containing:
            - collection_name: Name of the collection
            - embedding_fields: List of fields to embed
            - embedding_field_name: Optional field name for embedding (default: "embedding")
            
    Returns:
        Dictionary mapping collection names to their embedding statistics
    """
    all_stats = {}
    
    for config in collection_configs:
        collection_name = config["collection_name"]
        embedding_fields = config["embedding_fields"]
        embedding_field_name = config.get("embedding_field_name", "embedding")
        
        logger.info(f"\nEmbedding collection: {collection_name}")
        logger.info(f"Fields: {embedding_fields}")
        
        stats = embed_collection(
            db_name=db_name,
            collection_name=collection_name,
            embedding_fields=embedding_fields,
            embedding_field_name=embedding_field_name
        )
        
        all_stats[collection_name] = stats
    
    return all_stats

def validate_embeddings(db_name: str, collection_name: str, sample_size: int = 5):
    """
    Validate that embeddings were created correctly.
    
    Args:
        db_name: Name of the database
        collection_name: Name of the collection
        sample_size: Number of documents to sample
    """
    try:
        client = ArangoClient(hosts=ARANGO_HOST)
        db = client.db(db_name, username=ARANGO_USER, password=ARANGO_PASSWORD)
        collection = db.collection(collection_name)
        
        # Get sample documents with embeddings
        query = f"""
        FOR doc IN {collection_name}
            FILTER doc.embedding != null
            LIMIT {sample_size}
            RETURN {{
                _key: doc._key,
                name: doc.name,
                embedding_length: LENGTH(doc.embedding),
                embedding_sample: SLICE(doc.embedding, 0, 5)
            }}
        """
        
        cursor = db.aql.execute(query)
        results = list(cursor)
        
        print(f"\n Validation for {collection_name}:")
        for doc in results:
            print(f"  - {doc['_key']}: {doc.get('name', 'N/A')}")
            print(f"    Embedding length: {doc['embedding_length']}")
            print(f"    First 5 values: {doc['embedding_sample']}")
        
        # Count total embedded documents
        count_query = f"""
        FOR doc IN {collection_name}
            FILTER doc.embedding != null
            COLLECT WITH COUNT INTO total
            RETURN total
        """
        cursor = db.aql.execute(count_query)
        total = list(cursor)[0] if cursor else 0
        print(f"  Total documents with embeddings: {total}")
        
    except Exception as e:
        logger.error(f"Validation error: {e}")

if __name__ == "__main__":
    """
    Example usage and validation of the embedding utility.
    """
    # Define collections and their embedding configurations
    pizza_collections = [
        {
            "collection_name": "pizzas",
            "embedding_fields": ["name", "description", "tags"]
        },
        {
            "collection_name": "ingredients",
            "embedding_fields": ["name", "category", "tags"]
        },
        {
            "collection_name": "customers",
            "embedding_fields": ["name", "dietary_preferences", "tags"]
        },
        {
            "collection_name": "pizza_reviews",  # We'll create this collection'
            "embedding_fields": ["review_text", "summary", "tags"]
        },
        {
            "collection_name": "memories",  # For memory agent testing
            "embedding_fields": ["content", "summary", "metadata.context", "tags"]
        }
    ]
    
    # Embed all collections
    print(" Embedding Pizza Database Collections")
    print("=" * 50)
    
    stats = embed_multiple_collections("pizza_test", pizza_collections)
    
    # Print summary
    print("\n Embedding Summary:")
    for collection, stat in stats.items():
        print(f"\n{collection}:")
        print(f"  - Total documents: {stat['total_documents']}")
        print(f"  - Documents embedded: {stat['documents_embedded']}")
        print(f"  - Documents skipped: {stat['documents_skipped']}")
        print(f"  - Documents failed: {stat['documents_failed']}")
    
    # Validate embeddings
    print("\n Validating Embeddings:")
    for config in pizza_collections:
        if stats.get(config["collection_name"], {}).get("total_documents", 0) > 0:
            validate_embeddings("pizza_test", config["collection_name"], sample_size=3)