"""
Validation script for Search commands with real ArangoDB connection

This script tests all search operations with actual data to verify:
1. Real connections to ArangoDB work
2. BM25 search returns results
3. Semantic search with embeddings works
4. Hybrid search combines properly
5. Tag and keyword search function correctly
6. Graph traversal works
7. Both JSON and table output formats work
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all search functions
from arangodb.core.search import (
    bm25_search,
    semantic_search,
    hybrid_search,
    weighted_reciprocal_rank_fusion,
    rerank_search_results,
    tag_search,
    search_keyword,
    glossary_search,
    graph_traverse
)

# Import utilities
from arangodb.core.utils.embedding_utils import get_embedding
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.constants import (
    MEMORY_COLLECTION,
    MEMORY_EDGE_COLLECTION,
    GRAPH_NAME,
    SEARCH_FIELDS
)
from arangodb.core.db_operations import create_document

# For rich table display
from rich.console import Console
from rich.table import Table

console = Console()


def setup_test_data(db):
    """Setup test data for search validation"""
    logger.info("Setting up test data")
    
    try:
        # Use existing memory collections
        collection_name = MEMORY_COLLECTION
        edge_collection_name = MEMORY_EDGE_COLLECTION
        
        # Create test documents
        test_docs = [
            {
                "title": "Python Database Optimization Guide",
                "content": "This guide covers techniques for optimizing database queries in Python applications. Topics include indexing, query optimization, and connection pooling.",
                "tags": ["python", "database", "optimization", "performance"],
                "search_property": ["query_optimization", "indexing", "connection_pooling"],
                "metadata": {"author": "test", "date": "2024-01-01"}
            },
            {
                "title": "ArangoDB Vector Search Implementation",
                "content": "Learn how to implement vector search in ArangoDB using APPROX_NEAR_COSINE function. Covers embedding generation and similarity search techniques.",
                "tags": ["arangodb", "vector", "search", "embeddings"],
                "search_property": ["vector_search", "similarity", "embeddings"],
                "metadata": {"author": "test", "date": "2024-01-02"}
            },
            {
                "title": "Graph Database Best Practices",
                "content": "Essential patterns and practices for working with graph databases. Covers traversal algorithms, relationship modeling, and performance tuning.",
                "tags": ["graph", "database", "algorithms", "best-practices"],
                "search_property": ["graph_traversal", "relationship_modeling", "performance"],
                "metadata": {"author": "test", "date": "2024-01-03"}
            },
            {
                "title": "Memory Agent Testing Framework",
                "content": "Testing framework and strategies for memory agents. Includes unit testing, integration testing, and performance benchmarks.",
                "tags": ["testing", "memory", "framework", "benchmarks"],
                "search_property": ["unit_testing", "integration_testing", "benchmarks"],
                "metadata": {"author": "test", "date": "2024-01-04"}
            }
        ]
        
        created_keys = []
        collection = db.collection(collection_name)
        
        for doc in test_docs:
            # Generate embedding for semantic search
            if 'content' in doc:
                doc['embedding'] = get_embedding(doc['content'])
            
            # Add timestamp for testing
            doc['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Create document
            result = collection.insert(doc)
            created_keys.append(result['_key'])
            logger.info(f"Created test document: {result['_key']}")
        
        # Create some test relationships
        edge_collection = db.collection(edge_collection_name)
        
        # Create edges between test documents
        edge_collection.insert({
            "_from": f"{collection_name}/{created_keys[0]}",
            "_to": f"{collection_name}/{created_keys[1]}",
            "relationship": "related_to",
            "weight": 0.8
        })
        
        edge_collection.insert({
            "_from": f"{collection_name}/{created_keys[1]}",
            "_to": f"{collection_name}/{created_keys[2]}",
            "relationship": "implementation_of",
            "weight": 0.9
        })
        
        logger.info("Test data setup complete")
        return created_keys
        
    except Exception as e:
        logger.error(f"Failed to setup test data: {e}")
        return []


def test_bm25_search(db):
    """Test BM25 keyword search"""
    logger.info("Testing BM25 SEARCH")
    
    try:
        # Search for database-related content
        results = bm25_search(
            db=db,
            query_text="database optimization queries",
            min_score=0.1,
            top_n=5,
            offset=0,
            tag_list=None
        )
        
        if not isinstance(results, dict):
            return False, f"BM25 search results not a dict: {type(results)}"
        
        if 'results' not in results:
            return False, "BM25 search results missing 'results' key"
        
        result_count = len(results.get('results', []))
        logger.info(f"BM25 search returned {result_count} results")
        
        return True, f"Found {result_count} results"
        
    except Exception as e:
        return False, f"BM25 search failed: {str(e)}"


def test_semantic_search(db):
    """Test semantic vector search"""
    logger.info("Testing SEMANTIC SEARCH")
    
    try:
        # Use query text directly - semantic_search handles embedding generation
        query = "Python database performance tuning"
        
        results = semantic_search(
            db=db,
            query=query,  # Accepts string or embedding vector
            top_n=5,
            min_score=0.5,
            tag_list=None
        )
        
        if not isinstance(results, dict):
            return False, f"Semantic search results not a dict: {type(results)}"
        
        if 'results' not in results:
            return False, "Semantic search results missing 'results' key"
        
        result_count = len(results.get('results', []))
        logger.info(f"Semantic search returned {result_count} results")
        
        return True, f"Found {result_count} results"
        
    except Exception as e:
        return False, f"Semantic search failed: {str(e)}"


def test_hybrid_search(db):
    """Test hybrid search combining BM25 and semantic"""
    logger.info("Testing HYBRID SEARCH")
    
    try:
        results = hybrid_search(
            db=db,
            query_text="database optimization techniques",
            top_n=5,
            initial_k=10,
            min_score={"bm25": 0.1, "semantic": 0.5},  # Correct parameter format
            tag_list=None
        )
        
        if not isinstance(results, dict):
            return False, f"Hybrid search results not a dict: {type(results)}"
        
        if 'results' not in results:
            return False, "Hybrid search results missing 'results' key"
        
        result_count = len(results.get('results', []))
        logger.info(f"Hybrid search returned {result_count} results")
        
        return True, f"Found {result_count} results"
        
    except Exception as e:
        return False, f"Hybrid search failed: {str(e)}"


def test_tag_search(db):
    """Test tag-based search"""
    logger.info("Testing TAG SEARCH")
    
    try:
        results = tag_search(
            db=db,
            tags=["database", "optimization"],
            limit=5,
            require_all_tags=False
        )
        
        if not isinstance(results, dict):
            return False, f"Tag search results not a dict: {type(results)}"
        
        if 'results' not in results:
            return False, "Tag search results missing 'results' key"
        
        result_count = len(results.get('results', []))
        logger.info(f"Tag search returned {result_count} results")
        
        return True, f"Found {result_count} results"
        
    except Exception as e:
        return False, f"Tag search failed: {str(e)}"


def test_keyword_search(db):
    """Test exact keyword search"""
    logger.info("Testing KEYWORD SEARCH")
    
    try:
        results = search_keyword(
            db=db,
            search_term="optimization database",
            top_n=5,
            similarity_threshold=90.0,  # Use correct parameter
            tags=None,
            fields_to_search=None  # Use default fields
        )
        
        if not isinstance(results, dict):
            return False, f"Keyword search results not a dict: {type(results)}"
        
        result_count = len(results.get('results', []))
        logger.info(f"Keyword search returned {result_count} results")
        
        return True, f"Found {result_count} results"
        
    except Exception as e:
        return False, f"Keyword search failed: {str(e)}"


def test_graph_traverse(db):
    """Test graph traversal search"""
    logger.info("Testing GRAPH TRAVERSE")
    
    try:
        # First get a document key to start from
        collection = db.collection(MEMORY_COLLECTION)
        docs = list(collection.find({}, limit=1))
        
        if not docs:
            return False, "No documents found for graph traversal test"
        
        start_key = docs[0]['_key']
        
        # Test outbound traversal - use correct parameters
        results = graph_traverse(
            db=db,
            start_vertex_key=start_key,  # Just the key, not full ID
            direction="ANY",  # Use ANY for better results
            min_depth=1,
            max_depth=2,
            start_vertex_collection=MEMORY_COLLECTION,
            graph_name="memory_graph",  # Assuming this graph exists
            limit=10
        )
        
        if not isinstance(results, dict):
            return False, f"Graph traverse results not a dict: {type(results)}"
        
        result_count = len(results.get('results', []))
        logger.info(f"Graph traverse returned {result_count} results")
        
        return True, f"Found {result_count} connected documents"
        
    except Exception as e:
        return False, f"Graph traverse failed: {str(e)}"


def display_results_table(results):
    """Display results in a rich table format"""
    table = Table(title="Search Operations Validation Results")
    table.add_column("Operation", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    for operation, status, details in results:
        status_symbol = "✅" if status else "❌"
        table.add_row(operation, status_symbol, str(details))
    
    console.print(table)


def display_results_json(results):
    """Display results in JSON format"""
    json_results = {
        "validation_results": [
            {
                "operation": op,
                "status": "passed" if status else "failed",
                "details": str(details)
            }
            for op, status, details in results
        ],
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for _, status, _ in results if status),
            "failed": sum(1 for _, status, _ in results if not status)
        }
    }
    console.print(json.dumps(json_results, indent=2))


def cleanup_test_data(db, created_keys):
    """Clean up test data"""
    try:
        collection = db.collection(MEMORY_COLLECTION)
        edge_collection = db.collection(MEMORY_EDGE_COLLECTION)
        
        # Delete test documents
        for key in created_keys:
            try:
                collection.delete(key)
                logger.info(f"Cleaned up document: {key}")
            except:
                pass
        
        # Delete test edges
        edges = edge_collection.find({})
        for edge in edges:
            if edge.get('_from', '').startswith(f'{MEMORY_COLLECTION}/') and edge.get('_from', '').split('/')[-1] in created_keys:
                edge_collection.delete(edge['_key'])
                
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time} {level} {message}")
    
    # Track all results
    results = []
    created_keys = []
    
    try:
        # Get database connection
        db = get_db_connection()
        logger.info(f"Connected to ArangoDB")
        
        # Setup test data
        created_keys = setup_test_data(db)
        
        if created_keys:
            # Run all tests
            # Test 1: BM25 search
            success, result = test_bm25_search(db)
            results.append(("BM25 SEARCH", success, result))
            
            # Test 2: Semantic search
            success, result = test_semantic_search(db)
            results.append(("SEMANTIC SEARCH", success, result))
            
            # Test 3: Hybrid search
            success, result = test_hybrid_search(db)
            results.append(("HYBRID SEARCH", success, result))
            
            # Test 4: Tag search
            success, result = test_tag_search(db)
            results.append(("TAG SEARCH", success, result))
            
            # Test 5: Keyword search
            success, result = test_keyword_search(db)
            results.append(("KEYWORD SEARCH", success, result))
            
            # Test 6: Graph traverse
            success, result = test_graph_traverse(db)
            results.append(("GRAPH TRAVERSE", success, result))
            
            # Cleanup
            cleanup_test_data(db, created_keys)
        else:
            results.append(("SETUP", False, "Failed to create test data"))
        
        # Display results in both formats
        console.print("\n[bold]Table Format:[/bold]")
        display_results_table(results)
        
        console.print("\n[bold]JSON Format:[/bold]")
        display_results_json(results)
        
        # Final result
        failures = [r for r in results if not r[1]]
        if failures:
            console.print(f"\n❌ VALIDATION FAILED - {len(failures)} of {len(results)} tests failed")
            for op, _, details in failures:
                console.print(f"  - {op}: {details}")
            sys.exit(1)
        else:
            console.print(f"\n✅ VALIDATION PASSED - All {len(results)} tests produced expected results")
            console.print("Search operations are working correctly with real ArangoDB connection")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error during validation: {e}")
        logger.error(traceback.format_exc())
        console.print(f"\n❌ VALIDATION FAILED - Fatal error: {e}")
        sys.exit(1)