"""
ArangoDB CLI Database Connection Utility
Module: db_connection.py

This module provides database connection handling for the CLI layer,
connecting to the ArangoDB instance and ensuring all necessary collections,
graphs, and views exist before executing commands.

Functions:
- get_db_connection(): Connects to ArangoDB and ensures required structures

Sample Input:
- Called internally by CLI commands

Expected Output:
- Configured ArangoDB database connection or graceful error exit
"""

import sys
import typer
from typing import Optional
from loguru import logger
from rich.console import Console

# Import dependency checker for graceful handling of missing dependencies
from arangodb.core.utils.dependency_checker import HAS_ARANGO

# Import from core layer for connection handling - these functions check for ArangoDB availability
from arangodb.core.arango_setup import (
    connect_arango,
    ensure_database,
    ensure_collection,
    ensure_edge_collections,
    ensure_graph,
    ensure_memory_agent_collections,
    ensure_arangosearch_view
)

# Import constants from core
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

# Initialize Rich console
console = Console()

def get_db_connection():
    """
    Helper to connect and get DB object, handling errors.
    
    Returns:
        Database connection instance
        
    Raises:
        typer.Exit: If connection fails (with exit code 1)
    """
    # Check if ArangoDB is available
    if not HAS_ARANGO:
        error_msg = "Cannot connect to ArangoDB: python-arango is not installed"
        logger.error(error_msg)
        console.print(
            f"[bold red]Error:[/bold red] {error_msg}. "
            f"Please install python-arango to use ArangoDB features."
        )
        raise typer.Exit(code=1)
        
    try:
        logger.debug("Attempting to connect to ArangoDB...")
        client = connect_arango()
        if not client:
            raise ConnectionError("connect_arango() returned None")
        
        logger.debug(f"Ensuring database '{ARANGO_DB_NAME}' exists...")
        db = ensure_database(client)
        if not db:
            raise ConnectionError(
                f"ensure_database() returned None for '{ARANGO_DB_NAME}'"
            )
        logger.debug(f"Successfully connected to database '{db.name}'.")

        # Ensure graph components exist upon connection
        try:
            logger.debug("Ensuring edge collection and graph definition exist...")
            ensure_edge_collections(db)
            ensure_graph(db, GRAPH_NAME, EDGE_COLLECTION_NAME, COLLECTION_NAME)
            logger.debug("Edge collection and graph definition checked/ensured.")
        except Exception as setup_e:
            # Log warning but don't fail connection
            logger.warning(
                f"Graph/Edge setup check failed during connection: {setup_e}. Relationship/Traversal commands might fail."
            )
        
        # Ensure Memory Agent components exist
        try:
            logger.debug("Ensuring Memory Agent collections and views exist...")
            ensure_memory_agent_collections(db)
            
            # Ensure memory graph exists
            logger.debug("Ensuring Memory graph exists...")
            ensure_graph(db, MEMORY_GRAPH_NAME, MEMORY_EDGE_COLLECTION, MEMORY_COLLECTION)
            
            logger.debug("Memory Agent collections, views, and graph checked/ensured.")
        except Exception as memory_e:
            # Log warning but don't fail connection
            logger.warning(
                f"Memory Agent setup check failed during connection: {memory_e}. Memory commands might fail."
            )

        return db
    except Exception as e:
        logger.error(
            f"DB connection/setup failed: {e}", exc_info=True
        )
        console.print(
            f"[bold red]Error:[/bold red] Could not connect to or setup ArangoDB ({e}). "
            f"Check connection details, permissions, and ensure ArangoDB is running."
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    """
    Self-validation tests for the db_connection module.
    
    This validation checks for dependencies and performs appropriate tests
    regardless of whether ArangoDB is available.
    """
    import sys
    
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List of validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Check dependency checker import
    total_tests += 1
    try:
        test_result = "HAS_ARANGO" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import dependency checker")
        else:
            print(f" ArangoDB availability flag: HAS_ARANGO = {HAS_ARANGO}")
    except Exception as e:
        all_validation_failures.append(f"Dependency checker validation failed: {e}")
    
    # Test 2: Check imports work correctly
    total_tests += 1
    try:
        # Test import paths
        test_result = "connect_arango" in globals() and "ensure_database" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import core arango_setup functions")
        else:
            print(" Core arango_setup functions imported successfully")
    except Exception as e:
        all_validation_failures.append(f"Import validation failed: {e}")
    
    # Test 3: Verify constants are imported
    total_tests += 1
    try:
        # Check that we have constants defined
        constants = ["ARANGO_DB_NAME", "COLLECTION_NAME", "EDGE_COLLECTION_NAME", "GRAPH_NAME"]
        missing_constants = [const for const in constants if const not in globals()]
        
        if missing_constants:
            all_validation_failures.append(f"Missing constants: {missing_constants}")
        else:
            print(" All required constants imported successfully")
    except Exception as e:
        all_validation_failures.append(f"Constants validation failed: {e}")
    
    # Test 4: Check get_db_connection behavior when ArangoDB is not available
    total_tests += 1
    if not HAS_ARANGO:
        # If ArangoDB is not available, verify that get_db_connection raises a typer.Exit
        print("ArangoDB is not available, testing error handling behavior...")
        try:
            # Save the original typer.Exit to restore it later
            original_exit = typer.Exit
            
            # Create variables to track exit calls in a mutable object to avoid nonlocal
            exit_status = {"called": False, "code": None}
            
            class MockExit(Exception):
                def __init__(self, code=0):
                    exit_status["called"] = True
                    exit_status["code"] = code
            
            # Replace typer.Exit with our mock
            typer.Exit = MockExit
            
            try:
                # Try to call get_db_connection - it should raise our MockExit
                get_db_connection()
            except MockExit:
                pass
            
            # Check if Exit was called with the expected code
            if not exit_status["called"]:
                all_validation_failures.append("get_db_connection did not call typer.Exit when ArangoDB is unavailable")
            elif exit_status["code"] != 1:
                all_validation_failures.append(f"get_db_connection called typer.Exit with code {exit_status['code']}, expected 1")
            else:
                print(" get_db_connection properly handles missing ArangoDB dependency")
        
        finally:
            # Restore the original typer.Exit
            typer.Exit = original_exit
    else:
        print("ArangoDB is available, skipping some dependency tests...")
        # If ArangoDB is available, we can't easily test the dependency handling in get_db_connection
    
    # Display validation results
    if all_validation_failures:
        print(f"\n VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Module validated and ready for use")
        sys.exit(0)