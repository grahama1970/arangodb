#!/usr/bin/env python3
"""
Test semantic search integration after vector index fixes
"""

import sys
import time
from loguru import logger
from arango import ArangoClient

# Import our modules
from arangodb.core.search.semantic_search import semantic_search, check_and_fix_vector_index
from arangodb.core.utils.vector_utils import document_stats, ensure_vector_index
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
    
    # First, check the collection statistics
    logger.info(f"Checking embeddings in {COLLECTION_NAME}...")
    stats = document_stats(db, COLLECTION_NAME)
    
    print("\n=== Collection Statistics ===")
    print(f"Total documents: {stats['total_documents']}")
    print(f"Documents with embeddings: {stats['documents_with_embeddings']}")
    print(f"Documents with metadata: {stats['documents_with_metadata']}")
    print(f"Dimensions found: {stats['dimensions_found']}")
    print(f"Embedding models: {stats['embedding_models']}")
    
    if stats["issues"]:
        print("\nIssues found:")
        for issue in stats["issues"]:
            print(f"  - {issue}")
    
    # Check and fix vector index
    logger.info("Checking and fixing vector index...")
    index_result = check_and_fix_vector_index(db, COLLECTION_NAME)
    print(f"\nVector index check/fix result: {index_result}")
    
    # Run a test semantic search
    test_queries = [
        "test query",
        "Python programming",
        "machine learning",
        "database connections",
        "memory management"
    ]
    
    print("\n=== Semantic Search Tests ===")
    for query in test_queries:
        logger.info(f"Testing search with query: '{query}'")
        start_time = time.time()
        
        try:
            result = semantic_search(
                db, 
                query, 
                collections=[COLLECTION_NAME],
                min_score=0.1,  # Lower threshold for testing
                top_n=5
            )
            
            elapsed_time = time.time() - start_time
            
            print(f"\n--- Query: '{query}' ---")
            print(f"Search engine: {result['search_engine']}")
            print(f"Time: {elapsed_time:.3f} seconds")
            print(f"Results found: {result['total']}")
            
            if result['results']:
                print("Top results:")
                for i, res in enumerate(result['results'][:3]):
                    doc = res['doc']
                    score = res['similarity_score']
                    doc_id = doc.get('_id', 'unknown')
                    title = doc.get('title', doc.get('content', '')[:50] + '...')
                    print(f"  {i+1}. [{score:.4f}] {doc_id}: {title}")
            else:
                print("  No results found")
                
        except Exception as e:
            print(f"ERROR: {str(e)}")
            logger.error(f"Search failed for query '{query}': {e}")
            
    print("\n=== Test Summary ===")
    print("Semantic search test completed.")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Embeddings field: {EMBEDDING_FIELD}")
    print(f"Documents with embeddings: {stats['documents_with_embeddings']}")
    print(f"Vector index valid: {index_result}")

if __name__ == "__main__":
    main()