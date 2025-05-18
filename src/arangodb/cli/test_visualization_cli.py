"""Test script for visualization CLI integration

This script tests the visualization CLI commands.

Sample input: Test commands
Expected output: HTML visualizations
"""

import json
import sys
from pathlib import Path
import tempfile
from typer.testing import CliRunner
from loguru import logger

# Import the main CLI app - use absolute import
from arangodb.cli.main import app

# Initialize test runner
runner = CliRunner()

def test_visualization_cli():
    """Test visualization CLI commands"""
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Help command
    total_tests += 1
    try:
        result = runner.invoke(app, ["visualize", "--help"])
        if result.exit_code != 0:
            all_validation_failures.append(f"Help command: Exit code {result.exit_code}")
        if "visualiz" not in result.output.lower():
            all_validation_failures.append("Help command: Missing expected help text")
            logger.info(f"Help output: {result.output}")
        logger.info("Help command test completed")
    except Exception as e:
        all_validation_failures.append(f"Help command: Failed with error {e}")
    
    # Test 2: Layouts command
    total_tests += 1
    try:
        result = runner.invoke(app, ["visualize", "layouts"])
        if result.exit_code != 0:
            all_validation_failures.append(f"Layouts command: Exit code {result.exit_code}")
        if "force" not in result.output or "tree" not in result.output:
            all_validation_failures.append("Layouts command: Missing layout types")
        logger.info("Layouts command test completed")
    except Exception as e:
        all_validation_failures.append(f"Layouts command: Failed with error {e}")
    
    # Test 3: Examples command
    total_tests += 1
    try:
        result = runner.invoke(app, ["visualize", "examples"])
        if result.exit_code != 0:
            all_validation_failures.append(f"Examples command: Exit code {result.exit_code}")
        if "query" not in result.output.lower() and "example" not in result.output.lower():
            all_validation_failures.append("Examples command: Missing example queries")
            logger.info(f"Examples output: {result.output}")
        logger.info("Examples command test completed")
    except Exception as e:
        all_validation_failures.append(f"Examples command: Failed with error {e}")
    
    # Test 4: From file command
    total_tests += 1
    try:
        # Create test file
        test_data = {
            "nodes": [
                {"id": "1", "name": "Test Node 1"},
                {"id": "2", "name": "Test Node 2"}
            ],
            "links": [
                {"source": "1", "target": "2"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            test_file = Path(f.name)
        
        result = runner.invoke(app, [
            "visualize", "from-file", 
            str(test_file),
            "--no-open-browser",
            "--no-use-llm"
        ])
        
        if result.exit_code != 0:
            all_validation_failures.append(f"From file command: Exit code {result.exit_code}")
            if result.exception:
                logger.error(f"Exception: {result.exception}")
            logger.error(f"Output: {result.output}")
            logger.error(f"Stderr: {result.stderr if hasattr(result, 'stderr') else 'N/A'}")
        
        # Clean up
        test_file.unlink()
        output_file = test_file.with_suffix('.html')
        if output_file.exists():
            output_file.unlink()
        
        logger.info("From file command test completed")
    except Exception as e:
        all_validation_failures.append(f"From file command: Failed with error {e}")
    
    # Test 5: Generate command (mock)
    total_tests += 1
    try:
        # This would require a database connection, so we just test the help
        result = runner.invoke(app, ["visualize", "generate", "--help"])
        if result.exit_code != 0:
            all_validation_failures.append(f"Generate help: Exit code {result.exit_code}")
        if "AQL query" not in result.output:
            all_validation_failures.append("Generate help: Missing query parameter")
        logger.info("Generate command help test completed")
    except Exception as e:
        all_validation_failures.append(f"Generate help: Failed with error {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        return False
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Visualization CLI integration is working correctly")
        return True

def main():
    """Main test function"""
    logger.add("visualization_cli_test.log", rotation="10 MB")
    logger.info("Starting visualization CLI tests")
    
    success = test_visualization_cli()
    
    if success:
        print("\nVisualization commands are now available in the CLI:")
        print("  arangodb visualize layouts       - List available layouts")
        print("  arangodb visualize examples      - Show example queries")
        print("  arangodb visualize from-file     - Generate from JSON file")
        print("  arangodb visualize generate      - Generate from AQL query")
        print("  arangodb visualize server        - Send to visualization server")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()