#!/usr/bin/env python3
"""
Test the integrated semantic search functionality with embedding validation
"""

import sys
import time
from loguru import logger
from arango import ArangoClient

# Import the integrated semantic search module
from arangodb.core.search.semantic_search import (
    semantic_search,
    check_collection_readiness,
    prepare_collection_for_search,
    ensure_document_has_embedding
)
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
    
    print("\n=== INTEGRATED SEMANTIC SEARCH TEST ===")
    
    # 1. Check collection readiness
    print("\n1. Checking collection readiness...")
    is_ready, status = check_collection_readiness(db, COLLECTION_NAME)
    print(f"Collection {COLLECTION_NAME} ready: {is_ready}")
    print(f"Status: {status['message']}")
    
    if status["issues"]:
        print("Issues found:")
        for issue in status["issues"]:
            print(f"  - {issue}")
    
    # 2. Test document with missing embedding
    print("\n2. Testing document validation...")
    test_doc = {
        "_key": "test_validation_doc",
        "title": "Integration Test Document",
        "content": "This document tests the integrated embedding validation"
    }
    
    # Ensure document has proper embedding
    validated_doc = ensure_document_has_embedding(test_doc, db, COLLECTION_NAME)
    print(f"Document has embedding: {'embedding' in validated_doc}")
    print(f"Document has metadata: {'embedding_metadata' in validated_doc}")
    
    # Insert the document
    collection = db.collection(COLLECTION_NAME)
    try:
        collection.insert(validated_doc, overwrite=True)
        print("Document inserted successfully")
    except Exception as e:
        print(f"Error inserting document: {e}")
    
    # 3. Test semantic search with validation
    print("\n3. Testing semantic search with validation...")
    queries = [
        "integration test",
        "embedding validation",
        "document validation",
        "semantic search"
    ]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        
        # Search with validation and auto-fix enabled
        result = semantic_search(
            db,
            query,
            collections=[COLLECTION_NAME],
            min_score=0.1,
            top_n=3,
            validate_before_search=True,
            auto_fix_embeddings=True
        )
        
        print(f"Search engine: {result['search_engine']}")
        print(f"Results found: {result['total']}")
        print(f"Time taken: {result['time']:.3f} seconds")
        
        if result.get("error"):
            print(f"Error: {result['error']}")
        
        if result["results"]:
            print("Top results:")
            for i, res in enumerate(result["results"]):
                doc = res["doc"]
                score = res["similarity_score"]
                title = doc.get("title", "No title")
                content = doc.get("content", "")[:50] + "..."
                print(f"  {i+1}. [{score:.4f}] {title}: {content}")
    
    # 4. Test with a collection that has issues
    print("\n4. Testing with a problematic collection...")
    test_collection = "test_problematic_collection"
    
    # Create collection if it doesn't exist
    if not db.has_collection(test_collection):
        db.create_collection(test_collection)
    
    # Insert documents with various issues
    problematic_docs = [
        {
            "_key": "no_embedding",
            "title": "Document without embedding",
            "content": "This document has no embedding field"
        },
        {
            "_key": "wrong_format",
            "title": "Document with wrong embedding format",
            "content": "This document has incorrect embedding",
            "embedding": "not_an_array"  # Wrong format
        },
        {
            "_key": "wrong_dimensions",
            "title": "Document with wrong dimensions",
            "content": "This document has wrong embedding dimensions",
            "embedding": [0.1, 0.2, 0.3]  # Wrong dimensions
        }
    ]
    
    test_collection_obj = db.collection(test_collection)
    for doc in problematic_docs:
        try:
            test_collection_obj.insert(doc, overwrite=True)
        except:
            pass
    
    # Check readiness of problematic collection
    print(f"\nChecking readiness of {test_collection}...")
    is_ready, status = check_collection_readiness(db, test_collection)
    print(f"Collection ready: {is_ready}")
    print(f"Status: {status['message']}")
    
    # Try to prepare the collection for search
    print(f"\nPreparing {test_collection} for search...")
    success, prep_result = prepare_collection_for_search(
        db,
        test_collection,
        fix_embeddings=True
    )
    
    print(f"Preparation successful: {success}")
    if prep_result["fix_results"]:
        print(f"Documents fixed: {prep_result['fix_results'].get('documents_fixed', 0)}")
        print(f"Errors: {prep_result['fix_results'].get('errors', 0)}")
    
    # 5. Final summary
    print("\n=== FINAL SUMMARY ===")
    
    # Get final stats for main collection
    final_ready, final_status = check_collection_readiness(db, COLLECTION_NAME)
    
    print(f"\nMain collection ({COLLECTION_NAME}):")
    print(f"  Ready for search: {final_ready}")
    print(f"  Documents with embeddings: {final_status['embeddings_count']}")
    print(f"  Consistent dimensions: {final_status['consistent_dimensions']}")
    print(f"  Embedding model: {final_status['model']}")
    print(f"  Dimensions: {final_status['dimensions']}")
    
    if final_ready:
        print("\n✅ Collection is fully ready for semantic search!")
    else:
        print("\n❌ Collection still has issues:")
        for issue in final_status["issues"]:
            print(f"  - {issue}")

if __name__ == "__main__":
    main()