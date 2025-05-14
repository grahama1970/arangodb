"""
Common test utilities for GitGit utils tests.

This module provides helper functions and common fixtures for testing
utility modules in the GitGit project.
"""

import os
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable

# Constants for testing
TEST_JSON_DATA = {
    "name": "test-utils",
    "version": "1.0.0",
    "sections": [
        {"id": 1, "name": "Section 1", "content": "Content 1"},
        {"id": 2, "name": "Section 2", "content": "Content 2"},
        {"id": 3, "name": "Section 3", "content": "Content 3"}
    ]
}

TEST_ERROR_MESSAGES = {
    "value_error": "Test value error message",
    "type_error": "Test type error message",
    "key_error": "test_key_error",
    "file_not_found": "File not found: test_file.txt",
    "permission_denied": "Permission denied: test_file.txt"
}


def create_temp_json_file(data: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Create a temporary JSON file for testing.
    
    Args:
        data: Optional data to write to the file. If None, uses TEST_JSON_DATA.
        
    Returns:
        Tuple of (file_path, data)
    """
    if data is None:
        data = TEST_JSON_DATA
        
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False) as f:
        json.dump(data, f, indent=2)
        f.flush()
        file_path = f.name
        
    return file_path, data


def create_temp_directory_structure() -> Tuple[str, Dict[str, List[str]]]:
    """
    Create a temporary directory structure for testing.
    
    Returns:
        Tuple of (root_dir, structure)
    """
    temp_dir = tempfile.mkdtemp()
    
    # Create a structure with some directories and files
    structure = {
        "dir1": ["file1.txt", "file2.json"],
        "dir2": ["file3.py", "file4.md"],
        "dir3/subdir1": ["file5.py", "file6.json"],
        "dir3/subdir2": ["file7.md"]
    }
    
    # Create the structure
    for dir_path, files in structure.items():
        full_dir_path = os.path.join(temp_dir, dir_path)
        os.makedirs(full_dir_path, exist_ok=True)
        
        for file_name in files:
            file_path = os.path.join(full_dir_path, file_name)
            with open(file_path, "w") as f:
                f.write(f"Content of {file_name}")
    
    return temp_dir, structure


def create_error_raising_functions() -> Dict[str, Callable]:
    """
    Create functions that raise specific errors for testing error handlers.
    
    Returns:
        Dictionary mapping error names to functions that raise those errors
    """
    def raise_value_error():
        raise ValueError(TEST_ERROR_MESSAGES["value_error"])
        
    def raise_type_error():
        raise TypeError(TEST_ERROR_MESSAGES["type_error"])
        
    def raise_key_error():
        raise KeyError(TEST_ERROR_MESSAGES["key_error"])
        
    def raise_file_not_found_error():
        raise FileNotFoundError(TEST_ERROR_MESSAGES["file_not_found"])
        
    def raise_permission_error():
        raise PermissionError(TEST_ERROR_MESSAGES["permission_denied"])
    
    return {
        "ValueError": raise_value_error,
        "TypeError": raise_type_error,
        "KeyError": raise_key_error,
        "FileNotFoundError": raise_file_not_found_error,
        "PermissionError": raise_permission_error
    }


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