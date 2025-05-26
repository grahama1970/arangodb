"""
Validation script for validate_memory_commands.py module

This script tests the validation module itself, which is designed
to check memory commands functionality.
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# For rich table display
from rich.console import Console
from rich.table import Table

console = Console()


def test_validation_script():
    """Test the validate_memory_commands.py script"""
    logger.info("Testing VALIDATION SCRIPT EXECUTION")
    
    try:
        # Run the validation script as a subprocess
        validation_script = Path(__file__).parent.parent / "cli" / "validate_memory_commands.py"
        
        if not validation_script.exists():
            return False, f"Validation script not found at {validation_script}"
        
        # Run with Python interpreter
        result = subprocess.run(
            [sys.executable, str(validation_script)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check exit code
        if result.returncode != 0:
            return False, f"Script exited with code {result.returncode}: {result.stderr}"
        
        # Check output for expected validation results
        output = result.stdout
        if "memory_app is properly defined" not in output:
            return False, "Missing expected validation output"
        
        logger.info("Validation script executed successfully")
        return True, output
        
    except subprocess.TimeoutExpired:
        return False, "Script execution timed out after 30 seconds"
    except Exception as e:
        return False, f"Script execution failed: {str(e)}"


def test_module_imports():
    """Test if the module can be imported"""
    logger.info("Testing MODULE IMPORTS")
    
    try:
        # Import the validation module directly
        from arangodb.cli import validate_memory_commands
        
        # Check for expected functions/classes
        if not hasattr(validate_memory_commands, 'validate_with_rich_setting'):
            return False, "Missing validate_with_rich_setting function"
        
        if not hasattr(validate_memory_commands, 'MockStandardDatabase'):
            return False, "Missing MockStandardDatabase class"
        
        logger.info("Module imports successful")
        return True, "All expected components found"
        
    except ImportError as e:
        return False, f"Import failed: {str(e)}"
    except Exception as e:
        return False, f"Module test failed: {str(e)}"


def test_mock_functionality():
    """Test if the mocking functionality works"""
    logger.info("Testing MOCK FUNCTIONALITY")
    
    try:
        from arangodb.cli.validate_memory_commands import MockStandardDatabase
        
        # Create mock database
        mock_db = MockStandardDatabase()
        
        # Test basic methods
        if not hasattr(mock_db, 'collection'):
            return False, "MockStandardDatabase missing collection method"
        
        if not hasattr(mock_db, 'aql'):
            return False, "MockStandardDatabase missing aql method"
        
        # Test method calls
        collection = mock_db.collection('test')
        if collection is None:
            return False, "collection method returned None"
        
        logger.info("Mock functionality working correctly")
        return True, "Mock methods work as expected"
        
    except Exception as e:
        return False, f"Mock test failed: {str(e)}"


def test_validation_scenarios():
    """Test both Rich available and unavailable scenarios"""
    logger.info("Testing VALIDATION SCENARIOS")
    
    try:
        from arangodb.cli.validate_memory_commands import validate_with_rich_setting
        
        results = []
        
        # Test with Rich available
        logger.info("Testing with Rich available...")
        try:
            validate_with_rich_setting(True)
            results.append(("With Rich", True, "Validation passed"))
        except Exception as e:
            results.append(("With Rich", False, str(e)))
        
        # Test without Rich
        logger.info("Testing without Rich...")
        try:
            validate_with_rich_setting(False)
            results.append(("Without Rich", True, "Validation passed"))
        except Exception as e:
            results.append(("Without Rich", False, str(e)))
        
        # Check if both scenarios passed
        all_passed = all(status for _, status, _ in results)
        
        if all_passed:
            return True, results
        else:
            return False, results
            
    except Exception as e:
        return False, f"Scenario test failed: {str(e)}"


def display_results_table(results):
    """Display results in a rich table format"""
    table = Table(title="Validate Memory Commands Validation Results")
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
                "test": test,
                "status": "passed" if status else "failed",
                "details": str(details)
            }
            for test, status, details in results
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
    
    logger.info("Starting validate_memory_commands.py validation")
    
    # Test 1: Script execution
    success, result = test_validation_script()
    results.append(("SCRIPT EXECUTION", success, result))
    
    # Test 2: Module imports
    success, result = test_module_imports()
    results.append(("MODULE IMPORTS", success, result))
    
    # Test 3: Mock functionality
    success, result = test_mock_functionality()
    results.append(("MOCK FUNCTIONALITY", success, result))
    
    # Test 4: Validation scenarios
    success, result = test_validation_scenarios()
    if isinstance(result, list):
        # Add each scenario as separate result
        for scenario_name, scenario_status, scenario_detail in result:
            results.append((f"SCENARIO: {scenario_name}", scenario_status, scenario_detail))
    else:
        results.append(("VALIDATION SCENARIOS", success, result))
    
    # Display results in both formats
    console.print("\n[bold]Table Format:[/bold]")
    display_results_table(results)
    
    console.print("\n[bold]JSON Format:[/bold]")
    display_results_json(results)
    
    # Final result
    failures = [r for r in results if not r[1]]
    if failures:
        console.print(f"\n❌ VALIDATION FAILED - {len(failures)} of {len(results)} tests failed")
        for test, _, details in failures:
            console.print(f"  - {test}: {details}")
        sys.exit(1)
    else:
        console.print(f"\n✅ VALIDATION PASSED - All {len(results)} tests produced expected results")
        console.print("validate_memory_commands.py is working correctly")
        sys.exit(0)