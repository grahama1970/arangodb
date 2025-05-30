# ArangoDB Memory Bank Tests

This directory contains the comprehensive test suite for the ArangoDB Memory Bank project.

## Test Structure

The test directory structure **mirrors the source directory structure exactly** for easy navigation:

```
tests/
├── arangodb/
│   ├── cli/                    # CLI command tests
│   ├── core/                   # Core functionality tests
│   │   ├── graph/             # Graph operations tests
│   │   ├── memory/            # Memory agent tests
│   │   ├── search/            # Search algorithm tests
│   │   └── utils/             # Utility function tests
│   ├── mcp/                   # MCP integration tests
│   ├── qa_generation/         # Q&A generation tests
│   ├── qa_graph_integration/  # Q&A graph integration tests
│   ├── services/              # Service layer tests
│   ├── tasks/                 # Task tests
│   └── visualization/         # Visualization tests
├── data/                      # Test data fixtures (pizza shop data)
├── fixtures/                  # JSON fixtures for tests
├── integration/               # Integration tests
└── unit/                      # Unit tests
```

## Running Tests

### Prerequisites
```bash
# Ensure environment is set up
source .venv/bin/activate
cd /home/graham/workspace/experiments/arangodb

# Verify PYTHONPATH is set
grep PYTHONPATH .env  # Should show: PYTHONPATH=./src
```

### Run All Tests
```bash
# From project root - run all 96 tests
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ --cov=arangodb --cov-report=html

# Show output during tests
python -m pytest tests/ -v -s
```

### Run Specific Test Categories

```bash
# CLI tests only (96 tests)
python -m pytest tests/arangodb/cli/ -v

# Core functionality tests
python -m pytest tests/arangodb/core/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# Unit tests only
python -m pytest tests/unit/ -v
```

### Run Individual Test Files

```bash
# Memory command tests
python -m pytest tests/arangodb/cli/test_memory_commands.py -v

# Search tests
python -m pytest tests/arangodb/core/search/test_integrated_semantic_search.py -v

# Visualization tests
python -m pytest tests/arangodb/visualization/ -v
```

### Quick Verification Before Push

```bash
# Fast check - run CLI tests (most comprehensive)
python -m pytest tests/arangodb/cli/test_all_cli_commands.py -v

# Full verification - all tests must pass
python -m pytest tests/ -v --tb=short

# Expected output: 96 passed (for CLI tests alone)
```

## Test Database Setup

Before running tests, ensure the test database is set up:

```bash
# From project root
cd tests/data

# Setup pizza test database
python setup_pizza_database.py

# Or use the enhanced version with more data
python setup_enhanced_pizza_database.py

# Load test data
python load_pizza_data.py

# Create embeddings for test collections
python embed_collections.py
```

## Environment Variables

Tests use the following environment variables from `.env`:

```bash
PYTHONPATH=./src
ARANGO_TEST_DB_NAME=pizza_test
ARANGO_HOST=http://localhost:8529
ARANGO_USER=root
ARANGO_PASSWORD=your_password
```

## Test Guidelines

1. **No Mocking**: Tests use real database operations - no mocking of core functionality
2. **Isolation**: Each test should be independent and not rely on other tests
3. **Cleanup**: Tests should clean up after themselves
4. **Real Data**: Tests use realistic data from the pizza database fixture
5. **Mirror Structure**: Test files must be in the same relative location as the source files they test

## Common Test Issues and Solutions

### ArangoSearch Timing Issues
Some tests may fail due to ArangoSearch eventual consistency:
```python
# Tests include sleep delays for indexing
time.sleep(3)  # Wait for ArangoSearch to index documents
```

### Import Errors
```bash
# Ensure PYTHONPATH is set
echo $PYTHONPATH  # Should show: ./src

# If not, source the .env file
set -a && source .env && set +a
```

### Database Connection Errors
```bash
# Check ArangoDB is running
docker ps | grep arangodb

# Test connection
python -m arangodb.cli.main health
```

## Continuous Integration Checklist

Before pushing to GitHub, ensure:

✅ **All tests pass**
```bash
python -m pytest tests/ -v
# Should show: XX passed, 0 failed
```

✅ **No skipped tests**
```bash
python -m pytest tests/ -v | grep -i skip
# Should show no results
```

✅ **Good test coverage**
```bash
python -m pytest tests/ --cov=arangodb --cov-report=term-missing
# Target: >80% coverage
```

✅ **Code is formatted**
```bash
black src/ tests/
isort src/ tests/
```

✅ **No linting errors**
```bash
ruff check src/ tests/
```

## Writing New Tests

When adding new functionality:

1. Create test file in the corresponding test directory
2. Use the same naming convention: `test_<module_name>.py`
3. Import the module being tested
4. Write tests using real data, not mocks
5. Ensure tests are self-contained and repeatable

Example test structure:
```python
"""Test module for X functionality."""

import pytest
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.some_module import some_function

class TestSomeFeature:
    """Test cases for some feature."""
    
    @pytest.fixture
    def test_db(self):
        """Provide test database connection."""
        return get_db_connection(db_name="pizza_test")
    
    def test_basic_functionality(self, test_db):
        """Test basic functionality works."""
        result = some_function(test_db, "input")
        assert result == "expected"
        assert len(result) > 0
```

## Test Organization

- **tests/arangodb/**: Mirrors src/arangodb/ structure exactly
- **tests/integration/**: Cross-module integration tests
- **tests/unit/**: Isolated unit tests
- **tests/data/**: Test data setup scripts and fixtures
- **tests/fixtures/**: JSON fixtures for search tests

## Troubleshooting

### Test Failures
1. Check logs in `logs/` directory
2. Run failing test with `-s` flag to see output
3. Verify test database is properly set up
4. Ensure all dependencies are installed: `uv sync`

### Slow Tests
- First run may be slow due to embedding model download
- Use `pytest-xdist` for parallel execution: `pytest -n auto`

### Memory Issues
- Some tests create large datasets
- Run tests in smaller batches if needed
- Clear test data between runs if necessary

## Summary

The test suite ensures all functionality works correctly with real database operations. Always run tests before pushing changes, and maintain the mirror structure between src/ and tests/ directories.