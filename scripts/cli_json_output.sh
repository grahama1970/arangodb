#!/bin/bash
"""
CLI JSON Output Examples

This script demonstrates how to use the ArangoDB CLI with JSON output
for programmatic access and scripting.
"""

echo "=== CLI JSON Output Examples ==="
echo

# Base command
CLI="python -m arangodb.cli.main"

# 1. CRUD Operations with JSON output
echo "1. Creating a document..."
$CLI crud add-lesson --data '{"_key": "cli_test_1", "title": "Test Document", "content": "Example content", "tags": ["cli", "json"]}' --json-output
echo

echo "2. Getting document as JSON..."
$CLI crud get-lesson cli_test_1 --json-output
echo

echo "3. Updating document with JSON response..."
$CLI crud update-lesson cli_test_1 --data '{"content": "Updated content"}' --json-output
echo

# 2. Search Operations with JSON output
echo "4. Keyword search with JSON results..."
$CLI search keyword --query "test" --limit 5 --json-output
echo

echo "5. Semantic search with JSON results..."
$CLI search semantic --query "find examples of CLI usage" --limit 3 --json-output
echo

# 3. Graph Operations with JSON output
echo "6. Creating a relationship..."
$CLI crud add-lesson --data '{"_key": "cli_test_2", "title": "Second Document"}' --json-output
$CLI graph add-relationship --from cli_test_1 --to cli_test_2 --type "related_to" --rationale "Test relationship" --json-output
echo

echo "7. Graph traversal with JSON results..."
$CLI graph traverse --start cli_test_1 --max-depth 1 --json-output
echo

# 4. Memory Operations with JSON output
echo "8. Storing a memory..."
$CLI memory store --content "This is a test memory" --tags "cli,test" --json-output
echo

echo "9. Searching memories..."
$CLI memory search --query "test memory" --limit 5 --json-output
echo

# 5. Cleanup
echo "10. Cleanup..."
$CLI crud delete-lesson cli_test_1 --yes --json-output
$CLI crud delete-lesson cli_test_2 --yes --json-output
echo

echo "=== Examples Complete ===" 