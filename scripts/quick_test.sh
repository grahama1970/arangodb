#!/bin/bash

# Quick test runner for specific test categories
# Usage: ./quick_test.sh [marker]
# Example: ./quick_test.sh unit

set -e

MARKER=${1:-""}
PROJECT_ROOT="$(dirname "$(dirname "$0")")"

cd "$PROJECT_ROOT"

if [ -z "$MARKER" ]; then
    echo "Running all tests..."
    uv run pytest -v
else
    echo "Running tests marked as: $MARKER"
    uv run pytest -v -m "$MARKER"
fi