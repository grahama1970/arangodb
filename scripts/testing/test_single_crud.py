"""
Module: test_single_crud.py
Description: Test suite for single_crud functionality

External Dependencies:
- arango: https://docs.python-arango.com/

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))



#!/usr/bin/env python3
"""Test a single CRUD command to debug issues."""

import subprocess
import json
from datetime import datetime
from arangodb.cli.db_connection import get_db_connection

# Create test collection
print("Creating test collection...")
db = get_db_connection()
collection_name = "test_cli_validation"

if not db.has_collection(collection_name):
    db.create_collection(collection_name)
    print(f" Created collection: {collection_name}")
else:
    print(f" Collection already exists: {collection_name}")

# Create test document
test_doc = {
    "title": "CLI Test Document",
    "content": "Testing CRUD operations via CLI",
    "tags": ["test", "validation"],
    "timestamp": datetime.now().timestamp()
}

print(f"\nTest document: {json.dumps(test_doc)}")

# Run create command
cmd = [
    "python", "-m", "arangodb.cli", "crud", "create",
    collection_name, json.dumps(test_doc)
]

print(f"\nRunning command: {' '.join(cmd)}")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print(f"\nReturn code: {result.returncode}")
    print(f"STDOUT:\n{result.stdout}")
    print(f"STDERR:\n{result.stderr}")
except subprocess.TimeoutExpired:
    print("Command timed out!")
except Exception as e:
    print(f"Error: {e}")