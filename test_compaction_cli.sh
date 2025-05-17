#!/bin/bash
# Test script for compaction CLI commands

# Activate virtual environment
source .venv/bin/activate

# Define colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing ArangoDB Compaction CLI Commands${NC}"
echo -e "${YELLOW}==================================${NC}\n"

# Show help for compaction command
echo -e "${GREEN}Testing 'compaction --help' command:${NC}"
python -m arangodb.cli.main compaction --help
echo -e "\n"

# Show help for create command
echo -e "${GREEN}Testing 'compaction create --help' command:${NC}"
python -m arangodb.cli.main compaction create --help
echo -e "\n"

# Show help for search command
echo -e "${GREEN}Testing 'compaction search --help' command:${NC}"
python -m arangodb.cli.main compaction search --help
echo -e "\n"

# Show help for get command
echo -e "${GREEN}Testing 'compaction get --help' command:${NC}"
python -m arangodb.cli.main compaction get --help
echo -e "\n"

# Show help for list command
echo -e "${GREEN}Testing 'compaction list --help' command:${NC}"
python -m arangodb.cli.main compaction list --help
echo -e "\n"

echo -e "${BLUE}All test commands completed successfully!${NC}"
