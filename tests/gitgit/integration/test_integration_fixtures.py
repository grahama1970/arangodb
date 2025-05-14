"""
Tests for the GitGit integration module using actual repositories.

These tests verify the integration between components using real repositories
and actual operations instead of mocks.
"""
import os
import sys
import json
import pytest
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import directory manager to test
from src.complexity.gitgit.integration.directory_manager import DirectoryManager

# Constants for test repositories
PYTHON_ARANGO_REPO_URL = "https://github.com/arangodb/python-arango"

# Output dirs and files to check
OUTPUT_DIRS = ["chunks"]
OUTPUT_FILES = ["SUMMARY.txt", "DIGEST.txt", "TREE.txt"]

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output."""
    # Create a temporary directory for our tests
    with tempfile.TemporaryDirectory() as temp_dir:
        old_cwd = os.getcwd()
        os.chdir(temp_dir)  # Change working directory to temp_dir
        
        # Create a 'repos' subdirectory for GitGit to work with
        os.makedirs("repos", exist_ok=True)
        
        try:
            yield temp_dir
        finally:
            os.chdir(old_cwd)  # Restore original working directory

def run_gitgit_command(repo_url: str, output_dir: str, args: List[str] = None) -> Dict[str, Any]:
    """
    Run the gitgit command with the specified options and return the results.
    
    Args:
        repo_url: Repository URL to analyze
        output_dir: Directory to store output
        args: Additional command-line arguments
        
    Returns:
        Dictionary with test results
    """
    if args is None:
        args = []
    
    # Extract repository name from URL
    repo_name = repo_url.rstrip('/').split('/')[-1]
    
    # Form the command (note: GitGit CLI doesn't have an --output option)
    cmd = [
        sys.executable, "-m", "complexity.gitgit.gitgit",
        repo_url
    ] + args
    
    # Run the command
    process = subprocess.run(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True,
        cwd=output_dir  # Set the current working directory to the temp directory
    )
    
    # Check if the command was successful
    success = process.returncode == 0
    
    # GitGit creates a directory structure like: repos/repo_name_sparse
    # This is the full path to the repository directory
    repo_dir = os.path.join(output_dir, "repos", f"{repo_name}_sparse")
    
    # Check if expected directories exist
    dirs_exist = {}
    for dir_name in OUTPUT_DIRS:
        dir_path = os.path.join(repo_dir, dir_name)
        dirs_exist[dir_name] = os.path.exists(dir_path)
    
    # Check if expected files exist
    files_exist = {}
    for file_name in OUTPUT_FILES:
        file_path = os.path.join(repo_dir, file_name)
        files_exist[file_name] = os.path.exists(file_path)
    
    # Return results
    return {
        "success": success,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "repo_dir": repo_dir,
        "dirs_exist": dirs_exist,
        "files_exist": files_exist
    }

def test_directory_structure_creation(temp_output_dir):
    """
    Test that running GitGit creates the expected directory structure.
    
    This test verifies that when GitGit runs, it creates the correct directory
    structure for storing intermediate files.
    """
    # Run GitGit with minimal options
    result = run_gitgit_command(
        PYTHON_ARANGO_REPO_URL,
        temp_output_dir,
        ["--exts", "md", "--files", "README.md"]
    )
    
    # Assert the command succeeded
    assert result["success"], f"GitGit command failed: {result['stderr']}"
    
    # Check that directories were created
    assert result["dirs_exist"]["chunks"], "Chunks directory not created"
    
    # Create a DirectoryManager instance for the output directory
    dir_manager = DirectoryManager(result["repo_dir"])
    
    # Call create_directory_structure to verify it works
    dirs = dir_manager.create_directory_structure()
    
    # Verify that directories are created
    for name, path in dirs.items():
        assert os.path.exists(path), f"Directory {name} at {path} not created"

def test_markdown_processing(temp_output_dir):
    """
    Test that GitGit correctly processes markdown files.
    
    This test verifies that when GitGit analyzes a repository with markdown files,
    it correctly processes them and creates the expected output.
    """
    # Run GitGit with markdown-specific options
    result = run_gitgit_command(
        PYTHON_ARANGO_REPO_URL,
        temp_output_dir,
        ["--exts", "md", "--files", "README.md"]
    )
    
    # Assert the command succeeded
    assert result["success"], f"GitGit command failed: {result['stderr']}"
    
    # Check that SUMMARY.txt and DIGEST.txt exist
    assert result["files_exist"]["SUMMARY.txt"], "SUMMARY.txt not created"
    assert result["files_exist"]["DIGEST.txt"], "DIGEST.txt not created"
    
    # Read SUMMARY.txt to verify processing
    summary_path = os.path.join(result["repo_dir"], "SUMMARY.txt")
    with open(summary_path, 'r') as f:
        summary_content = f.read()
    
    # Check for expected content in the summary
    assert "Files analyzed:" in summary_content
    assert "README.md" in summary_content
    
    # Read DIGEST.txt to verify markdown processing
    digest_path = os.path.join(result["repo_dir"], "DIGEST.txt")
    with open(digest_path, 'r') as f:
        digest_content = f.read()
    
    # Check for expected content in the digest related to ArangoDB
    assert "ArangoDB" in digest_content, "ArangoDB not found in digest"
    assert "Markdown file parsed into" in digest_content, "Markdown parsing info not found in digest"

def test_chunking_functionality(temp_output_dir):
    """
    Test that GitGit's chunking functionality works as expected.
    
    This test verifies that GitGit correctly chunks text files and
    creates chunks with the expected metadata.
    """
    # Run GitGit with chunking options
    result = run_gitgit_command(
        PYTHON_ARANGO_REPO_URL,
        temp_output_dir,
        ["--exts", "md", "--files", "README.md", "--max-chunk-tokens", "250", "--chunk-overlap", "50"]
    )
    
    # Assert the command succeeded
    assert result["success"], f"GitGit command failed: {result['stderr']}"
    
    # Check if chunks directory exists
    chunks_dir = os.path.join(result["repo_dir"], "chunks")
    assert os.path.exists(chunks_dir), "Chunks directory not created"
    
    # Look for the all_chunks.json file
    all_chunks_path = os.path.join(chunks_dir, "all_chunks.json")
    assert os.path.exists(all_chunks_path), "all_chunks.json not created"
    
    # Read the chunks file to verify its structure
    with open(all_chunks_path, 'r') as f:
        chunks_data = json.load(f)
    
    # Verify chunks structure 
    assert isinstance(chunks_data, list), "Chunks data should be a list"
    assert len(chunks_data) > 0, "No chunks in all_chunks.json"
    
    # Check first chunk's structure
    first_chunk = chunks_data[0]
    
    # These are actual fields that should be in each chunk
    required_fields = ["file_path", "repo_link", "code"]
    for field in required_fields:
        assert field in first_chunk, f"Required field '{field}' missing from chunk"

def test_integration_with_code_metadata(temp_output_dir):
    """
    Test GitGit's integration with code metadata extraction.
    
    This test verifies that GitGit correctly extracts code metadata
    from Python files when the --code-metadata flag is used.
    """
    # Run GitGit with code metadata options - using a Python file
    result = run_gitgit_command(
        PYTHON_ARANGO_REPO_URL,
        temp_output_dir,
        ["--exts", "py", "--code-metadata", "--files", "setup.py"]
    )
    
    # Assert the command succeeded
    assert result["success"], f"GitGit command failed: {result['stderr']}"
    
    # Check for DIGEST.txt
    digest_path = os.path.join(result["repo_dir"], "DIGEST.txt")
    assert os.path.exists(digest_path), "DIGEST.txt not created"
    
    # Read DIGEST.txt to verify code metadata extraction
    with open(digest_path, 'r') as f:
        digest_content = f.read()
    
    # Looking for Python-specific content
    assert "setup.py" in digest_content, "setup.py not found in digest"

def test_backward_compatibility(temp_output_dir):
    """
    Test that GitGit maintains backward compatibility.
    
    This test verifies that the original functionality still works as expected.
    """
    # Run GitGit with minimal parameters
    result = run_gitgit_command(
        PYTHON_ARANGO_REPO_URL,
        temp_output_dir,
        ["--exts", "md", "--files", "README.md"]  # Minimal options
    )
    
    # Assert the command succeeded
    assert result["success"], f"GitGit command failed: {result['stderr']}"
    
    # Check for essential output files
    for file_name in ["SUMMARY.txt", "DIGEST.txt", "TREE.txt"]:
        assert result["files_exist"][file_name], f"{file_name} not created"
    
    # Read SUMMARY.txt to verify it has the expected format
    summary_path = os.path.join(result["repo_dir"], "SUMMARY.txt")
    with open(summary_path, 'r') as f:
        summary_content = f.read()
    
    # Check for expected content in the summary
    assert "Files analyzed:" in summary_content
    assert "Total bytes:" in summary_content
    assert "Estimated tokens:" in summary_content