#!/usr/bin/env python3
"""
Debug index validation issue
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
    
    # Get all indexes
    indexes = collection.indexes()
    
    print(f"\n=== All indexes for {COLLECTION_NAME} ===")
    for index in indexes:
        print(f"\nIndex ID: {index.get('id')}")
        print(f"Type: {index.get('type')}")
        print(f"Fields: {index.get('fields')}")
        
        # Print the entire index object
        print(f"Full index info:")
        print(json.dumps(index, indent=2))
        
        # Check specific vector index fields
        if index.get("type") == "vector":
            print(f"\nVector index analysis:")
            print(f"  Has 'params' key: {'params' in index}")
            if 'params' in index:
                params = index['params']
                print(f"  Params type: {type(params)}")
                print(f"  Params value: {params}")
                
                if params:
                    print(f"  Dimension: {params.get('dimension')}")
                    print(f"  Metric: {params.get('metric')}")
                    print(f"  nLists: {params.get('nLists')}")
                else:
                    print(f"  Params is empty/None: {params}")

if __name__ == "__main__":
    main()