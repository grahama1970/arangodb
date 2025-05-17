#!/usr/bin/env python3
"""Test CLI JSON and Rich Table Output"""

import subprocess
import json

def run_command(cmd):
    """Run a CLI command and return output."""
    print(f"\n=== Running: {cmd} ===")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    return result

def main():
    base_cmd = "cd /home/graham/workspace/experiments/arangodb && python -m arangodb.cli.main"
    
    # 1. First create a test document
    print("\n1. Creating test document...")
    cmd = f'{base_cmd} crud add-lesson --data \'{{"_key": "output_test", "title": "Output Test", "content": "Testing JSON and Table output", "tags": ["test", "output"]}}\''
    run_command(cmd)
    
    # 2. Get document with JSON output
    print("\n2. Get document with JSON output...")
    cmd = f'{base_cmd} crud get-lesson output_test --json-output'
    result = run_command(cmd)
    
    # 3. Get document without JSON flag (should show table/rich output)
    print("\n3. Get document with default (table) output...")
    cmd = f'{base_cmd} crud get-lesson output_test'
    result = run_command(cmd)
    
    # 4. Search with JSON output
    print("\n4. Search with JSON output...")
    cmd = f'{base_cmd} search keyword --query "output test" --limit 5 --json-output'
    result = run_command(cmd)
    
    # 5. Search with default output
    print("\n5. Search with default output...")
    cmd = f'{base_cmd} search keyword --query "output test" --limit 5'
    result = run_command(cmd)
    
    # 6. Cleanup
    print("\n6. Cleanup...")
    cmd = f'{base_cmd} crud delete-lesson output_test --yes'
    run_command(cmd)

if __name__ == "__main__":
    main()