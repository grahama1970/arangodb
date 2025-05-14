# Core Component Tests

This directory contains tests for the core functionality of the GitGit module.

## Test Files

- `test_cli.py`: Tests for the Typer CLI interface commands
- `test_code_metadata.py`: Tests for code metadata extraction
- `test_concat_summarize.py`: Tests for file concatenation and summarization
- `test_sparse_clone.py`: Tests for repository sparse cloning functionality
- `test_utils.py`: Common test utilities for core tests

## Purpose

These tests validate the primary functionality of GitGit:

1. Command-line interface (CLI) commands for repository analysis
2. Sparse cloning of repositories to analyze only essential files
3. Extraction of code metadata from repositories
4. Concatenation and summarization of repository content

## Test Utilities

The `test_utils.py` file provides common test utilities for core functionality testing:

- Functions for creating mock repositories
- Sample data for testing CLI commands
- Helper functions for running CLI commands in tests
- Validation functions for checking command outputs

## Running Tests

Run all core tests:

```bash
pytest -v tests/gitgit/core/
```

Run a specific test file:

```bash
pytest -v tests/gitgit/core/test_cli.py
```