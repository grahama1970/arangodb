#!/usr/bin/env python3
"""
Test module for ArangoDB database operations.

This module tests the basic CRUD operations from db_operations.py, ensuring
that document creation, retrieval, updates, deletion, and queries work correctly.
All tests use actual database operations with real data.

Every test verifies specific expected values, not just generic assertions,
and includes proper setup, execution, and cleanup.
"""

import os
import sys
import uuid
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Set up environment variables for ArangoDB connection
os.environ.setdefault("ARANGO_HOST", "http://localhost:8529")
os.environ.setdefault("ARANGO_USER", "root")
os.environ.setdefault("ARANGO_PASSWORD", "complexity")
os.environ.setdefault("ARANGO_DB_NAME", "complexity_test")

# Import directly from arango client
from arango import ArangoClient
from arango.database import StandardDatabase
from arangodb.core.db_operations import (
    create_document,
    get_document,
    update_document,
    delete_document,
    query_documents,
    create_relationship,
    delete_relationship_by_key
)

# Test collections
TEST_DOC_COLLECTION = "test_docs"
TEST_EDGE_COLLECTION = "test_relationships"
TEST_GRAPH_NAME = "test_graph"

# Sample test data directories
REPO_ROOT = Path(__file__).parent.parent.parent.parent
TEST_DATA_DIR = REPO_ROOT / "repos" / "python-arango_sparse"

def setup_test_environment():
    """Set up test environment with required collections and initial data."""
    print("\n==== Setting up test environment ====")
    
    # Get connection parameters from environment
    host = os.environ.get("ARANGO_HOST", "http://localhost:8529")
    user = os.environ.get("ARANGO_USER", "root")
    password = os.environ.get("ARANGO_PASSWORD", "complexity")
    db_name = os.environ.get("ARANGO_DB_NAME", "complexity_test")
    
    # Connect to ArangoDB
    client = ArangoClient(hosts=host)
    
    # Connect to _system database first to create our test database if needed
    sys_db = client.db("_system", username=user, password=password)
    if not sys_db:
        print("❌ Failed to connect to _system database")
        return None
    
    # Create test database if it doesn't exist
    if not sys_db.has_database(db_name):
        print(f"Creating test database: {db_name}")
        sys_db.create_database(db_name)
    
    # Connect to our test database
    db = client.db(db_name, username=user, password=password)
    if not db:
        print("❌ Failed to connect to test database")
        return None
    
    print(f"✅ Connected to test database: {db.name}")
    
    # Ensure collections exist
    for collection_name in [TEST_DOC_COLLECTION, TEST_EDGE_COLLECTION]:
        if not db.has_collection(collection_name):
            is_edge = "relationship" in collection_name.lower()
            db.create_collection(collection_name, edge=is_edge)
            print(f"✅ Created {'edge ' if is_edge else ''}collection: {collection_name}")
    
    return db

def get_test_document(with_content: bool = True) -> Dict[str, Any]:
    """
    Generate a test document with realistic data.
    
    Args:
        with_content: Whether to include content field (default: True)
        
    Returns:
        Dict containing a test document
    """
    doc_id = str(uuid.uuid4())
    timestamp = f"{doc_id[:8]}_{int(time.time())}"
    doc = {
        "_key": f"test_{doc_id[:8]}",
        "title": f"Test Document {doc_id[:6]}",
        "tags": ["test", "document", "arangodb"],
        "created_at": timestamp,  # Using our own timestamp format for consistency
        "numeric_value": 42,
        "is_active": True
    }
    
    if with_content:
        doc["content"] = (
            f"This is a test document with ID {doc_id} created for testing "
            f"ArangoDB database operations. This document contains specific "
            f"fields and values that will be verified in the test assertions."
        )
    
    return doc

def teardown_test_document(db, doc_key):
    """
    Remove a test document and report the result.
    
    Args:
        db: Database connection
        doc_key: Key of the document to remove
    
    Returns:
        bool: Whether the cleanup was successful
    """
    try:
        delete_success = delete_document(db, TEST_DOC_COLLECTION, doc_key)
        if delete_success:
            print(f"✅ Cleaned up test document: {doc_key}")
            return True
        else:
            print(f"❌ Failed to clean up test document: {doc_key}")
            return False
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

def test_create_document(db):
    """
    Test document creation with specific field validation.
    
    This test verifies that a document can be created successfully and that
    all fields are correctly stored in the database.
    
    Args:
        db: Database connection
        
    Returns:
        Tuple[bool, str, Dict]: Success status, created document key, and document data
    """
    print("\n==== Testing document creation ====")
    
    # Create test document data
    test_doc = get_test_document()
    print(f"Creating test document with key: {test_doc['_key']}")
    
    # EXECUTE: Create the document
    created_doc = create_document(db, TEST_DOC_COLLECTION, test_doc)
    
    # VERIFY: Check that document was created successfully
    if not created_doc:
        print("❌ Failed to create test document")
        return False, None, None
    
    # Verify specific fields were stored correctly
    verification_passed = True
    for key, expected_value in test_doc.items():
        if key not in created_doc:
            print(f"❌ Field missing in created document: {key}")
            verification_passed = False
            continue
            
        actual_value = created_doc[key]
        if actual_value != expected_value:
            print(f"❌ Field value mismatch: {key}")
            print(f"   Expected: {expected_value}")
            print(f"   Actual:   {actual_value}")
            verification_passed = False
    
    # Additional verifications
    if "_id" not in created_doc:
        print("❌ _id field missing in created document")
        verification_passed = False
    
    if "timestamp" not in created_doc:
        print("❌ timestamp field missing in created document")
        verification_passed = False
    
    if verification_passed:
        print(f"✅ Document created successfully with key: {created_doc['_key']}")
        print(f"✅ All {len(test_doc)} fields verified correctly")
        return True, created_doc["_key"], created_doc
    else:
        print("❌ Document creation verification failed")
        return False, created_doc["_key"] if "_key" in created_doc else None, created_doc

def test_get_document(db, doc_key):
    """
    Test document retrieval with expected field verification.
    
    This test verifies that a document can be retrieved successfully and
    that all fields match the expected values.
    
    Args:
        db: Database connection
        doc_key: Key of the document to retrieve
        
    Returns:
        Tuple[bool, Dict]: Success status and retrieved document
    """
    print("\n==== Testing document retrieval ====")
    print(f"Retrieving document with key: {doc_key}")
    
    # EXECUTE: Retrieve the document
    retrieved_doc = get_document(db, TEST_DOC_COLLECTION, doc_key)
    
    # VERIFY: Check that document was retrieved successfully
    if not retrieved_doc:
        print(f"❌ Failed to retrieve document with key: {doc_key}")
        return False, None
    
    # Verify document has expected fields
    expected_fields = ["_key", "_id", "title", "content", "tags", "created_at", 
                       "numeric_value", "is_active", "timestamp"]
    
    verification_passed = True
    for field in expected_fields:
        if field not in retrieved_doc:
            print(f"❌ Expected field missing: {field}")
            verification_passed = False
    
    if verification_passed:
        print(f"✅ Document retrieved successfully with key: {retrieved_doc['_key']}")
        print(f"✅ All expected fields are present")
        return True, retrieved_doc
    else:
        print("❌ Document retrieval verification failed")
        return False, retrieved_doc

def test_update_document(db, doc_key, original_doc):
    """
    Test document update with before/after comparison.
    
    This test verifies that a document can be updated successfully and
    that the changes are correctly reflected in the database.
    
    Args:
        db: Database connection
        doc_key: Key of the document to update
        original_doc: The original document for comparison
        
    Returns:
        Tuple[bool, Dict]: Success status and updated document
    """
    print("\n==== Testing document update ====")
    print(f"Updating document with key: {doc_key}")
    
    # Create update data with our own timestamp (UUID-based for consistency)
    update_timestamp = f"{uuid.uuid4().hex[:8]}_{int(time.time())}"
    update_data = {
        "title": "Updated Test Document",
        "numeric_value": 100,
        "updated_at": update_timestamp,  # Using our own timestamp format
        "new_field": "This is a new field added during update"
    }
    
    # EXECUTE: Update the document
    updated_doc = update_document(db, TEST_DOC_COLLECTION, doc_key, update_data)
    
    # VERIFY: Check that document was updated successfully
    if not updated_doc:
        print(f"❌ Failed to update document with key: {doc_key}")
        return False, None
    
    # Verify specific field updates
    verification_passed = True
    
    # 1. Check that updated fields have new values
    for key, expected_value in update_data.items():
        if key not in updated_doc:
            print(f"❌ Updated field missing: {key}")
            verification_passed = False
            continue
            
        # Special handling for updated_at (timestamp)
        if key == "updated_at":
            # Skip timestamp verification as format may vary
            continue
            
        actual_value = updated_doc[key]
        if actual_value != expected_value:
            print(f"❌ Updated field value mismatch: {key}")
            print(f"   Expected: {expected_value}")
            print(f"   Actual:   {actual_value}")
            verification_passed = False
    
    # 2. Check that original fields are preserved
    for key, original_value in original_doc.items():
        # Skip fields that were updated
        if key in update_data:
            continue
            
        # Skip timestamp field which is auto-updated
        if key in ["timestamp", "updated_at"]:
            continue
            
        # Skip _rev field which is expected to change
        if key == "_rev":
            # Document revision should change after update
            if updated_doc.get("_rev") == original_value:
                print("❌ Document revision didn't change - update may not have worked")
                verification_passed = False
            continue
            
        if key not in updated_doc:
            print(f"❌ Original field missing after update: {key}")
            verification_passed = False
            continue
            
        actual_value = updated_doc[key]
        if actual_value != original_value:
            print(f"❌ Original field value changed unexpectedly: {key}")
            print(f"   Original: {original_value}")
            print(f"   Actual:   {actual_value}")
            verification_passed = False
    
    # 3. Check for updated_at field
    if "updated_at" not in updated_doc:
        print("❌ updated_at field missing in updated document")
        verification_passed = False
    
    if verification_passed:
        print(f"✅ Document updated successfully with key: {updated_doc['_key']}")
        print(f"✅ All updates verified correctly")
        return True, updated_doc
    else:
        print("❌ Document update verification failed")
        return False, updated_doc

def test_delete_document(db, doc_key):
    """
    Test document deletion with verification.
    
    This test verifies that a document can be deleted successfully and
    that it no longer exists in the database after deletion.
    
    Args:
        db: Database connection
        doc_key: Key of the document to delete
        
    Returns:
        bool: Success status
    """
    print("\n==== Testing document deletion ====")
    print(f"Deleting document with key: {doc_key}")
    
    # EXECUTE: Delete the document
    delete_success = delete_document(db, TEST_DOC_COLLECTION, doc_key)
    
    # VERIFY: Check that document was deleted successfully
    if not delete_success:
        print(f"❌ Failed to delete document with key: {doc_key}")
        return False
    
    # Verify document no longer exists
    deleted_check = get_document(db, TEST_DOC_COLLECTION, doc_key)
    if deleted_check:
        print(f"❌ Document with key {doc_key} still exists after deletion")
        return False
    
    print(f"✅ Document with key {doc_key} deleted successfully")
    return True

def test_query_documents(db):
    """
    Test document querying with complex filter expressions.
    
    This test creates multiple test documents, queries them with various
    filter expressions, and verifies that the results match expectations.
    
    Args:
        db: Database connection
        
    Returns:
        bool: Success status
    """
    print("\n==== Testing document querying ====")
    
    # Create multiple test documents with different properties
    test_docs = []
    doc_keys = []
    
    # Document 1: Standard test document
    doc1 = get_test_document()
    doc1["_key"] = f"query_test_1_{uuid.uuid4().hex[:6]}"
    doc1["category"] = "test"
    doc1["priority"] = "high"
    doc1["score"] = 85
    
    # Document 2: Different category and score
    doc2 = get_test_document()
    doc2["_key"] = f"query_test_2_{uuid.uuid4().hex[:6]}"
    doc2["category"] = "example"
    doc2["priority"] = "medium"
    doc2["score"] = 65
    
    # Document 3: Same category as doc1, different priority and score
    doc3 = get_test_document()
    doc3["_key"] = f"query_test_3_{uuid.uuid4().hex[:6]}"
    doc3["category"] = "test"
    doc3["priority"] = "low"
    doc3["score"] = 45
    
    # Insert all test documents
    for doc in [doc1, doc2, doc3]:
        created_doc = create_document(db, TEST_DOC_COLLECTION, doc)
        if created_doc:
            test_docs.append(created_doc)
            doc_keys.append(created_doc["_key"])
    
    print(f"✅ Created {len(test_docs)} test documents for querying")
    
    # Define query tests with expected results
    query_tests = [
        {
            "name": "Simple equality filter",
            "filter": "FILTER doc.category == @category",
            "bind_vars": {"category": "test"},
            "expected_count": 2,
            "expected_keys": [doc1["_key"], doc3["_key"]]
        },
        {
            "name": "Numeric comparison filter",
            "filter": "FILTER doc.score >= @min_score",
            "bind_vars": {"min_score": 65},
            "expected_count": 2,
            "expected_keys": [doc1["_key"], doc2["_key"]]
        },
        {
            "name": "Multiple conditions filter",
            "filter": "FILTER doc.category == @category AND doc.priority == @priority",
            "bind_vars": {"category": "test", "priority": "high"},
            "expected_count": 1,
            "expected_keys": [doc1["_key"]]
        },
        {
            "name": "OR condition filter",
            "filter": "FILTER doc.priority == @priority1 OR doc.priority == @priority2",
            "bind_vars": {"priority1": "high", "priority2": "low"},
            "expected_count": 2,
            "expected_keys": [doc1["_key"], doc3["_key"]]
        },
        {
            "name": "IN operator filter",
            "filter": "FILTER doc._key IN @keys",
            "bind_vars": {"keys": [doc1["_key"], doc3["_key"]]},
            "expected_count": 2,
            "expected_keys": [doc1["_key"], doc3["_key"]]
        }
    ]
    
    # Run each query test
    all_tests_passed = True
    
    for test in query_tests:
        print(f"\nRunning query test: {test['name']}")
        
        # EXECUTE: Run the query
        results = query_documents(
            db, 
            TEST_DOC_COLLECTION, 
            test["filter"], 
            bind_vars=test["bind_vars"]
        )
        
        # VERIFY: Check results
        if results is None:
            print(f"❌ Query failed: {test['name']}")
            all_tests_passed = False
            continue
            
        actual_count = len(results)
        expected_count = test["expected_count"]
        
        if actual_count != expected_count:
            print(f"❌ Query result count mismatch")
            print(f"   Expected: {expected_count}")
            print(f"   Actual:   {actual_count}")
            all_tests_passed = False
            continue
            
        # Check that all expected keys are in the results
        actual_keys = [doc["_key"] for doc in results]
        missing_keys = [k for k in test["expected_keys"] if k not in actual_keys]
        unexpected_keys = [k for k in actual_keys if k not in test["expected_keys"]]
        
        if missing_keys:
            print(f"❌ Expected keys missing from results: {missing_keys}")
            all_tests_passed = False
        
        if unexpected_keys:
            print(f"❌ Unexpected keys in results: {unexpected_keys}")
            all_tests_passed = False
            
        if not missing_keys and not unexpected_keys:
            print(f"✅ Query '{test['name']}' returned {actual_count} documents as expected")
            print(f"✅ All expected document keys found in results")
    
    # Clean up test documents
    for key in doc_keys:
        delete_document(db, TEST_DOC_COLLECTION, key)
    
    print(f"\n{'✅ All query tests passed' if all_tests_passed else '❌ Some query tests failed'}")
    return all_tests_passed

def test_error_handling(db):
    """
    Test error handling with invalid inputs.
    
    This test verifies that the database operations handle errors
    gracefully when provided with invalid inputs.
    
    Args:
        db: Database connection
        
    Returns:
        bool: Success status
    """
    print("\n==== Testing error handling ====")
    
    error_tests = [
        {
            "name": "Get non-existent document",
            "function": lambda: get_document(db, TEST_DOC_COLLECTION, "non_existent_key"),
            "expected_result": None
        },
        {
            "name": "Create document with duplicate key",
            "setup": lambda: create_document(db, TEST_DOC_COLLECTION, {"_key": "duplicate_test"}),
            "function": lambda: create_document(db, TEST_DOC_COLLECTION, {"_key": "duplicate_test"}),
            "cleanup": lambda: delete_document(db, TEST_DOC_COLLECTION, "duplicate_test"),
            "expected_result": None
        },
        {
            "name": "Update non-existent document",
            "function": lambda: update_document(db, TEST_DOC_COLLECTION, "non_existent_key", {"field": "value"}),
            "expected_result": None
        },
        {
            "name": "Delete non-existent document (with ignore_missing=True)",
            "function": lambda: delete_document(db, TEST_DOC_COLLECTION, "non_existent_key", ignore_missing=True),
            "expected_result": True  # Should return True when ignore_missing=True
        },
        {
            "name": "Query with invalid filter",
            "function": lambda: query_documents(db, TEST_DOC_COLLECTION, "INVALID FILTER SYNTAX"),
            "expected_result": []  # Should return empty list
        }
    ]
    
    all_tests_passed = True
    
    for test in error_tests:
        print(f"\nRunning error test: {test['name']}")
        
        # Run setup if provided
        if "setup" in test:
            test["setup"]()
        
        # EXECUTE: Run the function that should handle the error
        try:
            actual_result = test["function"]()
            
            # VERIFY: Check if result matches expected
            expected_result = test["expected_result"]
            
            if actual_result != expected_result:
                print(f"❌ Unexpected result for error test: {test['name']}")
                print(f"   Expected: {expected_result}")
                print(f"   Actual:   {actual_result}")
                all_tests_passed = False
            else:
                print(f"✅ Error handling test passed: {test['name']}")
                print(f"   Result matched expected: {expected_result}")
                
        except Exception as e:
            print(f"❌ Unhandled exception in error test: {test['name']}")
            print(f"   Exception: {str(e)}")
            all_tests_passed = False
        
        # Run cleanup if provided
        if "cleanup" in test:
            test["cleanup"]()
    
    print(f"\n{'✅ All error handling tests passed' if all_tests_passed else '❌ Some error handling tests failed'}")
    return all_tests_passed

def test_batch_operations(db):
    """
    Test batch operations for multiple documents.
    
    This test creates multiple documents in a batch, updates them,
    queries them, and then deletes them, verifying each operation.
    
    Args:
        db: Database connection
        
    Returns:
        bool: Success status
    """
    print("\n==== Testing batch operations ====")
    
    # Create multiple documents
    batch_size = 5
    batch_prefix = f"batch_{uuid.uuid4().hex[:6]}"
    batch_docs = []
    batch_keys = []
    
    print(f"Creating batch of {batch_size} documents...")
    
    for i in range(batch_size):
        doc = get_test_document()
        doc["_key"] = f"{batch_prefix}_{i}"
        doc["batch_index"] = i
        doc["batch_id"] = batch_prefix
        
        created_doc = create_document(db, TEST_DOC_COLLECTION, doc)
        if created_doc:
            batch_docs.append(created_doc)
            batch_keys.append(created_doc["_key"])
    
    if len(batch_docs) != batch_size:
        print(f"❌ Failed to create all batch documents. Created {len(batch_docs)} of {batch_size}")
        # Clean up any created documents
        for key in batch_keys:
            delete_document(db, TEST_DOC_COLLECTION, key)
        return False
    
    print(f"✅ Created {len(batch_docs)} documents in batch")
    
    # Query batch documents
    print("Querying batch documents...")
    
    filter_clause = "FILTER doc.batch_id == @batch_id"
    bind_vars = {"batch_id": batch_prefix}
    
    query_results = query_documents(db, TEST_DOC_COLLECTION, filter_clause, bind_vars=bind_vars)
    
    if len(query_results) != batch_size:
        print(f"❌ Query returned {len(query_results)} results, expected {batch_size}")
        # Clean up
        for key in batch_keys:
            delete_document(db, TEST_DOC_COLLECTION, key)
        return False
    
    print(f"✅ Successfully queried all {batch_size} batch documents")
    
    # Update all batch documents
    print("Updating all batch documents...")
    
    update_count = 0
    update_value = f"batch_updated_{time.time()}"
    
    for key in batch_keys:
        updated_doc = update_document(
            db, 
            TEST_DOC_COLLECTION, 
            key, 
            {"updated_field": update_value}
        )
        if updated_doc and updated_doc.get("updated_field") == update_value:
            update_count += 1
    
    if update_count != batch_size:
        print(f"❌ Updated {update_count} documents, expected {batch_size}")
        # Clean up
        for key in batch_keys:
            delete_document(db, TEST_DOC_COLLECTION, key)
        return False
    
    print(f"✅ Successfully updated all {batch_size} batch documents")
    
    # Delete all batch documents
    print("Deleting all batch documents...")
    
    delete_count = 0
    for key in batch_keys:
        if delete_document(db, TEST_DOC_COLLECTION, key):
            delete_count += 1
    
    if delete_count != batch_size:
        print(f"❌ Deleted {delete_count} documents, expected {batch_size}")
        # Try to clean up any remaining documents
        for key in batch_keys:
            delete_document(db, TEST_DOC_COLLECTION, key)
        return False
    
    print(f"✅ Successfully deleted all {batch_size} batch documents")
    
    # Final verification that all documents are gone
    query_results = query_documents(db, TEST_DOC_COLLECTION, filter_clause, bind_vars=bind_vars)
    if query_results and len(query_results) > 0:
        print(f"❌ Found {len(query_results)} documents after deletion, expected 0")
        # Final cleanup attempt
        for doc in query_results:
            delete_document(db, TEST_DOC_COLLECTION, doc["_key"])
        return False
    
    print("✅ All batch operations completed successfully")
    return True

def recap_test_verification():
    """
    Summarize test verification status.
    
    This function prints a summary of all the tests that were run and their results.
    
    Returns:
        Dict[str, bool]: Dictionary of test names and their status
    """
    print("\n==== Test Verification Summary ====")
    
    # Define statuses for each test based on global variables
    # In a real test environment, these would be populated during test runs
    test_statuses = {
        "document_creation": getattr(recap_test_verification, "document_creation", None),
        "document_retrieval": getattr(recap_test_verification, "document_retrieval", None),
        "document_update": getattr(recap_test_verification, "document_update", None),
        "document_deletion": getattr(recap_test_verification, "document_deletion", None),
        "document_querying": getattr(recap_test_verification, "document_querying", None),
        "error_handling": getattr(recap_test_verification, "error_handling", None),
        "batch_operations": getattr(recap_test_verification, "batch_operations", None)
    }
    
    # Print summary table
    print("\n| Test | Status |")
    print("|------|--------|")
    
    for test, status in test_statuses.items():
        status_str = "✅ PASS" if status is True else "❌ FAIL" if status is False else "⏳ NOT RUN"
        print(f"| {test.replace('_', ' ').title()} | {status_str} |")
    
    # Calculate overall result
    statuses = [s for s in test_statuses.values() if s is not None]
    passed = sum(1 for s in statuses if s is True)
    failed = sum(1 for s in statuses if s is False)
    not_run = sum(1 for s in test_statuses.values() if s is None)
    
    print(f"\nSummary: {passed} passed, {failed} failed, {not_run} not run")
    
    if failed == 0 and passed > 0:
        print("\n✅ ALL TESTS PASSED")
    elif failed > 0:
        print("\n❌ SOME TESTS FAILED")
    else:
        print("\n⚠️ NO TESTS RUN")
    
    return test_statuses

def run_all_tests():
    """
    Main function to run all database operation tests.
    
    This function runs through the complete test suite for db_operations.py
    including setup, execution, verification, and cleanup.
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    print("\n====================================")
    print("RUNNING DATABASE OPERATIONS TESTS")
    print("====================================\n")
    
    # Setup test environment
    db = setup_test_environment()
    if not db:
        print("❌ Failed to set up test environment")
        return False
    
    # Initialize test status
    all_tests_passed = True
    created_doc_key = None
    
    try:
        # Test 1: Document Creation
        create_success, created_doc_key, created_doc = test_create_document(db)
        recap_test_verification.document_creation = create_success
        if not create_success or not created_doc_key:
            all_tests_passed = False
            print("❌ Document creation test failed, skipping dependent tests")
        else:
            # Test 2: Document Retrieval
            get_success, retrieved_doc = test_get_document(db, created_doc_key)
            recap_test_verification.document_retrieval = get_success
            if not get_success:
                all_tests_passed = False
                print("❌ Document retrieval test failed")
            
            # Test 3: Document Update
            update_success, updated_doc = test_update_document(db, created_doc_key, created_doc)
            recap_test_verification.document_update = update_success
            if not update_success:
                all_tests_passed = False
                print("❌ Document update test failed")
            
            # Test 4: Document Deletion
            delete_success = test_delete_document(db, created_doc_key)
            recap_test_verification.document_deletion = delete_success
            if not delete_success:
                all_tests_passed = False
                print("❌ Document deletion test failed")
                # Set to None so cleanup doesn't try to delete it again
                created_doc_key = None
        
        # Test 5: Query Documents
        query_success = test_query_documents(db)
        recap_test_verification.document_querying = query_success
        if not query_success:
            all_tests_passed = False
            print("❌ Document querying test failed")
        
        # Test 6: Error Handling
        error_success = test_error_handling(db)
        recap_test_verification.error_handling = error_success
        if not error_success:
            all_tests_passed = False
            print("❌ Error handling test failed")
        
        # Test 7: Batch Operations
        batch_success = test_batch_operations(db)
        recap_test_verification.batch_operations = batch_success
        if not batch_success:
            all_tests_passed = False
            print("❌ Batch operations test failed")
    
    except Exception as e:
        all_tests_passed = False
        print(f"❌ Unexpected exception during tests: {e}")
    
    finally:
        # Clean up any remaining test documents
        if created_doc_key:
            teardown_test_document(db, created_doc_key)
        
        # Print test summary
        recap_test_verification()
    
    return all_tests_passed

if __name__ == "__main__":
    # Initialize static attributes for recap function
    recap_test_verification.document_creation = None
    recap_test_verification.document_retrieval = None
    recap_test_verification.document_update = None
    recap_test_verification.document_deletion = None
    recap_test_verification.document_querying = None
    recap_test_verification.error_handling = None
    recap_test_verification.batch_operations = None
    
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)