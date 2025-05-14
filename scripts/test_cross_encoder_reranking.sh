#!/bin/bash

# Test script for cross-encoder reranking functionality
# This script tests the cross-encoder reranking feature in the CLI

echo "=== Testing Cross-Encoder Reranking ==="
echo

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test basic hybrid search first (without reranking)
echo -e "${YELLOW}Testing standard hybrid search (no reranking)...${NC}"
python -m arangodb.cli search hybrid "database optimization techniques" --top-n 3

# Wait for a moment
sleep 2
echo
echo "================================================="
echo

# Test with reranking enabled
echo -e "${YELLOW}Testing hybrid search with default reranking...${NC}"
python -m arangodb.cli search hybrid "database optimization techniques" --rerank --top-n 3

# Wait for a moment
sleep 2
echo
echo "================================================="
echo

# Test with a different reranking model
echo -e "${YELLOW}Testing hybrid search with alternative reranking model...${NC}"
python -m arangodb.cli search hybrid "database optimization techniques" --rerank --rerank-model "cross-encoder/ms-marco-TinyBERT-L-2-v2" --top-n 3

# Wait for a moment
sleep 2
echo
echo "================================================="
echo

# Test with different reranking strategy
echo -e "${YELLOW}Testing hybrid search with weighted reranking strategy...${NC}"
python -m arangodb.cli search hybrid "database optimization techniques" --rerank --rerank-strategy "weighted" --top-n 3

# Wait for a moment
sleep 2
echo
echo "================================================="
echo

# Test with json output
echo -e "${YELLOW}Testing hybrid search with JSON output...${NC}"
python -m arangodb.cli search hybrid "database optimization techniques" --rerank --json-output | head -20

echo
echo -e "${GREEN}===== All tests completed =====${NC}"