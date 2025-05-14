#!/usr/bin/env python3
"""
Validation script for contradiction detection and resolution in ArangoDB.

This script demonstrates how to use the contradiction detection and resolution
functionality in ArangoDB to identify and resolve conflicting relationships.

Key functionality demonstrated:
1. Creating relationships with temporal validity periods
2. Creating relationships that contradict existing ones
3. Detecting contradictions using temporal overlap
4. Resolving contradictions using different strategies
5. Validating the results of contradiction resolution

Usage:
    python -m arangodb.validate_contradiction_detection
"""

import sys
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

# Import ArangoDB setup functions
try:
    # Try standalone package imports first
    from arangodb.arango_setup import connect_arango, ensure_database, ensure_edge_collections, ensure_graph
    from arangodb.config import COLLECTION_NAME, EDGE_COLLECTION_NAME, GRAPH_NAME
    from arangodb.db_operations import create_document, create_relationship, delete_document
    from arangodb.contradiction_detection import (
        detect_contradicting_edges,
        detect_temporal_contradictions,
        resolve_contradiction,
        resolve_all_contradictions
    )
except ImportError:
    # Fall back to relative imports
    from src.arangodb.arango_setup import connect_arango, ensure_database, ensure_edge_collections, ensure_graph
    from src.arangodb.config import COLLECTION_NAME, EDGE_COLLECTION_NAME, GRAPH_NAME
    from src.arangodb.db_operations import create_document, create_relationship, delete_document
    from src.arangodb.contradiction_detection import (
        detect_contradicting_edges,
        detect_temporal_contradictions,
        resolve_contradiction,
        resolve_all_contradictions
    )

def setup_test_data(db) -> tuple:
    """
    Create test documents for contradiction detection validation.
    
    Args:
        db: ArangoDB database handle
        
    Returns:
        Tuple of (source_key, target_key)
    """
    # Create test documents
    source_doc = {
        "problem": "Source test document for contradiction detection",
        "solution": "This document is used to test contradiction detection",
        "context": "Testing scenario",
        "tags": ["test", "contradiction"]
    }
    
    target_doc = {
        "problem": "Target test document for contradiction detection",
        "solution": "This document is the target for contradiction tests",
        "context": "Testing scenario",
        "tags": ["test", "contradiction"]
    }
    
    source_result = create_document(db, COLLECTION_NAME, source_doc)
    target_result = create_document(db, COLLECTION_NAME, target_doc)
    
    logger.info(f"Created test documents with keys: {source_result['_key']}, {target_result['_key']}")
    
    return (source_result["_key"], target_result["_key"])


def create_contradicting_relationships(db, source_key: str, target_key: str) -> List[dict]:
    """
    Create a set of contradicting relationships for testing.
    
    Args:
        db: ArangoDB database handle
        source_key: Key of the source document
        target_key: Key of the target document
        
    Returns:
        List of created relationship metadata
    """
    # Define time periods for testing
    now = datetime.now(timezone.utc)
    past_1_month = now - timedelta(days=30)
    past_2_months = now - timedelta(days=60)
    past_3_months = now - timedelta(days=90)
    future_1_month = now + timedelta(days=30)
    
    # Create relationships with different temporal validity
    relationships = []
    
    # Relationship 1: Valid from 3 months ago until 2 months ago
    rel1 = create_relationship(
        db=db,
        from_doc_key=source_key,
        to_doc_key=target_key,
        relationship_type="TEST_CONTRADICTION",
        rationale="First test relationship with validity period in the past",
        attributes={"confidence": 0.7, "test_scenario": "past_validity"},
        reference_time=past_3_months.isoformat(),
        valid_until=past_2_months.isoformat()
    )
    relationships.append(rel1)
    logger.info(f"Created relationship 1 (past validity): {rel1['_key']}")
    
    # Relationship 2: Valid from 1 month ago until now
    rel2 = create_relationship(
        db=db,
        from_doc_key=source_key,
        to_doc_key=target_key,
        relationship_type="TEST_CONTRADICTION",
        rationale="Second test relationship with validity period until now",
        attributes={"confidence": 0.8, "test_scenario": "recent_validity"},
        reference_time=past_1_month.isoformat(),
        valid_until=now.isoformat()
    )
    relationships.append(rel2)
    logger.info(f"Created relationship 2 (recent validity): {rel2['_key']}")
    
    # Relationship 3: Valid from now onwards (no end date)
    rel3 = create_relationship(
        db=db,
        from_doc_key=source_key,
        to_doc_key=target_key,
        relationship_type="TEST_CONTRADICTION",
        rationale="Third test relationship with ongoing validity",
        attributes={"confidence": 0.9, "test_scenario": "current_validity"},
        reference_time=now.isoformat()
    )
    relationships.append(rel3)
    logger.info(f"Created relationship 3 (current validity): {rel3['_key']}")
    
    # Relationship 4: Will be valid in the future (contradicts relationship 3)
    rel4 = create_relationship(
        db=db,
        from_doc_key=source_key,
        to_doc_key=target_key,
        relationship_type="TEST_CONTRADICTION",
        rationale="Fourth test relationship with future validity",
        attributes={"confidence": 0.95, "test_scenario": "future_validity"},
        reference_time=now.isoformat(),
        valid_until=None  # No end date
    )
    relationships.append(rel4)
    logger.info(f"Created relationship 4 (future validity): {rel4['_key']}")
    
    # Relationship 5: Different relationship type (shouldn't contradict others)
    rel5 = create_relationship(
        db=db,
        from_doc_key=source_key,
        to_doc_key=target_key,
        relationship_type="DIFFERENT_TYPE",
        rationale="Fifth test relationship with different type",
        attributes={"confidence": 0.85, "test_scenario": "different_type"},
        reference_time=now.isoformat(),
        valid_until=future_1_month.isoformat()
    )
    relationships.append(rel5)
    logger.info(f"Created relationship 5 (different type): {rel5['_key']}")
    
    return relationships


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


def main():
    """Main validation function for contradiction detection and resolution."""
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
        
        # Create test data
        logger.info("Setting up test data...")
        source_key, target_key = setup_test_data(db)
        from_id = f"{COLLECTION_NAME}/{source_key}"
        to_id = f"{COLLECTION_NAME}/{target_key}"
        
        # Test 1: Create contradicting relationships
        total_tests += 1
        logger.info("Test 1: Creating contradicting relationships")
        
        try:
            relationships = create_contradicting_relationships(db, source_key, target_key)
            if len(relationships) != 5:
                all_validation_failures.append(f"Test 1: Failed to create all test relationships. Expected 5, got {len(relationships)}")
            else:
                logger.info("Successfully created all test relationships")
        except Exception as e:
            all_validation_failures.append(f"Test 1: Exception while creating relationships: {str(e)}")
        
        # Test 2: Detect contradictions by relationship type
        total_tests += 1
        logger.info("Test 2: Detecting contradictions by relationship type")
        
        try:
            # Detect contradictions for TEST_CONTRADICTION type
            contradictions = detect_contradicting_edges(
                db=db,
                edge_collection=EDGE_COLLECTION_NAME,
                from_id=from_id,
                to_id=to_id,
                relationship_type="TEST_CONTRADICTION"
            )
            
            # Should find 4 relationships of this type
            if len(contradictions) != 4:
                all_validation_failures.append(f"Test 2: Expected to find 4 'TEST_CONTRADICTION' relationships, found {len(contradictions)}")
            else:
                logger.info(f"Successfully detected 4 'TEST_CONTRADICTION' relationships")
                
            # Detect contradictions for DIFFERENT_TYPE
            different_type = detect_contradicting_edges(
                db=db,
                edge_collection=EDGE_COLLECTION_NAME,
                from_id=from_id,
                to_id=to_id,
                relationship_type="DIFFERENT_TYPE"
            )
            
            # Should find 1 relationship of this type
            if len(different_type) != 1:
                all_validation_failures.append(f"Test 2: Expected to find 1 'DIFFERENT_TYPE' relationship, found {len(different_type)}")
            else:
                logger.info(f"Successfully detected 1 'DIFFERENT_TYPE' relationship")
                
        except Exception as e:
            all_validation_failures.append(f"Test 2: Exception while detecting contradictions: {str(e)}")
        
        # Test 3: Detect temporal contradictions
        total_tests += 1
        logger.info("Test 3: Detecting temporal contradictions")
        
        try:
            # Get the most recent relationship
            aql = f"""
            FOR e IN {EDGE_COLLECTION_NAME}
            FILTER e._from == @from_id AND e._to == @to_id
            FILTER e.type == "TEST_CONTRADICTION"
            SORT e.created_at DESC
            LIMIT 1
            RETURN e
            """
            
            cursor = db.aql.execute(
                aql,
                bind_vars={
                    "from_id": from_id,
                    "to_id": to_id
                }
            )
            
            latest_edge = list(cursor)[0]
            
            # This should contradict relationship 3 (current validity)
            temporal_contradictions = detect_temporal_contradictions(
                db=db,
                edge_collection=EDGE_COLLECTION_NAME,
                edge_doc=latest_edge
            )
            
            # Should find at least one contradiction
            if len(temporal_contradictions) < 1:
                all_validation_failures.append(f"Test 3: Expected to find at least 1 temporal contradiction, found {len(temporal_contradictions)}")
            else:
                logger.info(f"Successfully detected {len(temporal_contradictions)} temporal contradiction(s)")
                
        except Exception as e:
            all_validation_failures.append(f"Test 3: Exception while detecting temporal contradictions: {str(e)}")
        
        # Test 4: Resolve contradictions with "newest_wins" strategy
        total_tests += 1
        logger.info("Test 4: Resolving contradictions with 'newest_wins' strategy")
        
        try:
            # Get a pair of contradicting edges
            if len(temporal_contradictions) > 0:
                # Use the latest edge and the first contradicting edge
                resolution = resolve_contradiction(
                    db=db,
                    edge_collection=EDGE_COLLECTION_NAME,
                    new_edge=latest_edge,
                    contradicting_edge=temporal_contradictions[0],
                    strategy="newest_wins"
                )
                
                if not resolution["success"]:
                    all_validation_failures.append(f"Test 4: Failed to resolve contradiction with 'newest_wins' strategy: {resolution['reason']}")
                else:
                    logger.info(f"Successfully resolved contradiction with 'newest_wins' strategy: {resolution['action']}")
                    
                    # Verify that the old edge was invalidated
                    old_edge = db.collection(EDGE_COLLECTION_NAME).get(temporal_contradictions[0]["_key"])
                    if old_edge.get("invalid_at") is None:
                        all_validation_failures.append("Test 4: Old edge was not properly invalidated")
                    else:
                        logger.info(f"Verified old edge was invalidated at: {old_edge['invalid_at']}")
            else:
                all_validation_failures.append("Test 4: No temporal contradictions found to resolve")
                
        except Exception as e:
            all_validation_failures.append(f"Test 4: Exception while resolving contradictions: {str(e)}")
        
        # Test 5: Resolve all contradictions
        total_tests += 1
        logger.info("Test 5: Resolving all contradictions")
        
        try:
            # Create a new contradicting edge
            now = datetime.now(timezone.utc)
            new_edge = {
                "_from": from_id,
                "_to": to_id,
                "type": "TEST_CONTRADICTION",
                "rationale": "New contradicting edge for Test 5",
                "attributes": {"confidence": 1.0, "test_scenario": "resolve_all"},
                "created_at": now.isoformat(),
                "valid_at": now.isoformat(),
                "invalid_at": None
            }
            
            # Insert the edge
            new_edge_result = db.collection(EDGE_COLLECTION_NAME).insert(new_edge)
            new_edge["_key"] = new_edge_result["_key"]
            
            # Resolve all contradictions
            resolutions, success = resolve_all_contradictions(
                db=db,
                edge_collection=EDGE_COLLECTION_NAME,
                edge_doc=new_edge,
                strategy="newest_wins"
            )
            
            if not success:
                all_validation_failures.append(f"Test 5: Failed to resolve all contradictions")
            else:
                logger.info(f"Successfully resolved {len(resolutions)} contradictions")
                
                # Verify that the contradicting edges were invalidated
                for resolution in resolutions:
                    if resolution["success"] and resolution["action"] == "invalidate_old":
                        resolved_edge = resolution["resolved_edge"]
                        if resolved_edge and resolved_edge.get("invalid_at") is not None:
                            logger.info(f"Verified edge {resolved_edge['_key']} was invalidated")
                        else:
                            all_validation_failures.append(f"Test 5: Edge {resolved_edge['_key']} was not properly invalidated")
                
        except Exception as e:
            all_validation_failures.append(f"Test 5: Exception while resolving all contradictions: {str(e)}")
        
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
            logger.info("Contradiction detection and resolution functionality is validated")
            sys.exit(0)  # Exit with success code
            
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()