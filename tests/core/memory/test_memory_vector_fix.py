#!/usr/bin/env python3
"""
Test the memory agent vector search fix
"""

import sys
import time
from datetime import datetime, timezone
from arango import ArangoClient
from loguru import logger

# Add src to path
sys.path.insert(0, '/home/graham/workspace/experiments/arangodb/src')

from arangodb.core.constants import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME
from arangodb.core.memory.memory_agent import MemoryAgent

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")

# Connect to ArangoDB
client = ArangoClient(hosts=ARANGO_HOST)
db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)

# Initialize memory agent
memory_agent = MemoryAgent(db=db)

# Create more test data
print("\n1. Creating test data...")
test_conversations = [
    {
        "user": "What is ArangoDB?",
        "agent": "ArangoDB is a multi-model NoSQL database supporting graphs, documents, and key-value pairs.",
        "conversation_id": "test_conv_001",
    },
    {
        "user": "How do I use vector search in ArangoDB?",
        "agent": "Vector search in ArangoDB uses APPROX_NEAR_COSINE function with vector indexes.",
        "conversation_id": "test_conv_001",
    },
    {
        "user": "Tell me about Python database connections",
        "agent": "Python can connect to various databases using drivers like psycopg2, mysql-connector, and python-arango.",
        "conversation_id": "test_conv_002",
    },
    {
        "user": "What are embeddings?",
        "agent": "Embeddings are numerical representations of text that capture semantic meaning in high-dimensional space.",
        "conversation_id": "test_conv_002",
    }
]

# Store conversations
for conv in test_conversations:
    result = memory_agent.store_conversation(
        user_message=conv["user"],
        agent_response=conv["agent"],
        conversation_id=conv["conversation_id"],
        auto_embed=True
    )
    print(f"Stored conversation: {conv['user'][:30]}...")

# Wait for indexing
time.sleep(1)

print("\n2. Testing vector search (no filters)...")
try:
    results = memory_agent.search("ArangoDB vector search", n_results=3)
    print(f"Found {len(results)} results:")
    for result in results:
        print(f"  - {result.get('type', '')}: {result.get('content', '')[:50]}... (score: {result.get('score', 0):.4f})")
except Exception as e:
    print(f"Vector search error: {e}")

print("\n3. Testing text search (with conversation_id filter)...")
try:
    results = memory_agent.search("database", conversation_id="test_conv_001", n_results=3)
    print(f"Found {len(results)} results:")
    for result in results:
        print(f"  - Conv: {result.get('conversation_id', '')}: {result.get('content', '')[:50]}... (score: {result.get('score', 0):.4f})")
except Exception as e:
    print(f"Text search error: {e}")

print("\n4. Testing text search (with time filter)...")
try:
    results = memory_agent.search("Python", point_in_time=datetime.now(timezone.utc), n_results=3)
    print(f"Found {len(results)} results:")
    for result in results:
        print(f"  - {result.get('type', '')}: {result.get('content', '')[:50]}... (score: {result.get('score', 0):.4f})")
except Exception as e:
    print(f"Text search with time filter error: {e}")

print("\n5. Checking vector index...")
collection = db.collection("agent_messages")
for index in collection.indexes():
    if index.get('type') == 'vector':
        print(f"Vector index found:")
        print(f"  Fields: {index.get('fields')}")
        print(f"  Params: {index.get('params')}")

print("\n6. Running CLI test simulation...")
# Simulate the CLI search command
from arangodb.cli.memory_commands import search_memories
from typer.testing import CliRunner

runner = CliRunner()

# Test without filters (should use vector search)
print("\nCLI test 1: Basic search (should use vector)...")
result = runner.invoke(search_memories, [
    "--query", "ArangoDB features",
    "--output", "json"
])
if result.exit_code == 0:
    print("CLI command succeeded")
else:
    print(f"CLI command failed: {result.stdout}")

# Test with filters (should use text search)
print("\nCLI test 2: Filtered search (should use text)...")
result = runner.invoke(search_memories, [
    "--query", "database",
    "--conversation-id", "test_conv_001",
    "--output", "json"
])
if result.exit_code == 0:
    print("CLI command succeeded")
else:
    print(f"CLI command failed: {result.stdout}")