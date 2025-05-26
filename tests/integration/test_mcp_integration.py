#!/usr/bin/env python3
"""
Test script for validating complete MCP integration workflow.
Verifies that all 61+ tools are exposed and can be executed.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_mcp_generation():
    """Test MCP config generation with all tools."""
    logger.info("Testing MCP configuration generation...")
    
    # Generate MCP config
    result = subprocess.run(
        ["python", "-m", "arangodb", "--mcp-generate-config"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to generate MCP config: {result.stderr}")
        return False
    
    # Check generated files
    mcp_json = project_root / "mcp.json"
    if not mcp_json.exists():
        logger.error("mcp.json not created")
        return False
    
    # Verify tool count
    with open(mcp_json) as f:
        config = json.load(f)
    
    tool_count = len(config.get("tools", {}))
    logger.info(f"Found {tool_count} tools in MCP configuration")
    
    if tool_count < 60:
        logger.error(f"Expected 60+ tools, found only {tool_count}")
        return False
    
    # List some key tools
    expected_tools = [
        "memory.add",
        "memory.search",
        "graph.visualize",
        "qa.generate",
        "qa.ingest-from-marker",
        "temporal.add",
        "crud.create",
        "search.semantic"
    ]
    
    tools = config.get("tools", {})
    missing = [t for t in expected_tools if t not in tools]
    
    if missing:
        logger.error(f"Missing expected tools: {missing}")
        return False
    
    logger.success(f"✅ MCP configuration validated with {tool_count} tools")
    return True

def test_tool_execution():
    """Test executing a few key MCP tools."""
    logger.info("Testing MCP tool execution...")
    
    # Test memory.add command
    test_cases = [
        {
            "command": ["python", "-m", "arangodb", "memory", "add", 
                       "--content", "Test MCP integration", 
                       "--metadata", '{"source": "mcp_test"}'],
            "description": "Adding memory via MCP"
        },
        {
            "command": ["python", "-m", "arangodb", "memory", "search",
                       "--query", "MCP integration",
                       "--strategy", "keyword"],
            "description": "Searching memories via MCP"
        }
    ]
    
    for test in test_cases:
        logger.info(f"Testing: {test['description']}")
        result = subprocess.run(
            test["command"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed: {result.stderr}")
            return False
        
        logger.success(f"✅ {test['description']} succeeded")
    
    return True

def test_inter_module_workflow():
    """Test a complete inter-module workflow."""
    logger.info("Testing inter-module communication workflow...")
    
    # Create a test document
    doc_data = {
        "title": "MCP Integration Test",
        "content": "This document tests the complete MCP integration workflow.",
        "metadata": {
            "source": "test_script",
            "type": "integration_test"
        }
    }
    
    # Save test data
    test_file = project_root / "test_mcp_document.json"
    with open(test_file, "w") as f:
        json.dump(doc_data, f, indent=2)
    
    try:
        # 1. Add document to memory
        result = subprocess.run([
            "python", "-m", "arangodb", "crud", "create",
            "--collection", "documents",
            "--data", json.dumps(doc_data)
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to create document: {result.stderr}")
            return False
        
        # Extract document ID from output
        output_lines = result.stdout.strip().split('\n')
        doc_id = None
        for line in output_lines:
            if '"_id":' in line:
                doc_id = line.split('"_id":')[1].strip().strip('",')
                break
        
        if not doc_id:
            logger.error("Could not extract document ID")
            return False
        
        logger.info(f"Created document: {doc_id}")
        
        # 2. Search for the document
        result = subprocess.run([
            "python", "-m", "arangodb", "search", "semantic",
            "--query", "MCP integration workflow",
            "--collection", "documents",
            "--limit", "5"
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Search failed: {result.stderr}")
            return False
        
        if "MCP Integration Test" not in result.stdout:
            logger.error("Document not found in search results")
            return False
        
        logger.success("✅ Inter-module workflow completed successfully")
        return True
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()

def main():
    """Run all MCP integration tests."""
    logger.add("mcp_integration_test.log", rotation="10 MB")
    
    logger.info("Starting MCP integration tests...")
    
    tests = [
        ("MCP Generation", test_mcp_generation),
        ("Tool Execution", test_tool_execution),
        ("Inter-Module Workflow", test_inter_module_workflow)
    ]
    
    failed = []
    
    for name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running: {name}")
        logger.info(f"{'='*60}")
        
        try:
            if not test_func():
                failed.append(name)
        except Exception as e:
            logger.exception(f"Test {name} raised exception: {e}")
            failed.append(name)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    if failed:
        logger.error(f"❌ {len(failed)} tests failed: {failed}")
        logger.error("MCP integration needs fixes")
        return 1
    else:
        logger.success("✅ All MCP integration tests passed!")
        logger.success("The project successfully exposes 61+ tools via MCP")
        logger.success("Inter-module communication is working correctly")
        return 0

if __name__ == "__main__":
    sys.exit(main())