"""
Validation script for DB Connection module with real ArangoDB connection

This script tests the database connection functionality to verify:
1. Connection to ArangoDB works
2. Database and collections are created properly
3. View setup completes successfully
4. Error handling works correctly
"""

import json
import sys
import os
from pathlib import Path
from loguru import logger
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the db connection
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.constants import (
    ARANGO_DB_NAME,
    COLLECTION_NAME,
    EDGE_COLLECTION_NAME,
    GRAPH_NAME,
    MEMORY_COLLECTION,
    MEMORY_EDGE_COLLECTION,
    MEMORY_GRAPH_NAME,
    MEMORY_VIEW_NAME
)

# For rich table display
from rich.console import Console
from rich.table import Table

console = Console()


def test_connection():
    """Test basic database connection"""
    logger.info("Testing database connection...")
    
    try:
        db = get_db_connection()
        
        if not db:
            return False, "get_db_connection returned None"
        
        # Check database name
        if db.name != ARANGO_DB_NAME:
            return False, f"Connected to wrong database: expected '{ARANGO_DB_NAME}', got '{db.name}'"
        
        logger.info(f"Successfully connected to database: {db.name}")
        return True, db
        
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def test_collections(db):
    """Test that required collections exist"""
    logger.info("Testing collection existence...")
    
    required_collections = [
        COLLECTION_NAME,
        EDGE_COLLECTION_NAME,
        MEMORY_COLLECTION,
        MEMORY_EDGE_COLLECTION
    ]
    
    missing_collections = []
    
    try:
        for collection_name in required_collections:
            if not db.has_collection(collection_name):
                missing_collections.append(collection_name)
        
        if missing_collections:
            return False, f"Missing collections: {missing_collections}"
        
        logger.info(f"All required collections exist: {required_collections}")
        return True, f"Found {len(required_collections)} collections"
        
    except Exception as e:
        return False, f"Collection check failed: {str(e)}"


def test_graph(db):
    """Test that graph structures exist"""
    logger.info("Testing graph existence...")
    
    required_graphs = [GRAPH_NAME, MEMORY_GRAPH_NAME]
    missing_graphs = []
    
    try:
        for graph_name in required_graphs:
            if not db.has_graph(graph_name):
                missing_graphs.append(graph_name)
        
        if missing_graphs:
            return False, f"Missing graphs: {missing_graphs}"
        
        logger.info(f"All required graphs exist: {required_graphs}")
        return True, f"Found {len(required_graphs)} graphs"
        
    except Exception as e:
        return False, f"Graph check failed: {str(e)}"


def test_view(db):
    """Test that ArangoSearch view exists"""
    logger.info("Testing ArangoSearch view...")
    
    try:
        views = db.views()
        view_names = [v['name'] for v in views]
        
        if MEMORY_VIEW_NAME not in view_names:
            return False, f"Missing view: {MEMORY_VIEW_NAME}"
        
        logger.info(f"Found ArangoSearch view: {MEMORY_VIEW_NAME}")
        return True, f"View {MEMORY_VIEW_NAME} exists"
        
    except Exception as e:
        return False, f"View check failed: {str(e)}"


def test_connection_retry():
    """Test multiple connection attempts"""
    logger.info("Testing connection reliability...")
    
    try:
        for i in range(3):
            logger.info(f"Connection attempt {i+1}/3")
            db = get_db_connection()
            
            if not db:
                return False, f"Connection attempt {i+1} failed"
        
        logger.info("All connection attempts successful")
        return True, "3/3 connections successful"
        
    except Exception as e:
        return False, f"Connection retry failed: {str(e)}"


def display_results_table(results):
    """Display results in a rich table format"""
    table = Table(title="DB Connection Validation Results")
    table.add_column("Test", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    for test_name, status, details in results:
        status_symbol = "✅" if status else "❌"
        table.add_row(test_name, status_symbol, str(details))
    
    console.print(table)


def display_results_json(results):
    """Display results in JSON format"""
    json_results = {
        "validation_results": [
            {
                "test": test_name,
                "status": "passed" if status else "failed",
                "details": str(details)
            }
            for test_name, status, details in results
        ],
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for _, status, _ in results if status),
            "failed": sum(1 for _, status, _ in results if not status)
        }
    }
    console.print(json.dumps(json_results, indent=2))


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time} {level} {message}")
    
    # Track all results
    results = []
    
    try:
        # Test 1: Basic connection
        success, result = test_connection()
        results.append(("Connection", success, result if not success else f"Connected to {ARANGO_DB_NAME}"))
        
        if not success:
            logger.error("Connection failed, skipping dependent tests")
        else:
            db = result
            
            # Test 2: Collections
            success, details = test_collections(db)
            results.append(("Collections", success, details))
            
            # Test 3: Graphs
            success, details = test_graph(db)
            results.append(("Graphs", success, details))
            
            # Test 4: Views
            success, details = test_view(db)
            results.append(("Views", success, details))
            
            # Test 5: Connection reliability
            success, details = test_connection_retry()
            results.append(("Reliability", success, details))
        
        # Display results in both formats
        console.print("\n[bold]Table Format:[/bold]")
        display_results_table(results)
        
        console.print("\n[bold]JSON Format:[/bold]")
        display_results_json(results)
        
        # Final result
        failures = [r for r in results if not r[1]]
        if failures:
            console.print(f"\n❌ VALIDATION FAILED - {len(failures)} of {len(results)} tests failed")
            for test_name, _, details in failures:
                console.print(f"  - {test_name}: {details}")
            sys.exit(1)
        else:
            console.print(f"\n✅ VALIDATION PASSED - All {len(results)} tests produced expected results")
            console.print("DB connection is working correctly with real ArangoDB")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error during validation: {e}")
        logger.error(traceback.format_exc())
        console.print(f"\n❌ VALIDATION FAILED - Fatal error: {e}")
        sys.exit(1)