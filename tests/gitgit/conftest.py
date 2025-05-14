"""
Test configuration and fixtures for GitGit tests.

Note: This file has been rewritten to avoid using MagicMock completely.
Instead, we use real components and fixtures wherever possible.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Import module paths
sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

# Test directory structure
TEST_DIRS = {
    "core": Path(__file__).parent / "core",
    "utils": Path(__file__).parent / "utils",
    "chunking": Path(__file__).parent / "chunking",
    "parser": Path(__file__).parent / "parser",
    "markdown": Path(__file__).parent / "markdown",
    "llm_summarizer": Path(__file__).parent / "llm_summarizer",
    "integration": Path(__file__).parent / "integration",
    "summarizer": Path(__file__).parent / "summarizer",
}

# Sample repository data for tests
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

@pytest.fixture
def test_dirs():
    """Return dictionary of test directory paths."""
    return TEST_DIRS

@pytest.fixture
def sample_repo_fixture():
    """Create a real sample repository structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the repository structure
        for file_data in SAMPLE_REPO_DATA["files"]:
            # Create directory if needed
            file_path = os.path.join(temp_dir, file_data["path"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the file content
            with open(file_path, "w") as f:
                f.write(file_data["content"])
        
        # Return the repository root and data
        return {
            "repo_path": temp_dir,
            "repo_data": SAMPLE_REPO_DATA
        }

@pytest.fixture
def sample_markdown_file():
    """Create a real markdown file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as f:
        f.write("""
# Sample Markdown

This is a sample markdown file for testing.

## Section 1

Content for section 1.

## Section 2

Content for section 2.
        """)
        f.flush()
        file_path = f.name
    
    # Return the file path and ensure it gets cleaned up
    yield file_path
    
    # Clean up the file after the test
    if os.path.exists(file_path):
        os.unlink(file_path)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def sample_json_data():
    """Provide sample JSON data for testing."""
    return {
        "name": "test-data",
        "version": "1.0.0",
        "items": [
            {"id": 1, "value": "first"},
            {"id": 2, "value": "second"},
            {"id": 3, "value": "third"}
        ],
        "metadata": {
            "created": "2025-05-04",
            "author": "Test User"
        }
    }

@pytest.fixture
def sample_json_file(sample_json_data):
    """Create a real JSON file with sample data."""
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False) as f:
        json.dump(sample_json_data, f, indent=2)
        f.flush()
        file_path = f.name
    
    # Return the file path and ensure it gets cleaned up
    yield file_path
    
    # Clean up the file after the test
    if os.path.exists(file_path):
        os.unlink(file_path)

@pytest.fixture
def sample_code_file():
    """Create a real Python code file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as f:
        f.write("""
def example_function(parameter1, parameter2=None):
    """
    This is an example function for testing.
    
    Args:
        parameter1: First parameter
        parameter2: Optional second parameter
        
    Returns:
        Result of the operation
    """
    if parameter2 is None:
        return parameter1
    return parameter1 + parameter2
    
class ExampleClass:
    def __init__(self, name):
        self.name = name
        
    def get_name(self):
        return self.name
        """)
        f.flush()
        file_path = f.name
    
    # Return the file path and ensure it gets cleaned up
    yield file_path
    
    # Clean up the file after the test
    if os.path.exists(file_path):
        os.unlink(file_path)

@pytest.fixture
def real_error_fixture():
    """Create real error conditions for testing error handlers."""
    
    # Define functions that will raise specific errors
    def raise_value_error():
        raise ValueError("Test value error")
        
    def raise_type_error():
        raise TypeError("Test type error")
        
    def raise_key_error():
        raise KeyError("test_key")
    
    # Create a dictionary to map error types to functions
    error_functions = {
        "ValueError": raise_value_error,
        "TypeError": raise_type_error,
        "KeyError": raise_key_error
    }
    
    return error_functions

@pytest.fixture
def chunking_sample_text():
    """Provide sample text for chunking tests."""
    return """
# Large Document Title

## Introduction

This is a sample document used to test text chunking functionality.
It contains multiple sections and paragraphs to simulate real content.

## Section 1

This is the first section with some content.
It has multiple lines of text that can be chunked.

## Section 2 

This is the second section with more content.
It also has multiple lines that can be processed.

### Subsection 2.1

This is a subsection with specific information.
The chunker should handle nested sections appropriately.

## Conclusion

This is the conclusion of the document.
It summarizes the key points and provides closure.
"""

# Skip LLM-specific tests when running in environments without API access
def needs_llm_access(func):
    """Decorator to skip tests that need LLM API access."""
    return pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ and "ANTHROPIC_API_KEY" not in os.environ,
        reason="LLM API access required"
    )(func)