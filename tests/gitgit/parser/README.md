# Parser Tests

This directory contains tests for the code parsing functionality of the GitGit module, primarily using the tree-sitter library.

## Test Files

- `test_tree_sitter.py`: Tests for basic tree-sitter parsing functionality
- `test_tree_sitter_utils.py`: Tests for tree-sitter utility functions
- `test_utils.py`: Common test utilities for parser tests

## Purpose

These tests validate the code parsing capabilities of GitGit:

1. Parsing source code files into syntax trees
2. Extracting metadata from code (functions, classes, imports)
3. Analyzing code structure and relationships
4. Supporting multiple programming languages

## Test Utilities

The `test_utils.py` file provides common test utilities for parser testing:

- Sample code snippets in various programming languages
- Functions for creating test source files
- Validation functions for checking parsing results
- Mock tree-sitter configurations for testing

## Running Tests

Run all parser tests:

```bash
pytest -v tests/gitgit/parser/
```

Run a specific test file:

```bash
pytest -v tests/gitgit/parser/test_tree_sitter_utils.py
```