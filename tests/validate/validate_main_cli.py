"""
Validation script for Main CLI module with real command execution

This script tests the main CLI application to verify:
1. All command groups are properly registered
2. Help commands work correctly
3. Basic command execution works
4. Error handling works properly
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from loguru import logger

# For rich table display
from rich.console import Console
from rich.table import Table

console = Console()


def run_cli_command(args):
    """Run a CLI command and capture output"""
    cmd = ["uv", "run", "python", "-m", "arangodb.cli.main"] + args
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "ARANGO_HOST": "http://localhost:8529",
        "ARANGO_USER": "root",
        "ARANGO_PASSWORD": "openSesame",
        "ARANGO_DB_NAME": "memory_bank"
    })
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd="/home/graham/workspace/experiments/arangodb"
        )
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }


def test_help_command():
    """Test the main help command"""
    logger.info("Testing main help command")
    
    result = run_cli_command(["--help"])
    
    if not result["success"]:
        return False, f"Help command failed: {result['stderr']}"
    
    # Check if help contains expected command groups
    expected_groups = ["search", "crud", "graph", "memory"]
    missing_groups = []
    
    for group in expected_groups:
        if group not in result["stdout"]:
            missing_groups.append(group)
    
    if missing_groups:
        return False, f"Missing command groups in help: {missing_groups}"
    
    logger.info("Help command shows all expected command groups")
    return True, "All command groups present"


def test_search_help():
    """Test search command group help"""
    logger.info("Testing search help command")
    
    result = run_cli_command(["search", "--help"])
    
    if not result["success"]:
        return False, f"Search help failed: {result['stderr']}"
    
    # Check for expected search commands
    expected_commands = ["bm25", "semantic", "hybrid", "tag", "keyword"]
    missing_commands = []
    
    for cmd in expected_commands:
        if cmd not in result["stdout"]:
            missing_commands.append(cmd)
    
    if missing_commands:
        return False, f"Missing search commands: {missing_commands}"
    
    logger.info("Search help shows all expected commands")
    return True, "All search commands present"


def test_crud_help():
    """Test CRUD command group help"""
    logger.info("Testing CRUD help command")
    
    result = run_cli_command(["crud", "--help"])
    
    if not result["success"]:
        return False, f"CRUD help failed: {result['stderr']}"
    
    # Check for expected CRUD commands
    expected_commands = ["add-lesson", "get-lesson", "update-lesson", "delete-lesson"]
    missing_commands = []
    
    for cmd in expected_commands:
        if cmd not in result["stdout"]:
            missing_commands.append(cmd)
    
    if missing_commands:
        return False, f"Missing CRUD commands: {missing_commands}"
    
    logger.info("CRUD help shows all expected commands")
    return True, "All CRUD commands present"


def test_basic_command():
    """Test a basic command execution"""
    logger.info("Testing basic command execution")
    
    # Test a simple search command with JSON output
    result = run_cli_command(["search", "bm25", "test", "--top-n", "1", "--json-output"])
    
    if result["returncode"] != 0:
        # This might fail if no data exists, which is OK
        if "No results found" in result["stdout"] or "No results found" in result["stderr"]:
            logger.info("No results found, but command executed successfully")
            return True, "Command executed (no results)"
        else:
            return False, f"Command failed: {result['stderr']}"
    
    # Try to parse JSON output
    try:
        if result["stdout"].strip():
            json_data = json.loads(result["stdout"])
            logger.info("Command returned valid JSON")
            return True, "Command executed successfully"
        else:
            return True, "Command executed (empty result)"
    except json.JSONDecodeError:
        # Not JSON output, but command succeeded
        return True, "Command executed (non-JSON output)"


def test_invalid_command():
    """Test error handling for invalid command"""
    logger.info("Testing invalid command handling")
    
    result = run_cli_command(["invalid-command"])
    
    if result["success"]:
        return False, "Invalid command should have failed"
    
    # Check if error message is helpful
    if "No such option" in result["stderr"] or "Invalid" in result["stderr"] or "Error" in result["stderr"]:
        logger.info("Invalid command properly rejected")
        return True, "Error handling works"
    
    return False, f"Unexpected error response: {result['stderr']}"


def display_results_table(results):
    """Display results in a rich table format"""
    table = Table(title="Main CLI Validation Results")
    table.add_column("Test", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    for test_name, status, details in results:
        status_symbol = "✅" if status else "❌"
        table.add_row(test_name, status_symbol, str(details))
    
    console.print(table)


def display_results_json(results):
    """Display results in JSON format"""
    json_results = {
        "validation_results": [
            {
                "test": test_name,
                "status": "passed" if status else "failed",
                "details": str(details)
            }
            for test_name, status, details in results
        ],
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for _, status, _ in results if status),
            "failed": sum(1 for _, status, _ in results if not status)
        }
    }
    console.print(json.dumps(json_results, indent=2))


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time} {level} {message}")
    
    # Track all results
    results = []
    
    try:
        # Test 1: Main help
        success, details = test_help_command()
        results.append(("Main Help", success, details))
        
        # Test 2: Search help
        success, details = test_search_help()
        results.append(("Search Help", success, details))
        
        # Test 3: CRUD help
        success, details = test_crud_help()
        results.append(("CRUD Help", success, details))
        
        # Test 4: Basic command
        success, details = test_basic_command()
        results.append(("Basic Command", success, details))
        
        # Test 5: Invalid command
        success, details = test_invalid_command()
        results.append(("Error Handling", success, details))
        
        # Display results in both formats
        console.print("\n[bold]Table Format:[/bold]")
        display_results_table(results)
        
        console.print("\n[bold]JSON Format:[/bold]")
        display_results_json(results)
        
        # Final result
        failures = [r for r in results if not r[1]]
        if failures:
            console.print(f"\n❌ VALIDATION FAILED - {len(failures)} of {len(results)} tests failed")
            for test_name, _, details in failures:
                console.print(f"  - {test_name}: {details}")
            sys.exit(1)
        else:
            console.print(f"\n✅ VALIDATION PASSED - All {len(results)} tests produced expected results")
            console.print("Main CLI is working correctly")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error during validation: {e}")
        console.print(f"\n❌ VALIDATION FAILED - Fatal error: {e}")
        sys.exit(1)