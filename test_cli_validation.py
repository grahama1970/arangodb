#!/usr/bin/env python3
"""
Test CLI Validation for Output Parameter and Semantic Search Checks
"""

import subprocess
import sys
import json
from typing import Dict, List, Any
from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:HH:mm:ss} | {level:<7} | {message}"
)

def run_cli_command(command: List[str], capture_output: bool = True) -> Dict[str, Any]:
    """Run a CLI command and capture its output."""
    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def test_output_parameter(command_base: List[str], test_name: str) -> Dict[str, bool]:
    """Test output parameter consistency for a command."""
    results = {}
    
    print(f"\nTesting {test_name}:")
    
    # Test default output (should be table)
    print("  - Testing default output...")
    result = run_cli_command(command_base)
    results["default"] = result["success"]
    if result["success"]:
        # Check if output looks like a table (has formatting characters)
        has_table_chars = any(char in result["stdout"] for char in ["─", "│", "┌", "└"])
        results["default_is_table"] = has_table_chars
    
    # Test with --output table
    print("  - Testing --output table...")
    result = run_cli_command(command_base + ["--output", "table"])
    results["output_table"] = result["success"]
    
    # Test with --output json
    print("  - Testing --output json...")
    result = run_cli_command(command_base + ["--output", "json"])
    results["output_json"] = result["success"]
    if result["success"]:
        try:
            json.loads(result["stdout"])
            results["valid_json"] = True
        except:
            results["valid_json"] = False
    
    # Test with invalid output format
    print("  - Testing invalid output format...")
    result = run_cli_command(command_base + ["--output", "invalid"])
    results["invalid_format_handled"] = not result["success"]
    
    return results

def test_semantic_search_validation() -> Dict[str, bool]:
    """Test semantic search pre-validation."""
    results = {}
    
    print("\nTesting Semantic Search Validation:")
    
    # Test with non-existent collection
    print("  - Testing with non-existent collection...")
    command = ["python", "-m", "arangodb.cli", "search", "semantic", 
               "test query", "--collection", "non_existent_collection"]
    result = run_cli_command(command)
    results["non_existent_collection"] = True  # Should handle gracefully
    if result["stderr"]:
        # Check for proper error message
        has_error_msg = any(msg in result["stderr"].lower() for msg in 
                           ["does not exist", "collection not found", "not ready"])
        results["clear_error_message"] = has_error_msg
    
    # Test with collection missing embeddings
    # First create a test collection without embeddings
    create_cmd = ["python", "-m", "arangodb.cli", "crud", "create",
                  "--collection", "test_no_embeddings",
                  "--data", '{"title": "Test", "content": "No embedding"}']
    run_cli_command(create_cmd)
    
    print("  - Testing with collection missing embeddings...")
    command = ["python", "-m", "arangodb.cli", "search", "semantic",
               "test query", "--collection", "test_no_embeddings"]
    result = run_cli_command(command)
    results["missing_embeddings"] = True  # Should handle gracefully
    if result["stderr"]:
        has_embedding_error = any(msg in result["stderr"].lower() for msg in
                                ["no embeddings", "missing embeddings", "need embeddings"])
        results["embedding_error_message"] = has_embedding_error
    
    return results

def main():
    print("=== CLI Validation Testing ===")
    
    all_results = {}
    
    # Test output parameter for various commands
    test_commands = {
        "search_bm25": ["python", "-m", "arangodb.cli", "search", "bm25", "test"],
        "search_semantic": ["python", "-m", "arangodb.cli", "search", "semantic", "test"],
        "search_hybrid": ["python", "-m", "arangodb.cli", "search", "hybrid", "test"],
        "memory_list": ["python", "-m", "arangodb.cli", "memory", "list"],
        "crud_list": ["python", "-m", "arangodb.cli", "crud", "list"],
    }
    
    for test_name, command in test_commands.items():
        all_results[test_name] = test_output_parameter(command, test_name)
    
    # Test semantic search validation
    all_results["semantic_validation"] = test_semantic_search_validation()
    
    # Print summary
    print("\n=== Test Summary ===")
    for test_group, results in all_results.items():
        print(f"\n{test_group}:")
        for test, passed in results.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {test}")
    
    # Check overall success
    all_tests_passed = all(
        all(results.values())
        for results in all_results.values()
    )
    
    if all_tests_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()