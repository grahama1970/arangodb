#!/usr/bin/env python3
"""
Force update all embeddings to have consistent metadata
"""

import sys
from loguru import logger
from arango import ArangoClient

from arangodb.core.constants import (
    ARANGO_HOST, ARANGO_DB_NAME, ARANGO_USER, ARANGO_PASSWORD,
    COLLECTION_NAME
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
    
    print("\n=== Force Updating Embedding Metadata ===")
    
    # Get collection
    collection = db.collection(COLLECTION_NAME)
    
    # Get all documents
    aql = f"""
    FOR doc IN {COLLECTION_NAME}
    RETURN doc
    """
    
    cursor = db.aql.execute(aql)
    documents = list(cursor)
    
    print(f"Found {len(documents)} documents")
    
    # Update each document to have consistent metadata
    updated_count = 0
    for doc in documents:
        if "embedding" in doc and isinstance(doc["embedding"], list):
            # Update metadata to use consistent model name
            doc["embedding_metadata"] = {
                "model": "BAAI/bge-large-en-v1.5",
                "dimensions": len(doc["embedding"]),
                "created_at": doc.get("embedding_metadata", {}).get("created_at", None) or int(time.time())
            }
            
            try:
                collection.update(doc)
                updated_count += 1
                print(f"Updated document {doc['_key']}")
            except Exception as e:
                print(f"Error updating document {doc['_key']}: {e}")
    
    print(f"\n✅ Updated {updated_count} documents with consistent metadata")
    
    # Verify the fix
    print("\nVerifying consistency...")
    aql_verify = f"""
    RETURN {{
        models: (
            FOR doc IN {COLLECTION_NAME}
            FILTER HAS(doc, "embedding_metadata")
                AND HAS(doc.embedding_metadata, "model")
            RETURN DISTINCT doc.embedding_metadata.model
        )
    }}
    """
    
    cursor = db.aql.execute(aql_verify)
    result = next(cursor)
    
    print(f"Embedding models after update: {result['models']}")
    
    if len(result['models']) == 1:
        print("✅ All embeddings now use consistent model!")
    else:
        print("⚠️ Still have multiple models - manual inspection needed")

if __name__ == "__main__":
    import time
    main()