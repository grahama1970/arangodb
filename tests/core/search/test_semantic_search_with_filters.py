#!/usr/bin/env python3
"""
Test to verify that semantic search fails with filters
and demonstrate the correct two-stage approach
"""

import sys
from arango import ArangoClient
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")

# Add src to path
sys.path.insert(0, '/home/graham/workspace/experiments/arangodb/src')

from arangodb.core.constants import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME
from arangodb.core.utils.embedding_utils import get_embedding

# Connect to ArangoDB
client = ArangoClient(hosts=ARANGO_HOST)
db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)

# Test data
test_docs = [
    {"title": "Machine Learning", "content": "ML is awesome", "tags": ["ml", "ai"]},
    {"title": "Deep Learning", "content": "DL uses neural networks", "tags": ["ml", "deep-learning"]},
    {"title": "Python Programming", "content": "Python is versatile", "tags": ["python", "programming"]},
]

# Create test collection
collection_name = "test_semantic_filter"
if db.has_collection(collection_name):
    db.delete_collection(collection_name)
collection = db.create_collection(collection_name)

# Add embeddings and insert docs
for doc in test_docs:
    doc['embedding'] = get_embedding(f"{doc['title']} {doc['content']}")
    
collection.insert_many(test_docs)

# Create vector index
collection.add_index({
    "type": "vector",
    "fields": ["embedding"],
    "params": {
        "dimension": 1024,
        "metric": "cosine",
        "nLists": 2
    }
})

query_embedding = get_embedding("machine learning")

print("\n1. Testing APPROX_NEAR_COSINE with filter (WILL FAIL):")
try:
    aql_with_filter = """
    FOR doc IN test_semantic_filter
        FILTER "ml" IN doc.tags
        LET score = APPROX_NEAR_COSINE(doc.embedding, @query_embedding)
        SORT score DESC
        LIMIT 5
        RETURN {title: doc.title, score: score}
    """
    cursor = db.aql.execute(aql_with_filter, bind_vars={"query_embedding": query_embedding})
    results = list(cursor)
    print(f"SUCCESS (unexpected): {results}")
except Exception as e:
    print(f"FAILED (expected): {e}")

print("\n2. Testing pure APPROX_NEAR_COSINE (NO FILTERS):")
try:
    aql_no_filter = """
    FOR doc IN test_semantic_filter
        LET score = APPROX_NEAR_COSINE(doc.embedding, @query_embedding)
        SORT score DESC
        LIMIT 5
        RETURN MERGE(doc, {score: score})
    """
    cursor = db.aql.execute(aql_no_filter, bind_vars={"query_embedding": query_embedding})
    results = list(cursor)
    print(f"SUCCESS: Found {len(results)} results")
    
    # Python filtering (stage 2)
    print("\n3. Python filtering (stage 2):")
    filtered = [r for r in results if "ml" in r.get("tags", [])]
    print(f"After filtering: {len(filtered)} results with 'ml' tag")
    for r in filtered:
        print(f"  - {r['title']}: {r['score']:.4f}")
        
except Exception as e:
    print(f"FAILED: {e}")

# Cleanup
db.delete_collection(collection_name)