# GitGit Module Test Suite

This directory contains non-mocked tests for the `complexity.gitgit` module. The tests have been organized into subdirectories that mirror the structure of the GitGit module itself.

## Directory Structure

- `core/`: Tests for core GitGit functionality (CLI, code metadata, sparse cloning)
- `utils/`: Tests for utility functions (error handling, directory management, JSON utilities)
- `chunking/`: Tests for text chunking functionality
- `parser/`: Tests for code parsing functionality (tree-sitter)
- `markdown/`: Tests for markdown parsing and extraction
- `llm_summarizer/`: Tests for LLM-based summarization
- `summarizer/`: Tests for text summarization
- `integration/`: Tests for integration between components

Each subdirectory has a `README.md` file explaining its purpose and test organization.

## Test Organization

Each test directory follows these conventions:

1. Each directory has a `__init__.py` to make it a proper package
2. Each directory has a `test_utils.py` with common test utilities for that component
3. Test files are named `test_*.py` and follow pytest conventions
4. Tests use real components instead of mocks whenever possible

## Running the Tests

### Basic Test Run

Run all tests except those marked as slow or requiring API keys:

```bash
pytest -v tests/gitgit/
```

### Run with Network Tests

Run all tests including those that make network calls:

```bash
pytest -v tests/gitgit/
```

### Run Specific Component Tests

To run tests for a specific component:

```bash
pytest -v tests/gitgit/core/
pytest -v tests/gitgit/utils/
pytest -v tests/gitgit/markdown/
```

### Skip Slow Tests

To skip slow tests (like those making network calls):

```bash
pytest -v -m "not slow" tests/gitgit/
```

### Skip LLM API Tests

Some tests require API keys for LLM services. To skip these:

```bash
SKIP_NETWORK_TESTS=1 pytest -v tests/gitgit/
```

## Test Fixtures

Common test fixtures are defined in `conftest.py` and include:

- `sample_repo_fixture`: Creates a sample repository structure
- `sample_markdown_file`: Creates a test markdown file
- `sample_json_file`: Creates a test JSON file
- `sample_code_file`: Creates a test Python code file
- `real_error_fixture`: Functions that raise specific errors for testing
- `chunking_sample_text`: Sample text for chunking tests
- `test_dirs`: Dictionary of test directory paths

## Test Environment

The tests require:

1. Git CLI installed and available in PATH
2. (Optional) API keys for LLM services to test the summarization functionality:
   - Set `OPENAI_API_KEY` for OpenAI models
   - Set `ANTHROPIC_API_KEY` for Anthropic/Claude models

## Notes on Testing Approach

- We avoid using MagicMock and prefer real components for testing
- Tests that require LLM API access are marked with the `needs_llm_access` decorator
- Each component has its own set of test utilities in `test_utils.py`