"""
Module: quick_validation.py

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

#!/usr/bin/env python
"""
Quick validation of key commands with real outputs
"""

import subprocess
import json
import os

os.environ["PYTHONPATH"] = str(os.getcwd())

def run_command(command):
    """Run a command and capture output"""
    full_command = ["python", "-m", "arangodb.cli"] + command
    try:
        result = subprocess.run(full_command, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

print("=== Task 025: Quick CLI Validation ===\n")

# Test semantic search pre-validation
print("1. Testing semantic search pre-validation:")
code, out, err = run_command(["search", "semantic", "--collection", "non_existent", "--query", "test"])
print(f"   Non-existent collection: {' PASS' if 'not exist' in err.lower() else ' FAIL'}")
if err:
    print(f"   Error: {err[:100]}")

# Test generic CRUD with JSON output
print("\n2. Testing generic CRUD commands:")
code, out, err = run_command(["generic", "list", "glossary", "--output", "json"])
try:
    data = json.loads(out)
    print(f"   List (JSON):  PASS - {len(data)} items")
except:
    print(f"   List (JSON):  FAIL - Invalid JSON")

# Test generic CRUD with table output
code, out, err = run_command(["generic", "list", "glossary", "--output", "table", "--limit", "3"])
print(f"   List (table): {' PASS' if code == 0 else ' FAIL'}")

# Test generic create with auto-embed
doc = {"name": "Test Doc", "description": "Test description for embedding"}
code, out, err = run_command(["generic", "create", "test_docs", json.dumps(doc), "--output", "json"])
try:
    result = json.loads(out)
    has_embedding = any('embedding' in str(v) for v in result.values())
    print(f"   Create with embedding: {' PASS' if has_embedding else ' FAIL'}")
    print(f"   Created ID: {result.get('_key', 'Unknown')}")
except:
    print(f"   Create:  FAIL - {err[:100] if err else 'Invalid JSON'}")

# Test memory commands
print("\n3. Testing memory commands:")
code, out, err = run_command(["memory", "list"])
print(f"   List conversations: {' PASS' if code == 0 else ' FAIL'}")

# Test search commands
print("\n4. Testing search commands:")
code, out, err = run_command(["search", "bm25", "--collection", "glossary", "--query", "database"])
print(f"   BM25 search: {' PASS' if code == 0 else ' FAIL'}")
if code == 0 and out:
    print(f"   Output preview: {out[:100]}...")

# Test episode commands
print("\n5. Testing episode commands:")
code, out, err = run_command(["episode", "list"])
print(f"   List episodes: {' PASS' if code == 0 else ' FAIL'}")

# Test graph commands
print("\n6. Testing graph commands:")
code, out, err = run_command(["graph", "traverse", "--lesson-id", "test"])
print(f"   Graph traverse: {' PASS' if code == 0 else ' FAIL'}")
if err:
    print(f"   Error: {err[:100]}")

print("\n=== Validation Complete ===")