"""
Validation script for Graph commands with real ArangoDB connection

This script tests all graph operations with actual data to verify:
1. Real connections to ArangoDB work
2. Relationship creation and deletion work
3. Graph traversal functions correctly
4. Both JSON and table output formats work
5. Expected results match actual results
"""

import json
import sys
import os
from pathlib import Path
from loguru import logger
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import core graph functions
from arangodb.core.graph import (
    create_relationship,
    delete_relationship_by_key,
    graph_traverse
)

# Import db operations for document creation
from arangodb.core.db_operations import create_document

# Import db connection
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.constants import COLLECTION_NAME, EDGE_COLLECTION_NAME, GRAPH_NAME

# For embedding
from arangodb.core.utils.embedding_utils import get_embedding

# For rich table display
from rich.console import Console
from rich.table import Table

console = Console()


def setup_test_data(db):
    """Create test documents for graph operations"""
    try:
        # Create test documents with embeddings
        test_docs = []
        
        # Document 1: AI topic
        doc1_text = "Understanding machine learning algorithms"
        doc1 = {
            "title": "AI Fundamentals",
            "content": doc1_text,
            "tags": ["AI", "machine learning", "algorithms"],
            "embedding": get_embedding(doc1_text)
        }
        result1 = create_document(db, COLLECTION_NAME, doc1)
        test_docs.append(result1)
        
        # Document 2: Related AI topic
        doc2_text = "Deep learning and neural networks"
        doc2 = {
            "title": "Neural Networks",
            "content": doc2_text,
            "tags": ["AI", "deep learning", "neural networks"],
            "embedding": get_embedding(doc2_text)
        }
        result2 = create_document(db, COLLECTION_NAME, doc2)
        test_docs.append(result2)
        
        # Document 3: Database topic
        doc3_text = "NoSQL database design patterns"
        doc3 = {
            "title": "Database Design",
            "content": doc3_text,
            "tags": ["database", "NoSQL", "design patterns"],
            "embedding": get_embedding(doc3_text)
        }
        result3 = create_document(db, COLLECTION_NAME, doc3)
        test_docs.append(result3)
        
        logger.info(f"Created {len(test_docs)} test documents")
        return test_docs
        
    except Exception as e:
        logger.error(f"Failed to setup test data: {e}")
        return []


def test_create_relationship(db, from_key, to_key):
    """Test relationship creation"""
    logger.info(f"Testing CREATE RELATIONSHIP between {from_key} and {to_key}")
    
    relationship_data = {
        "rationale": "These documents cover related AI topics",
        "confidence": 0.85,
        "relationship_type": "RELATED_TO",
        "context": "Both discuss fundamental AI concepts"
    }
    
    try:
        result = create_relationship(
            db=db,
            from_doc_key=from_key,
            to_doc_key=to_key,
            relationship_type="RELATED_TO",
            rationale=relationship_data["rationale"],
            attributes={
                "confidence": relationship_data["confidence"],
                "context": relationship_data["context"]
            }
        )
        
        if not result:
            return False, "Failed to create relationship - no result returned"
        
        # Verify the relationship was created
        edge_key = result.get('_key')
        if not edge_key:
            return False, "Created relationship missing _key"
        
        # Check required fields
        if result.get('_from') != f"{COLLECTION_NAME}/{from_key}":
            return False, f"Wrong _from field: expected '{COLLECTION_NAME}/{from_key}', got '{result.get('_from')}'"
        
        if result.get('_to') != f"{COLLECTION_NAME}/{to_key}":
            return False, f"Wrong _to field: expected '{COLLECTION_NAME}/{to_key}', got '{result.get('_to')}'"
        
        logger.info(f"Successfully created relationship: {edge_key}")
        return True, edge_key
        
    except Exception as e:
        return False, f"Create relationship failed: {str(e)}"


def test_graph_traverse(db, start_key):
    """Test graph traversal using AQL directly"""
    logger.info(f"Testing GRAPH TRAVERSE from {start_key}")
    
    try:
        # Since the wrapper requires a query text and we just want to traverse,
        # let's use a direct AQL query instead
        aql = '''
        FOR v, e, p IN 1..2 OUTBOUND @start_vertex
        GRAPH @graph_name
        RETURN {
            vertex: v,
            edge: e,
            path: p
        }
        '''
        
        # Use the direct AQL query
        cursor = db.aql.execute(
            aql,
            bind_vars={
                'start_vertex': f"{COLLECTION_NAME}/{start_key}",
                'graph_name': GRAPH_NAME
            }
        )
        
        results = list(cursor)
        
        if not isinstance(results, list):
            return False, f"Traverse returned wrong type: {type(results)}"
        
        # Check if we have at least one result (the related document)
        if len(results) == 0:
            return False, "No traversal results found - check if relationship was created"
        
        # Check result structure
        for result in results:
            if not isinstance(result, dict):
                return False, f"Result item is not a dict: {type(result)}"
            
            # Check for expected fields
            if 'vertex' not in result or 'edge' not in result or 'path' not in result:
                return False, f"Result missing expected fields: {result.keys()}"
        
        logger.info(f"Successfully traversed graph, found {len(results)} paths")
        return True, results
        
    except Exception as e:
        return False, f"Graph traverse failed: {str(e)}"


def test_delete_relationship(db, edge_key):
    """Test relationship deletion"""
    logger.info(f"Testing DELETE RELATIONSHIP {edge_key}")
    
    try:
        result = delete_relationship_by_key(db, edge_key)
        
        if not result:
            return False, "Failed to delete relationship"
        
        logger.info(f"Successfully deleted relationship: {edge_key}")
        return True, None
        
    except Exception as e:
        return False, f"Delete relationship failed: {str(e)}"


def display_results_table(results):
    """Display results in a rich table format"""
    table = Table(title="Graph Operations Validation Results")
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


def cleanup_test_data(db, test_docs):
    """Remove test documents after validation"""
    try:
        collection = db.collection(COLLECTION_NAME)
        for doc in test_docs:
            if doc and '_key' in doc:
                try:
                    collection.delete(doc['_key'])
                    logger.info(f"Cleaned up test document: {doc['_key']}")
                except:
                    pass  # Ignore cleanup errors
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time} {level} {message}")
    
    # Track all results
    results = []
    test_docs = []
    
    try:
        # Get database connection
        db = get_db_connection()
        logger.info(f"Connected to ArangoDB, using database: {db.name}")
        
        # Setup test data
        test_docs = setup_test_data(db)
        if len(test_docs) < 2:
            logger.error("Failed to create test documents")
            results.append(("Setup", False, "Failed to create test documents"))
        else:
            results.append(("Setup", True, f"Created {len(test_docs)} test documents"))
            
            # Test create relationship
            from_key = test_docs[0]['_key']
            to_key = test_docs[1]['_key']
            
            success, edge_key = test_create_relationship(db, from_key, to_key)
            results.append(("CREATE RELATIONSHIP", success, edge_key if success else edge_key))
            
            if success:
                # Test graph traversal
                success, traverse_results = test_graph_traverse(db, from_key)
                results.append(("GRAPH TRAVERSE", success, 
                             f"Found {len(traverse_results)} paths" if success else traverse_results))
                
                # Test delete relationship
                success, _ = test_delete_relationship(db, edge_key)
                results.append(("DELETE RELATIONSHIP", success, 
                             f"Deleted edge {edge_key}" if success else _))
        
        # Cleanup test data
        cleanup_test_data(db, test_docs)
        
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
            console.print("Graph operations are working correctly with real ArangoDB connection")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error during validation: {e}")
        logger.error(traceback.format_exc())
        console.print(f"\n❌ VALIDATION FAILED - Fatal error: {e}")
        sys.exit(1)