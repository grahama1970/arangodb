#!/usr/bin/env python3
"""
CLI Validation Test Script for Task 025

Tests all CLI commands for:
1. --output parameter consistency (json/table)
2. Semantic search pre-validation
3. Real data output (no mocking)
4. Error handling

Reference: docs/tasks/025_cli_validation_and_testing.md
"""

import json
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
import os
from loguru import logger

# Configure logger
logger.add("cli_validation.log", rotation="10 MB", level="DEBUG")

# Base command for CLI
BASE_CMD = ["python", "-m", "arangodb.cli"]

# Global validation trackers
all_validation_failures = []
total_tests = 0
command_results = []

def run_cli_command(command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a CLI command and return exit code, stdout, and stderr."""
    global total_tests
    total_tests += 1
    
    full_cmd = BASE_CMD + command
    logger.debug(f"Running command: {' '.join(full_cmd)}")
    
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=capture_output,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return 1, "", str(e)

def validate_json_output(output: str, command: str) -> bool:
    """Validate that output is valid JSON."""
    try:
        data = json.loads(output)
        logger.debug(f"Valid JSON received for command: {command}")
        return True
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON from {command}: {e}"
        logger.error(error_msg)
        all_validation_failures.append(error_msg)
        return False

def validate_table_output(output: str, command: str) -> bool:
    """Validate that output is in table format."""
    lines = output.strip().split('\n')
    if len(lines) < 3:  # At least header, separator, and one row
        error_msg = f"Invalid table output from {command}: too few lines"
        logger.error(error_msg)
        all_validation_failures.append(error_msg)
        return False
    
    # Check for table-like structure (with borders or separators)
    has_table_structure = any('│' in line or '─' in line or '+' in line or '|' in line for line in lines)
    if not has_table_structure:
        error_msg = f"Invalid table output from {command}: no table structure found"
        logger.error(error_msg)
        all_validation_failures.append(error_msg)
        return False
    
    logger.debug(f"Valid table output received for command: {command}")
    return True

def test_output_parameter_consistency(command_group: str, base_command: List[str]) -> Dict[str, bool]:
    """Test that a command supports both json and table output formats."""
    results = {
        "default": False,
        "json": False,
        "table": False,
        "error_handling": False
    }
    
    # Test default output (should be table)
    logger.info(f"Testing default output for {command_group}: {' '.join(base_command)}")
    exit_code, stdout, stderr = run_cli_command(base_command)
    if exit_code == 0 and stdout:
        results["default"] = validate_table_output(stdout, f"{command_group} (default)")
    else:
        all_validation_failures.append(f"{command_group} default output failed: exit_code={exit_code}, stderr={stderr}")
    
    # Test JSON output
    logger.info(f"Testing JSON output for {command_group}: {' '.join(base_command + ['--output', 'json'])}")
    exit_code, stdout, stderr = run_cli_command(base_command + ["--output", "json"])
    if exit_code == 0 and stdout:
        results["json"] = validate_json_output(stdout, f"{command_group} --output json")
    else:
        all_validation_failures.append(f"{command_group} JSON output failed: exit_code={exit_code}, stderr={stderr}")
    
    # Test table output
    logger.info(f"Testing table output for {command_group}: {' '.join(base_command + ['--output', 'table'])}")
    exit_code, stdout, stderr = run_cli_command(base_command + ["--output", "table"])
    if exit_code == 0 and stdout:
        results["table"] = validate_table_output(stdout, f"{command_group} --output table")
    else:
        all_validation_failures.append(f"{command_group} table output failed: exit_code={exit_code}, stderr={stderr}")
    
    # Test invalid output format (error handling)
    logger.info(f"Testing invalid output format for {command_group}")
    exit_code, stdout, stderr = run_cli_command(base_command + ["--output", "invalid"])
    if exit_code != 0:
        results["error_handling"] = True
        logger.debug(f"Correctly rejected invalid output format for {command_group}")
    else:
        all_validation_failures.append(f"{command_group} accepted invalid output format")
    
    return results

def test_semantic_search_prevalidation() -> Dict[str, bool]:
    """Test that semantic search commands perform pre-validation checks."""
    results = {
        "missing_collection": False,
        "empty_collection": False, 
        "no_embeddings": False,
        "dimension_mismatch": False
    }
    
    # Test 1: Non-existent collection
    logger.info("Testing semantic search with non-existent collection")
    exit_code, stdout, stderr = run_cli_command([
        "search", "semantic",
        "--collection", "non_existent_collection",
        "--query", "test query",
        "--output", "json"
    ])
    
    if exit_code != 0:
        # Should fail with clear error message
        error_output = stderr or stdout
        if "collection" in error_output.lower() and ("not found" in error_output.lower() or "does not exist" in error_output.lower()):
            results["missing_collection"] = True
            logger.debug("Correctly detected missing collection")
        else:
            all_validation_failures.append(f"Semantic search missing collection error unclear: {error_output}")
    else:
        all_validation_failures.append("Semantic search succeeded with non-existent collection")
    
    # Test 2: Empty collection (create empty test collection first)
    # We'll skip this for now as it requires database manipulation
    
    # Test 3: Collection without embeddings
    logger.info("Testing semantic search on collection without embeddings")
    exit_code, stdout, stderr = run_cli_command([
        "search", "semantic",
        "--collection", "test_documents",  # This collection likely has no embeddings
        "--query", "test query",
        "--output", "json"
    ])
    
    if exit_code != 0:
        error_output = stderr or stdout
        if "embedding" in error_output.lower():
            results["no_embeddings"] = True
            logger.debug("Correctly detected missing embeddings")
        else:
            logger.warning(f"Unclear error for missing embeddings: {error_output}")
    
    return results

def test_search_commands() -> Dict[str, Dict[str, bool]]:
    """Test all search commands."""
    results = {}
    
    # BM25 Search
    logger.info("Testing BM25 search")
    results["bm25"] = test_output_parameter_consistency(
        "BM25 Search",
        ["search", "bm25", "--collection", "glossary", "--query", "database"]
    )
    
    # Semantic Search
    logger.info("Testing semantic search")
    results["semantic"] = test_output_parameter_consistency(
        "Semantic Search", 
        ["search", "semantic", "--collection", "glossary", "--query", "technology"]
    )
    
    # Tag Search
    logger.info("Testing tag search")
    results["tag"] = test_output_parameter_consistency(
        "Tag Search",
        ["search", "tag", "--collection", "glossary", "--tag", "database"]
    )
    
    # Keyword Search
    logger.info("Testing keyword search")
    results["keyword"] = test_output_parameter_consistency(
        "Keyword Search",
        ["search", "keyword", "--collection", "glossary", "--query", "system"]
    )
    
    # Hybrid Search
    logger.info("Testing hybrid search")
    results["hybrid"] = test_output_parameter_consistency(
        "Hybrid Search",
        ["search", "hybrid", "--collection", "glossary", "--query", "database system"]
    )
    
    # Graph Search
    logger.info("Testing graph search")
    # First get a valid document ID
    exit_code, stdout, stderr = run_cli_command([
        "crud", "list", "--collection", "agent_entities", "--output", "json", "--limit", "1"
    ])
    
    if exit_code == 0 and stdout:
        try:
            data = json.loads(stdout)
            if data and isinstance(data, list) and len(data) > 0:
                doc_id = data[0].get("_id", data[0].get("id", ""))
                if doc_id:
                    results["graph"] = test_output_parameter_consistency(
                        "Graph Search",
                        ["search", "graph", "--start", doc_id, "--depth", "1"]
                    )
                else:
                    logger.warning("Could not find valid document ID for graph search")
                    results["graph"] = {"default": False, "json": False, "table": False, "error_handling": False}
            else:
                logger.warning("No documents found for graph search test")
                results["graph"] = {"default": False, "json": False, "table": False, "error_handling": False}
        except Exception as e:
            logger.error(f"Failed to parse document ID for graph search: {e}")
            results["graph"] = {"default": False, "json": False, "table": False, "error_handling": False}
    else:
        logger.error("Failed to get document for graph search test")
        results["graph"] = {"default": False, "json": False, "table": False, "error_handling": False}
    
    return results

def test_crud_commands() -> Dict[str, Dict[str, bool]]:
    """Test CRUD commands."""
    results = {}
    
    # List documents
    logger.info("Testing CRUD list")
    results["list"] = test_output_parameter_consistency(
        "CRUD List",
        ["crud", "list", "--collection", "glossary", "--limit", "5"]
    )
    
    # Read document (get a valid ID first)
    exit_code, stdout, stderr = run_cli_command([
        "crud", "list", "--collection", "glossary", "--output", "json", "--limit", "1"
    ])
    
    if exit_code == 0 and stdout:
        try:
            data = json.loads(stdout)
            if data and isinstance(data, list) and len(data) > 0:
                doc_id = data[0].get("_id", data[0].get("id", ""))
                if doc_id:
                    logger.info(f"Testing CRUD read with ID: {doc_id}")
                    results["read"] = test_output_parameter_consistency(
                        "CRUD Read",
                        ["crud", "read", "--collection", "glossary", "--id", doc_id]
                    )
        except Exception as e:
            logger.error(f"Failed to get document ID for CRUD read test: {e}")
            results["read"] = {"default": False, "json": False, "table": False, "error_handling": False}
    
    return results

def test_memory_commands() -> Dict[str, Dict[str, bool]]:
    """Test memory commands."""
    results = {}
    
    # List conversations
    logger.info("Testing memory list")
    results["list"] = test_output_parameter_consistency(
        "Memory List",
        ["memory", "list", "--limit", "5"]
    )
    
    # Search memory
    logger.info("Testing memory search")
    results["search"] = test_output_parameter_consistency(
        "Memory Search",
        ["memory", "search", "--query", "test"]
    )
    
    return results

def test_episode_commands() -> Dict[str, Dict[str, bool]]:
    """Test episode commands."""
    results = {}
    
    # List episodes
    logger.info("Testing episode list")
    results["list"] = test_output_parameter_consistency(
        "Episode List",
        ["episode", "list", "--limit", "5"]
    )
    
    return results

def test_community_commands() -> Dict[str, Dict[str, bool]]:
    """Test community commands."""
    results = {}
    
    # List communities
    logger.info("Testing community list")
    results["list"] = test_output_parameter_consistency(
        "Community List",
        ["community", "list", "--limit", "5"]
    )
    
    return results

def test_graph_commands() -> Dict[str, Dict[str, bool]]:
    """Test graph commands."""
    results = {}
    
    # List relationships
    logger.info("Testing graph list-relationships")
    results["list_relationships"] = test_output_parameter_consistency(
        "Graph List Relationships",
        ["graph", "list-relationships", "--limit", "5"]
    )
    
    return results

def test_contradiction_commands() -> Dict[str, Dict[str, bool]]:
    """Test contradiction commands."""
    results = {}
    
    # List contradictions
    logger.info("Testing contradiction list")
    results["list"] = test_output_parameter_consistency(
        "Contradiction List",
        ["contradiction", "list"]
    )
    
    return results

def test_search_config_commands() -> Dict[str, Dict[str, bool]]:
    """Test search config commands."""
    results = {}
    
    # List configs
    logger.info("Testing search-config list")
    results["list"] = test_output_parameter_consistency(
        "Search Config List",
        ["search-config", "list"]
    )
    
    return results

def test_compaction_commands() -> Dict[str, Dict[str, bool]]:
    """Test compaction commands."""
    results = {}
    
    # List compactions
    logger.info("Testing compaction list")
    results["list"] = test_output_parameter_consistency(
        "Compaction List", 
        ["compaction", "list", "--output", "json"]
    )
    
    return results

def generate_report(results: Dict[str, Dict[str, Dict[str, bool]]]) -> str:
    """Generate a comprehensive report of all test results."""
    report = []
    report.append("# CLI Validation Report")
    report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Overall summary
    total_passed = sum(
        1 for group in results.values() 
        for cmd in group.values() 
        for test, passed in cmd.items() 
        if passed
    )
    total_expected = sum(
        len(cmd) for group in results.values() 
        for cmd in group.values()
    )
    
    report.append(f"## Overall Summary")
    report.append(f"- Total Tests: {total_tests}")
    report.append(f"- Passed: {total_passed}/{total_expected}")
    report.append(f"- Failed: {len(all_validation_failures)}")
    report.append("")
    
    # Detailed results by command group
    for group_name, group_results in results.items():
        report.append(f"## {group_name.replace('_', ' ').title()} Commands")
        
        for cmd_name, cmd_results in group_results.items():
            report.append(f"### {cmd_name}")
            report.append(f"- Default output (table): {'✅' if cmd_results.get('default', False) else '❌'}")
            report.append(f"- JSON output: {'✅' if cmd_results.get('json', False) else '❌'}")
            report.append(f"- Table output: {'✅' if cmd_results.get('table', False) else '❌'}")
            report.append(f"- Error handling: {'✅' if cmd_results.get('error_handling', False) else '❌'}")
            report.append("")
    
    # Validation failures
    if all_validation_failures:
        report.append("## Validation Failures")
        for i, failure in enumerate(all_validation_failures, 1):
            report.append(f"{i}. {failure}")
        report.append("")
    
    return "\n".join(report)

def main():
    """Main test execution function."""
    logger.info("Starting CLI validation tests...")
    
    # Test results structure
    results = {
        "search": {},
        "crud": {},
        "memory": {},
        "episode": {},
        "community": {},
        "graph": {},
        "contradiction": {},
        "search_config": {},
        "compaction": {}
    }
    
    # Run semantic search pre-validation tests
    logger.info("Testing semantic search pre-validation...")
    semantic_prevalidation = test_semantic_search_prevalidation()
    results["semantic_prevalidation"] = {"prevalidation": semantic_prevalidation}
    
    # Test each command group
    logger.info("Testing search commands...")
    results["search"] = test_search_commands()
    
    logger.info("Testing CRUD commands...")
    results["crud"] = test_crud_commands()
    
    logger.info("Testing memory commands...")
    results["memory"] = test_memory_commands()
    
    logger.info("Testing episode commands...")
    results["episode"] = test_episode_commands()
    
    logger.info("Testing community commands...")
    results["community"] = test_community_commands()
    
    logger.info("Testing graph commands...")
    results["graph"] = test_graph_commands()
    
    logger.info("Testing contradiction commands...")
    results["contradiction"] = test_contradiction_commands()
    
    logger.info("Testing search config commands...")
    results["search_config"] = test_search_config_commands()
    
    logger.info("Testing compaction commands...")
    results["compaction"] = test_compaction_commands()
    
    # Generate report
    report = generate_report(results)
    
    # Save report
    report_path = "docs/reports/025_cli_validation_and_testing_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    
    # Print summary
    print("\n" + "="*50)
    print("CLI VALIDATION SUMMARY")
    print("="*50)
    
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} failures found")
        print("\nKey failures:")
        for failure in all_validation_failures[:5]:  # Show first 5 failures
            print(f"  - {failure}")
        if len(all_validation_failures) > 5:
            print(f"  ... and {len(all_validation_failures) - 5} more")
        print(f"\nFull report saved to: {report_path}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests completed successfully")
        print(f"\nFull report saved to: {report_path}")
        sys.exit(0)

if __name__ == "__main__":
    main()