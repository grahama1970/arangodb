# Task 7: CLI Module Validation

## Overview

This task involves validating all functions and commands in the `cli.py` module with real ArangoDB instances to ensure they operate correctly. The CLI (Command-Line Interface) module provides command-line access to search, manage (CRUD operations), and explore relationships within the database collections.

## Objectives

1. Test all CLI commands in `cli.py` with real ArangoDB data
2. Verify each command works correctly with typical inputs and edge cases
3. Test all error-handling flows and verify appropriate failure responses
4. Document expected behavior and output formats for each command
5. Ensure all commands conform to the project's validation standards

## Critical Testing and Validation Requirements

This project has strict requirements for testing and validation that MUST be followed:

1. **NO MagicMock**: MagicMock is strictly forbidden for testing core functionality. Use real ArangoDB with actual data.
2. **Validation First**: Every feature must be verified to work correctly with real data before proceeding to the next task.
3. **Track ALL Failures**: All validation functions must track and report every failure, not just the first one encountered.
4. **No Unconditional Success Messages**: Never print "All Tests Passed" or similar unless ALL tests have actually passed.
5. **Exit Codes**: Validation functions must exit with code 1 if ANY tests fail and 0 ONLY if ALL tests pass.
6. **External Research After 2 Failures**: If a usage function fails validation 2 times with different approaches, use perplexity_ask tool to get help.
7. **Ask Human After 5 Failures**: If a usage function fails validation 5 times after external research, STOP and ask for human help. DO NOT continue to the next task.
8. **Results Before Lint**: Functionality must work correctly before addressing any linting issues.
9. **Comprehensive Testing**: Test normal cases, edge cases, and error handling for each function.
10. **Explicit Verification**: Always verify actual results against expected results before reporting success.
11. **Count Reporting**: Include count of failed tests vs total tests in validation output.

## Task Breakdown

### Setup Phase

- [ ] Navigate to project directory: `cd /home/graham/workspace/experiments/arangodb`
- [ ] Activate virtual environment: `. .venv/bin/activate`
- [ ] Verify ArangoDB connection configuration (host, username, password)
- [ ] Prepare test database and collections for validation
- [ ] Set up necessary environment variables for testing

### Search Commands Testing

- [ ] Test `search bm25` command
  - [ ] Test with basic query parameters
  - [ ] Test with pagination (top-n, offset)
  - [ ] Test with threshold parameter
  - [ ] Test with tag filtering
  - [ ] Test with rich table output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify table formatting, columns, and styling in rich output
  - [ ] Verify JSON structure and data in JSON output
  - [ ] Test error cases (invalid parameters, connection issues)

- [ ] Test `search semantic` command
  - [ ] Test with basic query parameters
  - [ ] Test with various similarity thresholds
  - [ ] Test with tag filtering
  - [ ] Test embedding generation process
  - [ ] Test with rich table output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify table formatting, columns, and styling in rich output
  - [ ] Verify JSON structure and data in JSON output
  - [ ] Test error cases (invalid parameters, embedding failures)

- [ ] Test `search hybrid` command
  - [ ] Test with basic query parameters
  - [ ] Test with various candidate retrieval parameters (initial-k, thresholds)
  - [ ] Test with reranking enabled/disabled
  - [ ] Test different reranking strategies
  - [ ] Test with tag filtering
  - [ ] Test with rich table output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify table formatting, columns, and styling in rich output
  - [ ] Verify JSON structure and data in JSON output
  - [ ] Test error cases (invalid parameters, reranking failures)

- [ ] Test `search keyword` command
  - [ ] Test with single and multiple keywords
  - [ ] Test with match-all flag
  - [ ] Test with custom search fields
  - [ ] Test with various limit values
  - [ ] Test with rich table output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify table formatting, columns, and styling in rich output
  - [ ] Verify JSON structure and data in JSON output
  - [ ] Test error cases (invalid parameters)

- [ ] Test `search tag` command
  - [ ] Test with single and multiple tags
  - [ ] Test with match-all flag
  - [ ] Test with various limit values
  - [ ] Test with rich table output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify table formatting, columns, and styling in rich output
  - [ ] Verify JSON structure and data in JSON output
  - [ ] Test error cases (invalid parameters)

### CRUD Commands Testing

- [ ] Test `crud add-lesson` command
  - [ ] Test adding document with inline data
  - [ ] Test adding document with data file
  - [ ] Test adding document with embedding generation
  - [ ] Test validation of input data structure
  - [ ] Test with rich text output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify success message formatting and content in rich output
  - [ ] Verify JSON structure and metadata in JSON output
  - [ ] Test error cases (invalid JSON, missing required fields)

- [ ] Test `crud get-lesson` command
  - [ ] Test retrieving existing document
  - [ ] Test retrieving non-existent document
  - [ ] Test with rich text/JSON output format (default is JSON)
  - [ ] Test with explicit JSON output format (--json-output flag)
  - [ ] Verify document structure and formatting in rich output
  - [ ] Verify complete document structure in JSON output
  - [ ] Test error cases (invalid key format)

- [ ] Test `crud update-lesson` command
  - [ ] Test updating with inline data
  - [ ] Test updating with data file
  - [ ] Test embedding regeneration on relevant field updates
  - [ ] Test update with revision checking
  - [ ] Test with rich text output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify success message formatting and content in rich output
  - [ ] Verify JSON structure and updated metadata in JSON output
  - [ ] Test error cases (non-existent document, invalid JSON)

- [ ] Test `crud delete-lesson` command
  - [ ] Test deleting existing document
  - [ ] Test confirmation bypass with --yes flag
  - [ ] Test with rich text output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify success/confirmation message in rich output
  - [ ] Verify JSON status structure in JSON output
  - [ ] Test error cases (non-existent document)

### Graph Commands Testing

- [ ] Test `graph add-relationship` command
  - [ ] Test creating relationship with basic parameters
  - [ ] Test creating relationship with additional attributes
  - [ ] Test with various relationship types
  - [ ] Test with rich text output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify success message formatting and content in rich output
  - [ ] Verify JSON structure and metadata in JSON output
  - [ ] Test error cases (non-existent documents, invalid parameters)

- [ ] Test `graph delete-relationship` command
  - [ ] Test deleting existing relationship
  - [ ] Test confirmation bypass with --yes flag
  - [ ] Test with rich text output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify success/confirmation message in rich output
  - [ ] Verify JSON status structure in JSON output
  - [ ] Test error cases (non-existent relationship)

- [ ] Test `graph traverse` command
  - [ ] Test traversal with default parameters
  - [ ] Test with various depth parameters
  - [ ] Test with different direction parameters
  - [ ] Test with limit parameter
  - [ ] Test with rich output format (shows path structure)
  - [ ] Test with JSON output format (--json-output flag, default)
  - [ ] Verify path structure visualization in rich output
  - [ ] Verify complete path data in JSON output
  - [ ] Test error cases (invalid start node, non-existent graph)

### Memory Commands Testing (If Applicable)

- [ ] Test memory-related commands if they exist
  - [ ] Test basic memory operations
  - [ ] Test with various parameters
  - [ ] Test with rich output format (default)
  - [ ] Test with JSON output format (--json-output flag)
  - [ ] Verify memory display formatting in rich output
  - [ ] Verify memory data structure in JSON output
  - [ ] Test error cases

### Integration Testing

- [ ] Test common workflows combining multiple commands
  - [ ] Add document, retrieve, update, delete workflow
  - [ ] Add documents, create relationships, traverse graph workflow
  - [ ] Search with various methods, retrieve full documents workflow
  - [ ] Test piping JSON output between commands (if applicable)

### Validation Function Implementation

- [ ] Create a comprehensive validation script that:
  - [ ] Tracks all test failures in a list
  - [ ] Counts total tests performed
  - [ ] Exits with appropriate status code based on results
  - [ ] Reports detailed failure information
  - [ ] Tests all command groups

## Environment Requirements

- Working ArangoDB instance (either local or remote)
- Python environment with all required dependencies
- Proper environment variables for connection details:
  - ARANGO_HOST
  - ARANGO_USER
  - ARANGO_PASSWORD
  - ARANGO_DB_NAME
- Environment variables for embedding generation (e.g., OPENAI_API_KEY)
- Test data including documents, relationships, and tags

## Success Criteria

- All CLI commands successfully tested with real data
- Validation function properly tracks and reports all test results
- All edge cases and error conditions handled appropriately
- Clean test environment with proper database cleanup
- Comprehensive documentation of expected outputs and command behavior

## Validation Structure Template

```python
if __name__ == "__main__":
    import sys
    import subprocess
    from typing import List, Dict, Any, Tuple, Optional
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Helper function to run CLI commands and capture output
    def run_command(cmd: List[str]) -> Tuple[int, str, str]:
        """Run a CLI command and capture stdout, stderr, and return code."""
        process = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True
        )
        return process.returncode, process.stdout, process.stderr
    
    # Test setup - ensure connection to ArangoDB and test data
    try:
        # Test command group 1: Search Commands
        # Test 1.1: Search BM25 - basic query
        total_tests += 1
        # Test code with real data...
        # Compare actual result with expected result
        if actual_result != expected_result:
            all_validation_failures.append(f"Test 1.1 failed: {actual_result} != {expected_result}")
        
        # Additional tests...
        
    except Exception as e:
        all_validation_failures.append(f"Unexpected exception: {e}")
        
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)  # Exit with success code
```

## Critical Failure Escalation Protocol

If validation fails:
1. Try a different approach focusing on specific failures
2. If second attempt fails, use perplexity_ask tool to get external help
3. Document all research findings and recommendations
4. Make no more than 5 total attempts before asking for human help
5. NEVER proceed to the next task without successful validation

## Timeline

- Start Date: May 15, 2025
- Expected Completion: May 17, 2025 
- Allocation: 2-3 days

## Progress Tracking

Current Status: Planning phase