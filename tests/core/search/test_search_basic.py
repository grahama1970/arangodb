#!/usr/bin/env python3
"""
Test all search functions to ensure they work correctly.
"""

import json
import sys
from loguru import logger

# Import all search functions
from arangodb.core.arango_setup import connect_arango, ensure_database
from arangodb.core.db_operations import create_document
from arangodb.core.search.keyword_search import search_keyword
from arangodb.core.search.semantic_search import semantic_search
from arangodb.core.search.bm25_search import bm25_search
from arangodb.core.search.hybrid_search import hybrid_search
from arangodb.core.constants import COLLECTION_NAME


def main():
    """Test all search functions with real data."""
    # Track all validation failures
    failures = []
    total_tests = 0
    
    # Connect to database
    logger.info("Connecting to ArangoDB...")
    client = connect_arango()
    db = ensure_database(client)
    
    # Create test documents
    logger.info("Creating test documents...")
    test_docs = [
        {
            "_key": "search_test_1",
            "title": "Python Programming Guide",
            "problem": "How to write efficient Python code",
            "solution": "Use list comprehensions, generators, and proper data structures",
            "context": "Best practices for Python development",
            "tags": ["python", "programming", "guide"],
            "content": "Python programming involves understanding best practices and efficient coding techniques"
        },
        {
            "_key": "search_test_2",
            "title": "JavaScript Error Handling",
            "problem": "Dealing with asynchronous errors in JavaScript",
            "solution": "Use try-catch blocks and Promise error handlers",
            "context": "JavaScript error handling patterns",
            "tags": ["javascript", "error", "async"],
            "content": "JavaScript error handling requires careful consideration of asynchronous operations"
        },
        {
            "_key": "search_test_3", 
            "title": "Database Optimization",
            "problem": "Slow query performance in database",
            "solution": "Add indexes and optimize query structure",
            "context": "Database performance tuning",
            "tags": ["database", "sql", "optimization"],
            "content": "Database optimization involves proper indexing and query optimization techniques"
        }
    ]
    
    # Add documents
    for doc in test_docs:
        try:
            result = create_document(db, COLLECTION_NAME, doc)
            logger.info(f"Added document: {doc['_key']}")
        except Exception as e:
            logger.warning(f"Document may already exist: {e}")
    
    # Wait for indexing
    import time
    time.sleep(2)
    
    # Test 1: Keyword Search
    total_tests += 1
    logger.info("\n=== Test 1: Keyword Search ===")
    try:
        results = search_keyword(
            db=db,
            search_term="python programming",
            similarity_threshold=80.0,
            top_n=5
        )
        
        if not results or len(results) == 0:
            failures.append("Keyword search returned 0 results")
            logger.error("FAIL: Keyword search returned 0 results")
        else:
            logger.info(f"PASS: Keyword search found {len(results)} results")
            for result in results[:2]:
                logger.info(f"  - {result.get('key', 'Unknown')}: {result.get('title', 'No title')}")
    except Exception as e:
        failures.append(f"Keyword search failed: {e}")
        logger.error(f"FAIL: Keyword search error: {e}")
    
    # Test 2: BM25 Search
    total_tests += 1
    logger.info("\n=== Test 2: BM25 Search ===")
    try:
        results = bm25_search(
            db=db,
            query="python code",
            limit=5
        )
        
        if not results or len(results) == 0:
            failures.append("BM25 search returned 0 results")
            logger.error("FAIL: BM25 search returned 0 results")
        else:
            logger.info(f"PASS: BM25 search found {len(results)} results")
            for result in results[:2]:
                doc = result.get('doc', {})
                logger.info(f"  - {doc.get('_key', 'Unknown')}: {doc.get('title', 'No title')}")
    except Exception as e:
        failures.append(f"BM25 search failed: {e}")
        logger.error(f"FAIL: BM25 search error: {e}")
    
    # Test 3: Semantic Search
    total_tests += 1
    logger.info("\n=== Test 3: Semantic Search ===")
    try:
        results = semantic_search(
            db=db,
            query="how to write efficient code",
            top_n=5
        )
        
        if not results or len(results) == 0:
            failures.append("Semantic search returned 0 results")
            logger.error("FAIL: Semantic search returned 0 results")
        else:
            logger.info(f"PASS: Semantic search found {len(results)} results")
            for result in results[:2]:
                logger.info(f"  - {result.get('doc', {}).get('_key', 'Unknown')}: {result.get('doc', {}).get('title', 'No title')}")
    except Exception as e:
        failures.append(f"Semantic search failed: {e}")
        logger.error(f"FAIL: Semantic search error: {e}")
    
    # Test 4: Hybrid Search
    total_tests += 1
    logger.info("\n=== Test 4: Hybrid Search ===")
    try:
        results = hybrid_search(
            db=db,
            query="database performance optimization",
            search_type=2,  # Combined search
            top_n=5
        )
        
        if not results or isinstance(results, dict) and results.get('total_results', 0) == 0:
            failures.append("Hybrid search returned 0 results")
            logger.error("FAIL: Hybrid search returned 0 results")
        else:
            count = len(results) if isinstance(results, list) else results.get('total_results', 0)
            logger.info(f"PASS: Hybrid search found {count} results")
    except Exception as e:
        failures.append(f"Hybrid search failed: {e}")
        logger.error(f"FAIL: Hybrid search error: {e}")
    
    # Cleanup test documents
    logger.info("\n=== Cleanup ===")
    for doc in test_docs:
        try:
            db.collection(COLLECTION_NAME).delete(doc['_key'])
            logger.info(f"Deleted test document: {doc['_key']}")
        except:
            pass
    
    # Final results
    logger.info("\n=== Test Summary ===")
    if failures:
        logger.error(f"❌ VALIDATION FAILED - {len(failures)} of {total_tests} tests failed:")
        for failure in failures:
            logger.error(f"  - {failure}")
        sys.exit(1)
    else:
        logger.success(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)


if __name__ == "__main__":
    main()