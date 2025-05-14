"""
Common test utilities for GitGit core functionality tests.

This module provides helper functions and common fixtures for testing
core GitGit functionality such as CLI tools, repository operations, etc.
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Sample repository data
SAMPLE_REPO_DATA = {
    "name": "test-repo",
    "description": "Test repository for GitGit",
    "files": [
        {
            "path": "README.md",
            "content": "# Test Repository\n\nThis is a test repository for GitGit testing."
        },
        {
            "path": "src/main.py",
            "content": "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"
        },
        {
            "path": "src/utils.py",
            "content": "def helper_function():\n    return 'Helper result'"
        }
    ]
}

# CLI command examples
CLI_COMMANDS = {
    "clone": "gitgit clone https://github.com/example/repo",
    "summarize": "gitgit summarize ./repo_dir",
    "analyze": "gitgit analyze ./repo_dir --output ./output.json",
    "extract": "gitgit extract ./repo_dir --format markdown",
    "help": "gitgit --help"
}


def create_sample_repo_structure() -> Tuple[str, Dict[str, Any]]:
    """
    Create a real sample repository structure for testing.
    
    Returns:
        Tuple of (repo_path, repo_data)
    """
    temp_dir = tempfile.mkdtemp()
    
    # Create the repository structure
    for file_data in SAMPLE_REPO_DATA["files"]:
        # Create directory if needed
        file_path = os.path.join(temp_dir, file_data["path"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write the file content
        with open(file_path, "w") as f:
            f.write(file_data["content"])
    
    # Create a git repo
    try:
        os.chdir(temp_dir)
        os.system("git init > /dev/null 2>&1")
        os.system("git config user.name 'Test User' > /dev/null 2>&1")
        os.system("git config user.email 'test@example.com' > /dev/null 2>&1")
        os.system("git add . > /dev/null 2>&1")
        os.system("git commit -m 'Initial commit' > /dev/null 2>&1")
    except:
        pass  # Ignore errors, as we just need a basic structure
    
    return temp_dir, SAMPLE_REPO_DATA


def create_cli_args(command: str) -> List[str]:
    """
    Parse a CLI command into argument list.
    
    Args:
        command: CLI command string
        
    Returns:
        List of arguments
    """
    return command.split()[1:]  # Skip the 'gitgit' command


def create_mock_repo_api_response() -> Dict[str, Any]:
    """
    Create a mock response for repository API.
    
    Returns:
        Mock API response data
    """
    return {
        "name": "example-repo",
        "description": "Example repository for testing",
        "html_url": "https://github.com/example/repo",
        "clone_url": "https://github.com/example/repo.git",
        "default_branch": "main",
        "size": 1024,
        "language": "Python",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-05-01T00:00:00Z",
        "owner": {
            "login": "example"
        }
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