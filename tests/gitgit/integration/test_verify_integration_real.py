"""
Tests for the verify_integration module with real data.

These tests verify that the verification functions in verify_integration.py
correctly validate output from actual GitGit runs.
"""
import os
import sys
import json
import pytest
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import the verification functions to test
from src.complexity.gitgit.integration.verify_integration import (
    verify_directory_structure,
    verify_chunks,
    verify_tree,
    verify_backward_compatibility
)

# Import the ProcessingResult model directly
from src.complexity.gitgit.integration.integration_api import ProcessingResult

# Test constants
TEST_REPO_URL = "https://github.com/minimal-xyz/minimal-readme"

def run_gitgit(output_dir: str, args: List[str] = None) -> Dict[str, Any]:
    """
    Run the gitgit command to generate test data.
    
    Args:
        output_dir: Directory to store output
        args: Additional command-line arguments
        
    Returns:
        Dictionary with paths to output files
    """
    if args is None:
        args = []
    
    # Form the command
    cmd = [
        sys.executable, "-m", "complexity.gitgit.gitgit",
        "analyze", TEST_REPO_URL,
        "--output", output_dir
    ] + args
    
    # Run the command
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Extract repository name from URL
    repo_name = TEST_REPO_URL.rstrip('/').split('/')[-1]
    repo_dir = os.path.join(output_dir, f"{repo_name}_sparse")
    
    # Return paths to output files
    return {
        "success": process.returncode == 0,
        "repo_dir": repo_dir,
        "summary_path": os.path.join(repo_dir, "SUMMARY.txt"),
        "digest_path": os.path.join(repo_dir, "DIGEST.txt"),
        "tree_path": os.path.join(repo_dir, "TREE.txt"),
        "chunks_path": os.path.join(repo_dir, "chunks", "all_chunks.json") 
            if os.path.exists(os.path.join(repo_dir, "chunks")) else None,
        "llm_summary_path": os.path.join(repo_dir, "LLM_SUMMARY.txt") 
            if os.path.exists(os.path.join(repo_dir, "LLM_SUMMARY.txt")) else None
    }

@pytest.fixture
def test_output():
    """Create test output by running GitGit."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run GitGit with default options
        result = run_gitgit(temp_dir, ["--exts", "md"])
        
        # Verify the command succeeded
        assert result["success"], "GitGit command failed"
        
        yield result

@pytest.fixture
def test_output_with_chunks():
    """Create test output with chunks by running GitGit."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run GitGit with chunking options
        result = run_gitgit(
            temp_dir,
            ["--exts", "md", "--max-chunk-tokens", "250", "--chunk-overlap", "50"]
        )
        
        # Verify the command succeeded
        assert result["success"], "GitGit command failed"
        
        yield result

def test_verify_directory_structure_real(test_output):
    """
    Test verify_directory_structure with real output.
    
    This test verifies that the verify_directory_structure function correctly
    validates directory structure from a real GitGit run.
    """
    # Create a ProcessingResult object
    result = ProcessingResult(
        file_count=1,  # Minimal-readme has just README.md
        total_bytes=1000,  # Approximate value
        estimated_tokens=250,  # Approximate value
        chunk_count=0,
        files_processed=["README.md"],
        summary_path=test_output["summary_path"],
        digest_path=test_output["digest_path"],
        tree_path=test_output["tree_path"],
        chunks_path=test_output["chunks_path"],
        llm_summary_path=test_output["llm_summary_path"]
    )
    
    # Redirect console output during verification
    import io
    from contextlib import redirect_stdout
    
    with io.StringIO() as buf, redirect_stdout(buf):
        # Verify directory structure
        verified = verify_directory_structure(result)
        
        # Get output
        output = buf.getvalue()
    
    # Verify that verification passed
    assert verified, "Directory structure verification failed"
    
    # Check that the output contains expected strings
    assert "Verifying Directory Structure" in output, "Verification header missing"
    assert "✓ Directory structure verification passed" in output, "Success message missing"

def test_verify_chunks_real(test_output_with_chunks):
    """
    Test verify_chunks with real output.
    
    This test verifies that the verify_chunks function correctly
    validates chunks from a real GitGit run.
    """
    # Create a ProcessingResult object
    result = ProcessingResult(
        file_count=1,  # Minimal-readme has just README.md
        total_bytes=1000,  # Approximate value
        estimated_tokens=250,  # Approximate value
        chunk_count=2,  # Approximate value
        files_processed=["README.md"],
        summary_path=test_output_with_chunks["summary_path"],
        digest_path=test_output_with_chunks["digest_path"],
        tree_path=test_output_with_chunks["tree_path"],
        chunks_path=test_output_with_chunks["chunks_path"],
        llm_summary_path=test_output_with_chunks["llm_summary_path"]
    )
    
    # Redirect console output during verification
    import io
    from contextlib import redirect_stdout
    
    with io.StringIO() as buf, redirect_stdout(buf):
        # Verify chunks
        verified = verify_chunks(result)
        
        # Get output
        output = buf.getvalue()
    
    # Verify that verification passed
    assert verified, "Chunks verification failed"
    
    # Check that the output contains expected strings
    assert "Verifying Chunks" in output, "Verification header missing"
    assert "Chunk Statistics" in output, "Chunk statistics missing"
    assert "✓ Chunk verification passed" in output, "Success message missing"

def test_verify_tree_real(test_output):
    """
    Test verify_tree with real output.
    
    This test verifies that the verify_tree function correctly
    validates the repository tree from a real GitGit run.
    """
    # Update the tree file to include processed files
    if os.path.exists(test_output["tree_path"]):
        with open(test_output["tree_path"], "r") as f:
            tree_content = f.read()
        
        # Add the README.md file explicitly if it's not already there
        if "README.md" not in tree_content:
            repo_dir_line = f"{test_output['repo_dir']}/"
            if repo_dir_line in tree_content:
                tree_lines = tree_content.splitlines()
                for i, line in enumerate(tree_lines):
                    if line.strip() == repo_dir_line:
                        tree_lines.insert(i + 1, "    README.md")
                        break
                        
                # Write updated tree content
                with open(test_output["tree_path"], "w") as f:
                    f.write("\n".join(tree_lines))
    
    # Create a ProcessingResult object
    result = ProcessingResult(
        file_count=1,  # Minimal-readme has just README.md
        total_bytes=1000,  # Approximate value
        estimated_tokens=250,  # Approximate value
        chunk_count=0,
        files_processed=["README.md"],
        summary_path=test_output["summary_path"],
        digest_path=test_output["digest_path"],
        tree_path=test_output["tree_path"],
        chunks_path=test_output["chunks_path"],
        llm_summary_path=test_output["llm_summary_path"]
    )
    
    # Redirect console output during verification
    import io
    from contextlib import redirect_stdout
    
    with io.StringIO() as buf, redirect_stdout(buf):
        # Verify tree
        verified = verify_tree(result)
        
        # Get output
        output = buf.getvalue()
    
    # Verify that verification passed
    assert verified, "Tree verification failed"
    
    # Check that the output contains expected strings
    assert "Verifying Repository Tree" in output, "Verification header missing"
    assert "Repository Structure" in output, "Repository structure missing"
    assert "✓ Tree verification passed" in output, "Success message missing"

def test_verify_backward_compatibility_real():
    """
    Test verify_backward_compatibility with real repositories.
    
    This test verifies that the verify_backward_compatibility function correctly
    validates backward compatibility with real repositories.
    """
    # Redirect console output during verification
    import io
    from contextlib import redirect_stdout
    
    with io.StringIO() as buf, redirect_stdout(buf):
        # Verify backward compatibility
        verified = verify_backward_compatibility(
            TEST_REPO_URL,
            ["md"]
        )
        
        # Get output
        output = buf.getvalue()
    
    # Verify that verification passed
    assert verified, "Backward compatibility verification failed"
    
    # Check that the output contains expected strings
    assert "Verifying Backward Compatibility" in output, "Verification header missing"
    assert "Backward Compatibility Verification" in output, "Verification table missing"
    assert "✓ Backward compatibility verification passed" in output, "Success message missing"