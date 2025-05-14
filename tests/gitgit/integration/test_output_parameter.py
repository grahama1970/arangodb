"""
Tests for the --output parameter in GitGit CLI.

This module tests the functionality of the --output parameter which allows
users to specify a custom output directory for GitGit analysis results.
"""
import os
import sys
import tempfile
import shutil
import subprocess
import pytest
from pathlib import Path

# Constants for test
PYTHON_ARANGO_REPO_URL = "https://github.com/arangodb/python-arango"
OUTPUT_FILES = ["SUMMARY.txt", "DIGEST.txt", "TREE.txt"]

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a subdirectory inside the temp directory for output
        custom_output = os.path.join(temp_dir, "custom_output")
        os.makedirs(custom_output, exist_ok=True)
        yield temp_dir, custom_output

def test_output_parameter(temp_output_dir):
    """
    Test that the --output parameter correctly directs output to the specified directory.
    
    This test verifies that when the --output parameter is used, GitGit creates the output
    files in the specified directory rather than the default location.
    """
    temp_dir, custom_output = temp_output_dir
    repo_name = PYTHON_ARANGO_REPO_URL.rstrip('/').split('/')[-1]
    expected_output_dir = os.path.join(custom_output, f"{repo_name}_sparse")
    
    # Run GitGit with --output parameter
    cmd = [
        sys.executable, "-m", "complexity.gitgit.gitgit",
        PYTHON_ARANGO_REPO_URL,
        "--exts", "md",
        "--files", "README.md",
        "--output", custom_output
    ]
    
    # Change working directory to temp_dir to isolate the test
    old_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        
        # Run the command
        process = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Assert the command succeeded
        assert process.returncode == 0, f"GitGit command failed: {process.stderr}"
        
        # Verify the output directory exists
        assert os.path.exists(expected_output_dir), f"Expected output directory not created: {expected_output_dir}"
        
        # Check that output files were created in the custom directory
        for file_name in OUTPUT_FILES:
            file_path = os.path.join(expected_output_dir, file_name)
            assert os.path.exists(file_path), f"Output file {file_name} not created in custom directory"
        
        # Verify the chunks directory was created
        chunks_dir = os.path.join(expected_output_dir, "chunks")
        assert os.path.exists(chunks_dir), "Chunks directory not created in custom output directory"
        
        # Check that the default output location was not used
        default_output_dir = os.path.join(temp_dir, "repos", f"{repo_name}_sparse")
        assert not os.path.exists(default_output_dir), "Default output directory was created despite using --output"
        
    finally:
        # Restore working directory
        os.chdir(old_cwd)

def test_output_parameter_absolute_path(temp_output_dir):
    """
    Test that the --output parameter works with absolute paths.
    
    This test verifies that GitGit correctly handles absolute paths for the output directory.
    """
    temp_dir, custom_output = temp_output_dir
    # Convert to absolute path
    absolute_output_path = os.path.abspath(custom_output)
    repo_name = PYTHON_ARANGO_REPO_URL.rstrip('/').split('/')[-1]
    expected_output_dir = os.path.join(absolute_output_path, f"{repo_name}_sparse")
    
    # Run GitGit with --output parameter using absolute path
    cmd = [
        sys.executable, "-m", "complexity.gitgit.gitgit",
        PYTHON_ARANGO_REPO_URL,
        "--exts", "md",
        "--files", "README.md",
        "--output", absolute_output_path
    ]
    
    # Run the command
    process = subprocess.run(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Assert the command succeeded
    assert process.returncode == 0, f"GitGit command failed: {process.stderr}"
    
    # Verify the output directory exists
    assert os.path.exists(expected_output_dir), f"Expected output directory not created: {expected_output_dir}"
    
    # Check that output files were created in the custom directory
    for file_name in OUTPUT_FILES:
        file_path = os.path.join(expected_output_dir, file_name)
        assert os.path.exists(file_path), f"Output file {file_name} not created in custom directory"

def test_output_parameter_creates_directory(temp_output_dir):
    """
    Test that the --output parameter creates the output directory if it doesn't exist.
    
    This test verifies that GitGit creates the output directory if it doesn't already exist.
    """
    temp_dir, _ = temp_output_dir
    
    # Create a path to a non-existent directory
    nonexistent_dir = os.path.join(temp_dir, "nonexistent_dir")
    repo_name = PYTHON_ARANGO_REPO_URL.rstrip('/').split('/')[-1]
    expected_output_dir = os.path.join(nonexistent_dir, f"{repo_name}_sparse")
    
    # Ensure the directory doesn't exist before the test
    if os.path.exists(nonexistent_dir):
        shutil.rmtree(nonexistent_dir)
    
    assert not os.path.exists(nonexistent_dir), "Test directory should not exist at start"
    
    # Run GitGit with --output parameter pointing to non-existent directory
    cmd = [
        sys.executable, "-m", "complexity.gitgit.gitgit",
        PYTHON_ARANGO_REPO_URL,
        "--exts", "md",
        "--files", "README.md",
        "--output", nonexistent_dir
    ]
    
    # Run the command
    process = subprocess.run(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Assert the command succeeded
    assert process.returncode == 0, f"GitGit command failed: {process.stderr}"
    
    # Verify the output directory was created
    assert os.path.exists(nonexistent_dir), "Output parent directory was not created"
    assert os.path.exists(expected_output_dir), "Repository output directory was not created"
    
    # Check that output files were created in the custom directory
    for file_name in OUTPUT_FILES:
        file_path = os.path.join(expected_output_dir, file_name)
        assert os.path.exists(file_path), f"Output file {file_name} not created in custom directory"