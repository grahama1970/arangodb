#!/usr/bin/env python3
"""
Final test to confirm semantic search is working with the vector index fixes
"""

import sys
import time
from loguru import logger
from arango import ArangoClient

# Import our modules
from arangodb.core.search.semantic_search import semantic_search, validate_vector_index
from arangodb.core.utils.vector_utils import document_stats
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
    
    # Check collection statistics first
    logger.info(f"Checking embeddings in {COLLECTION_NAME}...")
    stats = document_stats(db, COLLECTION_NAME)
    
    print("\n=== SEMANTIC SEARCH VALIDATION TEST ===")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Total documents: {stats['total_documents']}")
    print(f"Documents with embeddings: {stats['documents_with_embeddings']}")
    print(f"Embedding dimensions: {stats['dimensions_found']}")
    
    # Validate vector index
    logger.info("Validating vector index...")
    index_valid = validate_vector_index(db, COLLECTION_NAME, EMBEDDING_FIELD)
    print(f"Vector index validation: {index_valid}")
    
    # Run test searches
    test_queries = [
        "Python programming",
        "machine learning",
        "database connections"
    ]
    
    all_tests_passed = True
    
    print("\n=== SEMANTIC SEARCH TESTS ===")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        try:
            result = semantic_search(
                db, 
                query, 
                collections=[COLLECTION_NAME],
                min_score=0.1,  # Lower threshold for testing
                top_n=3
            )
            
            if result['search_engine'] == "arangodb-approx-near-cosine" and result['total'] > 0:
                print(f"✓ PASSED - Found {result['total']} results")
                for i, res in enumerate(result['results']):
                    doc = res['doc']
                    score = res['similarity_score']
                    title = doc.get('title', 'No title')[:30]
                    print(f"  {i+1}. [{score:.4f}] {title}")
            else:
                print(f"✗ FAILED - No results found ({result['search_engine']})")
                all_tests_passed = False
                
        except Exception as e:
            print(f"✗ FAILED - Error: {str(e)}")
            all_tests_passed = False
    
    # Summary
    print("\n=== FINAL SUMMARY ===")
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - Semantic search is working properly!")
        print("The APPROX_NEAR_COSINE function is operational with:")
        print(f"- {stats['documents_with_embeddings']} documents with embeddings")
        print(f"- Embeddings of dimension {stats['dimensions_found']}")
        print(f"- Vector index status: {index_valid}")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Some semantic searches did not return results")
        sys.exit(1)

if __name__ == "__main__":
    main()