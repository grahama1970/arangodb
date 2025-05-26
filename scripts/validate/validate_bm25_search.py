#!/usr/bin/env python3
"""
Validation script for bm25_search.py

This script tests the BM25 search functionality with a real ArangoDB connection.
It ensures that the module can be properly imported, and the search function can be called.
"""

import sys
import os
import json
from pathlib import Path
from loguru import logger

# Set up logger
logger.remove()
logger.add(sys.stderr, level="INFO")

def validate_bm25_search():
    """
    Validate bm25_search.py functionality with a real ArangoDB connection.
    """
    total_tests = 0
    failures = []
    
    try:
        # Add the src directory to the path
        sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        
        # Test 1: Import the module
        total_tests += 1
        logger.info("Test 1: Import the bm25_search module")
        try:
            from arangodb.core.search.bm25_search import bm25_search
            logger.info("✓ Successfully imported bm25_search")
        except ImportError as e:
            failures.append(f"Import error: {e}")
            logger.error(f"✗ Failed to import bm25_search: {e}")
            # Can't continue if import fails
            return False, total_tests, failures
        
        # Test 2: Import ArangoDB connection
        total_tests += 1
        logger.info("Test 2: Import and use arango_setup")
        try:
            from arangodb.core.arango_setup import connect_arango, ensure_database
            logger.info("✓ Successfully imported arango_setup")
        except ImportError as e:
            failures.append(f"arango_setup import error: {e}")
            logger.error(f"✗ Failed to import arango_setup: {e}")
            # Can't continue without connection
            return False, total_tests, failures
        
        # Test 3: Connect to ArangoDB
        total_tests += 1
        logger.info("Test 3: Connect to ArangoDB")
        try:
            client = connect_arango()
            db = ensure_database(client)
            logger.info(f"✓ Successfully connected to ArangoDB and ensured database")
        except Exception as e:
            failures.append(f"ArangoDB connection error: {e}")
            logger.error(f"✗ Failed to connect to ArangoDB: {e}")
            # Can't continue without database
            return False, total_tests, failures
        
        # Test 4: Execute a basic BM25 search
        total_tests += 1
        logger.info("Test 4: Execute a basic BM25 search")
        try:
            # Use a simple test query
            test_query = "test"
            results = bm25_search(
                db=db,
                query_text=test_query,
                top_n=5,
                min_score=0.0
            )
            
            # Verify results structure
            if not isinstance(results, dict):
                failures.append("bm25_search did not return a dictionary")
                logger.error("✗ bm25_search did not return a dictionary")
            elif "results" not in results:
                failures.append("bm25_search results missing 'results' key")
                logger.error("✗ bm25_search results missing 'results' key")
            elif "total" not in results:
                failures.append("bm25_search results missing 'total' key")
                logger.error("✗ bm25_search results missing 'total' key")
            else:
                logger.info(f"✓ Successfully executed BM25 search and got {len(results['results'])} results")
                logger.info(f"  Total results in database: {results['total']}")
        except Exception as e:
            failures.append(f"BM25 search execution error: {e}")
            logger.error(f"✗ Failed to execute BM25 search: {e}")
            # Continue to next test even if this fails
        
        # Return validation status
        return len(failures) == 0, total_tests, failures
    
    except Exception as e:
        failures.append(f"Unexpected error: {e}")
        logger.error(f"✗ Unexpected error during validation: {e}")
        return False, total_tests, failures

if __name__ == "__main__":
    logger.info("Running bm25_search validation...")
    passed, total_tests, failures = validate_bm25_search()
    
    if passed:
        logger.info(f"✅ VALIDATION PASSED - All {total_tests} tests for bm25_search passed")
        sys.exit(0)
    else:
        logger.error(f"❌ VALIDATION FAILED - {len(failures)} of {total_tests} tests failed:")
        for i, failure in enumerate(failures, 1):
            logger.error(f"  {i}. {failure}")
        sys.exit(1)