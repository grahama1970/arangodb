#!/usr/bin/env python3
"""
Validation script for arango_setup.py

This script tests the core database setup functionality with a real ArangoDB connection.
"""

import sys
import os
from loguru import logger

# Set up logger
logger.remove()
logger.add(sys.stderr, level="INFO")

def validate_arango_setup():
    """
    Validate arango_setup.py functionality with a real ArangoDB connection.
    """
    try:
        # Add the src directory to the path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
        
        # Import necessary modules directly using absolute imports
        from arangodb.core.constants import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME
        from arangodb.core.arango_setup import (
            connect_arango,
            ensure_database,
            ensure_collection,
            ensure_edge_collections,
            ensure_arangosearch_view,
            ensure_graph,
            ensure_vector_index
        )
        
        # Track validation failures
        all_validation_failures = []
        total_tests = 0
        
        # Test 1: Connect to ArangoDB
        total_tests += 1
        logger.info(f"Test 1: Connecting to ArangoDB at {ARANGO_HOST}")
        try:
            client = connect_arango()
            logger.info(f"✓ Successfully connected to ArangoDB at {ARANGO_HOST}")
        except Exception as e:
            all_validation_failures.append(f"Connection test failed: {str(e)}")
            client = None
        
        # Only proceed with further tests if connection succeeds
        if client:
            # Test 2: Ensure database
            total_tests += 1
            try:
                logger.info(f"Test 2: Ensuring database: {ARANGO_DB_NAME}")
                db = ensure_database(client)
                logger.info(f"✓ Successfully connected to database: {db.name}")
            except Exception as e:
                all_validation_failures.append(f"Database test failed: {str(e)}")
                db = None
            
            # Only proceed with collection/graph tests if database connection succeeds
            if db:
                # Test 3: Ensure test collection
                total_tests += 1
                try:
                    test_collection = "test_validation"
                    logger.info(f"Test 3: Creating test collection: {test_collection}")
                    ensure_collection(db, test_collection)
                    
                    if not db.has_collection(test_collection):
                        all_validation_failures.append(f"Collection test failed: Collection {test_collection} was not created")
                    else:
                        logger.info(f"✓ Successfully created collection: {test_collection}")
                except Exception as e:
                    all_validation_failures.append(f"Collection test failed: {str(e)}")
                
                # Test 4: Ensure edge collection
                total_tests += 1
                try:
                    test_edge_collection = "test_validation_edges"
                    logger.info(f"Test 4: Creating test edge collection: {test_edge_collection}")
                    ensure_collection(db, test_edge_collection, is_edge_collection=True)
                    
                    if not db.has_collection(test_edge_collection):
                        all_validation_failures.append(f"Edge collection test failed: Collection {test_edge_collection} was not created")
                    else:
                        # Verify it's an edge collection
                        collection = db.collection(test_edge_collection)
                        if not collection.properties()["edge"]:
                            all_validation_failures.append(f"Edge collection test failed: Collection {test_edge_collection} is not an edge collection")
                        else:
                            logger.info(f"✓ Successfully created edge collection: {test_edge_collection}")
                except Exception as e:
                    all_validation_failures.append(f"Edge collection test failed: {str(e)}")
                
                # Test 5: Ensure graph
                total_tests += 1
                try:
                    test_graph = "test_validation_graph"
                    logger.info(f"Test 5: Creating test graph: {test_graph}")
                    ensure_graph(db, test_graph, test_edge_collection, test_collection)
                    
                    if not db.has_graph(test_graph):
                        all_validation_failures.append(f"Graph test failed: Graph {test_graph} was not created")
                    else:
                        logger.info(f"✓ Successfully created graph: {test_graph}")
                except Exception as e:
                    all_validation_failures.append(f"Graph test failed: {str(e)}")
                
                # Test 6: Ensure ArangoSearch view
                total_tests += 1
                try:
                    test_view = "test_validation_view"
                    test_fields = ["name", "description", "tags"]
                    logger.info(f"Test 6: Creating test view: {test_view}")
                    ensure_arangosearch_view(db, test_view, test_collection, test_fields)
                    
                    if not db.has_view(test_view):
                        all_validation_failures.append(f"View test failed: View {test_view} was not created")
                    else:
                        logger.info(f"✓ Successfully created view: {test_view}")
                except Exception as e:
                    all_validation_failures.append(f"View test failed: {str(e)}")
                
                # Test 7: Ensure vector index
                total_tests += 1
                try:
                    test_field = "embedding"
                    logger.info(f"Test 7: Creating vector index on {test_collection}.{test_field}")
                    ensure_vector_index(db, test_collection, test_field, 128)
                    
                    # Check if index exists
                    collection = db.collection(test_collection)
                    indexes = collection.indexes()
                    index_exists = False
                    for index in indexes:
                        if index["type"] == "persistent" and test_field in index["fields"]:
                            index_exists = True
                            break
                    
                    if not index_exists:
                        all_validation_failures.append(f"Vector index test failed: Index on {test_field} was not created")
                    else:
                        logger.info(f"✓ Successfully created vector index on {test_collection}.{test_field}")
                except Exception as e:
                    all_validation_failures.append(f"Vector index test failed: {str(e)}")
                
                # Clean up test resources
                try:
                    logger.info("Cleaning up test resources...")
                    
                    # Delete graph first (to remove edge definitions)
                    if db.has_graph(test_graph):
                        db.delete_graph(test_graph)
                    
                    # Delete view
                    if db.has_view(test_view):
                        db.delete_view(test_view)
                    
                    # Delete collections
                    if db.has_collection(test_edge_collection):
                        db.delete_collection(test_edge_collection)
                    
                    if db.has_collection(test_collection):
                        db.delete_collection(test_collection)
                    
                    logger.info("✓ Test resources cleaned up successfully")
                except Exception as e:
                    logger.warning(f"Could not clean up all test resources: {e}")
        
        # Final validation result
        if all_validation_failures:
            logger.error(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                logger.error(f"  - {failure}")
            return False
        else:
            logger.info(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            logger.info("Core arango_setup module is validated and ready for use")
            return True
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Running arango_setup validation...")
    is_valid = validate_arango_setup()
    sys.exit(0 if is_valid else 1)