# LLM Summarizer Tests

This directory contains tests for the LLM-based summarization functionality of the GitGit module.

## Test Files

- `test_llm_summary.py`: Tests for LLM summarization integration
- `test_utils.py`: Common test utilities for LLM summarizer tests

## Purpose

These tests validate the LLM summarization capabilities of GitGit:

1. Generating concise summaries of repository content using LLMs
2. Handling API interactions with LLM providers
3. Processing LLM responses and formatting summaries
4. Managing prompt templates and response parsing

## Test Utilities

The `test_utils.py` file provides common test utilities for LLM summarizer testing:

- Mock LLM API responses for testing without API keys
- Sample content for summarization
- Validation functions for checking summary quality
- Configuration for different LLM providers

## Notes on API Access

Some tests in this directory require API keys for LLM services. These tests are marked with the `needs_llm_access` decorator and will be skipped if the API keys are not available in the environment.

You can provide these API keys as environment variables:
- `OPENAI_API_KEY` for OpenAI models
- `ANTHROPIC_API_KEY` for Anthropic/Claude models

## Running Tests

Run all LLM summarizer tests:

```bash
pytest -v tests/gitgit/llm_summarizer/
```

Run a specific test file:

```bash
pytest -v tests/gitgit/llm_summarizer/test_llm_summary.py
```

Skip tests requiring API keys:

```bash
SKIP_NETWORK_TESTS=1 pytest -v tests/gitgit/llm_summarizer/
```