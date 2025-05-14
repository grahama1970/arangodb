# Utilities Tests

This directory contains tests for utility functions and classes that support the GitGit module.

## Test Files

- `test_directory_manager.py`: Tests for directory management functionality
- `test_directory_manager_real.py`: Tests for directory management with real filesystem
- `test_error_handler.py`: Tests for error handling utilities
- `test_error_handling_real.py`: Tests for error handling with real errors
- `test_json_utils.py`: Tests for JSON utility functions
- `test_log_utils.py`: Tests for logging utilities
- `test_workflow_logging.py`: Tests for workflow logging functionality
- `test_utils.py`: Common test utilities for utility tests

## Purpose

These tests validate the support functionality of GitGit:

1. Directory management for organizing repository analysis files
2. Error handling and reporting for robust operation
3. JSON utilities for working with configuration and output files
4. Logging utilities for tracing execution and debugging

## Test Utilities

The `test_utils.py` file provides common test utilities for utility functionality testing:

- Functions for creating temporary files and directories
- Sample data for testing JSON operations
- Error generation functions for testing error handling
- Mock logging configurations for testing logging

## Running Tests

Run all utility tests:

```bash
pytest -v tests/gitgit/utils/
```

Run a specific test file:

```bash
pytest -v tests/gitgit/utils/test_error_handler.py
```