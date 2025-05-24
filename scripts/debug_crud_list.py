#!/usr/bin/env python3
"""Debug CRUD list query."""

from arangodb.cli.db_connection import get_db_connection

collection = "test_cli_validation"
limit = 5
offset = 0

# Build query - use backticks for collection name
query = f"FOR doc IN `{collection}` LIMIT @offset, @limit RETURN doc"
bind_vars = {"offset": offset, "limit": limit}

print(f"Query: {query}")
print(f"Bind vars: {bind_vars}")

# Try to execute
try:
    db = get_db_connection()
    cursor = db.aql.execute(query, bind_vars=bind_vars)
    results = list(cursor)
    print(f"Results: {len(results)} documents")
    for doc in results:
        print(f"  - {doc.get('_key', 'unknown')}: {doc.get('title', 'no title')}")
except Exception as e:
    print(f"Error: {e}")