#!/usr/bin/env python3
"""
Fix embedding consistency in the collection by standardizing all embeddings to the same model
"""

import sys
from loguru import logger
from arango import ArangoClient

from arangodb.core.utils.vector_utils import fix_collection_embeddings
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
    
    print("\n=== Fixing Embedding Consistency ===")
    
    # Fix embeddings to use consistent model
    print(f"\nStandardizing all embeddings in {COLLECTION_NAME} to use the same model...")
    
    # Use the proper model name from our config
    fix_results = fix_collection_embeddings(
        db=db,
        collection_name=COLLECTION_NAME,
        embedding_model="BAAI/bge-large-en-v1.5",  # Use the standard model
        target_dimensions=1024,
        dry_run=False
    )
    
    print(f"\nFix Results:")
    print(f"Total documents: {fix_results['total_documents']}")
    print(f"Documents fixed: {fix_results['documents_fixed']}")
    print(f"Documents skipped: {fix_results['documents_skipped']}")
    print(f"Errors: {fix_results['errors']}")
    
    if fix_results["details"]:
        print("\nDetails:")
        for detail in fix_results["details"]:
            print(f"  - {detail}")
    
    print("\n✅ Embedding consistency fix completed!")

if __name__ == "__main__":
    main()