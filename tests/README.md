# ArangoDB Memory Bank Tests

This directory contains all tests for the ArangoDB Memory Bank project. The test structure mirrors the source code structure in `src/arangodb/` for easy navigation and maintenance.

## Test Structure

```
tests/
├── arangodb/           # Mirrors src/arangodb/
│   ├── cli/           # CLI command tests
│   ├── core/          # Core functionality tests
│   │   ├── graph/     # Graph operations tests
│   │   ├── memory/    # Memory management tests
│   │   ├── search/    # Search functionality tests
│   │   └── utils/     # Utility function tests
│   ├── mcp/           # MCP integration tests
│   ├── qa/            # Q&A module tests
│   ├── qa_generation/ # Q&A generation tests
│   ├── services/      # Service layer tests
│   ├── tasks/         # Task module tests
│   └── visualization/ # Visualization tests
├── data/              # Test data files (JSON, etc.)
├── fixtures/          # Test fixtures
├── integration/       # Integration tests
└── unit/             # Unit tests
```

## Running Tests

### Run All Tests
```bash
# From project root
python -m pytest tests/ -v

# Or using the test runner script
python scripts/testing/run_tests.py
```

### Run Specific Test Categories

#### CLI Tests Only
```bash
python -m pytest tests/arangodb/cli/ -v
```

#### Core Functionality Tests
```bash
python -m pytest tests/arangodb/core/ -v
```

#### Integration Tests
```bash
python -m pytest tests/integration/ -v
```

#### Unit Tests
```bash
python -m pytest tests/unit/ -v
```

### Run Tests with Coverage
```bash
python -m pytest tests/ --cov=arangodb --cov-report=html
```

### Run Tests in Parallel
```bash
python -m pytest tests/ -n auto
```

## Test Requirements

1. **ArangoDB**: Must have ArangoDB running locally on default port (8529)
2. **Test Database**: Tests use `pizza_test` and `memory_bank` databases
3. **Redis**: Required for LiteLLM caching (localhost:6379)
4. **Dependencies**: Install all dependencies with `pip install -e ".[dev]"`

## Writing Tests

### Test Naming Convention
- Test files must be named `test_*.py`
- Test classes should be named `Test*`
- Test methods should be named `test_*`

### No Mocking Policy
Per CLAUDE.md requirements:
- **NEVER mock core functionality**
- Always test with real database connections
- Use actual data, not fake inputs
- Verify outputs against concrete expected results

### Test Organization
- Place tests in directories that mirror the source structure
- Integration tests go in `tests/integration/`
- Unit tests for isolated functions go in `tests/unit/`
- Test data files go in `tests/data/`
- Test fixtures go in `tests/fixtures/`

## Common Test Patterns

### Database Setup
Most tests use fixtures from `conftest.py` that provide:
- `get_test_db()`: Returns a test database connection
- `setup_test_data`: Populates test collections with sample data

### CLI Testing
```python
from typer.testing import CliRunner
from arangodb.cli.main import app

runner = CliRunner()
result = runner.invoke(app, ["command", "subcommand", "--option", "value"])
assert result.exit_code == 0
```

### Async Testing
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected_value
```

## Continuous Integration

Before pushing code:
1. Run all tests: `python -m pytest tests/ -v`
2. Check for any warnings or deprecations
3. Ensure 100% of tests pass
4. No skipped tests (all functionality should be testable)

## Test Data

Test data files are located in `tests/data/`:
- Pizza shop example data for testing general functionality
- Memory/conversation data for testing memory operations
- Graph relationship data for testing graph operations

Setup scripts for test data are in `scripts/setup/test_data/`

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure ArangoDB is running: `sudo systemctl status arangodb3`
   - Check credentials in environment variables

2. **Redis Connection Errors**
   - Ensure Redis is running: `redis-cli ping`
   - Should return "PONG"

3. **Import Errors**
   - Install package in development mode: `pip install -e .`
   - Ensure PYTHONPATH includes project root

4. **Test Discovery Issues**
   - Ensure all test directories have `__init__.py` files
   - Use proper test naming conventions

## Maintenance

- Keep tests synchronized with source code changes
- Remove obsolete tests when features are removed
- Update test data when schemas change
- Document any special test requirements in test docstrings

## Quick Verification

Before committing changes, run:
```bash
# Quick smoke test (fast)
python -m pytest tests/unit/ -v --maxfail=1

# Full test suite
python -m pytest tests/ -v
```

For 100% confidence that nothing is broken:
```bash
python -m pytest tests/arangodb/cli/ -v  # All 96 CLI tests should pass
```