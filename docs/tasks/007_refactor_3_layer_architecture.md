# Task 7: Refactor ArangoDB to 3-Layer Architecture ⏳ Not Started

## Overview

This task involves refactoring the ArangoDB project into a clean 3-layer architecture following the completion of the Graphiti integration. The refactoring will separate concerns into core business logic, CLI interface, and MCP integration layers, improving maintainability, testability, and extensibility.

## Objectives

- Restructure the codebase to follow the mandatory 3-layer architecture
- Ensure proper separation of concerns between layers
- Maintain all existing functionality during the refactoring
- Improve code quality and testability
- Ensure independent debugging capabilities for each layer

## Requirements

- Follow the 3-layer architecture principles from `/docs/memory_bank/REFACTOR_3_LAYER.md`
- Use the screenshot example project as a reference for structure
- Maintain all current functionality while improving organization
- Ensure backward compatibility with existing APIs
- Add comprehensive validation in each core module

## Critical Testing and Validation Requirements

This project has strict requirements for testing and validation that MUST be followed:

1. **NO MagicMock**: MagicMock is strictly forbidden for testing core functionality. Use real data and real database connections.
2. **Validation First**: Every feature must be verified to work correctly with real data before proceeding to the next task.
3. **Track ALL Failures**: All validation functions must track and report every failure, not just the first one encountered.
4. **No Unconditional Success Messages**: Never print "All Tests Passed" or similar unless ALL tests have actually passed.
5. **Exit Codes**: Validation functions must exit with code 1 if ANY tests fail and 0 ONLY if ALL tests pass.
6. **External Research After 2 Failures**: If a usage function fails validation 2 times with different approaches, use perplexity_ask tool to get help.
7. **Ask Human After 5 Failures**: If a usage function fails validation 5 times after external research, STOP and ask the human for help. DO NOT continue to the next task.
8. **Results Before Lint**: Functionality must work correctly before addressing any linting issues.
9. **Comprehensive Testing**: Test normal cases, edge cases, and error handling for each function.
10. **Explicit Verification**: Always verify actual results against expected results before reporting success.
11. **Count Reporting**: Include count of failed tests vs total tests in validation output.

## Task Breakdown

### Phase 1: Analysis and Planning ⏳ Not Started

- [ ] Task 1.1: Create a complete inventory of existing functionality
  - [ ] Step 1.1.1: Catalog all CLI commands and their parameters
  - [ ] Step 1.1.2: Identify core business logic functions
  - [ ] Step 1.1.3: Document external dependencies and their uses
  - [ ] Step 1.1.4: Map relationships between modules

- [ ] Task 1.2: Design the new project structure
  - [ ] Step 1.2.1: Create directory structure plan for core, CLI, and MCP layers
  - [ ] Step 1.2.2: Map existing functions to appropriate layers
  - [ ] Step 1.2.3: Identify shared utilities and constants
  - [ ] Step 1.2.4: Plan testing strategy for each layer

- [ ] Task 1.3: Establish refactoring guidelines
  - [ ] Step 1.3.1: Define naming conventions for refactored modules
  - [ ] Step 1.3.2: Document API contracts between layers
  - [ ] Step 1.3.3: Create validation requirements for each module
  - [ ] Step 1.3.4: Set up tracking system for refactoring progress

### Phase 2: Core Layer Implementation ⏳ Not Started

- [ ] Task 2.1: Create core layer directory structure
  - [ ] Step 2.1.1: Create `arangodb/core/` directory with appropriate subdirectories
  - [ ] Step 2.1.2: Set up `__init__.py` files with proper exports
  - [ ] Step 2.1.3: Establish constants and configuration modules
  - [ ] Step 2.1.4: Create validation for directory structure

- [ ] Task 2.2: Implement database operations core modules
  - [ ] Step 2.2.1: Extract pure business logic from `db_operations.py` into core modules
  - [ ] Step 2.2.2: Create `core/db_operations.py` with no UI dependencies
  - [ ] Step 2.2.3: Implement validation functions for all core operations
  - [ ] Step 2.2.4: Add self-validation tests in each module
  - [ ] Step 2.2.5: Test with real data and verify results

- [ ] Task 2.3: Implement search API core modules
  - [ ] Step 2.3.1: Extract business logic from all search API modules
  - [ ] Step 2.3.2: Create dedicated modules for different search types
  - [ ] Step 2.3.3: Implement cross-encoder reranking in core layer
  - [ ] Step 2.3.4: Add validation for all search functions
  - [ ] Step 2.3.5: Test with real queries and verify results

- [ ] Task 2.4: Implement memory agent core functionality
  - [ ] Step 2.4.1: Extract memory agent logic into dedicated core modules
  - [ ] Step 2.4.2: Move validation logic into core utility functions
  - [ ] Step 2.4.3: Ensure proper error handling in core functions
  - [ ] Step 2.4.4: Add comprehensive validation tests
  - [ ] Step 2.4.5: Test with real data and verify results

- [ ] Task 2.5: Implement graph operations core functionality
  - [ ] Step 2.5.1: Extract graph traversal and relationship management
  - [ ] Step 2.5.2: Create dedicated modules for different graph operations
  - [ ] Step 2.5.3: Implement validation tests for all graph functions
  - [ ] Step 2.5.4: Ensure proper error handling
  - [ ] Step 2.5.5: Test with real graph data and verify results

- [ ] Task 2.6: Implement utility functions and shared code
  - [ ] Step 2.6.1: Create core utility modules for common operations
  - [ ] Step 2.6.2: Extract embedding utilities into core layer
  - [ ] Step 2.6.3: Implement logging utilities that work across layers
  - [ ] Step 2.6.4: Create validation module for shared validation logic
  - [ ] Step 2.6.5: Test utilities with real data and verify results

### Phase 3: CLI Layer Implementation ⏳ Not Started

- [ ] Task 3.1: Create CLI layer directory structure
  - [ ] Step 3.1.1: Create `arangodb/cli/` directory with appropriate subdirectories
  - [ ] Step 3.1.2: Set up `__init__.py` files with proper exports
  - [ ] Step 3.1.3: Establish shared CLI utilities
  - [ ] Step 3.1.4: Validate directory structure

- [ ] Task 3.2: Implement CLI commands for database operations
  - [ ] Step 3.2.1: Create Typer commands for all database operations
  - [ ] Step 3.2.2: Implement input validation and error handling
  - [ ] Step 3.2.3: Use rich formatting for human-readable output
  - [ ] Step 3.2.4: Ensure JSON output option for all commands
  - [ ] Step 3.2.5: Test with real data and verify results

- [ ] Task 3.3: Implement CLI commands for search operations
  - [ ] Step 3.3.1: Create commands for all search types
  - [ ] Step 3.3.2: Implement parameter validation and help text
  - [ ] Step 3.3.3: Create rich formatting for search results
  - [ ] Step 3.3.4: Add reranking command options
  - [ ] Step 3.3.5: Test with real queries and verify results

- [ ] Task 3.4: Implement CLI commands for memory agent
  - [ ] Step 3.4.1: Create memory agent command group
  - [ ] Step 3.4.2: Implement all memory operation commands
  - [ ] Step 3.4.3: Add rich formatting for memory display
  - [ ] Step 3.4.4: Ensure proper error handling and validation
  - [ ] Step 3.4.5: Test with real data and verify results

- [ ] Task 3.5: Implement CLI commands for graph operations
  - [ ] Step 3.5.1: Create graph traversal and relationship commands
  - [ ] Step 3.5.2: Implement validation and error handling
  - [ ] Step 3.5.3: Add rich formatting for graph output
  - [ ] Step 3.5.4: Ensure JSON output option
  - [ ] Step 3.5.5: Test with real graph data and verify results

- [ ] Task 3.6: Create CLI formatters and display utilities
  - [ ] Step 3.6.1: Implement rich table formatters for different result types
  - [ ] Step 3.6.2: Create error and warning display utilities
  - [ ] Step 3.6.3: Implement progress indicators for long-running operations
  - [ ] Step 3.6.4: Add consistent styling across all commands
  - [ ] Step 3.6.5: Test formatters with diverse data and verify results

- [ ] Task 3.7: Implement CLI validators and schemas
  - [ ] Step 3.7.1: Create input validation utilities
  - [ ] Step 3.7.2: Implement Pydantic schemas for data structures
  - [ ] Step 3.7.3: Add callback validation for command parameters
  - [ ] Step 3.7.4: Create schema output command for API documentation
  - [ ] Step 3.7.5: Test validators with various inputs and verify results

### Phase 4: MCP Layer Implementation ⏳ Not Started

- [ ] Task 4.1: Create MCP layer directory structure
  - [ ] Step 4.1.1: Create `arangodb/mcp/` directory with appropriate subdirectories
  - [ ] Step 4.1.2: Set up `__init__.py` files with proper exports
  - [ ] Step 4.1.3: Establish MCP utilities and constants
  - [ ] Step 4.1.4: Validate directory structure

- [ ] Task 4.2: Implement MCP server and entry point
  - [ ] Step 4.2.1: Create FastMCP server implementation
  - [ ] Step 4.2.2: Set up server configuration and startup
  - [ ] Step 4.2.3: Implement health check and diagnostics
  - [ ] Step 4.2.4: Add schema endpoint for API documentation
  - [ ] Step 4.2.5: Test server startup and endpoints

- [ ] Task 4.3: Implement MCP tools for database operations
  - [ ] Step 4.3.1: Create MCP wrappers for database operations
  - [ ] Step 4.3.2: Implement proper parameter mapping
  - [ ] Step 4.3.3: Add error handling for MCP context
  - [ ] Step 4.3.4: Ensure consistent response format
  - [ ] Step 4.3.5: Test with real data and verify results

- [ ] Task 4.4: Implement MCP tools for search operations
  - [ ] Step 4.4.1: Create search API MCP functions
  - [ ] Step 4.4.2: Implement reranking MCP tools
  - [ ] Step 4.4.3: Add parameter validation and documentation
  - [ ] Step 4.4.4: Ensure proper error handling
  - [ ] Step 4.4.5: Test with real queries and verify results

- [ ] Task 4.5: Implement MCP tools for memory agent
  - [ ] Step 4.5.1: Create memory agent MCP functions
  - [ ] Step 4.5.2: Map parameters between MCP and core functions
  - [ ] Step 4.5.3: Implement result formatting for MCP
  - [ ] Step 4.5.4: Add error handling for MCP context
  - [ ] Step 4.5.5: Test with real data and verify results

- [ ] Task 4.6: Implement MCP tools for graph operations
  - [ ] Step 4.6.1: Create graph operation MCP functions
  - [ ] Step 4.6.2: Map parameters between MCP and core functions
  - [ ] Step 4.6.3: Add proper documentation for all functions
  - [ ] Step 4.6.4: Ensure consistent error handling
  - [ ] Step 4.6.5: Test with real graph data and verify results

- [ ] Task 4.7: Create MCP wrappers and adapters
  - [ ] Step 4.7.1: Implement adapter functions between MCP and core
  - [ ] Step 4.7.2: Create parameter mapping utilities
  - [ ] Step 4.7.3: Ensure type consistency between layers
  - [ ] Step 4.7.4: Add validation for all MCP inputs
  - [ ] Step 4.7.5: Test adapters with various data and verify results

### Phase 5: Testing and Validation ⏳ Not Started

- [ ] Task 5.1: Create test framework for all layers
  - [ ] Step 5.1.1: Set up testing structure for each layer
  - [ ] Step 5.1.2: Implement test runners for different module types
  - [ ] Step 5.1.3: Create test fixtures and mocks
  - [ ] Step 5.1.4: Establish CI/CD integration
  - [ ] Step 5.1.5: Validate test framework functionality

- [ ] Task 5.2: Implement core layer tests
  - [ ] Step 5.2.1: Create unit tests for all core functions
  - [ ] Step 5.2.2: Test error conditions and edge cases
  - [ ] Step 5.2.3: Verify validation functions
  - [ ] Step 5.2.4: Measure test coverage
  - [ ] Step 5.2.5: Run tests with real data and verify results

- [ ] Task 5.3: Implement CLI layer tests
  - [ ] Step 5.3.1: Test CLI command functionality
  - [ ] Step 5.3.2: Verify formatting and display
  - [ ] Step 5.3.3: Test error handling and validation
  - [ ] Step 5.3.4: Ensure backward compatibility
  - [ ] Step 5.3.5: Run CLI tests with real data and verify results

- [ ] Task 5.4: Implement MCP layer tests
  - [ ] Step 5.4.1: Test MCP function implementations
  - [ ] Step 5.4.2: Verify adapter functions
  - [ ] Step 5.4.3: Test error handling and responses
  - [ ] Step 5.4.4: Validate schema output
  - [ ] Step 5.4.5: Run MCP tests with real data and verify results

- [ ] Task 5.5: Create integration tests
  - [ ] Step 5.5.1: Test cross-layer functionality
  - [ ] Step 5.5.2: Verify end-to-end workflows
  - [ ] Step 5.5.3: Test backward compatibility
  - [ ] Step 5.5.4: Validate performance
  - [ ] Step 5.5.5: Run integration tests with real data and verify results

### Phase 6: Documentation and Deployment ⏳ Not Started

- [ ] Task 6.1: Update documentation
  - [ ] Step 6.1.1: Create detailed documentation for each layer
  - [ ] Step 6.1.2: Update README with new architecture
  - [ ] Step 6.1.3: Document API changes and improvements
  - [ ] Step 6.1.4: Add usage examples for all layers
  - [ ] Step 6.1.5: Verify documentation accuracy and completeness

- [ ] Task 6.2: Create migration guide
  - [ ] Step 6.2.1: Document breaking changes
  - [ ] Step 6.2.2: Provide migration examples
  - [ ] Step 6.2.3: Update import paths and examples
  - [ ] Step 6.2.4: Add transition guidance
  - [ ] Step 6.2.5: Validate guide with test migration

- [ ] Task 6.3: Update deployment and packaging
  - [ ] Step 6.3.1: Update package configuration
  - [ ] Step 6.3.2: Verify dependencies
  - [ ] Step 6.3.3: Test installation process
  - [ ] Step 6.3.4: Update CI/CD pipelines
  - [ ] Step 6.3.5: Verify packaging and deployment

- [ ] Task 6.4: Final validation and release
  - [ ] Step 6.4.1: Perform final validation tests
  - [ ] Step 6.4.2: Create release notes
  - [ ] Step 6.4.3: Tag release version
  - [ ] Step 6.4.4: Deploy updated package
  - [ ] Step 6.4.5: Verify deployment and functionality

## Validation Structure Template

All validation functions MUST follow this structure as per project guidelines:

```python
if __name__ == "__main__":
    import sys
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Basic functionality
    total_tests += 1
    # Test specific functionality with real data
    result = function_to_test(real_data)
    expected = {"expected": "result"}
    if result != expected:
        all_validation_failures.append(f"Basic test: Expected {expected}, got {result}")
    
    # Test 2: Edge case handling
    total_tests += 1
    # Test edge case with real data
    edge_result = function_to_test(edge_case_data)
    edge_expected = {"expected": "edge result"}
    if edge_result != edge_expected:
        all_validation_failures.append(f"Edge case: Expected {edge_expected}, got {edge_result}")
    
    # Test 3: Error handling
    total_tests += 1
    try:
        error_result = function_to_test(invalid_data)
        all_validation_failures.append("Error handling: Expected exception for invalid input, but no exception was raised")
    except ExpectedException:
        # This is expected - test passes
        pass
    except Exception as e:
        all_validation_failures.append(f"Error handling: Expected ExpectedException for invalid input, but got {type(e).__name__}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)  # Exit with success code
```

## Critical Failure Escalation Protocol

For every task implementation:

1. If validation fails once, try a different approach focusing on fixing the specific failures
2. If validation fails a second time with a different approach, USE THE PERPLEXITY_ASK TOOL to get help
3. Document the advice from perplexity_ask and try again with the recommendations
4. If validation still fails for a total of 5 attempts, STOP COMPLETELY and ask the human for help
5. NEVER proceed to the next task without successful validation of the current task
6. BE VERY CLEAR about exactly what is failing when asking for help

This strict policy ensures that we don't waste time on approaches that won't work and get human expertise when needed.

## Usage Table

| Layer | Component | Key Functions | Example Usage |
|-------|-----------|--------------|---------------|
| Core | Database Operations | `connect_to_db()`, `create_document()`, `query_documents()` | `from arangodb.core.db_operations import create_document` |
| Core | Search | `perform_search()`, `rerank_results()`, `hybrid_search()` | `from arangodb.core.search import hybrid_search` |
| Core | Memory | `store_memory()`, `retrieve_memories()`, `find_related()` | `from arangodb.core.memory import store_memory` |
| Core | Graph | `traverse_graph()`, `create_relationship()`, `find_paths()` | `from arangodb.core.graph import traverse_graph` |
| CLI | DB Commands | `db_group`, `add_command()`, `get_command()` | `python -m arangodb.cli.db add --data '{...}'` |
| CLI | Search Commands | `search_group`, `hybrid_command()`, `rerank_command()` | `python -m arangodb.cli.search hybrid "query text" --rerank` |
| CLI | Memory Commands | `memory_group`, `store_command()`, `relate_command()` | `python -m arangodb.cli.memory store "user message" "agent response"` |
| CLI | Graph Commands | `graph_group`, `traverse_command()`, `visualize_command()` | `python -m arangodb.cli.graph traverse "node_id" --depth 2` |
| MCP | DB Tools | `db_create_tool()`, `db_query_tool()` | Used by Claude via MCP protocol |
| MCP | Search Tools | `search_tool()`, `rerank_tool()` | Used by Claude via MCP protocol |
| MCP | Memory Tools | `memory_store_tool()`, `memory_search_tool()` | Used by Claude via MCP protocol |
| MCP | Graph Tools | `graph_traverse_tool()`, `graph_relate_tool()` | Used by Claude via MCP protocol |

## Dependencies

- Completion of Task 6 (Graphiti Integration)
- Understanding of the 3-layer architecture principles
- Familiarity with the existing ArangoDB codebase
- Knowledge of Typer, Rich, and FastMCP libraries

## Timeline

- Phase 1 (Analysis and Planning): 1 week
- Phase 2 (Core Layer Implementation): 2 weeks
- Phase 3 (CLI Layer Implementation): 2 weeks
- Phase 4 (MCP Layer Implementation): 2 weeks
- Phase 5 (Testing and Validation): 1 week
- Phase 6 (Documentation and Deployment): 1 week

Total timeline: 9 weeks

## Success Criteria

- All functionality preserved with improved organization
- Clean separation between core, CLI, and MCP layers
- Comprehensive tests for all layers
- Validation functions in all core modules
- Improved error handling and user feedback
- Consistent formatting and output options
- Complete documentation of the new architecture
- Successful migration with minimal disruption

## Progress Tracking

- Start date: [Future Date - After Task 6]
- Current phase: Planning
- Expected completion: [Start Date + 9 weeks]
- Completion criteria: 
  1. All tasks implemented and verified with real data
  2. All layers properly separated with clean interfaces
  3. All validation functions passing with real data
  4. Documentation updated with new architecture details
  5. Migration guide completed and verified
  6. No MagicMock used anywhere in the codebase

## Summary

This refactoring task will transform the ArangoDB project into a highly maintainable, testable, and extensible 3-layer architecture following the mandatory standards for Claude MCP tools. By separating concerns into core business logic, CLI interface, and MCP integration, we'll improve code quality, enable better testing, and facilitate future enhancements.

---

This task document serves as a memory reference for implementation progress. Update status emojis and checkboxes as tasks are completed to maintain continuity across work sessions.