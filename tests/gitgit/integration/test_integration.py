"""
Integration tests for GitGit functionality.

This file has been rewritten to avoid using MagicMock completely.
Instead, we use real integration tests with actual components.
"""
import os
import sys
import tempfile
import subprocess
import json
import pytest

# Import module path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

# Helper function to check if the module can be imported
def can_import_gitgit():
    """Check if GitGit can be imported."""
    try:
        from complexity.gitgit.gitgit import main
        return True
    except ImportError:
        return False

def test_module_imports():
    """Test that all required modules can be imported."""
    if not can_import_gitgit():
        pytest.skip("GitGit module not available")
    
    # Try to import core modules
    try:
        from complexity.gitgit.gitgit import (
            main,
            process_repository, 
            concatenate_markdown,
            llm_summarize
        )
        assert callable(main), "main should be callable"
        assert callable(process_repository), "process_repository should be callable"
        assert callable(concatenate_markdown), "concatenate_markdown should be callable"
        assert callable(llm_summarize), "llm_summarize should be callable"
    except ImportError as e:
        pytest.fail(f"Failed to import required modules: {e}")

def test_simple_cli_invocation():
    """Test simple CLI invocation with real process."""
    if not can_import_gitgit():
        pytest.skip("GitGit module not available")
    
    # Run the CLI with --help option
    result = subprocess.run(
        [sys.executable, "-m", "complexity.gitgit.gitgit", "--help"],
        capture_output=True,
        text=True
    )
    
    # Check that it ran successfully
    assert result.returncode == 0, "CLI should exit with code 0"
    assert "Usage:" in result.stdout, "Help output should contain 'Usage:'"

def test_file_processing():
    """Test file processing with real files."""
    if not can_import_gitgit():
        pytest.skip("GitGit module not available")
    
    # Import required functions
    from complexity.gitgit.gitgit import process_directory
    
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files
        readme_path = os.path.join(temp_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write("# Test Repository\n\nThis is a test repository.\n")
        
        # Create a source directory
        src_dir = os.path.join(temp_dir, "src")
        os.makedirs(src_dir)
        
        # Create a Python file
        main_py = os.path.join(src_dir, "main.py")
        with open(main_py, "w") as f:
            f.write("def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()")
        
        # Create a documentation file
        docs_dir = os.path.join(temp_dir, "docs")
        os.makedirs(docs_dir)
        
        api_md = os.path.join(docs_dir, "api.md")
        with open(api_md, "w") as f:
            f.write("# API Documentation\n\nThis document describes the API.\n")
        
        # Process the directory
        result = process_directory(temp_dir)
        
        # Verify all files were processed
        assert "README.md" in result
        assert os.path.join("src", "main.py") in result
        assert os.path.join("docs", "api.md") in result
        
        # Verify content was correctly extracted
        assert "# Test Repository" in result["README.md"]
        assert "def main():" in result[os.path.join("src", "main.py")]
        assert "# API Documentation" in result[os.path.join("docs", "api.md")]

def test_markdown_concatenation():
    """Test markdown concatenation with real files."""
    if not can_import_gitgit():
        pytest.skip("GitGit module not available")
    
    # Import required functions
    from complexity.gitgit.gitgit import concatenate_markdown
    
    # Create test file mapping
    file_mapping = {
        "README.md": "# Test Repository\n\nThis is a test repository.\n",
        "docs/intro.md": "# Introduction\n\nWelcome to the project.\n",
        "docs/api.md": "# API\n\nAPI documentation.\n",
        "src/main.py": "def main():\n    print('Hello, World!')\n",
    }
    
    # Concatenate markdown files
    result = concatenate_markdown(file_mapping)
    
    # Verify markdown files were concatenated
    assert "# Test Repository" in result
    assert "# Introduction" in result
    assert "# API" in result
    
    # Verify Python files were excluded
    assert "def main():" not in result

def test_error_handling():
    """Test error handling with real errors."""
    if not can_import_gitgit():
        pytest.skip("GitGit module not available")
    
    # Try to import error handling module
    try:
        from complexity.gitgit.integration.error_handler import handle_error
    except ImportError:
        pytest.skip("Error handler not available")
    
    # Generate a real error
    try:
        # This will raise a ZeroDivisionError
        result = 1 / 0
        # Should not reach here
        assert False, "Expected exception not raised"
    except ZeroDivisionError as e:
        # Handle the error
        error_info = handle_error(e, "test division")
        
        # Verify error info
        assert "error_type" in error_info
        assert error_info["error_type"] == "ZeroDivisionError"
        assert "error_message" in error_info
        assert "division by zero" in error_info["error_message"]
        assert "error_context" in error_info
        assert "test division" in error_info["error_context"]

def test_json_serialization():
    """Test JSON serialization with real data."""
    if not can_import_gitgit():
        pytest.skip("GitGit module not available")
    
    # Create a temporary file for output
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False) as f:
        output_path = f.name
    
    try:
        # Import json utils
        try:
            from complexity.gitgit.json_utils import write_json
        except ImportError:
            pytest.skip("JSON utils not available")
        
        # Create test data
        data = {
            "name": "test-repo",
            "files": [
                {
                    "path": "README.md",
                    "content": "# Test Repository"
                },
                {
                    "path": "src/main.py",
                    "content": "def main(): pass"
                }
            ],
            "metadata": {
                "date": "2025-05-04",
                "version": "1.0"
            }
        }
        
        # Write data to file
        write_json(data, output_path)
        
        # Verify file was created
        assert os.path.exists(output_path)
        
        # Read the file and verify content
        with open(output_path, "r") as f:
            read_data = json.load(f)
            
            # Check data integrity
            assert read_data["name"] == "test-repo"
            assert len(read_data["files"]) == 2
            assert read_data["files"][0]["path"] == "README.md"
            assert read_data["metadata"]["version"] == "1.0"
    finally:
        # Clean up
        if os.path.exists(output_path):
            os.unlink(output_path)

if __name__ == "__main__":
    # Run tests manually
    test_module_imports()
    test_simple_cli_invocation()
    test_file_processing()
    test_markdown_concatenation()
    test_error_handling()
    test_json_serialization()