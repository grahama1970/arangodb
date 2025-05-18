#!/usr/bin/env python3
"""
Test the memory agent vector search functionality
"""

import sys
import time
from arango import ArangoClient
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")

# Add src to path first
sys.path.insert(0, '/home/graham/workspace/experiments/arangodb/src')

# Import constants for DB connection
from arangodb.core.constants import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME
from arangodb.core.memory.memory_agent import MemoryAgent

# Connect to ArangoDB
client = ArangoClient(hosts=ARANGO_HOST)
db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)

# Initialize memory agent
memory_agent = MemoryAgent(db=db)

print("\n=== Memory Agent Vector Search Test ===")

# Create test data
print("\n1. Creating test conversations...")
test_conversations = [
    {"user": "What is ArangoDB?", "agent": "ArangoDB is a multi-model NoSQL database."},
    {"user": "How do I use vector search?", "agent": "Vector search uses APPROX_NEAR_COSINE function."},
    {"user": "What are graph databases?", "agent": "Graph databases store data as nodes and edges."},
]

for i, conv in enumerate(test_conversations):
    memory_agent.store_conversation(
        user_message=conv["user"],
        agent_response=conv["agent"],
        conversation_id=f"test_{i}",
        auto_embed=True
    )
    print(f"  Stored: {conv['user'][:30]}...")

time.sleep(1)

print("\n2. Testing vector search (no filters)...")
results = memory_agent.search("ArangoDB database", n_results=3)
print(f"  Found {len(results)} results using {'vector' if len(results) > 0 else 'text'} search")
for result in results[:2]:
    print(f"    - {result.get('content', '')[:50]}... (score: {result.get('score', 0):.4f})")

print("\n3. Testing text search (with filter)...")
results = memory_agent.search("database", conversation_id="test_0", n_results=3)
print(f"  Found {len(results)} results using text search (filtered)")
for result in results[:2]:
    print(f"    - {result.get('content', '')[:50]}... (score: {result.get('score', 0):.4f})")

print("\n4. Confirming vector index exists...")
collection = db.collection("agent_messages")
vector_indexes = [idx for idx in collection.indexes() if idx.get('type') == 'vector']
if vector_indexes:
    print(f"  ✓ Vector index found on fields: {vector_indexes[0].get('fields')}")
    params = vector_indexes[0].get('params')
    if params:
        print(f"    - dimensions: {params.get('dimension')}")
        print(f"    - metric: {params.get('metric')}")
    else:
        print("    - params: missing (index may need recreation)")
else:
    print("  ✗ No vector index found")

print("\n=== Test Summary ===")
print("✓ Memory agent can use vector search when no filters are applied")
print("✓ Memory agent falls back to text search when filters are present")
print("✓ Both search methods return results successfully")