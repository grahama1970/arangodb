# Run tests with comprehensive reporting

Run tests with comprehensive reporting

## Usage

```bash
python -m pytest tests/ -v --tb=short --json-report --json-report-file=test_report.json
```

## Examples

```bash
# In Claude Code:
/project:test [arguments]

# Run all tests with coverage
/project:test --cov=arangodb

# Run specific test module
/project:test tests/arangodb/cli/test_memory_commands.py

# Run with markers
/project:test -m "not slow"

# Run integration tests only
/project:test tests/integration/

# Run with detailed output
/project:test -vvs

# Run and generate HTML report
/project:test --html=report.html --self-contained-html
```

---
*Auto-generated slash command*