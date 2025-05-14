"""
Common test utilities for GitGit integration tests.

This module provides helper functions and common fixtures for testing
integration between GitGit components, comprehensive workflows, and
backward compatibility.
"""

import os
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable

# Integration test configuration
INTEGRATION_TEST_CONFIG = {
    "repositories": [
        {
            "url": "https://github.com/example/repo",
            "branch": "main",
            "name": "example-repo",
            "files": ["README.md", "src/*.py"],
            "expected_file_count": 3
        },
        {
            "url": "https://github.com/minimal/repo",
            "branch": "main",
            "name": "minimal-repo",
            "files": ["*.md"],
            "expected_file_count": 1
        }
    ],
    "workflow_steps": [
        "clone",
        "analyze",
        "chunk",
        "summarize"
    ],
    "test_scenarios": [
        {
            "name": "basic_workflow",
            "description": "Test basic workflow with all steps",
            "steps": ["clone", "analyze", "chunk", "summarize"],
            "options": {}
        },
        {
            "name": "code_metadata",
            "description": "Test workflow with code metadata extraction",
            "steps": ["clone", "analyze", "summarize"],
            "options": {"code_metadata": True}
        },
        {
            "name": "markdown_focus",
            "description": "Test workflow focusing on markdown files",
            "steps": ["clone", "chunk", "summarize"],
            "options": {"enhanced_markdown": True, "file_extensions": ["md"]}
        }
    ]
}


def create_integration_test_config() -> str:
    """
    Create a temporary config file for integration tests.
    
    Returns:
        Path to the temporary config file
    """
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False) as f:
        json.dump(INTEGRATION_TEST_CONFIG, f, indent=2)
        f.flush()
        return f.name


def create_mock_repository(files: Dict[str, str]) -> str:
    """
    Create a mock repository with specified files.
    
    Args:
        files: Dictionary mapping file paths to content
        
    Returns:
        Path to the repository directory
    """
    repo_dir = tempfile.mkdtemp()
    
    # Create the files
    for file_path, content in files.items():
        full_path = os.path.join(repo_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w") as f:
            f.write(content)
    
    # Initialize git repo
    try:
        os.chdir(repo_dir)
        subprocess.run(["git", "init"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "config", "user.name", "Test User"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "config", "user.email", "test@example.com"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "add", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "commit", "-m", "Initial commit"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        pass  # Ignore errors, as we just need a basic structure
    
    return repo_dir


def run_workflow_steps(steps: List[str], repo_dir: str, output_dir: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run a workflow with the specified steps.
    
    Args:
        steps: List of workflow steps to run
        repo_dir: Repository directory
        output_dir: Output directory
        options: Additional options for the workflow
        
    Returns:
        Dictionary with workflow results
    """
    from complexity.gitgit.gitgit import GitGit
    
    options = options or {}
    gitgit = GitGit()
    
    results = {
        "repo_dir": repo_dir,
        "output_dir": output_dir,
        "steps": {},
        "errors": []
    }
    
    try:
        if "clone" in steps:
            results["steps"]["clone"] = {"status": "skipped", "message": "Using existing repo"}
        
        if "analyze" in steps:
            metadata = gitgit.analyze_repository(repo_dir, output_dir, code_metadata=options.get("code_metadata", False))
            results["steps"]["analyze"] = {"status": "success", "file_count": len(metadata.get("files", []))}
        
        if "chunk" in steps:
            chunks = gitgit.chunk_repository(
                repo_dir, 
                output_dir, 
                file_extensions=options.get("file_extensions", ["md", "py", "js", "html"]),
                enhanced_markdown=options.get("enhanced_markdown", True),
                max_chunk_tokens=options.get("max_chunk_tokens", 500),
                chunk_overlap=options.get("chunk_overlap", 100)
            )
            results["steps"]["chunk"] = {"status": "success", "chunk_count": len(chunks)}
        
        if "summarize" in steps:
            summary = gitgit.summarize_repository(
                repo_dir, 
                output_dir,
                model=options.get("model", "test-model")
            )
            results["steps"]["summarize"] = {"status": "success", "summary_length": len(summary)}
    
    except Exception as e:
        results["errors"].append(str(e))
    
    return results


def compare_workflow_outputs(output1: str, output2: str) -> Dict[str, Any]:
    """
    Compare two workflow outputs for compatibility testing.
    
    Args:
        output1: First output directory
        output2: Second output directory
        
    Returns:
        Dictionary with comparison results
    """
    comparison = {
        "file_count_match": False,
        "files_compared": 0,
        "files_identical": 0,
        "differing_files": [],
        "missing_files": []
    }
    
    # Get files in both directories
    files1 = set()
    files2 = set()
    
    for root, _, files in os.walk(output1):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), output1)
            files1.add(rel_path)
    
    for root, _, files in os.walk(output2):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), output2)
            files2.add(rel_path)
    
    # Check file count
    comparison["file_count_match"] = len(files1) == len(files2)
    
    # Check for missing files
    missing1 = files2 - files1
    missing2 = files1 - files2
    comparison["missing_files"].extend([f"Only in {output1}: {f}" for f in missing2])
    comparison["missing_files"].extend([f"Only in {output2}: {f}" for f in missing1])
    
    # Compare common files
    common_files = files1.intersection(files2)
    comparison["files_compared"] = len(common_files)
    
    for file in common_files:
        path1 = os.path.join(output1, file)
        path2 = os.path.join(output2, file)
        
        try:
            with open(path1, "rb") as f1, open(path2, "rb") as f2:
                content1 = f1.read()
                content2 = f2.read()
                
                if content1 == content2:
                    comparison["files_identical"] += 1
                else:
                    comparison["differing_files"].append(file)
        except:
            comparison["differing_files"].append(file)
    
    return comparison


def cleanup_temp_files(files: List[str]) -> None:
    """
    Clean up temporary files after tests.
    
    Args:
        files: List of file paths to clean up
    """
    for file_path in files:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                import shutil
                shutil.rmtree(file_path)
            else:
                os.unlink(file_path)