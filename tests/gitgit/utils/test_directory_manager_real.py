"""
Tests for the DirectoryManager using actual directory operations.

These tests verify the functionality of the DirectoryManager class by performing
real directory operations rather than mocking.
"""
import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import the DirectoryManager to test
from src.complexity.gitgit.integration.directory_manager import (
    DirectoryManager,
    create_repo_directory_structure
)

@pytest.fixture
def test_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_create_directory_structure(test_dir):
    """
    Test that directories are created correctly.
    
    This test verifies that the DirectoryManager creates all required directories
    when the create_directory_structure method is called.
    """
    # Create a test repository path
    repo_path = os.path.join(test_dir, "test_repo")
    
    # Initialize directory manager
    manager = DirectoryManager(repo_path)
    
    # Create directory structure
    dir_paths = manager.create_directory_structure()
    
    # Check that all expected directories were created
    expected_dirs = ["chunks", "parsed", "metadata", "output"]
    for dir_name in expected_dirs:
        # Check the directory exists in the dir_paths dict
        assert dir_name in dir_paths, f"Directory {dir_name} missing from returned paths"
        
        # Check that the directory exists on disk
        dir_path = dir_paths[dir_name]
        assert os.path.exists(dir_path), f"Directory {dir_name} was not created at {dir_path}"
        assert os.path.isdir(dir_path), f"Path {dir_path} is not a directory"

def test_create_repo_directory_structure(test_dir):
    """
    Test the create_repo_directory_structure function.
    
    This test verifies that the create_repo_directory_structure function correctly
    creates a DirectoryManager and initializes the directories.
    """
    # Call the function
    repo_name = "test_repo"
    manager = create_repo_directory_structure(repo_name, test_dir)
    
    # Verify that the manager was created
    assert isinstance(manager, DirectoryManager), "Should return a DirectoryManager instance"
    
    # Verify that the directories were created
    expected_dirs = ["chunks", "parsed", "metadata", "output"]
    for dir_name in expected_dirs:
        dir_path = os.path.join(test_dir, dir_name)
        assert os.path.exists(dir_path), f"Directory {dir_name} was not created"
        assert os.path.isdir(dir_path), f"Path {dir_path} is not a directory"

def test_file_path_generation(test_dir):
    """
    Test generating file paths for different file types.
    
    This test verifies that the DirectoryManager generates correct paths for
    different types of files.
    """
    # Initialize directory manager
    repo_path = os.path.join(test_dir, "test_repo")
    manager = DirectoryManager(repo_path)
    
    # Create directory structure
    manager.create_directory_structure()
    
    # Test different path methods
    test_cases = [
        # Function, arguments, expected suffix
        (manager.get_chunk_path, ("README.md",), "chunks/README.json"),
        (manager.get_chunk_path, ("src/main.py", "chunk1"), "chunks/main_chunk1.json"),
        (manager.get_parsed_path, ("README.md",), "parsed/README_parsed.json"),
        (manager.get_metadata_path, ("src/utils.py",), "metadata/utils_metadata.json"),
        (manager.get_output_path, ("SUMMARY.txt",), "output/SUMMARY.txt")
    ]
    
    for func, args, expected_suffix in test_cases:
        path = func(*args)
        assert str(path).endswith(expected_suffix), f"Path {path} doesn't end with {expected_suffix}"
        
        # Create the parent directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Verify we can write to the path
        with open(path, "w") as f:
            f.write("Test content")
        
        # Verify the file was created
        assert os.path.exists(path), f"Failed to create file at {path}"

def test_cleanup_functionality(test_dir):
    """
    Test the cleanup functionality.
    
    This test verifies that the cleanup method correctly removes directories and files.
    """
    # Initialize directory manager
    repo_path = os.path.join(test_dir, "test_repo")
    manager = DirectoryManager(repo_path)
    
    # Create directory structure
    dirs = manager.create_directory_structure()
    
    # Create some test files
    test_files = {
        "chunks": "test_chunk.json",
        "parsed": "test_parsed.json",
        "metadata": "test_metadata.json",
        "output": "test_output.txt"
    }
    
    for dir_name, file_name in test_files.items():
        file_path = os.path.join(dirs[dir_name], file_name)
        with open(file_path, "w") as f:
            f.write("Test content")
        
        # Verify file was created
        assert os.path.exists(file_path), f"Failed to create test file at {file_path}"
    
    # Test cleanup with keep_output=True
    manager.cleanup(keep_output=True)
    
    # Verify intermediate directories were removed
    for dir_name in ["chunks", "parsed", "metadata"]:
        assert not os.path.exists(dirs[dir_name]), f"Directory {dir_name} not removed"
    
    # Verify output directory still exists
    assert os.path.exists(dirs["output"]), "Output directory should not be removed"
    assert os.path.exists(os.path.join(dirs["output"], "test_output.txt")), "Output file should not be removed"
    
    # Recreate directories for the next test
    manager.create_directory_structure()
    
    # Recreate test files
    for dir_name, file_name in test_files.items():
        file_path = os.path.join(dirs[dir_name], file_name)
        with open(file_path, "w") as f:
            f.write("Test content")
    
    # Test cleanup with keep_output=False
    manager.cleanup(keep_output=False)
    
    # Verify all directories were removed
    for dir_name in ["chunks", "parsed", "metadata", "output"]:
        assert not os.path.exists(dirs[dir_name]), f"Directory {dir_name} not removed"

def test_real_file_operations(test_dir):
    """
    Test real file operations with the DirectoryManager.
    
    This test performs actual file operations using the DirectoryManager to verify
    that it works correctly with real files.
    """
    # Initialize directory manager
    repo_path = os.path.join(test_dir, "test_repo")
    manager = DirectoryManager(repo_path)
    
    # Create directory structure
    manager.create_directory_structure()
    
    # Create a test file
    test_file = "test_file.md"
    test_content = "# Test File\n\nThis is a test file for DirectoryManager."
    
    # Get paths for different types of processed files
    chunk_path = manager.get_chunk_path(test_file)
    parsed_path = manager.get_parsed_path(test_file)
    metadata_path = manager.get_metadata_path(test_file)
    output_path = manager.get_output_path("test_output.txt")
    
    # Create test data for each file
    chunk_data = [{"text": "Test chunk", "metadata": {"file": test_file}}]
    parsed_data = {"sections": [{"title": "Test File", "content": "This is a test file"}]}
    metadata_data = {"functions": [], "classes": []}
    output_data = "Test output file content."
    
    # Write files
    with open(chunk_path, "w") as f:
        json.dump(chunk_data, f)
    
    with open(parsed_path, "w") as f:
        json.dump(parsed_data, f)
    
    with open(metadata_path, "w") as f:
        json.dump(metadata_data, f)
    
    with open(output_path, "w") as f:
        f.write(output_data)
    
    # Verify files were created
    assert os.path.exists(chunk_path), f"Failed to create chunk file at {chunk_path}"
    assert os.path.exists(parsed_path), f"Failed to create parsed file at {parsed_path}"
    assert os.path.exists(metadata_path), f"Failed to create metadata file at {metadata_path}"
    assert os.path.exists(output_path), f"Failed to create output file at {output_path}"
    
    # Read files back and verify content
    with open(chunk_path, "r") as f:
        read_chunk_data = json.load(f)
        assert read_chunk_data == chunk_data, "Chunk data not preserved"
    
    with open(parsed_path, "r") as f:
        read_parsed_data = json.load(f)
        assert read_parsed_data == parsed_data, "Parsed data not preserved"
    
    with open(metadata_path, "r") as f:
        read_metadata_data = json.load(f)
        assert read_metadata_data == metadata_data, "Metadata not preserved"
    
    with open(output_path, "r") as f:
        read_output_data = f.read()
        assert read_output_data == output_data, "Output data not preserved"