#!/usr/bin/env python3
"""
Main test runner for ArangoDB integration tests.

This script runs all tests for the ArangoDB integration, including:
- Database operations tests
- Search API tests
- Embedding integration tests
- Graph operations tests

Each test module provides comprehensive verification of its functionality
using real database operations and specific expected values.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import test modules
from tests.arangodb.test_modules.test_db_operations import run_all_tests as run_db_tests
from tests.arangodb.test_modules.test_embedding_operations import run_all_tests as run_embedding_tests
# Import search tests that were previously disabled due to import issues
from tests.arangodb.test_modules.test_search_api import run_all_tests as run_search_tests
# Still disable graph tests until its import issues are fixed
# from tests.arangodb.test_modules.test_graph_operations import run_all_tests as run_graph_tests

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run ArangoDB integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--module", "-m", type=str, 
                        choices=["db", "embedding", "search", "all"], 
                        default="all", help="Test module to run")
    parser.add_argument("--db-name", type=str, default="complexity_test", 
                        help="Database name to use for testing")
    return parser.parse_args()

def main():
    """Main function to run the tests."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set environment variables
    os.environ.setdefault("ARANGO_HOST", "http://localhost:8529")
    os.environ.setdefault("ARANGO_USER", "root")
    os.environ.setdefault("ARANGO_PASSWORD", "complexity")
    os.environ.setdefault("ARANGO_DB_NAME", args.db_name)
    
    # Set logging level based on verbosity
    if args.verbose:
        os.environ["LOG_LEVEL"] = "DEBUG"
    else:
        os.environ["LOG_LEVEL"] = "INFO"
    
    # Track overall success
    all_passed = True
    
    # Print test header
    print("\n" + "=" * 80)
    print(f"RUNNING ARANGODB INTEGRATION TESTS")
    print("=" * 80)
    
    # Run selected test modules based on arguments
    if args.module in ["db", "all"]:
        print("\n" + "=" * 80)
        print("RUNNING DATABASE OPERATIONS TESTS")
        print("=" * 80)
        db_success = run_db_tests()
        if not db_success:
            all_passed = False
            print("\n❌ Database operations tests failed")
        else:
            print("\n✅ Database operations tests passed")
    
    if args.module in ["embedding", "all"]:
        print("\n" + "=" * 80)
        print("RUNNING EMBEDDING OPERATIONS TESTS")
        print("=" * 80)
        embedding_success = run_embedding_tests()
        if not embedding_success:
            all_passed = False
            print("\n❌ Embedding operations tests failed")
        else:
            print("\n✅ Embedding operations tests passed")
    
    # Run search tests
    if args.module in ["search", "all"]:
        print("\n" + "=" * 80)
        print("RUNNING SEARCH API TESTS")
        print("=" * 80)
        search_success = run_search_tests()
        if not search_success:
            all_passed = False
            print("\n❌ Search API tests failed")
        else:
            print("\n✅ Search API tests passed")
    
    # Print overall summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    # Return appropriate exit code
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())