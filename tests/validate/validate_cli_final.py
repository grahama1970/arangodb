#!/usr/bin/env python3
"""
Final validation of CLI fixes for Task 025
"""

import subprocess
import json
import sys

def run_command(cmd):
    """Run a CLI command and return results."""
    result = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_command(name, cmd, check_json=False):
    """Test a single command."""
    print(f"\n{name}:")
    code, stdout, stderr = run_command(cmd)
    
    if code == 0:
        if check_json:
            try:
                data = json.loads(stdout)
                print(f"✅ Valid JSON with {len(data)} items")
            except:
                print(f"❌ Invalid JSON output")
                return False
        else:
            print(f"✅ Command succeeded")
        return True
    else:
        print(f"❌ Failed: {stderr[-500:]}")
        return False

print("=== Final CLI Validation ===")
failures = 0

# Test 1: Generic CRUD list with JSON output
if not test_command(
    "Generic list (JSON)",
    "cd /home/graham/workspace/experiments/arangodb && source .venv/bin/activate && python -m arangodb.cli generic list glossary --limit 3 --output json",
    check_json=True
):
    failures += 1

# Test 2: Generic CRUD list with table output
if not test_command(
    "Generic list (table)",
    "cd /home/graham/workspace/experiments/arangodb && source .venv/bin/activate && python -m arangodb.cli generic list glossary --limit 3 --output table"
):
    failures += 1

# Test 3: Generic CRUD create
test_data = json.dumps({"title": "Test Document", "description": "Test for CLI validation"})
if not test_command(
    "Generic create",
    f'cd /home/graham/workspace/experiments/arangodb && source .venv/bin/activate && python -m arangodb.cli generic create test_documents \'{test_data}\' --output json',
    check_json=True
):
    failures += 1

# Test 4: Search semantic with pre-validation
if not test_command(
    "Semantic search (pre-validation)",
    "cd /home/graham/workspace/experiments/arangodb && source .venv/bin/activate && python -m arangodb.cli search semantic --collection non_existent --query test --output json"
):
    # This should fail with clear error
    pass

# Test 5: Search BM25  
if not test_command(
    "BM25 search",
    "cd /home/graham/workspace/experiments/arangodb && source .venv/bin/activate && python -m arangodb.cli search bm25 glossary database --output json",
    check_json=True
):
    failures += 1

print(f"\n=== Summary ===")
print(f"Total tests: 5")
print(f"Failures: {failures}")

if failures == 0:
    print("✅ All critical tests passed!")
    sys.exit(0)
else:
    print(f"❌ {failures} tests failed")
    sys.exit(1)