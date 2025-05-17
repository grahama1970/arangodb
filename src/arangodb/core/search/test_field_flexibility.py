"""
Test Field Flexibility
======================

This module demonstrates the field flexibility improvements that allow text searches
to work with different document structures while keeping the embedding field standardized.

Third-party packages:
- python-arango: https://python-driver.arangodb.com/

Sample test document structure:
```json
{
    "_key": "test_doc_1",
    "custom_title": "Example Document",
    "body_text": "This is the main content of the document",
    "description": "This is a summary of the document",
    "keywords": ["example", "test"],
    "embedding": [0.1, 0.2, 0.3, ...]  # Always standardized
}
```

Expected output: Successfully runs searches with custom field names.
"""

import sys
import json
from typing import List
from loguru import logger
from colorama import init, Fore, Style

# Import database functions
from arangodb.core.arango_setup import connect_arango, ensure_database, ensure_collection
from arangodb.core.constants import DEFAULT_EMBEDDING_DIMENSIONS

# Import search functions  
from arangodb.core.search.keyword_search import search_keyword
from arangodb.core.search.bm25_search import bm25_search
from arangodb.core.search.hybrid_search import hybrid_search

# Import embedding utilities
from arangodb.core.utils.embedding_utils import get_embedding


def setup_test_collection(db, collection_name: str = "test_custom_fields"):
    """Create a test collection with documents having custom field names."""
    if db.has_collection(collection_name):
        db.delete_collection(collection_name)
    
    collection = db.create_collection(collection_name)
    
    # Create test documents with custom field names
    test_docs = [
        {
            "_key": "doc1",
            "custom_title": "Python Programming Guide",
            "body_text": "Learn Python programming with this comprehensive guide",
            "description": "A complete guide to Python programming",
            "keywords": ["python", "programming", "tutorial"],
            "embedding": get_embedding("Python programming tutorial guide")
        },
        {
            "_key": "doc2", 
            "custom_title": "Database Systems",
            "body_text": "Understanding modern database systems and architectures",
            "description": "Overview of database technology",
            "keywords": ["database", "systems", "architecture"],
            "embedding": get_embedding("Database systems and architectures")
        },
        {
            "_key": "doc3",
            "custom_title": "Web Development",
            "body_text": "Building modern web applications with JavaScript",
            "description": "Web development with modern frameworks",
            "keywords": ["web", "javascript", "development"],
            "embedding": get_embedding("Web development JavaScript applications")
        }
    ]
    
    # Insert documents
    for doc in test_docs:
        collection.insert(doc)
    
    logger.info(f"Created test collection '{collection_name}' with {len(test_docs)} documents")
    return collection_name


def test_keyword_search_flexibility(db, collection_name: str):
    """Test keyword search with custom field names."""
    print(f"\n{Fore.CYAN}Testing Keyword Search Flexibility{Style.RESET_ALL}")
    
    # Create a view that includes our custom fields
    view_name = f"{collection_name}_view"
    try:
        # Delete existing view if it exists (use correct method)
        all_views = db.views()
        if view_name in [v['name'] for v in all_views]:
            db.delete_view(view_name)
            
        # Create a new view with custom field analyzers
        view = db.create_view(
            view_name,
            view_type="arangosearch",
            properties={
                "links": {
                    collection_name: {
                        "fields": {
                            "custom_title": {
                                "analyzers": ["text_en"]
                            },
                            "body_text": {
                                "analyzers": ["text_en"]  
                            },
                            "description": {
                                "analyzers": ["text_en"]
                            }
                        }
                    }
                }
            }
        )
        logger.info(f"Created view '{view_name}' for keyword search")
    except Exception as e:
        logger.error(f"Error creating view: {e}")
        return False
    
    # Test with custom fields
    print("\n1. Custom fields keyword search:")
    results = search_keyword(
        db=db,
        search_term="python",
        collection_name=collection_name,
        fields_to_search=["custom_title", "body_text", "description"],
        view_name=view_name,  # Use custom view
        output_format="json"
    )
    print(f"   Found {results['total']} results (expected 1)")
    if results.get('results'):
        doc = results['results'][0]['doc']
        print(f"   Found document: {doc.get('custom_title', 'No title')}")
    
    return results.get('total', 0) >= 1


def test_bm25_search_flexibility(db, collection_name: str):
    """Test BM25 search with custom field names."""
    print(f"\n{Fore.CYAN}Testing BM25 Search Flexibility{Style.RESET_ALL}")
    
    # Use existing view created by keyword test
    view_name = f"{collection_name}_view"
    
    # Test with custom fields
    print("\n1. Custom fields BM25 search:")
    results = bm25_search(
        db=db,
        query_text="python programming",
        collections=[collection_name],
        fields_to_search=["custom_title", "body_text", "description"],
        view_name=view_name,
        output_format="json"
    )
    print(f"   Found {results['total']} results (expected 1)")
    if results.get('results'):
        doc = results['results'][0]['doc']
        print(f"   Found document: {doc.get('custom_title', 'No title')}")
        print(f"   Score: {results['results'][0]['score']}")
    
    return results.get('total', 0) >= 1


def test_hybrid_search_flexibility(db, collection_name: str):
    """Test hybrid search with custom field names."""
    print(f"\n{Fore.CYAN}Testing Hybrid Search Flexibility{Style.RESET_ALL}")
    
    # Test with custom fields
    print("\n1. Custom fields hybrid search:")
    results = hybrid_search(
        db=db,
        query_text="database systems",
        collections=[collection_name],
        fields_to_search=["custom_title", "body_text", "description"],
        output_format="json",
        top_n=5
    )
    print(f"   Found {results['total']} results (expected at least 1)")
    if results.get('results'):
        for i, result in enumerate(results['results'][:3]):
            doc = result['doc']
            print(f"   Result {i+1}: {doc.get('custom_title', 'No title')}")
            print(f"   Score: {result.get('combined_score', 'N/A')}")
    
    return results.get('total', 0) >= 1


if __name__ == "__main__":
    """Validate field flexibility with real test data."""
    init(autoreset=True)
    
    print(f"{Fore.GREEN}Testing Search Field Flexibility{Style.RESET_ALL}")
    print("=" * 50)
    
    # Connect to database
    print(f"\n{Fore.YELLOW}Connecting to database...{Style.RESET_ALL}")
    try:
        # Use a clean test database
        client = connect_arango()
        sys_db = client.db("_system", username="root", password="openSesame")
        
        # Create test database if it doesn't exist
        test_db_name = "test_field_flexibility"
        if not sys_db.has_database(test_db_name):
            sys_db.create_database(test_db_name)
        
        # Connect to test database
        db = client.db(test_db_name, username="root", password="openSesame")
        print(f"{Fore.GREEN}✓ Connected to test database{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Failed to connect to database: {e}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Setup test collection
    print(f"\n{Fore.YELLOW}Setting up test collection...{Style.RESET_ALL}")
    collection_name = setup_test_collection(db)
    
    # Run tests
    tests_passed = []
    
    # Test 1: Keyword search
    try:
        passed = test_keyword_search_flexibility(db, collection_name)
        tests_passed.append(passed)
        print(f"\n{Fore.GREEN}✓ Keyword search test {'passed' if passed else 'failed'}{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}✗ Keyword search test failed: {e}{Style.RESET_ALL}")
        tests_passed.append(False)
    
    # Test 2: BM25 search
    try:
        passed = test_bm25_search_flexibility(db, collection_name)
        tests_passed.append(passed)
        print(f"\n{Fore.GREEN}✓ BM25 search test {'passed' if passed else 'failed'}{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}✗ BM25 search test failed: {e}{Style.RESET_ALL}")
        tests_passed.append(False)
    
    # Test 3: Hybrid search  
    try:
        passed = test_hybrid_search_flexibility(db, collection_name)
        tests_passed.append(passed)
        print(f"\n{Fore.GREEN}✓ Hybrid search test {'passed' if passed else 'failed'}{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}✗ Hybrid search test failed: {e}{Style.RESET_ALL}")
        tests_passed.append(False)
    
    # Cleanup
    try:
        db.delete_collection(collection_name)
        # Delete the view as well
        view_name = f"{collection_name}_view"
        all_views = db.views()
        if view_name in [v['name'] for v in all_views]:
            db.delete_view(view_name)
        # Delete the test database
        sys_db.drop_database(test_db_name)
    except Exception as e:
        print(f"Cleanup error: {e}")
        pass
    
    # Summary
    print(f"\n{Fore.CYAN}Test Summary{Style.RESET_ALL}")
    print("=" * 50)
    passed_count = sum(tests_passed)
    total_tests = len(tests_passed)
    
    if passed_count == total_tests:
        print(f"{Fore.GREEN}✓ All {total_tests} tests passed!{Style.RESET_ALL}")
        print("\nField flexibility is working correctly:")
        print("- Text searches can use custom field names")
        print("- Embedding field remains standardized as 'embedding'")
        print("- Agents can work with different document structures")
        sys.exit(0)
    else:
        print(f"{Fore.RED}✗ {total_tests - passed_count} of {total_tests} tests failed{Style.RESET_ALL}")
        sys.exit(1)