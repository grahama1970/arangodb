#!/usr/bin/env python
"""
Task 025 - Comprehensive CLI Validation Script
Executes all commands and captures real outputs
"""

import subprocess
import json
import sys
import os
from typing import Dict, List, Tuple

# Set up environment
os.environ["PYTHONPATH"] = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Command groups to test
COMMAND_GROUPS = {
    "Search Commands": [
        ["search", "bm25", "--collection", "glossary", "--query", "database"],
        ["search", "semantic", "--collection", "glossary", "--query", "technology"],
        ["search", "keyword", "--collection", "glossary", "--query", "graph"],
        ["search", "tag", "--collection", "glossary", "--tag", "database"],
    ],
    "Memory Commands": [
        ["memory", "list"],
        ["memory", "store", "--user-input", "test query", "--agent-response", "test response"],
        ["memory", "search", "--query", "test"],
    ],
    "CRUD Commands": [
        ["add-lesson", "--title", "Test Lesson", "--description", "Test Description", "--content", "Test Content"],
        ["list-lessons"],
        ["get-lesson", "--lesson-id", "test_id"],  # Will likely fail
    ],
    "Generic CRUD Commands": [
        ["generic", "list", "glossary", "--output", "json"],
        ["generic", "list", "glossary", "--output", "table"],
        ["generic", "create", "test_collection", '{"name": "test", "type": "testing"}', "--output", "json"],
    ],
    "Episode Commands": [
        ["episode", "list"],
        ["episode", "create", "--user-message", "test user", "--agent-message", "test agent", "--summary", "test summary"],
    ],
    "Graph Commands": [
        ["graph", "traverse", "--lesson-id", "test_id"],
        ["graph", "add-relationship", "--from-id", "id1", "--to-id", "id2", "--relationship-type", "related_to"],
    ],
    "Community Commands": [
        ["community", "list"],
        ["community", "detect"],
    ],
    "Contradiction Commands": [
        ["contradiction", "list"],
        ["contradiction", "check", "--entity-id", "test_entity"],
    ],
    "Search Config Commands": [
        ["search-config", "list"],
        ["search-config", "analyze", "--query", "test query"],
    ],
    "Compaction Commands": [
        ["compaction", "list"],
        ["compaction", "create", "--content", "test content"],
    ]
}

def run_command(command: List[str]) -> Tuple[int, str, str]:
    """Run a CLI command and capture output"""
    full_command = ["python", "-m", "arangodb.cli"] + command
    
    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out after 30 seconds"
    except Exception as e:
        return -1, "", str(e)

def validate_json_output(output: str) -> bool:
    """Validate that output is valid JSON"""
    try:
        json.loads(output)
        return True
    except:
        return False

def main():
    print("Task 025: CLI Command Validation")
    print("=" * 40)
    
    all_results = {}
    total_commands = sum(len(commands) for commands in COMMAND_GROUPS.values())
    passed = 0
    failed = 0
    
    for group_name, commands in COMMAND_GROUPS.items():
        print(f"\n\n## {group_name}")
        print("-" * 20)
        
        group_results = []
        
        for command in commands:
            command_str = " ".join(command)
            print(f"\nTesting: {command_str}")
            
            returncode, stdout, stderr = run_command(command)
            
            # Check if command has --output json
            has_json_output = "--output" in command and "json" in command
            
            # Validate results
            status = "PASS" if returncode == 0 else "FAIL"
            
            # Additional JSON validation if expected
            json_valid = "N/A"
            if has_json_output and stdout:
                json_valid = "VALID" if validate_json_output(stdout) else "INVALID"
            
            if status == "PASS":
                passed += 1
            else:
                failed += 1
            
            result = {
                "command": command_str,
                "status": status,
                "returncode": returncode,
                "json_valid": json_valid,
                "stdout_length": len(stdout),
                "stderr_length": len(stderr),
                "stdout_preview": stdout[:200] + "..." if len(stdout) > 200 else stdout,
                "stderr_preview": stderr[:200] + "..." if len(stderr) > 200 else stderr,
            }
            
            group_results.append(result)
            
            # Print summary
            print(f"  Status: {status}")
            print(f"  Return Code: {returncode}")
            if has_json_output:
                print(f"  JSON Valid: {json_valid}")
            if stdout:
                print(f"  Output Length: {len(stdout)} chars")
            if stderr:
                print(f"  Error: {stderr[:100]}...")
        
        all_results[group_name] = group_results
    
    # Generate final report
    print("\n\n# FINAL VALIDATION REPORT")
    print("=" * 40)
    print(f"Total Commands Tested: {total_commands}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/total_commands*100:.1f}%")
    
    # Save results to JSON
    with open("cli_validation_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\nDetailed results saved to: cli_validation_results.json")
    
    # Create a summary for the report
    print("\n\n# DETAILED RESULTS BY GROUP")
    print("=" * 40)
    
    for group_name, results in all_results.items():
        print(f"\n## {group_name}")
        for result in results:
            print(f"\n### Command: {result['command']}")
            print(f"Status: {result['status']}")
            
            if result['stdout_preview']:
                print("\n#### Output:")
                print("```")
                print(result['stdout_preview'])
                print("```")
            
            if result['stderr_preview']:
                print("\n#### Error:")
                print("```")
                print(result['stderr_preview'])
                print("```")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())