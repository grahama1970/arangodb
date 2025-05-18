#!/usr/bin/env python3
"""
Test the generic CRUD commands
"""

import subprocess
import json

def run_command(cmd):
    """Run a CLI command and return stdout."""
    result = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

# Test commands
print("=== Testing Generic CRUD Commands ===")

# Test help
print("\n1. Testing generic help:")
code, stdout, stderr = run_command("cd /home/graham/workspace/experiments/arangodb && source .venv/bin/activate && python -m arangodb.cli generic --help")
if code == 0:
    print("✅ Generic help works")
else:
    print(f"❌ Error: {stderr}")

# Test list command directly from generic_crud_commands.py
print("\n2. Testing list command directly:")
code, stdout, stderr = run_command("cd /home/graham/workspace/experiments/arangodb && source .venv/bin/activate && python -m arangodb.cli.generic_crud_commands list glossary --limit 3 --output json")
if code == 0:
    print("✅ List command works")
    print(f"Output: {stdout[:200]}...")
else:
    print(f"❌ Error: {stderr}")