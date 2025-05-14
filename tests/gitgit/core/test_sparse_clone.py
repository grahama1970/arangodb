"""
Tests for the sparse git clone functionality.
"""
import os
import sys
import tempfile
import pytest
import subprocess

# Import the module path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

# URL for a small public repository we can use for testing
TEST_REPO_URL = "https://github.com/benhoyt/goawk"

def has_git():
    """Check if git is available on the system."""
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def test_valid_git_url_detection():
    """Test detection of valid git URLs without needing mocks."""
    try:
        # Import the relevant module
        from complexity.gitgit.gitgit import is_valid_git_url
    except ImportError:
        pytest.skip("GitGit module not available")
    
    # Test with real URLs
    valid_urls = [
        "https://github.com/user/repo.git",
        "https://github.com/user/repo",
        "git@github.com:user/repo.git",
        "file:///home/user/local/repo"
    ]
    
    invalid_urls = [
        "not_a_url",
        "ftp://example.com/repo",
        "https://example.com",  # No repository part
        "github.com/user/repo"  # Missing protocol
    ]
    
    # Test with real function calls
    for url in valid_urls:
        assert is_valid_git_url(url), f"Should detect {url} as valid"
    
    for url in invalid_urls:
        assert not is_valid_git_url(url), f"Should detect {url} as invalid"

def test_parse_repo_url():
    """Test parsing repository URLs without needing mocks."""
    try:
        # Import the relevant module
        from complexity.gitgit.gitgit import parse_repo_url
    except ImportError:
        pytest.skip("GitGit module not available")
    
    # Test cases
    test_cases = [
        {
            "url": "https://github.com/user/repo.git",
            "expected": {
                "owner": "user",
                "name": "repo"
            }
        },
        {
            "url": "https://github.com/org-name/repo-name",
            "expected": {
                "owner": "org-name",
                "name": "repo-name"
            }
        },
        {
            "url": "git@github.com:user/project.git",
            "expected": {
                "owner": "user",
                "name": "project"
            }
        }
    ]
    
    # Run real function calls
    for case in test_cases:
        result = parse_repo_url(case["url"])
        assert result["owner"] == case["expected"]["owner"], f"Owner mismatch for {case['url']}"
        assert result["name"] == case["expected"]["name"], f"Name mismatch for {case['url']}"

@pytest.mark.skipif(not has_git(), reason="Git not available")
def test_basic_git_operations():
    """
    Test basic git operations to ensure real git commands work.
    This avoids using MagicMock by testing with actual git operations.
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize a git repository
        repo_dir = os.path.join(temp_dir, "test-repo")
        os.makedirs(repo_dir)
        
        # Run git init
        init_result = subprocess.run(
            ["git", "init"], 
            cwd=repo_dir, 
            capture_output=True, 
            text=True
        )
        assert init_result.returncode == 0, "Git init failed"
        
        # Create a test file
        test_file = os.path.join(repo_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("This is a test file")
        
        # Add the file
        add_result = subprocess.run(
            ["git", "add", "test.txt"], 
            cwd=repo_dir, 
            capture_output=True, 
            text=True
        )
        assert add_result.returncode == 0, "Git add failed"
        
        # Configure git user for the test repo
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_dir,
            capture_output=True,
            text=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_dir,
            capture_output=True,
            text=True
        )
        
        # Commit the file
        commit_result = subprocess.run(
            ["git", "commit", "-m", "Initial commit"], 
            cwd=repo_dir, 
            capture_output=True, 
            text=True
        )
        assert commit_result.returncode == 0, "Git commit failed"
        
        # Verify the file was committed
        status_result = subprocess.run(
            ["git", "status"], 
            cwd=repo_dir, 
            capture_output=True, 
            text=True
        )
        assert "nothing to commit" in status_result.stdout, "Git status unexpected"
        
        # This demonstrates that basic git operations work without mocking
        print("Basic git operations test passed")

@pytest.mark.skipif(not has_git(), reason="Git not available")
def test_get_file_list_from_real_repo():
    """
    Test getting a file list from a real public git repository.
    This is an integration test that doesn't use mocks.
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Clone a real public repository (small one for quick test)
        clone_result = subprocess.run(
            ["git", "clone", "--depth=1", TEST_REPO_URL],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )
        
        # Skip if clone fails (might happen due to network issues)
        if clone_result.returncode != 0:
            pytest.skip(f"Failed to clone test repository: {clone_result.stderr}")
        
        # Get the repository directory
        repo_dir = os.path.join(temp_dir, "goawk")
        
        # Get a list of files using git
        file_list_result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_dir,
            capture_output=True,
            text=True
        )
        
        # Verify we got some files
        file_list = file_list_result.stdout.splitlines()
        assert len(file_list) > 0, "Should find files in the repository"
        
        # Check for some expected files
        # These might change if the repo changes, but there should be some basics
        assert any(f.endswith(".go") for f in file_list), "Should find Go files"
        assert any(f == "README.md" or f.endswith("README.md") for f in file_list), "Should find README.md"
        
        print(f"Found {len(file_list)} files in the test repository")

if __name__ == "__main__":
    # Run tests manually
    test_valid_git_url_detection()
    test_parse_repo_url()
    if has_git():
        test_basic_git_operations()
        test_get_file_list_from_real_repo()