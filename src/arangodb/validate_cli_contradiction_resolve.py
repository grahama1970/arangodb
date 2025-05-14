#!/usr/bin/env python3
"""
Validation script for the CLI contradiction resolution command.

This script tests the CLI command for resolving contradictions by:
1. Creating test documents and relationships with temporal contradictions
2. Executing the CLI command with different strategies 
3. Verifying that contradictions are properly detected and resolved

Usage:
    python -m arangodb.validate_cli_contradiction_resolve
"""

import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

# Import ArangoDB setup functions
try:
    # Try standalone package imports first
    from arangodb.arango_setup import connect_arango, ensure_database, ensure_edge_collections, ensure_graph
    from arangodb.config import COLLECTION_NAME, EDGE_COLLECTION_NAME, GRAPH_NAME
    from arangodb.db_operations import create_document, create_relationship, delete_document
    from arangodb.validate_contradiction_detection import setup_test_data, create_contradicting_relationships, cleanup_test_data
    from arangodb.cli_contradiction_resolve import resolve_contradictions_command
except ImportError:
    # Fall back to relative imports
    from src.arangodb.arango_setup import connect_arango, ensure_database, ensure_edge_collections, ensure_graph
    from src.arangodb.config import COLLECTION_NAME, EDGE_COLLECTION_NAME, GRAPH_NAME
    from src.arangodb.db_operations import create_document, create_relationship, delete_document
    from src.arangodb.validate_contradiction_detection import setup_test_data, create_contradicting_relationships, cleanup_test_data
    from src.arangodb.cli_contradiction_resolve import resolve_contradictions_command


def validate_cli_command(source_key: str, target_key: str):
    """
    Validate the CLI command function directly.
    
    Args:
        source_key: Key of the source document
        target_key: Key of the target document
        
    Returns:
        True if validation succeeds, False otherwise
    """
    try:
        # Connect to database
        client = connect_arango()
        db = ensure_database(client)
        
        # Test 1: Show only mode (no resolution)
        logger.info("Test 1: Show contradictions without resolving")
        
        result = resolve_contradictions_command(
            db=db,
            from_key=source_key,
            to_key=target_key,
            collection_name=COLLECTION_NAME,
            edge_collection=EDGE_COLLECTION_NAME,
            relationship_type="TEST_CONTRADICTION",
            strategy="newest_wins",
            show_only=True,
            yes=True,
            json_output=True
        )
        
        if not result or not isinstance(result, dict):
            logger.error("Test 1 failed: Command returned no result")
            return False
        
        if result.get("status") != "info":
            logger.error(f"Test 1 failed: Expected status 'info', got '{result.get('status')}'")
            return False
        
        edges = result.get("edges", [])
        if not edges or len(edges) < 2:
            logger.error(f"Test 1 failed: Expected at least 2 edges, got {len(edges)}")
            return False
            
        logger.info(f"Test 1 passed: Found {len(edges)} edges in show-only mode")
            
        # Test 2: Resolve with newest_wins strategy
        logger.info("Test 2: Resolve contradictions with newest_wins strategy")
        
        result = resolve_contradictions_command(
            db=db,
            from_key=source_key,
            to_key=target_key,
            collection_name=COLLECTION_NAME,
            edge_collection=EDGE_COLLECTION_NAME,
            relationship_type="TEST_CONTRADICTION",
            strategy="newest_wins",
            show_only=False,
            yes=True,
            json_output=True
        )
        
        if not result or not isinstance(result, dict):
            logger.error("Test 2 failed: Command returned no result")
            return False
        
        if result.get("status") != "success":
            logger.error(f"Test 2 failed: Expected status 'success', got '{result.get('status')}'")
            return False
        
        resolutions = result.get("resolutions", [])
        if not resolutions:
            logger.error("Test 2 failed: No resolutions performed")
            return False
        
        # Check if at least one resolution succeeded with the "newest_wins" action
        newest_wins_success = False
        for res in resolutions:
            if res.get("success") and res.get("action") in ["invalidate_old", "keep_old"]:
                newest_wins_success = True
                break
                
        if not newest_wins_success:
            logger.error("Test 2 failed: No successful resolutions with newest_wins strategy")
            return False
            
        logger.info(f"Test 2 passed: Successfully resolved contradictions with newest_wins strategy")
        
        # Test 3: Different relationship type (should find no contradictions)
        logger.info("Test 3: Check different relationship type")
        
        result = resolve_contradictions_command(
            db=db,
            from_key=source_key,
            to_key=target_key,
            collection_name=COLLECTION_NAME,
            edge_collection=EDGE_COLLECTION_NAME,
            relationship_type="DIFFERENT_TYPE",  # This type was created in create_contradicting_relationships
            strategy="newest_wins",
            show_only=True,
            yes=True,
            json_output=True
        )
        
        if not result or not isinstance(result, dict):
            logger.error("Test 3 failed: Command returned no result")
            return False
        
        edges = result.get("edges", [])
        if not edges or len(edges) != 1:  # Should find exactly one edge of this type
            logger.error(f"Test 3 failed: Expected 1 edge of type DIFFERENT_TYPE, got {len(edges)}")
            return False
            
        logger.info("Test 3 passed: Correctly found one edge of different type")
        
        # All tests passed
        return True
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        return False


def main():
    """Main validation function for the CLI contradiction resolution command."""
    # Initialize logger
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    # Track validation failures
    all_validation_failures = []
    total_tests = 1
    
    try:
        # Connect to database
        logger.info("Connecting to ArangoDB...")
        client = connect_arango()
        db = ensure_database(client)
        
        # Ensure collections and graph exist
        ensure_edge_collections(db)
        ensure_graph(db, GRAPH_NAME, EDGE_COLLECTION_NAME, COLLECTION_NAME)
        
        # Create test data
        logger.info("Setting up test data...")
        source_key, target_key = setup_test_data(db)
        
        # Create contradicting relationships
        logger.info("Creating contradicting relationships...")
        relationships = create_contradicting_relationships(db, source_key, target_key)
        
        if len(relationships) != 5:
            all_validation_failures.append(f"Failed to create all test relationships. Expected 5, got {len(relationships)}")
        
        # Validate the CLI command
        logger.info("Validating CLI contradiction resolution...")
        cli_success = validate_cli_command(source_key, target_key)
        
        if not cli_success:
            all_validation_failures.append("CLI contradiction resolution validation failed")
        
        # Clean up test data
        logger.info("Cleaning up test data...")
        cleanup_test_data(db, source_key, target_key)
        
        # Final validation result
        if all_validation_failures:
            logger.error(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                logger.error(f"  - {failure}")
            sys.exit(1)  # Exit with error code
        else:
            logger.info(f"✅ VALIDATION PASSED - All tests produced expected results")
            logger.info("CLI contradiction resolution command is validated")
            sys.exit(0)  # Exit with success code
            
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()