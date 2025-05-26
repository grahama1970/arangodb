#!/bin/bash
# Quick test runner for common test scenarios

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}ArangoDB Memory Bank - Quick Test Runner${NC}"
echo "========================================"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Attempting to activate .venv..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}Error: No virtual environment found${NC}"
        exit 1
    fi
fi

# Check if ArangoDB is running
echo -e "\n${YELLOW}Checking ArangoDB connection...${NC}"
if curl -s -u root:password http://localhost:8529/_api/version > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ArangoDB is running${NC}"
else
    echo -e "${RED}✗ ArangoDB is not running or not accessible${NC}"
    echo "Please start ArangoDB before running tests"
    exit 1
fi

# Menu
echo -e "\n${YELLOW}Select test suite to run:${NC}"
echo "1) Quick smoke test (unit + core tests)"
echo "2) All CLI tests"
echo "3) Search functionality tests"
echo "4) Memory agent tests"
echo "5) Integration tests"
echo "6) Full test suite"
echo "7) Full test suite with coverage"
echo "0) Exit"

read -p "Enter choice [0-7]: " choice

case $choice in
    1)
        echo -e "\n${YELLOW}Running quick smoke tests...${NC}"
        python -m pytest tests/unit/ tests/arangodb/core/ -v --maxfail=5 -x
        ;;
    2)
        echo -e "\n${YELLOW}Running CLI tests...${NC}"
        python -m pytest tests/arangodb/cli/ -v
        ;;
    3)
        echo -e "\n${YELLOW}Running search tests...${NC}"
        python -m pytest tests/arangodb/core/search/ -v
        ;;
    4)
        echo -e "\n${YELLOW}Running memory agent tests...${NC}"
        python -m pytest tests/arangodb/core/memory/ -v
        ;;
    5)
        echo -e "\n${YELLOW}Running integration tests...${NC}"
        python -m pytest tests/integration/ -v
        ;;
    6)
        echo -e "\n${YELLOW}Running full test suite...${NC}"
        python tests/run_tests.py
        ;;
    7)
        echo -e "\n${YELLOW}Running full test suite with coverage...${NC}"
        python -m pytest tests/ --cov=arangodb --cov-report=html --cov-report=term-missing
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    0)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Tests passed!${NC}"
else
    echo -e "\n${RED}✗ Tests failed!${NC}"
    exit 1
fi