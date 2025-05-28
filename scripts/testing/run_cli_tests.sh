#!/bin/bash
# Run ArangoDB CLI Tests

echo "=================================================="
echo "ArangoDB CLI Test Suite"
echo "NO MOCKING - All tests use real components"
echo "=================================================="

# Set test database
export ARANGODB_DATABASE="test_memory_db"

# Determine the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../../.."

# Add project to Python path
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Change to test directory
cd "$SCRIPT_DIR"

# Setup test database
echo "Setting up test database..."
python setup_test_db.py

if [ $? -ne 0 ]; then
    echo "Database setup failed!"
    exit 1
fi

echo ""
echo "Running CLI tests..."
echo ""

# Run tests with coverage if requested
if [ "$1" == "--coverage" ]; then
    echo "Running with coverage..."
    pytest -v --cov=arangodb.cli --cov-report=term-missing --cov-report=html:coverage_html .
else
    # Run all tests
    pytest -v --no-header --tb=short -ra .
fi

# Capture exit code
EXIT_CODE=$?

echo ""
echo "=================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL CLI TESTS PASSED"
else
    echo "❌ SOME CLI TESTS FAILED"
fi
echo "=================================================="

exit $EXIT_CODE