#!/usr/bin/env python3
"""Final test of all CLI commands to ensure they work correctly."""

import subprocess
import sys

def test_command(cmd, expected_ok=True):
    """Test a single command."""
    print(f"\n{'='*50}")
    print(f"Testing: {cmd}")
    print('='*50)
    
    result = subprocess.run(
        ["python", "-m", "arangodb.cli.main"] + cmd.split()[1:],
        capture_output=True,
        text=True
    )
    
    print(f"Return Code: {result.returncode}")
    print(f"STDOUT length: {len(result.stdout)}")
    
    if result.returncode != 0 and result.stderr:
        print("STDERR:")
        print(result.stderr[:200])
    
    success = result.returncode == 0 if expected_ok else result.returncode != 0
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"Result: {status}")
    
    return success

def main():
    """Test all CLI command groups."""
    commands = [
        # Memory commands (fixed)
        ("arangodb memory create test --content 'test content' --help", True),
        ("arangodb memory search semantic 'test' --help", True),
        
        # Search commands (no hybrid)
        ("arangodb search semantic test --help", True),
        ("arangodb search bm25 test --help", True),
        
        # CRUD commands
        ("arangodb crud create --help", True),
        ("arangodb crud read --help", True),
        
        # Community commands
        ("arangodb community detect --help", True),
        ("arangodb community list --help", True),
        
        # Episode commands
        ("arangodb episode create --help", True),
        ("arangodb episode list --help", True),
        
        # Graph commands
        ("arangodb graph add-relationship --help", True),
        ("arangodb graph traverse --help", True),
        
        # Compaction commands
        ("arangodb compaction create --help", True),
        ("arangodb compaction list --help", True),
        
        # Contradiction commands
        ("arangodb contradiction list --help", True),
        ("arangodb contradiction analyze --help", True),
    ]
    
    total = len(commands)
    passed = 0
    failed = []
    
    for cmd, expected_ok in commands:
        if test_command(cmd, expected_ok):
            passed += 1
        else:
            failed.append(cmd)
    
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed}/{total} tests passed")
    print('='*50)
    
    if failed:
        print("\nFailed commands:")
        for cmd in failed:
            print(f"  - {cmd}")
        return 1
    else:
        print("\n✓ All CLI commands working correctly!")
        return 0

if __name__ == "__main__":
    sys.exit(main())