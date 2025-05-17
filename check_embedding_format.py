#!/usr/bin/env python3
"""
Check the format of embeddings in the collection
"""

import sys
import json
from loguru import logger
from arango import ArangoClient

from arangodb.core.constants import (
    ARANGO_HOST, ARANGO_DB_NAME, ARANGO_USER, ARANGO_PASSWORD,
    COLLECTION_NAME, EMBEDDING_FIELD
)

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:HH:mm:ss} | {level:<7} | {message}"
)

def main():
    # Connect to ArangoDB
    logger.info("Connecting to ArangoDB...")
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    # Get collection
    collection = db.collection(COLLECTION_NAME)
    
    # Query all documents with embeddings
    aql = f"""
    FOR doc IN {COLLECTION_NAME}
    FILTER HAS(doc, "{EMBEDDING_FIELD}")
    RETURN {{
        "_key": doc._key,
        "_id": doc._id,
        "embedding_type": TYPENAME(doc.{EMBEDDING_FIELD}),
        "is_array": IS_ARRAY(doc.{EMBEDDING_FIELD}),
        "is_object": IS_OBJECT(doc.{EMBEDDING_FIELD}),
        "embedding_sample": doc.{EMBEDDING_FIELD},
        "embedding_length": IS_ARRAY(doc.{EMBEDDING_FIELD}) ? LENGTH(doc.{EMBEDDING_FIELD}) : null,
        "metadata": doc.embedding_metadata
    }}
    """
    
    cursor = db.aql.execute(aql)
    docs_with_embeddings = list(cursor)
    
    print(f"\n=== Documents with embeddings: {len(docs_with_embeddings)} ===")
    
    for doc in docs_with_embeddings:
        print(f"\nDocument ID: {doc['_id']}")
        print(f"  Type: {doc['embedding_type']}")
        print(f"  Is Array: {doc['is_array']}")
        print(f"  Is Object: {doc['is_object']}")
        print(f"  Length: {doc['embedding_length']}")
        print(f"  Metadata: {doc.get('metadata', 'None')}")
        
        # Check embedding sample
        embedding = doc['embedding_sample']
        if embedding is not None:
            # Print type info
            print(f"  Actual Python type: {type(embedding)}")
            
            # If it's a dict/object, show its structure
            if isinstance(embedding, dict):
                print(f"  Dict keys: {list(embedding.keys())[:5]}")
                print(f"  First few values: {list(embedding.values())[:3]}")
            # If it's a list, show first few elements 
            elif isinstance(embedding, list):
                if len(embedding) > 0:
                    print(f"  First element type: {type(embedding[0])}")
                    print(f"  First few elements: {embedding[:3]}")
            else:
                print(f"  Value: {str(embedding)[:100]}")
    
    # Now check documents WITHOUT embeddings
    aql_no_embeddings = f"""
    FOR doc IN {COLLECTION_NAME}
    FILTER NOT HAS(doc, "{EMBEDDING_FIELD}")
    RETURN {{
        "_key": doc._key,
        "_id": doc._id,
        "title": doc.title,
        "content": SUBSTRING(doc.content, 0, 50)
    }}
    """
    
    cursor = db.aql.execute(aql_no_embeddings)
    docs_without_embeddings = list(cursor)
    
    print(f"\n=== Documents WITHOUT embeddings: {len(docs_without_embeddings)} ===")
    for doc in docs_without_embeddings:
        print(f"\nDocument ID: {doc['_id']}")
        print(f"  Title: {doc.get('title', 'No title')}")
        print(f"  Content: {doc.get('content', 'No content')}...")

if __name__ == "__main__":
    main()