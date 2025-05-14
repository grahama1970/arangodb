# Summarizer Tests

This directory contains tests for the text summarization functionality of the GitGit module that doesn't rely on LLMs.

## Purpose

These tests validate the non-LLM text summarization capabilities of GitGit:

1. Rule-based summarization techniques
2. Statistical text summarization
3. Extractive summarization methods
4. Text preprocessing for summarization

## Current Status

This directory is prepared for future tests of the non-LLM summarization functionality. Currently, most summarization in GitGit uses LLM-based approaches, which are tested in the `llm_summarizer` directory.

## Planned Test Files

- `test_text_summarizer.py`: Tests for basic text summarization
- `test_extractive_summarizer.py`: Tests for extractive summarization techniques
- `test_utils.py`: Common test utilities for summarizer tests

## Running Tests

Once tests are implemented, you will be able to run them with:

```bash
pytest -v tests/gitgit/summarizer/
```