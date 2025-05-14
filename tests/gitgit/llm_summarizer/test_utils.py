"""
Common test utilities for GitGit LLM summarization tests.

This module provides helper functions and common fixtures for testing
LLM summarization functionality in the GitGit project.
"""

import os
import json
import tempfile
from typing import Dict, List, Any, Optional, Tuple

# Sample text for summarization
SAMPLE_TEXT = """
# GitGit Project

GitGit is a tool for analyzing and summarizing Git repositories.

## Features

- Repository cloning with sparse checkout
- Markdown parsing and extraction
- Code analysis using tree-sitter
- Text chunking for efficient processing
- LLM-based summarization of repositories

## Architecture

The project is organized into several components:
1. Cloning and file management
2. Text chunking and processing
3. Code parsing and metadata extraction
4. LLM integration for summarization
5. CLI tools for user interaction

## Implementation

The core functionality is implemented in Python, with a focus on modularity
and extensibility. Tree-sitter is used for parsing code and extracting metadata.
"""

# Sample code for summarization
SAMPLE_CODE = """
def process_repository(repo_url: str, output_dir: str) -> Dict[str, Any]:
    \"\"\"
    Process a repository by cloning, analyzing, and summarizing it.
    
    Args:
        repo_url: URL of the Git repository to process
        output_dir: Directory to store output files
        
    Returns:
        Dictionary with processing results
    \"\"\"
    # Step 1: Clone the repository
    clone_dir = clone_repository(repo_url, output_dir)
    
    # Step 2: Analyze files
    file_data = analyze_files(clone_dir)
    
    # Step 3: Extract metadata
    metadata = extract_metadata(file_data)
    
    # Step 4: Generate chunks
    chunks = generate_chunks(file_data)
    
    # Step 5: Summarize repository
    summary = summarize_repository(chunks, metadata)
    
    return {
        "clone_dir": clone_dir,
        "file_count": len(file_data),
        "metadata": metadata,
        "chunk_count": len(chunks),
        "summary": summary
    }
"""

# Mock LLM responses
MOCK_LLM_RESPONSES = {
    "summary": "GitGit is a Python tool for analyzing and summarizing Git repositories. It features repository cloning with sparse checkout, markdown parsing, code analysis using tree-sitter, and text chunking for efficient processing. The architecture includes components for cloning, text processing, code parsing, LLM integration, and CLI tools.",
    "code_explanation": "This function processes a Git repository by performing several steps: 1) cloning the repository, 2) analyzing files, 3) extracting metadata, 4) generating chunks, and 5) summarizing the repository. It returns a dictionary with information about the processed repository including the cloned directory, file count, metadata, chunk count, and summary.",
    "error": "I cannot generate a summary for this content as it appears to contain harmful instructions."
}


def create_sample_text_file() -> str:
    """
    Create a temporary file with sample text for summarization.
    
    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as f:
        f.write(SAMPLE_TEXT)
        f.flush()
        return f.name


def create_sample_code_file() -> str:
    """
    Create a temporary file with sample code for summarization.
    
    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write(SAMPLE_CODE)
        f.flush()
        return f.name


def create_sample_digest_file() -> str:
    """
    Create a temporary digest file for summarization testing.
    
    Returns:
        Path to the temporary file
    """
    digest_content = {
        "repository": "test-repo",
        "files": [
            {
                "path": "README.md",
                "content": SAMPLE_TEXT,
                "type": "markdown"
            },
            {
                "path": "src/main.py",
                "content": SAMPLE_CODE,
                "type": "python"
            }
        ],
        "file_count": 2,
        "total_bytes": len(SAMPLE_TEXT) + len(SAMPLE_CODE)
    }
    
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False) as f:
        json.dump(digest_content, f, indent=2)
        f.flush()
        return f.name


class MockLLMResponse:
    """Mock LLM response class for testing without actual API calls."""
    
    def __init__(self, content_type: str = "summary"):
        self.content_type = content_type
        
    def json(self) -> Dict[str, Any]:
        """Simulate JSON response from LLM API."""
        return {
            "choices": [
                {
                    "text": MOCK_LLM_RESPONSES.get(self.content_type, MOCK_LLM_RESPONSES["summary"])
                }
            ]
        }
        
    def text(self) -> str:
        """Simulate text response from LLM API."""
        return MOCK_LLM_RESPONSES.get(self.content_type, MOCK_LLM_RESPONSES["summary"])


def cleanup_temp_files(files: List[str]) -> None:
    """
    Clean up temporary files after tests.
    
    Args:
        files: List of file paths to clean up
    """
    for file_path in files:
        if os.path.exists(file_path):
            os.unlink(file_path)