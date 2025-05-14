# Integration Tests

This directory contains integration tests that validate how different components of the GitGit module work together.

## Test Files

- `test_integration.py`: Basic integration tests for GitGit workflow
- `test_integration_comprehensive.py`: Comprehensive end-to-end workflow tests
- `test_integration_fixtures.py`: Tests using shared integration fixtures
- `test_verify_integration_real.py`: Tests verifying real integration behavior
- `test_backward_compatibility.py`: Tests for backward compatibility
- `test_output_parameter.py`: Tests for output parameter functionality
- `test_utils.py`: Common test utilities for integration tests

## Purpose

These tests validate the integrated functionality of GitGit:

1. End-to-end workflow from repository cloning to summary generation
2. Integration between components like parser, chunker, and summarizer
3. Backward compatibility with previous versions
4. Proper handling of output across component boundaries

## Test Utilities

The `test_utils.py` file provides common test utilities for integration testing:

- Functions for creating test workflows
- Sample repository data for integration testing
- Validation functions for checking integrated output
- Helper functions for running multi-stage workflows

## Running Tests

Run all integration tests:

```bash
pytest -v tests/gitgit/integration/
```

Run a specific test file:

```bash
pytest -v tests/gitgit/integration/test_integration_comprehensive.py
```

Skip slow integration tests:

```bash
pytest -v -m "not slow" tests/gitgit/integration/
```