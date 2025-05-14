#!/bin/bash
# CLI Verification Script
# Runs a series of CLI commands to verify functionality after tests pass

echo "Running CLI verification tests..."

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Array to track failed tests
failed_tests=()

# Function to run test and check result
run_test() {
  local test_name="$1"
  local command="$2"
  local expected_pattern="$3"
  
  echo -e "${CYAN}Testing ${test_name}...${NC}"
  echo -e "${YELLOW}Command: ${command}${NC}"
  
  # Run command and capture output
  output=$(eval "$command" 2>&1)
  result=$?
  
  # Check if command succeeded and output matches expected pattern
  if [ $result -eq 0 ] && echo "$output" | grep -q "$expected_pattern"; then
    echo -e "${GREEN}PASS${NC}"
  else
    echo -e "${RED}FAIL${NC}"
    echo "  Expected pattern: $expected_pattern"
    echo "  Exit code: $result"
    echo "  Actual output: $output"
    failed_tests+=("$test_name")
  fi
  
  echo "" # Add blank line between tests
}

echo "=== Verifying Environment ==="
# Verify environment variables
if [ -z "$ARANGO_HOST" ]; then
  echo -e "${YELLOW}Warning: ARANGO_HOST not set, using default${NC}"
  export ARANGO_HOST="http://localhost:8529"
fi

if [ -z "$ARANGO_USER" ]; then
  echo -e "${YELLOW}Warning: ARANGO_USER not set, using default${NC}"
  export ARANGO_USER="root"
fi

if [ -z "$ARANGO_PASSWORD" ]; then
  echo -e "${YELLOW}Warning: ARANGO_PASSWORD not set, using default${NC}"
  export ARANGO_PASSWORD="openSesame"
fi

if [ -z "$ARANGO_DB_NAME" ]; then
  echo -e "${YELLOW}Warning: ARANGO_DB_NAME not set, using default${NC}"
  export ARANGO_DB_NAME="memory_bank"
fi

if [ -z "$EMBEDDING_DIMENSION" ]; then
  echo -e "${YELLOW}Warning: EMBEDDING_DIMENSION not set, using default${NC}"
  export EMBEDDING_DIMENSION=1024
fi

echo "=== Starting CLI Verification ==="

# Run verification tests
run_test "help display" \
  "python -m complexity.cli --help" \
  "Usage:"

run_test "database connection" \
  "python -m complexity.cli db-status" \
  "Connected"

# Basic search tests
run_test "keyword search" \
  "python -m complexity.cli search keyword 'python programming' --limit 3" \
  "results"

run_test "semantic search" \
  "python -m complexity.cli search semantic 'database concepts' --limit 3" \
  "results"

run_test "hybrid search" \
  "python -m complexity.cli search hybrid 'graph database' --limit 3" \
  "results"

run_test "tag search" \
  "python -m complexity.cli search tags python,database --limit 3" \
  "results"

# Embedding test
run_test "embedding generation" \
  "python -m complexity.cli generate-embedding 'Test sentence' --verbose" \
  "embedding"

# Document operations - create, retrieve, delete
echo "=== Testing Document Operations ==="
echo -e "${YELLOW}Creating test document...${NC}"
create_output=$(python -m complexity.cli create-document --title "Test Document" --content "This is a test document for CLI verification" --tags "test,verification" 2>&1)
doc_id=$(echo "$create_output" | grep -oP '(?<=Created document with ID: )[^ ]+')

if [ -n "$doc_id" ]; then
  echo -e "${GREEN}Document created with ID: $doc_id${NC}"
  
  # Test document retrieval
  run_test "document retrieval" \
    "python -m complexity.cli get-document $doc_id" \
    "Test Document"
  
  # Test document deletion
  run_test "document deletion" \
    "python -m complexity.cli delete-document $doc_id" \
    "Document deleted"
else
  echo -e "${RED}Failed to create test document for verification${NC}"
  echo "Output: $create_output"
  failed_tests+=("document creation")
fi

# Test error handling
run_test "invalid search type error" \
  "python -m complexity.cli search invalid-type 'test query' 2>&1" \
  "Invalid search type"

run_test "non-existent document error" \
  "python -m complexity.cli get-document non-existent-id-123 2>&1" \
  "not found"

# Report results
echo "=== CLI Verification Results ==="
if [ ${#failed_tests[@]} -eq 0 ]; then
  echo -e "${GREEN}All CLI verification tests passed!${NC}"
  exit 0
else
  echo -e "${RED}Some CLI verification tests failed:${NC}"
  for test in "${failed_tests[@]}"; do
    echo "  - $test"
  done
  exit 1
fi