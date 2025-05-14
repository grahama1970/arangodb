#!/usr/bin/env python3
"""
Test fixtures and utilities for ArangoDB tests.

This module provides common test fixtures and utility functions that are
shared across multiple test modules. It includes standard test data,
connection handling, and verification utilities.
"""

import os
import sys
import json
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Set up environment variables for ArangoDB connection
os.environ.setdefault("ARANGO_HOST", "http://localhost:8529")
os.environ.setdefault("ARANGO_USER", "root")
os.environ.setdefault("ARANGO_PASSWORD", "openSesame")  # Using provided password
os.environ.setdefault("ARANGO_DB_NAME", "memory_bank")  # Use the existing database name

from complexity.arangodb.arango_setup import connect_arango, ensure_database
from complexity.arangodb.db_operations import (
    create_document,
    delete_document,
    query_documents
)

# Test collections
TEST_DOC_COLLECTION = "test_docs"
TEST_EDGE_COLLECTION = "test_relationships"
TEST_GRAPH_NAME = "test_graph"

# Sample test data directories
REPO_ROOT = Path(__file__).parent.parent.parent.parent
TEST_DATA_DIR = REPO_ROOT / "repos" / "python-arango_sparse"

def setup_test_database():
    """
    Set up a test database with required collections.
    
    Returns:
        The database connection object or None if setup failed.
    """
    # Connect to ArangoDB
    client = connect_arango()
    if not client:
        print("❌ Failed to connect to ArangoDB")
        return None
    
    # Use a separate test database specified in the environment variables
    # Ensure database_name is set in environment
    os.environ["ARANGO_DB_NAME"] = os.environ.get("ARANGO_DB_NAME", "complexity_test")
    
    # Call ensure_database without parameters - it will use the DB name from environment
    db = ensure_database(client)
    if not db:
        print("❌ Failed to ensure test database")
        return None
    
    print(f"✅ Connected to test database: {db.name}")
    
    # Ensure collections exist
    for collection_name in [TEST_DOC_COLLECTION, TEST_EDGE_COLLECTION]:
        if not db.has_collection(collection_name):
            is_edge = "relationship" in collection_name.lower()
            db.create_collection(collection_name, edge=is_edge)
            print(f"✅ Created {'edge ' if is_edge else ''}collection: {collection_name}")
    
    return db

def generate_test_document(prefix: str = "test", with_embedding: bool = False) -> Dict[str, Any]:
    """
    Generate a test document with specific fields for testing.
    
    Args:
        prefix: Prefix for the document key
        with_embedding: Whether to include a mock embedding vector
        
    Returns:
        A dictionary containing a test document
    """
    doc_id = str(uuid.uuid4())
    doc = {
        "_key": f"{prefix}_{doc_id[:8]}",
        "title": f"Test Document {doc_id[:6]}",
        "content": (
            f"This is a test document with ID {doc_id} created for testing "
            f"ArangoDB operations. This document contains standard fields and values "
            f"that can be used for testing various database operations."
        ),
        "tags": ["test", "document", "arangodb"],
        "created_at": time.time(),
        "numeric_value": 42,
        "is_active": True
    }
    
    # Add a mock embedding if requested
    if with_embedding:
        # Create a 1024-dimensional vector to match production embedding dimensions
        doc["embedding"] = [0.1] * 1024  # 1024-dimensional vector
    
    return doc

def create_test_documents_batch(db, count: int = 5, prefix: str = "batch", with_embedding: bool = False) -> List[str]:
    """
    Create a batch of test documents for testing.
    
    Args:
        db: Database connection
        count: Number of documents to create
        prefix: Prefix for document keys
        with_embedding: Whether to include mock embeddings
        
    Returns:
        List of created document keys
    """
    batch_keys = []
    batch_id = f"{prefix}_{uuid.uuid4().hex[:6]}"
    
    for i in range(count):
        doc = generate_test_document(prefix=batch_id, with_embedding=with_embedding)
        doc["batch_index"] = i
        doc["batch_id"] = batch_id
        
        created_doc = create_document(db, TEST_DOC_COLLECTION, doc)
        if created_doc:
            batch_keys.append(created_doc["_key"])
    
    return batch_keys

def cleanup_test_documents(db, doc_keys: List[str]) -> bool:
    """
    Clean up test documents after testing.
    
    Args:
        db: Database connection
        doc_keys: List of document keys to delete
        
    Returns:
        True if all documents were successfully deleted, False otherwise
    """
    success = True
    for key in doc_keys:
        if not delete_document(db, TEST_DOC_COLLECTION, key, ignore_missing=True):
            print(f"⚠️ Failed to delete test document: {key}")
            success = False
    
    return success

def create_search_test_documents(db) -> List[Dict[str, Any]]:
    """
    Create a set of test documents specifically for search testing.
    
    Args:
        db: Database connection
        
    Returns:
        List of created documents
    """
    documents = []
    doc_keys = []
    
    # Document 1: Python programming
    doc1 = generate_test_document(prefix="search", with_embedding=True)
    doc1["title"] = "Introduction to Python Programming"
    doc1["content"] = """
    Python is a high-level, interpreted programming language known for
    its readability and versatility. It supports multiple programming
    paradigms including procedural, object-oriented, and functional
    programming. Python has a comprehensive standard library and a rich
    ecosystem of third-party packages for various domains.
    """
    doc1["tags"] = ["python", "programming", "language"]
    doc1["category"] = "programming"
    doc1["difficulty"] = "beginner"
    
    # Document 2: Database-related
    doc2 = generate_test_document(prefix="search", with_embedding=True)
    doc2["title"] = "ArangoDB Database Overview"
    doc2["content"] = """
    ArangoDB is a multi-model database system that supports key-value,
    document, and graph data models. It provides a unified query language
    called AQL (ArangoDB Query Language) for all data models. ArangoDB
    offers high performance, scalability, and flexibility for modern
    applications requiring complex data relationships.
    """
    doc2["tags"] = ["database", "arangodb", "nosql"]
    doc2["category"] = "database"
    doc2["difficulty"] = "intermediate"
    
    # Document 3: Python with ArangoDB
    doc3 = generate_test_document(prefix="search", with_embedding=True)
    doc3["title"] = "Using Python with ArangoDB"
    doc3["content"] = """
    Python provides excellent integration with ArangoDB through the
    python-arango driver. This library allows developers to interact with
    ArangoDB databases, collections, and documents using Python code.
    It supports all ArangoDB features including document operations,
    AQL queries, graph traversals, and more.
    """
    doc3["tags"] = ["python", "arangodb", "integration"]
    doc3["category"] = "integration"
    doc3["difficulty"] = "intermediate"
    
    # Document 4: Search algorithms
    doc4 = generate_test_document(prefix="search", with_embedding=True)
    doc4["title"] = "Search Algorithms and Techniques"
    doc4["content"] = """
    Search algorithms are methods for retrieving information from large
    datasets. Common techniques include keyword-based search, semantic
    search, and hybrid approaches. BM25 is a popular ranking function
    used in keyword search, while vector embeddings are used for semantic
    search to capture meaning beyond keywords.
    """
    doc4["tags"] = ["search", "algorithms", "information-retrieval"]
    doc4["category"] = "algorithms"
    doc4["difficulty"] = "advanced"
    
    # Document 5: Graph databases
    doc5 = generate_test_document(prefix="search", with_embedding=True)
    doc5["title"] = "Graph Database Fundamentals"
    doc5["content"] = """
    Graph databases store data in nodes (vertices) and edges (relationships).
    They excel at managing highly connected data and complex relationships.
    Graph traversal algorithms like breadth-first search and depth-first
    search are commonly used to navigate the graph structure. Graph databases
    are ideal for social networks, recommendation systems, and knowledge graphs.
    """
    doc5["tags"] = ["graph", "database", "relationships"]
    doc5["category"] = "database"
    doc5["difficulty"] = "intermediate"
    
    # Insert all documents
    for doc in [doc1, doc2, doc3, doc4, doc5]:
        created_doc = create_document(db, TEST_DOC_COLLECTION, doc)
        if created_doc:
            documents.append(created_doc)
            doc_keys.append(created_doc["_key"])
    
    print(f"✅ Created {len(documents)} test documents for search testing")
    
    # Store the keys for cleanup
    create_search_test_documents.doc_keys = doc_keys
    
    return documents

def verify_search_results(results: Dict[str, Any], expected_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify search results against expected data.
    
    Args:
        results: Actual search results
        expected_data: Expected data to compare against
        
    Returns:
        Tuple of (success, dict of failures)
    """
    failures = {}
    
    # Basic structure check
    if not isinstance(results, dict):
        failures["result_structure"] = {"expected": "dictionary", "actual": type(results).__name__}
        return False, failures
    
    # Check for required fields
    required_fields = ["results", "total", "query"]
    for field in required_fields:
        if field not in results:
            failures[f"missing_{field}"] = {"expected": f"{field} field present", "actual": "field missing"}
    
    if "results" not in results:
        # Can't continue without results field
        return False, failures
    
    # Check query
    if "query" in expected_data and results.get("query") != expected_data.get("query"):
        failures["query"] = {
            "expected": expected_data.get("query"),
            "actual": results.get("query")
        }
    
    # Check result count if specified
    if "expected_count" in expected_data:
        actual_count = len(results.get("results", []))
        expected_count = expected_data["expected_count"]
        if actual_count != expected_count:
            failures["result_count"] = {
                "expected": expected_count,
                "actual": actual_count
            }
    
    # Check for expected result keys
    if "expected_keys" in expected_data:
        actual_keys = [r.get("doc", {}).get("_key") for r in results.get("results", [])]
        expected_keys = expected_data["expected_keys"]
        
        # Check if all expected keys are present
        missing_keys = [k for k in expected_keys if k not in actual_keys]
        if missing_keys:
            failures["missing_keys"] = {
                "expected": expected_keys,
                "actual": actual_keys,
                "missing": missing_keys
            }
    
    # Check for expected score minimum if specified
    if "min_score" in expected_data:
        min_score = expected_data["min_score"]
        for idx, result in enumerate(results.get("results", [])):
            score = result.get("score", 0)
            if score < min_score:
                failures[f"result_{idx}_score"] = {
                    "expected": f">= {min_score}",
                    "actual": score
                }
    
    return len(failures) == 0, failures

def save_fixture_data(data: Dict[str, Any], filename: str) -> bool:
    """
    Save fixture data to a JSON file for future test runs.
    
    Args:
        data: Data to save
        filename: Name of the fixture file
        
    Returns:
        True if save was successful, False otherwise
    """
    fixture_dir = Path(__file__).parent / "fixtures"
    fixture_dir.mkdir(exist_ok=True)
    
    fixture_path = fixture_dir / filename
    
    try:
        with open(fixture_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Failed to save fixture data: {e}")
        return False

def load_fixture_data(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load fixture data from a JSON file.
    
    Args:
        filename: Name of the fixture file
        
    Returns:
        Loaded data or None if load failed
    """
    fixture_dir = Path(__file__).parent / "fixtures"
    fixture_path = fixture_dir / filename
    
    if not fixture_path.exists():
        print(f"❌ Fixture file does not exist: {fixture_path}")
        return None
    
    try:
        with open(fixture_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load fixture data: {e}")
        return None

def print_verification_summary(test_name: str, passed: bool, failures: Dict[str, Any]) -> None:
    """
    Print a summary of verification results.
    
    Args:
        test_name: Name of the test
        passed: Whether verification passed
        failures: Dictionary of verification failures
    """
    if passed:
        print(f"\n✅ {test_name} VERIFICATION PASSED")
    else:
        print(f"\n❌ {test_name} VERIFICATION FAILED")
        print("\nFailure details:")
        
        for key, details in failures.items():
            print(f"  - {key}:")
            if isinstance(details, dict) and "expected" in details and "actual" in details:
                print(f"    Expected: {details['expected']}")
                print(f"    Actual:   {details['actual']}")
            else:
                print(f"    {details}")
        
        print(f"\nTotal failures: {len(failures)}")

# Static storage for cleanup
create_search_test_documents.doc_keys = []

if __name__ == "__main__":
    # Simple self-test
    print("Setting up test connection...")
    db = setup_test_database()
    if not db:
        print("❌ Failed to connect to database")
        sys.exit(1)
    
    print("\nGenerating test document...")
    test_doc = generate_test_document()
    print(f"Generated document with key: {test_doc['_key']}")
    
    print("\nCreating test document batch...")
    batch_keys = create_test_documents_batch(db, count=3)
    print(f"Created {len(batch_keys)} documents in batch")
    
    print("\nCreating search test documents...")
    search_docs = create_search_test_documents(db)
    print(f"Created {len(search_docs)} search test documents")
    
    # Clean up
    print("\nCleaning up test documents...")
    cleanup_test_documents(db, batch_keys)
    cleanup_test_documents(db, create_search_test_documents.doc_keys)
    
    print("\n✅ Test fixtures module self-test completed successfully")