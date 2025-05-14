# Markdown Tests

This directory contains tests for the markdown parsing and extraction functionality of the GitGit module.

## Test Files

- `test_markdown_extractor.py`: Tests for extracting structured content from markdown files
- `test_utils.py`: Common test utilities for markdown tests

## Purpose

These tests validate the markdown processing capabilities of GitGit:

1. Parsing markdown files into structured sections
2. Extracting headings and content from markdown
3. Converting markdown to structured data for analysis
4. Handling various markdown formatting and syntax

## Test Utilities

The `test_utils.py` file provides common test utilities for markdown testing:

- Sample markdown content in various formats
- Functions for creating test markdown files
- Validation functions for checking extraction results
- Helper functions for comparing markdown structures

## Running Tests

Run all markdown tests:

```bash
pytest -v tests/gitgit/markdown/
```

Run a specific test file:

```bash
pytest -v tests/gitgit/markdown/test_markdown_extractor.py
```