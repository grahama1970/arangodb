# Chunking Tests

This directory contains tests for the text chunking functionality of the GitGit module.

## Test Files

- `test_chunker.py`: Tests for text chunking functionality
- `test_utils.py`: Common test utilities for chunking tests

## Purpose

These tests validate the text chunking capabilities of GitGit:

1. Breaking down large text documents into smaller chunks
2. Maintaining context across chunks
3. Handling different chunking strategies (fixed size, paragraph, section)
4. Processing various document formats

## Test Utilities

The `test_utils.py` file provides common test utilities for chunking testing:

- Sample text data of various lengths and structures
- Functions for creating test text files
- Validation functions for checking chunking results
- Helper functions for comparing chunk boundaries and content

## Running Tests

Run all chunking tests:

```bash
pytest -v tests/gitgit/chunking/
```

Run a specific test file:

```bash
pytest -v tests/gitgit/chunking/test_chunker.py
```