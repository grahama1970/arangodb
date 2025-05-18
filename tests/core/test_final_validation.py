#!/usr/bin/env python3
"""
Final validation test for integrated semantic search functionality
"""

import sys
import time
import json
from loguru import logger
from arango import ArangoClient

# Import the integrated semantic search module
from arangodb.core.search.semantic_search import (
    semantic_search,
    check_collection_readiness,
    ensure_document_has_embedding,
    check_collection_readiness
)
from arangodb.core.utils.vector_utils import document_stats
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

def run_comprehensive_tests():
    # Connect to ArangoDB
    logger.info("Connecting to ArangoDB...")
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    print("\n=== FINAL SEMANTIC SEARCH VALIDATION ===")
    
    test_results = {
        "collection_readiness": False,
        "embedding_validation": False,
        "search_functionality": False,
        "error_handling": False,
        "consistency_check": False
    }
    
    # 1. Collection Readiness Check
    print("\n1. Collection Readiness Check")
    print("-" * 40)
    
    is_ready, status = check_collection_readiness(db, COLLECTION_NAME)
    test_results["collection_readiness"] = is_ready
    
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Ready: {is_ready}")
    print(f"Documents with embeddings: {status['embeddings_count']}")
    print(f"Consistent dimensions: {status['consistent_dimensions']}")
    print(f"Embedding model: {status['model']}")
    
    # 2. Embedding Validation Test
    print("\n2. Embedding Validation Test")
    print("-" * 40)
    
    test_docs = [
        {
            "title": "Final Test Document 1",
            "content": "This document tests the embedding validation system"
        },
        {
            "title": "Final Test Document 2",
            "content": "Another document to verify consistency",
            "embedding": [0.1, 0.2]  # Intentionally wrong dimensions
        },
        {
            "title": "Final Test Document 3",
            "content": "Document with pre-existing valid embedding",
            "embedding": [0.1] * 1024,  # Correct dimensions
            "embedding_metadata": {
                "model": "wrong_model",  # Wrong model name
                "dimensions": 1024
            }
        }
    ]
    
    collection = db.collection(COLLECTION_NAME)
    validated_count = 0
    
    for i, doc in enumerate(test_docs):
        print(f"\nValidating document {i+1}...")
        validated_doc = ensure_document_has_embedding(doc.copy(), db, COLLECTION_NAME)
        
        # Check if validation worked
        if "embedding" in validated_doc and "embedding_metadata" in validated_doc:
            metadata = validated_doc["embedding_metadata"]
            # Check if embedding was properly created/fixed
            if (isinstance(validated_doc["embedding"], list) and 
                len(validated_doc["embedding"]) == 1024 and
                metadata.get("model") == "BAAI/bge-large-en-v1.5" and 
                metadata.get("dimensions") == 1024):
                validated_count += 1
                print(f"✓ Document {i+1} validated successfully")
            else:
                print(f"✗ Document {i+1} validation failed")
                print(f"  Embedding type: {type(validated_doc.get('embedding'))}")
                print(f"  Embedding dimensions: {len(validated_doc.get('embedding', []))}")
                print(f"  Metadata: {metadata}")
        else:
            print(f"✗ Document {i+1} missing embedding or metadata")
    
    test_results["embedding_validation"] = validated_count == len(test_docs)
    print(f"\nValidation success rate: {validated_count}/{len(test_docs)}")
    
    # 3. Search Functionality Test
    print("\n3. Search Functionality Test")
    print("-" * 40)
    
    test_queries = [
        ("embedding validation", 0.3),
        ("final test document", 0.5),
        ("semantic search functionality", 0.1),
        ("Python programming", 0.3),
        ("machine learning", 0.3)
    ]
    
    successful_searches = 0
    for query, min_score in test_queries:
        print(f"\nSearching for: '{query}' (min_score: {min_score})")
        
        result = semantic_search(
            db,
            query,
            collections=[COLLECTION_NAME],
            min_score=min_score,
            top_n=3,
            validate_before_search=True
        )
        
        if result["search_engine"] == "arangodb-approx-near-cosine" and result["total"] >= 0:
            successful_searches += 1
            print(f"✓ Search successful - found {result['total']} results")
            
            if result["results"]:
                for i, res in enumerate(result["results"][:2]):
                    doc = res["doc"]
                    score = res["similarity_score"]
                    title = doc.get("title", "No title")
                    print(f"  {i+1}. [{score:.4f}] {title}")
        else:
            print(f"✗ Search failed: {result.get('error', 'Unknown error')}")
    
    test_results["search_functionality"] = successful_searches == len(test_queries)
    print(f"\nSearch success rate: {successful_searches}/{len(test_queries)}")
    
    # 4. Error Handling Test
    print("\n4. Error Handling Test")
    print("-" * 40)
    
    # Test with invalid query - semantic_search may return an error instead of raising exception
    result = semantic_search(
        db,
        None,  # Invalid query
        collections=[COLLECTION_NAME]
    )
    
    if result["search_engine"] == "failed" and "error" in result:
        print("✓ Correctly handled invalid query")
        test_results["error_handling"] = True
    else:
        print("✗ Should have returned an error for None query")
        test_results["error_handling"] = False
    
    # Test with non-existent collection
    result = semantic_search(
        db,
        "test query",
        collections=["non_existent_collection"],
        validate_before_search=True
    )
    
    if result["search_engine"] == "failed" and "error" in result:
        print("✓ Correctly handled non-existent collection")
    else:
        print("✗ Did not properly handle non-existent collection")
        test_results["error_handling"] = False
    
    # 5. Consistency Check
    print("\n5. Consistency Check")
    print("-" * 40)
    
    stats = document_stats(db, COLLECTION_NAME)
    
    consistency_issues = []
    if len(stats["dimensions_found"]) > 1:
        consistency_issues.append(f"Multiple dimensions: {stats['dimensions_found']}")
    if len(stats["embedding_models"]) > 1:
        consistency_issues.append(f"Multiple models: {stats['embedding_models']}")
    if stats["documents_with_embeddings"] < stats["total_documents"]:
        consistency_issues.append(f"{stats['total_documents'] - stats['documents_with_embeddings']} documents missing embeddings")
    
    test_results["consistency_check"] = len(consistency_issues) == 0
    
    if consistency_issues:
        print("✗ Consistency issues found:")
        for issue in consistency_issues:
            print(f"  - {issue}")
    else:
        print("✓ All embeddings are consistent")
        print(f"  Model: {next(iter(stats['embedding_models']))}")
        print(f"  Dimensions: {next(iter(stats['dimensions_found']))}")
        print(f"  Documents: {stats['documents_with_embeddings']}/{stats['total_documents']}")
    
    # Final Summary
    print("\n" + "=" * 50)
    print("FINAL TEST RESULTS")
    print("=" * 50)
    
    all_passed = all(test_results.values())
    for test, passed in test_results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test.replace('_', ' ').title()}: {status}")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("Semantic search with embedding validation is fully operational!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the failed tests above.")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_comprehensive_tests())