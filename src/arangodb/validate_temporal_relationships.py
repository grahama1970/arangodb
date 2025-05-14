#!/usr/bin/env python3
"""
Validation script for temporal relationship features in ArangoDB integration.

This script demonstrates the use of temporal metadata for relationships in the ArangoDB
integration, including:

1. Creating relationships with temporal validity periods
2. Checking for and resolving contradictions
3. Searching for relationships valid at specific points in time

Usage:
    python -m arangodb.validate_temporal_relationships
"""

import sys
import json
from datetime import datetime, timezone, timedelta
from loguru import logger
from typing import List, Dict, Any, Optional

# Import ArangoDB setup functions
try:
    # Try standalone package imports first
    from arangodb.arango_setup import connect_arango, ensure_database, ensure_edge_collections, ensure_graph
except ImportError:
    # Fall back to relative imports
    from src.arangodb.arango_setup import connect_arango, ensure_database, ensure_edge_collections, ensure_graph

# Import database operations
try:
    # Try standalone package imports first
    from arangodb.db_operations import create_document, create_relationship, delete_document
    from arangodb.enhanced_relationships import (
        enhance_edge_with_temporal_metadata,
        validate_temporal_metadata,
        is_temporal_edge_valid,
        invalidate_edge,
        find_contradicting_edges,
        search_temporal_relationships
    )
    from arangodb.config import COLLECTION_NAME, EDGE_COLLECTION_NAME, GRAPH_NAME
except ImportError:
    # Fall back to relative imports
    from src.arangodb.db_operations import create_document, create_relationship, delete_document
    from src.arangodb.enhanced_relationships import (
        enhance_edge_with_temporal_metadata,
        validate_temporal_metadata,
        is_temporal_edge_valid,
        invalidate_edge,
        find_contradicting_edges,
        search_temporal_relationships
    )
    from src.arangodb.config import COLLECTION_NAME, EDGE_COLLECTION_NAME, GRAPH_NAME


def setup_test_data(db) -> tuple:
    """
    Create test documents for temporal relationship validation.
    
    Args:
        db: ArangoDB database handle
        
    Returns:
        Tuple of (source_key, target_key)
    """
    # Create test documents
    source_doc = {
        "problem": "Source test document for temporal relationships",
        "solution": "This document is used to test temporal relationship features",
        "context": "Testing scenario",
        "tags": ["test", "temporal"]
    }
    
    target_doc = {
        "problem": "Target test document for temporal relationships",
        "solution": "This document is the target for temporal relationship tests",
        "context": "Testing scenario",
        "tags": ["test", "temporal"]
    }
    
    source_result = create_document(db, COLLECTION_NAME, source_doc)
    target_result = create_document(db, COLLECTION_NAME, target_doc)
    
    return (source_result["_key"], target_result["_key"])


def cleanup_test_data(db, source_key: str, target_key: str):
    """
    Remove test documents and their relationships.
    
    Args:
        db: ArangoDB database handle
        source_key: Key of the source document
        target_key: Key of the target document
    """
    try:
        # Delete relationships first
        aql = f"""
        FOR e IN {EDGE_COLLECTION_NAME}
        FILTER e._from == @from_id OR e._to == @to_id
        REMOVE e IN {EDGE_COLLECTION_NAME}
        """
        
        db.aql.execute(
            aql,
            bind_vars={
                "from_id": f"{COLLECTION_NAME}/{source_key}",
                "to_id": f"{COLLECTION_NAME}/{target_key}"
            }
        )
        
        # Delete documents
        delete_document(db, COLLECTION_NAME, source_key)
        delete_document(db, COLLECTION_NAME, target_key)
        
        logger.info(f"Cleaned up test documents and relationships")
        
    except Exception as e:
        logger.error(f"Failed to clean up test data: {e}")


if __name__ == "__main__":
    # Initialize logger
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    try:
        # Connect to database
        logger.info("Connecting to ArangoDB...")
        client = connect_arango()
        db = ensure_database(client)
        
        # Ensure collections and graph exist
        ensure_edge_collections(db)
        ensure_graph(db, GRAPH_NAME, EDGE_COLLECTION_NAME, COLLECTION_NAME)
        
        logger.info(f"Setting up test data in {COLLECTION_NAME} and {EDGE_COLLECTION_NAME}...")
        source_key, target_key = setup_test_data(db)
        
        # Test 1: Create relationship with default temporal metadata
        total_tests += 1
        logger.info("Test 1: Creating relationship with default temporal metadata")
        
        rel_default = create_relationship(
            db=db,
            from_doc_key=source_key,
            to_doc_key=target_key,
            relationship_type="DEFAULT_TEMPORAL",
            rationale="Testing default temporal metadata",
            attributes={"test_case": "default_temporal"}
        )
        
        if not rel_default or "created_at" not in rel_default or "valid_at" not in rel_default:
            all_validation_failures.append("Test 1: Failed to create relationship with default temporal metadata")
        else:
            logger.info(f"Created relationship with default temporal metadata: {rel_default['_key']}")
        
        # Test 2: Create relationship with custom temporal metadata
        total_tests += 1
        logger.info("Test 2: Creating relationship with custom temporal metadata")
        
        # Create a relationship that became valid in the past and is still valid
        past_time = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        rel_custom = create_relationship(
            db=db,
            from_doc_key=source_key,
            to_doc_key=target_key,
            relationship_type="CUSTOM_TEMPORAL",
            rationale="Testing custom temporal metadata",
            attributes={"test_case": "custom_temporal"},
            reference_time=past_time,
            valid_until=None  # Still valid
        )
        
        if not rel_custom or rel_custom.get("valid_at") != past_time:
            all_validation_failures.append("Test 2: Failed to create relationship with custom temporal metadata")
        else:
            logger.info(f"Created relationship with custom temporal metadata: {rel_custom['_key']}")
        
        # Test 3: Create relationship with limited validity period
        total_tests += 1
        logger.info("Test 3: Creating relationship with limited validity period")
        
        # Create a relationship that was valid for a specific period
        start_time = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        end_time = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        rel_limited = create_relationship(
            db=db,
            from_doc_key=source_key,
            to_doc_key=target_key,
            relationship_type="LIMITED_TEMPORAL",
            rationale="Testing limited validity period",
            attributes={"test_case": "limited_temporal"},
            reference_time=start_time,
            valid_until=end_time
        )
        
        if not rel_limited or rel_limited.get("valid_at") != start_time or rel_limited.get("invalid_at") != end_time:
            all_validation_failures.append("Test 3: Failed to create relationship with limited validity period")
        else:
            logger.info(f"Created relationship with limited validity period: {rel_limited['_key']}")
        
        # Test 4: Check for contradictions
        total_tests += 1
        logger.info("Test 4: Creating contradicting relationship with automatic resolution")
        
        # Create a relationship that contradicts the one with default temporal metadata
        rel_contradicting = create_relationship(
            db=db,
            from_doc_key=source_key,
            to_doc_key=target_key,
            relationship_type="DEFAULT_TEMPORAL",  # Same type as the first one
            rationale="This contradicts the first relationship",
            attributes={"test_case": "contradiction"},
            check_contradictions=True  # Enable contradiction checking
        )
        
        # Query both relationships
        aql = f"""
        FOR e IN {EDGE_COLLECTION_NAME}
        FILTER e._from == @from_id AND e._to == @to_id AND e.type == 'DEFAULT_TEMPORAL'
        RETURN e
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                "from_id": f"{COLLECTION_NAME}/{source_key}",
                "to_id": f"{COLLECTION_NAME}/{target_key}"
            }
        )
        
        edges = list(cursor)
        valid_edges = [e for e in edges if e.get("invalid_at") is None]
        invalid_edges = [e for e in edges if e.get("invalid_at") is not None]
        
        if len(valid_edges) != 1 or len(invalid_edges) != 1:
            all_validation_failures.append(f"Test 4: Contradiction resolution failed, found {len(valid_edges)} valid and {len(invalid_edges)} invalid edges")
        else:
            logger.info(f"Successfully resolved contradiction: invalidated {invalid_edges[0]['_key']}, kept {valid_edges[0]['_key']}")
        
        # Test 5: Search for relationships valid at specific time
        total_tests += 1
        logger.info("Test 5: Searching for relationships valid at specific time")
        
        # Search for relationships valid 45 days ago
        point_in_time = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        
        results = search_temporal_relationships(
            db=db,
            edge_collection=EDGE_COLLECTION_NAME,
            point_in_time=point_in_time,
            from_id=f"{COLLECTION_NAME}/{source_key}",
            to_id=f"{COLLECTION_NAME}/{target_key}"
        )
        
        if not results:
            all_validation_failures.append("Test 5: Failed to find relationships valid at specified time")
        else:
            # We expect to find the CUSTOM_TEMPORAL relationship and the LIMITED_TEMPORAL one
            found_types = [r.get("type") for r in results]
            if "CUSTOM_TEMPORAL" not in found_types or "LIMITED_TEMPORAL" not in found_types:
                all_validation_failures.append(f"Test 5: Expected to find CUSTOM_TEMPORAL and LIMITED_TEMPORAL relationships, found: {found_types}")
            else:
                logger.info(f"Successfully found relationships valid at {point_in_time}: {found_types}")
        
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
            logger.info(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            logger.info("Temporal relationship enhancements are working correctly")
            sys.exit(0)  # Exit with success code
            
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        sys.exit(1)