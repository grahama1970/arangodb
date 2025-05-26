# ArangoDB Memory Bank - Test Suite

This directory contains all tests for the ArangoDB Memory Bank project. Tests are organized to mirror the `src/arangodb/` structure for consistency and easy navigation.

## Directory Structure

```
tests/
├── arangodb/              # Mirrors src/arangodb structure
│   ├── cli/              # CLI command tests
│   ├── core/             # Core functionality tests
│   │   ├── graph/        # Graph operations
│   │   ├── memory/       # Memory agent
│   │   ├── search/       # Search functionality
│   │   └── utils/        # Utilities
│   ├── mcp/              # MCP integration tests
│   ├── qa/               # Q&A module tests
│   ├── qa_generation/    # Q&A generation tests
│   ├── test_modules/     # Test-specific modules
│   └── visualization/    # Visualization tests
├── data/                  # Test data and database setup
├── fixtures/              # Test fixtures (JSON files)
├── integration/           # Cross-module integration tests
└── unit/                  # Pure unit tests
```

## Test Organization Principle

**The test directory mirrors the source directory structure:**
- `src/arangodb/cli/` → `tests/arangodb/cli/`
- `src/arangodb/core/memory/` → `tests/arangodb/core/memory/`
- `src/arangodb/visualization/` → `tests/arangodb/visualization/`

This makes it easy to find tests for any module.

## Running Tests

### Prerequisites

1. **ArangoDB Running**: Ensure ArangoDB is running on `http://localhost:8529`
   ```bash
   # Check ArangoDB status
   curl -u root:password http://localhost:8529/_api/version
   ```

2. **Environment Setup**: Activate the project virtual environment
   ```bash
   cd /path/to/arangodb
   source .venv/bin/activate  # or `uv venv` if using uv
   ```

3. **Install Dependencies**: Ensure all dependencies are installed
   ```bash
   uv pip install -e .  # Install project in editable mode
   uv pip install pytest pytest-asyncio pytest-cov
   ```

### Quick Test Menu

Use the interactive test runner:
```bash
./scripts/run_quick_tests.sh
```

This provides options for:
1. Quick smoke test (unit + core tests)
2. All CLI tests
3. Search functionality tests
4. Memory agent tests
5. Integration tests
6. Full test suite
7. Full test suite with coverage

### Running All Tests

```bash
# From project root
python -m pytest tests/ -v

# Or using the test runner
python tests/run_tests.py

# With coverage report
python -m pytest tests/ --cov=arangodb --cov-report=html
```

### Running Specific Test Categories

```bash
# CLI tests
python -m pytest tests/arangodb/cli/ -v

# Core functionality tests
python -m pytest tests/arangodb/core/ -v

# Search tests
python -m pytest tests/arangodb/core/search/ -v

# Memory agent tests
python -m pytest tests/arangodb/core/memory/ -v

# Visualization tests
python -m pytest tests/arangodb/visualization/ -v

# Integration tests
python -m pytest tests/integration/ -v
```

### Running Individual Test Files

```bash
# Specific test file
python -m pytest tests/arangodb/core/memory/test_memory_agent_integration.py -v

# Specific test function
python -m pytest tests/arangodb/core/search/test_integrated_semantic_search.py::test_semantic_search -v
```

### Test Markers and Filtering

```bash
# Run only fast tests
python -m pytest tests/ -m "not slow" -v

# Run tests matching a pattern
python -m pytest tests/ -k "search" -v

# Skip integration tests
python -m pytest tests/ -m "not integration" -v
```

### Environment Variables

Set these environment variables if your ArangoDB setup differs from defaults:

```bash
export ARANGO_HOST=http://localhost:8529
export ARANGO_USER=root
export ARANGO_PASSWORD=password
export ARANGO_DB=natrium_arangodb  # Test database name
```

## Test Categories

### Module Tests (`tests/arangodb/`)
- Mirror the source code structure
- Test specific module functionality
- May include both unit and integration aspects

### Integration Tests (`tests/integration/`)
- Test interactions between multiple modules
- Complete workflow tests
- End-to-end scenarios

### Unit Tests (`tests/unit/`)
- Pure unit tests with no external dependencies
- Fast, isolated tests
- Focus on individual functions/methods

### Data Directory (`tests/data/`)
- Test datasets (e.g., pizza database)
- Database setup scripts
- Sample data for testing

## Writing New Tests

### Test Placement
1. **Module-specific tests**: Place in the corresponding test directory
   - Testing `src/arangodb/core/memory/memory_agent.py`?
   - Create `tests/arangodb/core/memory/test_memory_agent.py`

2. **Cross-module tests**: Place in `tests/integration/`

3. **Pure unit tests**: Place in `tests/unit/`

### Test File Naming
- Prefix with `test_` (e.g., `test_new_feature.py`)
- Match the source file name when possible
- Use descriptive names for integration tests

### Test Function Naming
```python
def test_function_name_describes_what_is_tested():
    """Test that specific functionality works correctly."""
    # Arrange
    # Act
    # Assert
```

### Using Fixtures
```python
import pytest
from arangodb.core import db_operations

@pytest.fixture
def test_db():
    """Create and cleanup test database."""
    db = db_operations.ensure_database("test_db")
    yield db
    # Cleanup after test
    db_operations.delete_database("test_db")

def test_with_database(test_db):
    """Test using the database fixture."""
    assert test_db is not None
```

## Common Test Patterns

### Testing CLI Commands
```python
def test_cli_command():
    result = subprocess.run(
        ["python", "-m", "arangodb", "memory", "add", "--content", "test"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Success" in result.stdout
```

### Testing Async Functions
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Testing with Real Data
```python
def test_with_real_data():
    # Always use real data, never mock core functionality
    data = load_test_data("tests/data/memories.json")
    result = process_data(data)
    assert len(result) > 0
```

## Troubleshooting

### Common Issues

1. **ArangoDB Connection Error**
   ```
   Error: Cannot connect to ArangoDB
   Solution: Ensure ArangoDB is running and credentials are correct
   ```

2. **Import Errors**
   ```
   Error: ModuleNotFoundError: No module named 'arangodb'
   Solution: Install project in editable mode: uv pip install -e .
   ```

3. **Test Database Already Exists**
   ```
   Error: Database 'test_db' already exists
   Solution: Clean up test databases: python scripts/cleanup_test_dbs.py
   ```

### Debug Mode

Run tests with detailed output:
```bash
# Maximum verbosity
python -m pytest tests/ -vvv

# Show print statements
python -m pytest tests/ -s

# Drop into debugger on failure
python -m pytest tests/ --pdb
```

## Continuous Integration

For CI/CD pipelines, use:
```bash
# Run all tests with coverage and junit output
python -m pytest tests/ \
    --cov=arangodb \
    --cov-report=xml \
    --cov-report=term-missing \
    --junit-xml=test-results.xml
```

## Maintaining Tests

1. **Keep Tests Fast**: Unit tests should run in < 1 second
2. **Use Real Data**: Follow project standards - no mocking core functionality
3. **Clean Up**: Always clean up test data after tests
4. **Document Complex Tests**: Add docstrings explaining test purpose
5. **Update Tests**: When adding features, add corresponding tests
6. **Mirror Structure**: Keep test directory structure in sync with src

## Test Coverage Goals

- Unit Tests: 80%+ coverage
- Integration Tests: Cover all major workflows
- CLI Tests: 100% of commands tested
- Edge Cases: Test error conditions and boundaries

## Quick Test Verification

Before pushing changes, run this quick verification:
```bash
# Fast smoke test (< 30 seconds)
python -m pytest tests/unit/ tests/arangodb/core/ -v --maxfail=1

# Full test suite (may take several minutes)
python tests/run_tests.py
```

---

For more information about the project structure and development guidelines, see the main [README.md](../README.md) and [CLAUDE.md](../CLAUDE.md).