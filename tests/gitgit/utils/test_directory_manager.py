"""
Tests for the directory_manager module without using mocks.

This module contains tests for the DirectoryManager class using real implementations.
"""
import os
import json
import shutil
import pytest
from pathlib import Path

# Import fixtures
from tests.gitgit.fixtures.repository_mock import setup_complete_test_repository

# Path to fixture files
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_STRUCTURE_FILE = os.path.join(FIXTURES_DIR, "sample_repo_structure.json")

@pytest.fixture
def directory_manager():
    """Import the directory manager module."""
    # Import the real implementation
    from src.complexity.gitgit.integration.directory_manager import DirectoryManager
    return DirectoryManager

def test_directory_creation(tmp_path, directory_manager):
    """Test that directories are created correctly."""
    # Create a test repository path
    repo_path = os.path.join(str(tmp_path), "test_repo_sparse")
    
    # Initialize directory manager
    manager = directory_manager(repo_path)
    
    # Create directory structure and verify directories are created
    dirs = manager.create_directory_structure()
    
    # Check that all expected directories were created
    expected_dirs = ["chunks", "parsed", "metadata", "output"]
    for dir_name in expected_dirs:
        # Check the directory exists in the dir_paths dict
        assert dir_name in dirs, f"Directory {dir_name} missing from returned paths"
        
        # Check that the directory exists on disk
        dir_path = dirs[dir_name]
        assert os.path.exists(dir_path), f"Directory {dir_name} was not created at {dir_path}"
        assert os.path.isdir(dir_path), f"Path {dir_path} is not a directory"

def test_get_directory_paths(tmp_path, directory_manager):
    """Test getting directory paths."""
    # Create a test repository path
    repo_path = os.path.join(str(tmp_path), "test_repo_sparse")
    
    # Initialize directory manager
    manager = directory_manager(repo_path)
    dirs = manager.create_directory_structure()
    
    # Verify directory paths are in dirs dictionary
    assert dirs["chunks"] == Path(repo_path) / "chunks"
    assert dirs["parsed"] == Path(repo_path) / "parsed"
    assert dirs["metadata"] == Path(repo_path) / "metadata"
    assert dirs["output"] == Path(repo_path) / "output"

def test_get_file_paths(tmp_path, directory_manager):
    """Test getting file paths."""
    # Create a test repository path
    repo_path = os.path.join(str(tmp_path), "test_repo_sparse")
    
    # Initialize directory manager
    manager = directory_manager(repo_path)
    dirs = manager.create_directory_structure()
    
    # Test different paths using the get_output_path method
    assert manager.get_output_path("SUMMARY.txt") == dirs["output"] / "SUMMARY.txt"
    assert manager.get_output_path("DIGEST.txt") == dirs["output"] / "DIGEST.txt"
    assert manager.get_output_path("TREE.txt") == dirs["output"] / "TREE.txt"
    assert manager.get_output_path("LLM_SUMMARY.txt") == dirs["output"] / "LLM_SUMMARY.txt"
    assert manager.get_output_path("CODE_METADATA.json") == dirs["output"] / "CODE_METADATA.json"

def test_get_chunk_file_path(tmp_path, directory_manager):
    """Test getting chunk file path."""
    # Create a test repository path
    repo_path = os.path.join(str(tmp_path), "test_repo_sparse")
    
    # Initialize directory manager
    manager = directory_manager(repo_path)
    dirs = manager.create_directory_structure()
    
    # Verify chunk file path
    file_path = "src/main.py"
    expected_path = dirs["chunks"] / "main.json"
    assert manager.get_chunk_path(file_path) == expected_path
    
    # Test with chunk_id
    expected_path_with_id = dirs["chunks"] / "main_chunk1.json"
    assert manager.get_chunk_path(file_path, "chunk1") == expected_path_with_id

def test_get_parsed_file_path(tmp_path, directory_manager):
    """Test getting parsed file path."""
    # Create a test repository path
    repo_path = os.path.join(str(tmp_path), "test_repo_sparse")
    
    # Initialize directory manager
    manager = directory_manager(repo_path)
    dirs = manager.create_directory_structure()
    
    # Verify parsed file path
    file_path = "README.md"
    expected_path = dirs["parsed"] / "README_parsed.json"
    assert manager.get_parsed_path(file_path) == expected_path

def test_get_metadata_file_path(tmp_path, directory_manager):
    """Test getting metadata file path."""
    # Create a test repository path
    repo_path = os.path.join(str(tmp_path), "test_repo_sparse")
    
    # Initialize directory manager
    manager = directory_manager(repo_path)
    dirs = manager.create_directory_structure()
    
    # Verify metadata file path
    file_path = "src/utils.py"
    expected_path = dirs["metadata"] / "utils_metadata.json"
    assert manager.get_metadata_path(file_path) == expected_path

# Note: clean_path_for_filename is not in the current API
# The current DirectoryManager uses Path.name and Path.stem instead

def test_create_directory_structure(tmp_path, directory_manager):
    """Test creating directory structure."""
    # Create a test repository path
    repo_path = os.path.join(str(tmp_path), "test_repo_sparse")
    
    # Initialize directory manager
    manager = directory_manager(repo_path)
    
    # Create directory structure
    dirs = manager.create_directory_structure()
    
    # Verify directories are created
    assert os.path.isdir(dirs["chunks"])
    assert os.path.isdir(dirs["parsed"])
    assert os.path.isdir(dirs["metadata"])
    assert os.path.isdir(dirs["output"])

def test_cleanup_functionality(tmp_path, directory_manager):
    """Test cleanup functionality."""
    # Create a test repository path
    repo_path = os.path.join(str(tmp_path), "test_repo_sparse")
    
    # Initialize directory manager
    manager = directory_manager(repo_path)
    
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