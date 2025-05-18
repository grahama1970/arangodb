#!/usr/bin/env python
"""
Comprehensive CLI test to verify all commands work as expected
"""

import subprocess
import json
import sys

def run_command(cmd):
    """Execute a CLI command and return status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_command(description, command):
    """Test a single command and report results"""
    print(f"\nTesting: {description}")
    print(f"Command: {command}")
    success, stdout, stderr = run_command(command)
    
    if success:
        print("✅ SUCCESS")
        if stdout:
            print(f"Output preview: {stdout[:200]}...")
    else:
        print("❌ FAILED")
        if stderr:
            print(f"Error: {stderr[:200]}...")
    
    return success

def main():
    print("=== Comprehensive CLI Verification ===\n")
    
    tests = [
        # Generic CRUD Commands
        ("Generic list glossary", "python -m arangodb.cli generic list glossary --limit 2"),
        ("Generic list JSON", "python -m arangodb.cli generic list glossary --output json --limit 1"),
        
        # Search Commands  
        ("BM25 search", "python -m arangodb.cli search bm25 --collection glossary --query database"),
        ("Keyword search", "python -m arangodb.cli search keyword --collection glossary --query graph"),
        ("Tag search", "python -m arangodb.cli search tag --collection glossary --tag database"),
        
        # Memory Commands
        ("List conversations", "python -m arangodb.cli memory list"),
        ("Store conversation", "python -m arangodb.cli memory store --user-input 'test' --agent-response 'response'"),
        
        # Episode Commands
        ("List episodes", "python -m arangodb.cli episode list"),
        ("Create episode", "python -m arangodb.cli episode create --user-message 'test' --agent-message 'response' --summary 'test episode'"),
        
        # Graph Commands
        ("List relationships", "python -m arangodb.cli graph list-relationships"),
        
        # Community Commands
        ("List communities", "python -m arangodb.cli community list"),
        ("Detect communities", "python -m arangodb.cli community detect"),
        
        # Contradiction Commands
        ("List contradictions", "python -m arangodb.cli contradiction list"),
        
        # Search Config Commands
        ("List search configs", "python -m arangodb.cli search-config list"),
        ("Analyze query", "python -m arangodb.cli search-config analyze --query 'test query'"),
        
        # Compaction Commands
        ("List compactions", "python -m arangodb.cli compaction list"),
        
        # Lesson-specific CRUD
        ("List lessons", "python -m arangodb.cli list-lessons"),
        ("Add lesson", "python -m arangodb.cli add-lesson --title 'Test' --description 'Desc' --content 'Content'"),
    ]
    
    passed = 0
    failed = 0
    
    for desc, cmd in tests:
        if test_command(desc, cmd):
            passed += 1
        else:
            failed += 1
    
    print(f"\n\n=== FINAL RESULTS ===")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/len(tests)*100:.1f}%")
    
    if failed > 0:
        print("\n⚠️  Some commands failed - investigation needed")
        return 1
    else:
        print("\n✅ All commands working as expected!")
        return 0

if __name__ == "__main__":
    sys.exit(main())