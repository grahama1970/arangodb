"""
Test Search Configuration Module

Tests the search configuration functionality including config management,
query routing, and integration with hybrid search.
"""

import sys
import os
import time
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from loguru import logger
from arango import ArangoClient
from arangodb.core.search.search_config import (
    SearchConfig,
    SearchConfigManager,
    SearchMethod,
    QueryTypeConfig
)
from arangodb.core.search.hybrid_search import search_with_config
from arangodb.core.constants import (
    COLLECTION_NAME,
    EDGE_COLLECTION_NAME,
    GRAPH_NAME
)
from arangodb.core.db_operations import (
    create_document,
    create_relationship
)
# from arangodb.core.search.semantic_search import create_fixed_embeddings_if_needed  # Function doesn't exist
from arangodb.core.utils.embedding_utils import get_embedding


def get_test_db_connection():
    """Get test database connection."""
    client = ArangoClient(hosts='http://localhost:8529')
    return client.db('test', username='root', password='root')


def setup_test_data(db):
    """Setup test documents and relationships for search testing."""
    logger.info("Setting up test data for search configuration")
    
    # Ensure collections exist
    # ensure_collections_and_views(db)  # Function no longer exists
    
    # Create test documents with different content types
    test_docs = [
        {
            "title": "Python Basics",
            "content": "Python is a high-level programming language known for its simplicity",
            "tags": ["python", "programming", "tutorial"],
            "doc_type": "tutorial"
        },
        {
            "title": "Why Python is Popular",
            "content": "Python has become popular due to its readable syntax and vast ecosystem",
            "tags": ["python", "analysis", "programming"],
            "doc_type": "article"
        },
        {
            "title": "How many Python developers exist",
            "content": "Statistics show there are millions of Python developers worldwide",
            "tags": ["python", "statistics", "developers"],
            "doc_type": "factoid"
        },
        {
            "title": "Recent Python Updates",
            "content": "Latest Python 3.12 brings improved performance and new features",
            "tags": ["python", "updates", "recent"],
            "doc_type": "news"
        }
    ]
    
    created_docs = []
    for doc_data in test_docs:
        # Add embedding
        doc_data["embedding"] = get_embedding(f"{doc_data['title']} {doc_data['content']}")
        doc_data["created_at"] = time.time()
        
        result = create_document(db, COLLECTION_NAME, doc_data)
        created_docs.append(result)
        logger.info(f"Created test document: {doc_data['title']}")
    
    # Create some relationships
    if len(created_docs) >= 2:
        create_relationship(
            db,
            created_docs[0]["_key"],  # Use _key not _id
            created_docs[1]["_key"],  # Use _key not _id
            "relates_to",
            "Both about Python",  # rationale is a string, not dict
            {"reason": "Both about Python"}  # This is the attributes dict
        )
    
    logger.info("Test data setup complete")
    return created_docs


def test_search_config_basics():
    """Test basic search configuration functionality."""
    logger.info("Testing search configuration basics")
    
    # Test default config
    config = SearchConfig()
    assert config.preferred_method == SearchMethod.HYBRID
    assert config.result_limit == 20
    assert config.bm25_weight == 0.5
    assert config.semantic_weight == 0.5
    logger.info("✓ Default config created successfully")
    
    # Test query type configs
    assert QueryTypeConfig.FACTUAL.preferred_method == SearchMethod.BM25
    assert QueryTypeConfig.CONCEPTUAL.preferred_method == SearchMethod.SEMANTIC
    assert QueryTypeConfig.TAG_BASED.preferred_method == SearchMethod.TAG
    logger.info("✓ Query type configs validated")
    
    # Test config manager
    manager = SearchConfigManager()
    
    # Test query routing
    factual_config = manager.get_config_for_query("What is Python?")
    assert factual_config.preferred_method == SearchMethod.BM25
    
    conceptual_config = manager.get_config_for_query("Why is Python important?")
    assert conceptual_config.preferred_method == SearchMethod.SEMANTIC
    
    tag_config = manager.get_config_for_query("Show me tag:python")
    assert tag_config.preferred_method == SearchMethod.TAG
    
    graph_config = manager.get_config_for_query("What's related to Python?")
    assert graph_config.preferred_method == SearchMethod.GRAPH
    
    logger.info("✓ Query routing working correctly")
    
    # Test custom config registration
    custom = SearchConfig(
        preferred_method=SearchMethod.SEMANTIC,
        result_limit=50,
        enable_reranking=True
    )
    manager.register_custom_config("semantic_heavy", custom)
    retrieved = manager.get_custom_config("semantic_heavy")
    assert retrieved is not None
    assert retrieved.result_limit == 50
    assert retrieved.enable_reranking == True
    logger.info("✓ Custom config registration working")
    
    return True


def test_search_with_config(db):
    """Test search execution with different configurations."""
    logger.info("Testing search with configuration")
    
    # Setup test data
    setup_test_data(db)
    
    # Create fixed embeddings for search
    # create_fixed_embeddings_if_needed(db, [COLLECTION_NAME])  # Function no longer exists
    
    test_cases = [
        {
            "query": "What is Python?",
            "expected_method": SearchMethod.BM25,
            "description": "Factual query"
        },
        {
            "query": "Why is Python popular?", 
            "expected_method": SearchMethod.SEMANTIC,
            "description": "Conceptual query"
        },
        {
            "query": "Recent Python updates",
            "expected_method": SearchMethod.HYBRID,
            "description": "Recent/temporal query"
        }
    ]
    
    manager = SearchConfigManager()
    
    for test_case in test_cases:
        query = test_case["query"]
        expected_method = test_case["expected_method"]
        description = test_case["description"]
        
        # Get config for query
        config = manager.get_config_for_query(query)
        logger.info(f"Testing {description}: '{query}'")
        logger.info(f"Config method: {config.preferred_method.value}")
        
        # Execute search with config
        results = search_with_config(
            db=db,
            query_text=query,
            config=config,
            output_format="json"
        )
        
        # Validate results
        assert "results" in results
        assert "total" in results
        assert "search_engine" in results
        
        if results["total"] > 0:
            logger.info(f"✓ Found {results['total']} results")
            # Check first result has expected fields
            first_result = results["results"][0]
            assert "doc" in first_result
            assert any(key in first_result for key in ["score", "hybrid_score", "bm25_score", "semantic_score"])
        else:
            logger.warning(f"No results found for query: {query}")
    
    # Test custom configuration
    custom_config = SearchConfig(
        preferred_method=SearchMethod.BM25,
        result_limit=5,
        min_score=0.5
    )
    
    results = search_with_config(
        db=db,
        query_text="Python",
        config=custom_config,
        output_format="json"
    )
    
    assert len(results.get("results", [])) <= 5
    logger.info("✓ Custom config limit working")
    
    return True


def test_search_config_cli():
    """Test CLI command functionality."""
    logger.info("Testing search configuration CLI")
    
    # Test imports
    try:
        from arangodb.cli.search_config_commands import app
        logger.info("✓ CLI commands module imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import CLI commands: {e}")
        return False
    
    # Basic validation (actual CLI testing would require running commands)
    return True


def main():
    """Run all search configuration tests."""
    logger.info("Starting search configuration tests")
    
    # Initialize database connection
    db = get_test_db_connection()
    
    # Run tests
    test_results = []
    
    # Test 1: Basic configuration
    try:
        result = test_search_config_basics()
        test_results.append(("Config Basics", result))
    except Exception as e:
        logger.error(f"Config basics test failed: {e}")
        test_results.append(("Config Basics", False))
    
    # Test 2: Search with configuration
    try:
        result = test_search_with_config(db)
        test_results.append(("Search with Config", result))
    except Exception as e:
        logger.error(f"Search with config test failed: {e}")
        test_results.append(("Search with Config", False))
    
    # Test 3: CLI functionality
    try:
        result = test_search_config_cli()
        test_results.append(("CLI Commands", result))
    except Exception as e:
        logger.error(f"CLI test failed: {e}")
        test_results.append(("CLI Commands", False))
    
    # Report results
    print("\n=== Search Configuration Test Results ===")
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ All search configuration tests passed!")
    else:
        print("\n❌ Some tests failed")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)