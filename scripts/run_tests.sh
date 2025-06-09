#!/bin/bash

# ArangoDB Test Runner with Reporting
# Generates test reports in multiple formats

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Set up paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_DIR="$PROJECT_ROOT/tests"
REPORTS_DIR="$PROJECT_ROOT/docs/06_reports/reports"

# Ensure reports directory exists
mkdir -p "$REPORTS_DIR"

# Timestamp for report files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Running ArangoDB Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Run tests with coverage and JSON report
echo -e "\n${YELLOW}Running pytest with coverage...${NC}"
uv run pytest \
    --cov=src/arangodb \
    --cov-report=html \
    --cov-report=term \
    --json-report \
    --json-report-file="test_results_${TIMESTAMP}.json" \
    -v

# Capture exit code
TEST_EXIT_CODE=$?

# Generate markdown report
echo -e "\n${YELLOW}Generating test report...${NC}"
uv run python scripts/generate_test_summary.py \
    --json-file "test_results_${TIMESTAMP}.json" \
    --output-file "$REPORTS_DIR/test_report_${TIMESTAMP}.md"

# Move JSON report to reports directory
mv "test_results_${TIMESTAMP}.json" "$REPORTS_DIR/"

# Display summary
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
else
    echo -e "\n${RED}❌ Some tests failed!${NC}"
fi

echo -e "\n${YELLOW}Reports generated:${NC}"
echo "  - Markdown: $REPORTS_DIR/test_report_${TIMESTAMP}.md"
echo "  - JSON: $REPORTS_DIR/test_results_${TIMESTAMP}.json"
echo "  - Coverage HTML: htmlcov/index.html"

exit $TEST_EXIT_CODE