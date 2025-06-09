# Test Reporting Guide

This guide explains how to run comprehensive tests and generate detailed markdown reports that verify all functionality is working correctly and provides evidence of real (non-hallucinated) results.

## Quick Start

### Simple One-Command Test Verification

```bash
# Run all tests and generate report
python scripts/run_full_test_report.py

# Run quick tests only (faster)
python scripts/run_full_test_report.py --quick

# Run specific test suite
python scripts/run_full_test_report.py --suite cli
```

## What the Reports Show

The generated markdown reports include:

### 1. **Test Summary Table**
- Total tests, passed, failed, errors, skipped
- Success rate and overall status
- Test execution time and duration

### 2. **Detailed Results Table**
- Each test with pass/fail status
- ArangoDB query results and evidence
- Error messages and assertion details
- Test execution times

### 3. **ArangoDB Query Evidence**
- Actual database queries executed during tests
- Real query results (not mocked or hallucinated)
- Number of database operations per test
- Query performance information

### 4. **Failure Analysis**
- Detailed breakdown of any failed tests
- Expected vs. actual outputs
- Full error traces and debugging information
- ArangoDB query results that led to failures

## Report Structure

Reports follow the Task List Template Guide format:

```markdown
# Test Results Report

## Test Suite Summary
| Metric | Value |
|--------|-------|
| Test Suite | complete_test_suite |
| Total Tests | 45 |
| ✅ Passed | 42 |
| ❌ Failed | 3 |
| Success Rate | 93.3% |

## Detailed Test Results
| Test ID | Module | Status | Duration | ArangoDB Results | Assertion Details |
|---------|--------|--------|----------|------------------|-------------------|
| TEST001 | core.memory | ✅ PASS | 0.234s | 2 queries<br/>Q1: [1 item: {_id: memories/123}] | Expected 1 memory, got 1 |
| TEST002 | core.search | ❌ FAIL | 1.456s | 1 query<br/>Q1: [] | Expected 5 results, got 0 |

## ArangoDB Summary
| Metric | Value |
|--------|-------|
| Total Queries | 127 |
| Tests with DB Access | 38/45 |
| Avg Queries per Test | 3.3 |
```

## Usage Examples

### Run Full Test Suite
```bash
# All tests with complete report
python scripts/run_full_test_report.py

# Output will be saved to test_reports/test_report_complete_test_suite_YYYYMMDD_HHMMSS.md
```

### Run Quick Verification
```bash
# Quick smoke test (unit + core tests only)
python scripts/run_full_test_report.py --quick

# Faster execution, covers essential functionality
```

### Run Specific Test Categories
```bash
# CLI tests only
python scripts/run_full_test_report.py --suite cli

# Core functionality tests
python scripts/run_full_test_report.py --suite core

# Integration tests
python scripts/run_full_test_report.py --suite integration
```

### Custom Output Directory
```bash
# Save reports to specific directory
python scripts/run_full_test_report.py --output custom_reports/
```

## Interactive Test Menu

For interactive testing, use:
```bash
./scripts/run_quick_tests.sh
```

This provides a menu with options:
1. Quick smoke test
2. All CLI tests  
3. Search functionality tests
4. Memory agent tests
5. Integration tests
6. Full test suite
7. Full test suite with coverage

## Understanding Test Results

### ✅ PASS Status
- Test executed successfully
- All assertions passed
- ArangoDB queries returned expected results
- No errors or exceptions

### ❌ FAIL Status  
- Test executed but assertions failed
- Expected results didn't match actual results
- ArangoDB queries may have returned unexpected data
- Detailed failure information in report

### ⚠️ ERROR Status
- Test could not complete due to exceptions
- System errors or configuration issues
- ArangoDB connection problems
- Code errors or missing dependencies

### ⏭️ SKIP Status
- Test was skipped (usually due to missing requirements)
- Conditional tests that don't apply
- Tests disabled for current environment

## ArangoDB Evidence

The reports capture real database evidence:

### Query Logging
```markdown
**ArangoDB Queries** (3 queries):

**Query 1**:
```aql
FOR doc IN memories 
FILTER doc.content == "test memory"
RETURN doc
```
**Result**: [1 item: {_id: memories/123456, keys: [content, timestamp]}]

**Query 2**:
```aql
INSERT {content: "new memory", timestamp: DATE_NOW()} INTO memories
```
**Result**: {_id: memories/789012, _key: 789012}
```

### Performance Data
- Query execution times
- Number of documents processed
- Database operations per test
- Memory usage during tests

## CI/CD Integration

For automated testing in CI/CD pipelines:

```bash
# Run tests and check exit code
python scripts/run_full_test_report.py
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "❌ Tests failed - check report"
    exit 1
fi
```

## Troubleshooting

### Common Issues

1. **ArangoDB Not Running**
   ```
   Error: Cannot connect to ArangoDB
   Solution: Start ArangoDB server on localhost:8529
   ```

2. **No Test Results**
   ```
   Error: No tests found
   Solution: Check test paths exist in tests/ directory
   ```

3. **Import Errors**
   ```
   Error: ModuleNotFoundError
   Solution: Install project in editable mode: uv pip install -e .
   ```

### Debug Mode

Run with maximum verbosity:
```bash
# Add debug flags
python scripts/run_full_test_report.py --suite core 2>&1 | tee debug.log
```

## Report Analysis

### Identifying Issues

1. **Check Success Rate**: Should be > 95% for stable project
2. **Review Failed Tests**: Look for patterns in failures
3. **Analyze ArangoDB Results**: Verify database operations are working
4. **Check Error Messages**: Look for configuration or dependency issues

### Example Analysis

```markdown
## Analysis Example

**Success Rate**: 87% (39/45 tests passed)
**Key Issues**:
- 4 search tests failing: returning 0 results instead of expected results
- 2 memory tests failing: ArangoDB connection timeouts

**Root Cause**: Vector index not properly configured
**Action**: Run setup scripts to rebuild indexes
```

## Best Practices

1. **Run Before Commits**: Always run quick tests before pushing code
2. **Full Suite Weekly**: Run complete test suite weekly
3. **Monitor Trends**: Track success rates over time
4. **Archive Reports**: Keep historical reports for comparison
5. **Review Failures**: Don't ignore intermittent failures

## Integration with Development Workflow

```bash
# Pre-commit verification
python scripts/run_full_test_report.py --quick
if [ $? -eq 0 ]; then
    git commit -m "Feature: xyz"
else
    echo "Tests failed - fix before committing"
fi

# Weekly full verification
python scripts/run_full_test_report.py
```

---

This reporting system ensures all functionality is verified with real database evidence, providing confidence that the system is working correctly and nothing is broken or hallucinated.