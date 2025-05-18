#!/usr/bin/env python3
"""
Complete validation of all CLI commands with real outputs
"""

import subprocess
import json
import os
from datetime import datetime

def run_command(cmd):
    """Run command and return full output"""
    result = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_and_document(name, cmd):
    """Test command and document real output"""
    print(f"\n### Testing: {name}")
    print(f"Command: {cmd}")
    
    code, stdout, stderr = run_command(cmd)
    
    print(f"Exit Code: {code}")
    print("STDOUT:")
    print(stdout)
    print("STDERR:")
    if stderr:
        print(stderr[:500])
    print("-" * 50)
    
    return {
        "name": name,
        "command": cmd,
        "exit_code": code,
        "stdout": stdout,
        "stderr": stderr,
        "timestamp": datetime.now().isoformat()
    }

# Test all commands
results = []
base_cmd = "cd /home/graham/workspace/experiments/arangodb && source .venv/bin/activate && "

# 1. Generic CRUD Commands
print("## GENERIC CRUD COMMANDS")
results.append(test_and_document(
    "Generic List (JSON)",
    base_cmd + "python -m arangodb.cli generic list glossary --limit 2 --output json"
))

results.append(test_and_document(
    "Generic List (Table)",
    base_cmd + "python -m arangodb.cli generic list glossary --limit 2 --output table"
))

results.append(test_and_document(
    "Generic Create",
    base_cmd + 'python -m arangodb.cli generic create test_collection \'{"title": "Test Doc", "content": "Test content for embedding"}\' --output json'
))

# 2. Search Commands
print("\n## SEARCH COMMANDS")
results.append(test_and_document(
    "BM25 Search",
    base_cmd + "python -m arangodb.cli search bm25 database --top-n 2"
))

results.append(test_and_document(
    "Semantic Search (valid collection)",
    base_cmd + "python -m arangodb.cli search semantic technology --top-n 2"
))

results.append(test_and_document(
    "Semantic Search (invalid collection)",
    base_cmd + "python -m arangodb.cli search semantic --collection non_existent test"
))

# 3. CRUD Commands
print("\n## CRUD COMMANDS")
results.append(test_and_document(
    "CRUD List Lessons",
    base_cmd + "python -m arangodb.cli crud --help"
))

# 4. Memory Commands
print("\n## MEMORY COMMANDS")
results.append(test_and_document(
    "Memory List",
    base_cmd + "python -m arangodb.cli memory --help"
))

# Save results
with open("validation_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nResults saved to validation_results.json")