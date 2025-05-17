# ArangoDB Tests

This directory contains all tests for the ArangoDB project, organized to mirror the source code structure.

## Test Structure

```
tests/
├── cli/           # Tests for CLI commands
├── core/          # Tests for core functionality
│   ├── graph/     # Graph operations tests
│   ├── memory/    # Memory agent tests
│   ├── search/    # Search functionality tests
│   └── utils/     # Utility function tests
├── mcp/           # MCP integration tests
├── integration/   # Integration tests
├── unit/          # Unit tests
├── fixtures/      # Test data and fixtures
├── validate/      # Validation scripts
└── conftest.py    # Pytest configuration
```

## Running Tests

### Run all tests
```bash
python tests/run_tests.py
```

### Run specific test module
```bash
python tests/run_tests.py tests/cli/
python tests/run_tests.py tests/core/search/
```

### Run tests with specific pattern
```bash
python tests/run_tests.py -k "search"
python tests/run_tests.py -k "memory and not integration"
```

### Run with coverage
```bash
python tests/run_tests.py --cov=arangodb --cov-report=html
```

## Test Categories

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test interaction between modules
- **CLI Tests**: Test command-line interface functionality
- **Validation Scripts**: Scripts to validate module functionality with real data

## Writing Tests

1. Place tests in the appropriate directory mirroring the source structure
2. Use descriptive test names: `test_<functionality>_<condition>_<expected_result>`
3. Use fixtures from `conftest.py` for common setup
4. Add test data to `fixtures/` directory
5. Follow the existing test patterns in each module

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `arangodb_test_db`: Provides test database connection
- `test_data_dir`: Path to test fixtures directory

## Environment

Tests use a separate test database (`test_arangodb`) to avoid interfering with development data.