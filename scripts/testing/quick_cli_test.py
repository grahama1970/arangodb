"""
Module: quick_cli_test.py
Description: Command line interface functionality

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
"""Quick CLI test to verify key commands are working."""

import subprocess
import json
import time
from datetime import datetime

def run_command(cmd, timeout=30):
    """Run a command and return result."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - start
        
        print(f"Return code: {result.returncode}")
        print(f"Time taken: {elapsed:.2f}s")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout[:500])  # First 500 chars
            if len(result.stdout) > 500:
                print("... (truncated)")
                
        if result.stderr:
            print("STDERR:")
            print(result.stderr[:500])  # First 500 chars
            if len(result.stderr) > 500:
                print("... (truncated)")
                
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f" Command timed out after {timeout}s")
        return False
    except Exception as e:
        print(f" Error: {e}")
        return False

# Quick tests for critical commands
tests = [
    # 1. Health check
    ["python", "-m", "arangodb.cli", "health"],
    
    # 2. CRUD list (should work even if no docs)
    ["python", "-m", "arangodb.cli", "crud", "list", "test_cli_validation", "--limit", "5"],
    
    # 3. Search help (no actual search, just help)
    ["python", "-m", "arangodb.cli", "search", "--help"],
    
    # 4. Memory help
    ["python", "-m", "arangodb.cli", "memory", "--help"],
    
    # 5. Episode list
    ["python", "-m", "arangodb.cli", "episode", "list", "--limit", "5"],
]

# Run tests
print(f" Quick CLI Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Running {len(tests)} quick tests...")

passed = 0
failed = 0

for test_cmd in tests:
    if run_command(test_cmd, timeout=20):
        passed += 1
        print(" PASSED")
    else:
        failed += 1
        print(" FAILED")

print(f"\n{'='*60}")
print(f"SUMMARY: {passed} passed, {failed} failed")
print(f"{'='*60}")

if failed == 0:
    print(" All quick tests passed!")
else:
    print(f" {failed} tests failed")