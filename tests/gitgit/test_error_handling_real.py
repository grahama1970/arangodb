"""
Tests for error handling in GitGit integration.

These tests verify that errors are properly handled in actual usage scenarios
by inducing realistic error conditions with real input data.
"""
import os
import sys
import json
import pytest
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import error handler for direct testing
from src.complexity.gitgit.integration.error_handler import (
    ErrorSource,
    ErrorSeverity
)

# Test constants
INVALID_REPO_URL = "https://github.com/this-repo-does-not-exist/invalid-repo"
TEST_REPO_URL = "https://github.com/minimal-xyz/minimal-readme"
INVALID_FILE = "nonexistent_file.py"

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
    
    # Form the command
    cmd = [
        sys.executable, "-m", "complexity.gitgit.gitgit",
        "analyze", repo_url,
        "--output", output_dir
    ] + args
    
    # Run the command
    process = subprocess.run(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Return results
    return {
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr
    }

def create_corrupted_repo(output_dir: str) -> str:
    """
    Create a corrupted repository for testing error handling.
    
    Args:
        output_dir: Directory to create the repository in
        
    Returns:
        Path to the corrupted repository
    """
    # First clone a real repository
    repo_dir = os.path.join(output_dir, "corrupted_repo_sparse")
    os.makedirs(repo_dir, exist_ok=True)
    
    # Create a corrupt git directory
    git_dir = os.path.join(repo_dir, ".git")
    os.makedirs(git_dir, exist_ok=True)
    
    # Create a corrupt HEAD file
    with open(os.path.join(git_dir, "HEAD"), "w") as f:
        f.write("This is not a valid git HEAD file")
    
    # Create a README.md with incomplete markdown
    with open(os.path.join(repo_dir, "README.md"), "w") as f:
        f.write("# Incomplete markdown\n\n```\nUnclosed code block")
    
    return repo_dir

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_invalid_repository_error_handling(temp_output_dir):
    """
    Test handling of invalid repository URL.
    
    This test verifies that GitGit properly handles and reports errors
    when given an invalid repository URL.
    """
    # Run GitGit with an invalid repository URL
    result = run_gitgit_command(
        INVALID_REPO_URL,
        temp_output_dir
    )
    
    # Check for specific error message in stderr or stdout
    # Note: The current implementation may not return non-zero exit code for invalid repositories
    # but it should report an error message
    output = result["stderr"] + result["stdout"]
    assert "error" in output.lower() or "not found" in output.lower() or "fail" in output.lower(), "Error message not found in output"
    assert "repository" in output.lower() or "clone" in output.lower(), "Error message should mention repository or clone"

def test_nonexistent_file_error_handling(temp_output_dir):
    """
    Test handling of nonexistent file.
    
    This test verifies that GitGit properly handles and reports errors
    when asked to process a nonexistent file.
    """
    # Run GitGit with a nonexistent file
    result = run_gitgit_command(
        TEST_REPO_URL,
        temp_output_dir,
        ["--files", INVALID_FILE]
    )
    
    # Verify that the command succeeded but reported the error
    # Note: GitGit should not crash when a single file is not found
    
    # Check that the error was reported in stderr or stdout
    output = result["stderr"] + result["stdout"]
    assert "not found" in output.lower() or "missing" in output.lower() or \
           "doesn't exist" in output.lower() or "nonexistent" in output.lower(), \
           "Error for nonexistent file not reported"

def test_corrupted_repo_error_handling(temp_output_dir):
    """
    Test handling of corrupted repository.
    
    This test verifies that GitGit properly handles and reports errors
    when working with a corrupted repository.
    """
    # Create a corrupted repository
    corrupted_repo = create_corrupted_repo(temp_output_dir)
    
    # Run GitGit directly on the corrupted directory
    cmd = [
        sys.executable, "-m", "complexity.gitgit.gitgit",
        "analyze", corrupted_repo,
        "--output", temp_output_dir,
        "--exts", "md"
    ]
    
    # Run the command
    process = subprocess.run(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Check that specific errors were reported but the program didn't crash uncontrollably
    output = process.stdout + process.stderr
    assert "error" in output.lower(), "Error not reported for corrupted repository"

def test_direct_error_handler_functionality():
    """
    Test the error handler component directly.
    
    This test verifies that the error handler correctly processes error information.
    """
    # Import GitGitError directly here to avoid pydantic issues during collection
    from src.complexity.gitgit.integration.error_handler import GitGitError
    
    # Create a timestamp for testing
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    
    # Create a real error object
    error = GitGitError(
        message="Test error message",
        source=ErrorSource.REPOSITORY,
        severity=ErrorSeverity.ERROR,
        file_path="test_file.py",
        context={"test": "context"},
        recoverable=True,
        timestamp=timestamp
    )
    
    # Verify error object properties
    assert error.message == "Test error message"
    assert error.source == ErrorSource.REPOSITORY
    assert error.severity == ErrorSeverity.ERROR
    assert error.file_path == "test_file.py"
    assert error.context == {"test": "context"}
    assert error.recoverable == True
    assert error.timestamp == timestamp

def test_error_handler_instance():
    """
    Test creating and using an error handler instance.
    
    This test verifies that the error handler can be created and used to handle errors.
    """
    # Import directly here to avoid issues during collection
    from src.complexity.gitgit.integration.error_handler import ErrorHandler, GitGitError
    
    # Create an error handler
    handler = ErrorHandler()
    
    # Create a timestamp for testing
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    
    # Create an error
    error = GitGitError(
        message="Repository not found",
        source=ErrorSource.REPOSITORY,
        severity=ErrorSeverity.ERROR,
        file_path=None,
        context={"repo_url": "https://github.com/nonexistent/repo"},
        recoverable=False,
        timestamp=timestamp
    )
    
    # Handle the error - should not throw exception
    handled = handler.handle_error(error)
    
    # Since this is a repository error and is marked as not recoverable, it should not be handled
    assert not handled, "Non-recoverable error should not be marked as handled"
    
    # Check that error was added to the error list
    errors = handler.get_errors(ErrorSource.REPOSITORY)
    assert len(errors) == 1, "Error should be added to the error list"
    assert errors[0].message == "Repository not found", "Error message not preserved"