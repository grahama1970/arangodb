#!/usr/bin/env python3
"""
Test error logging for semantic search
"""

import sys
from loguru import logger
from arango import ArangoClient
from arangodb.core.search.semantic_search import safe_semantic_search
from arangodb.core.constants import (
    ARANGO_HOST, ARANGO_DB_NAME, ARANGO_USER, ARANGO_PASSWORD
)

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:HH:mm:ss} | {level:<7} | {message}"
)

# Connect to ArangoDB
client = ArangoClient(hosts=ARANGO_HOST)
db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)

print("\n=== Testing Error Logging for Various Failure Scenarios ===\n")

# Test 1: Empty collection
print("1. Testing with empty collection:")
result = safe_semantic_search(db, "test query", collections=["empty_collection"])
print(f"Search engine: {result['search_engine']}")
print(f"Error: {result.get('error', 'None')}")
print()

# Test 2: Non-existent collection
print("2. Testing with non-existent collection:")
result = safe_semantic_search(db, "test query", collections=["non_existent_collection"])
print(f"Search engine: {result['search_engine']}")
print(f"Error: {result.get('error', 'None')}")
print()

# Test 3: Valid collection
print("3. Testing with valid collection:")
result = safe_semantic_search(db, "semantic search", collections=["memory_documents"])
print(f"Search engine: {result['search_engine']}")
print(f"Results found: {len(result['results'])}")
if result['results']:
    print(f"Top result: {result['results'][0]['doc'].get('title', 'No title')}")
print()

# Test 4: Invalid query
print("4. Testing with invalid query (None):")
result = safe_semantic_search(db, None, collections=["memory_documents"])
print(f"Search engine: {result['search_engine']}")
print(f"Error: {result.get('error', 'None')}")
print()

# Test 5: Collection with no embeddings
print("5. Creating collection with documents but no embeddings:")
test_collection = "test_no_embeddings"
if db.has_collection(test_collection):
    db.delete_collection(test_collection)
    
collection = db.create_collection(test_collection)
# Insert documents without embeddings
docs = [
    {"title": "Test Doc 1", "content": "This is a test document"},
    {"title": "Test Doc 2", "content": "Another test document"}
]
collection.insert_many(docs)

result = safe_semantic_search(db, "test", collections=[test_collection])
print(f"Search engine: {result['search_engine']}")
print(f"Error: {result.get('error', 'None')}")

# Clean up
db.delete_collection(test_collection)
print("\nTest completed!")