#!/usr/bin/env python3
"""Test episode command output"""

import subprocess
import json
import sys

# Run the episode create command
cmd = [
    sys.executable, "-m", "arangodb.cli", 
    "episode", "create", "Test Episode",
    "--output", "json"
]

result = subprocess.run(cmd, capture_output=True, text=True)

print(f"Exit code: {result.returncode}")
print(f"Stdout length: {len(result.stdout)}")
print(f"Stderr length: {len(result.stderr)}")

if result.stdout:
    print("\nSTDOUT:")
    print(result.stdout)
    
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr[-1000:])  # Last 1000 chars

# Try to parse JSON from stdout
if result.stdout:
    try:
        # The output might have success message before JSON
        lines = result.stdout.strip().split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_str = '\n'.join(lines[i:])
                data = json.loads(json_str)
                print("\nParsed JSON:")
                print(json.dumps(data, indent=2))
                break
    except Exception as e:
        print(f"\nFailed to parse JSON: {e}")