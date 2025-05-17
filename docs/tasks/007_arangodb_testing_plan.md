# ArangoDB 3-Layer Architecture Testing Plan

## Overview

This document outlines the comprehensive testing plan for the ArangoDB 3-layer architecture refactoring. The testing process will cover all three layers (core, CLI, and MCP) to ensure correct functionality, proper error handling, and appropriate output formatting.

## Testing Goals

1. Verify the integrity and correctness of the core layer implementation
2. Ensure the CLI layer correctly interfaces with the core layer and produces properly formatted output
3. Validate that the MCP layer follows the appropriate protocol and provides consistent responses
4. Identify and document any issues or inconsistencies in the implementation

## Testing Approach

The testing will be conducted in a structured, bottom-up manner:

1. **Module Structure Analysis**: Verify the organization and import/export structure
2. **Import Compatibility Testing**: Ensure all modules can be properly imported
3. **Validation Block Testing**: Run all validation blocks in `if __name__ == "__main__"` sections
4. **Function Input/Output Testing**: Test individual functions with various inputs
5. **CLI Output Formatting**: Test CLI commands for correct Rich and JSON output formatting
6. **Integration Testing**: Test full workflows across multiple layers

## Detailed Test Plan

### 1. Core Layer Testing

#### 1.1 Module Structure Analysis

- Check directory structure for core, CLI, and MCP layers
- Verify `__init__.py` files contain appropriate exports
- Examine import statements for consistency and correctness
- Verify constants are properly defined and imported

#### 1.2 Import Compatibility Testing

For each core module:
- Attempt to import the module directly
- Attempt to import via the package path
- Verify imported functions are callable

Modules to test:
- `arangodb.core.search.*`
- `arangodb.core.memory.*`
- `arangodb.core.arango_setup`
- `arangodb.core.db_operations`
- `arangodb.core.graph`
- `arangodb.core.utils.*`

#### 1.3 Validation Block Testing

For each core module with validation blocks:
- Run the file directly to execute validation blocks
- Verify validation passes without errors
- Document any validation failures

#### 1.4 Function Input/Output Testing

For key functions in each module:
- Test with valid inputs
- Test with edge case inputs
- Test error handling with invalid inputs
- Verify return types match annotations

### 2. CLI Layer Testing

#### 2.1 Command Structure Testing

- Verify command group organization
- Check command parameter definitions
- Test help text formatting
- Verify command option defaults

#### 2.2 Rich Output Formatting Testing

For each CLI command:
- Verify table formatting for search results
- Check color coding in Rich console output
- Test error message formatting
- Verify progress indicators and status messages

#### 2.3 JSON Output Testing

For each CLI command with `--json-output` option:
- Verify JSON output is valid and properly formatted
- Check all expected fields are included
- Test nested JSON structures
- Verify error responses follow consistent format

### 3. MCP Layer Testing

#### 3.1 Response Format Testing

For each MCP function:
- Verify the structure follows MCP protocol
- Check status field for success/error states
- Verify data field contains expected results
- Test message field for descriptive content

#### 3.2 Error Handling Testing

For each MCP function:
- Test with invalid inputs
- Verify error responses follow MCP format
- Check error message clarity
- Test recovery from expected errors

## Test Cases

### Core Search Module Tests

1. **BM25 Search**
   - Search with simple query text
   - Search with complex query text
   - Search with tag filtering
   - Search with minimum score threshold
   - Test pagination with offset and limit

2. **Semantic Search**
   - Search with embedding-friendly query
   - Test with various threshold values
   - Test with tag filtering
   - Verify embedding generation works

3. **Hybrid Search**
   - Test with various weight configurations
   - Test with reranking enabled/disabled
   - Verify results contain both lexical and semantic matches

### Core Memory Module Tests

1. **Memory Agent**
   - Test conversation storage
   - Test conversation retrieval
   - Test temporal search with various time points
   - Test edge creation with temporal metadata
   - Test contradiction detection and resolution

### CLI Formatting Tests

1. **Search Commands**
   - Test rich table output formatting
   - Test JSON output structure
   - Verify score fields are properly formatted
   - Test pagination output

2. **CRUD Commands**
   - Test document creation confirmation
   - Test retrieval formatting
   - Test update confirmation
   - Test deletion confirmation and prompting

3. **Graph Commands**
   - Test relationship creation confirmation
   - Test traversal result formatting
   - Test visualization helpers if available

## Testing Schedule

1. Core Layer Module Structure Analysis (Day 1)
2. Core Layer Import/Export Testing (Day 1)
3. Core Layer Validation Block Testing (Day 1-2)
4. CLI Layer Output Formatting Tests (Day 2)
5. MCP Layer Response Format Tests (Day 3)
6. Integration Testing Across Layers (Day 3)
7. Documentation and Issue Reporting (Day 4)

## Test Documentation

All test results will be documented with:
- Test case description
- Expected result
- Actual result
- Pass/Fail status
- Any issues or observations
- Screenshots for UI-related tests

## Issue Prioritization

Issues will be categorized as:
- **Critical**: Prevents basic functionality from working
- **High**: Significant impact on usability but has workarounds
- **Medium**: Minor issues that don't prevent functionality
- **Low**: Cosmetic or enhancement suggestions

## Testing Tools

1. Python's built-in `unittest` or `pytest` for automated tests
2. Manual testing for CLI output verification
3. JSON validators for MCP response testing
4. Bash scripts for integration testing

## Post-Testing Actions

1. Document all identified issues
2. Prioritize fixes based on severity
3. Implement fixes for critical and high-priority issues
4. Re-test to verify fixes
5. Update documentation based on testing insights