# Test Environment Setup Guide

## Overview

This document provides instructions for setting up a proper testing environment for the refactored ArangoDB package. A complete testing environment requires installing dependencies, configuring ArangoDB, and setting up environment variables.

## Requirements

To fully test the ArangoDB package, you need:

1. **Python 3.10+** - Required for all modern language features used in the code
2. **ArangoDB 3.7+** - Required for graph and search features
3. **Redis** (optional) - For caching embeddings to reduce API calls
4. **Embedding API Access** - For generating vector embeddings (OpenAI, Cohere, etc.)

## Setup Steps

### 1. Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### 2. Install Dependencies

There are two ways to install the required dependencies:

#### A. Using the editable install:

```bash
# Install the package and dependencies in development mode
pip install -e .
```

#### B. Using pip with the pyproject.toml:

```bash
# Install build tools
pip install build pip-tools

# Generate requirements from pyproject.toml
pip-compile --output-file=requirements.txt pyproject.toml

# Install requirements
pip install -r requirements.txt
```

### 3. Install Test Dependencies

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

### 4. Setup ArangoDB

#### A. Using Docker:

```bash
# Pull and run ArangoDB Docker image
docker run -e ARANGO_ROOT_PASSWORD=password -p 8529:8529 -d --name arangodb arangodb:latest
```

#### B. Local Installation:

Follow [ArangoDB Installation Guide](https://www.arangodb.com/docs/stable/installation.html) for your operating system.

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```dotenv
# ArangoDB Connection
ARANGO_HOST="http://localhost:8529"
ARANGO_USER="root"
ARANGO_PASSWORD="password"
ARANGO_DB_NAME="doc_retriever"

# Embedding API Keys (choose one based on your provider)
OPENAI_API_KEY="your-openai-api-key"
# COHERE_API_KEY="your-cohere-api-key"
# AZURE_OPENAI_API_KEY="your-azure-openai-api-key"

# Redis Configuration (optional)
# REDIS_HOST="localhost"
# REDIS_PORT="6379"
# REDIS_PASSWORD=""

# Logging Level
LOG_LEVEL="DEBUG"
```

## Testing Workflow

### 1. Basic Import Tests

```bash
# Run the import test script
python src/test_imports.py
```

### 2. Validation Block Tests

```bash
# Run the validation block test script
python src/test_validation_blocks.py
```

### 3. CLI Tests

For testing CLI formatting, you can run commands directly:

```bash
# Test search commands
python -m arangodb.cli.main search bm25 "test query"

# Test CRUD commands (viewing help)
python -m arangodb.cli.main crud --help

# Test with JSON output
python -m arangodb.cli.main search semantic "test query" --json-output
```

### 4. Running Specific Tests

To test specific modules or features:

```bash
# Test a specific core module
python src/arangodb/core/search/bm25_search.py

# Test CLI with specific parameters
python -m arangodb.cli.main memory store --user-message "Hello" --agent-response "World"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure your PYTHONPATH includes the project root:
   ```bash
   export PYTHONPATH=/path/to/arangodb:$PYTHONPATH
   ```

2. **ArangoDB Connection Issues**: Verify ArangoDB is running:
   ```bash
   curl http://localhost:8529/_api/version
   ```

3. **Missing Dependencies**: Install any missing packages:
   ```bash
   pip install <package-name>
   ```

4. **Environment Variables**: Verify .env file is loaded correctly:
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.environ.get('ARANGO_HOST', 'Not set'))"
   ```

## Testing in Docker

For completely isolated testing, you can use Docker Compose to set up both ArangoDB and a Python environment:

```yaml
# docker-compose.yml
version: '3'

services:
  arangodb:
    image: arangodb:latest
    environment:
      - ARANGO_ROOT_PASSWORD=password
    ports:
      - "8529:8529"
    volumes:
      - arangodb_data:/var/lib/arangodb3

  app:
    build: .
    environment:
      - ARANGO_HOST=http://arangodb:8529
      - ARANGO_USER=root
      - ARANGO_PASSWORD=password
      - ARANGO_DB_NAME=doc_retriever
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - .:/app
    command: bash -c "pip install -e . && pytest"
    depends_on:
      - arangodb

volumes:
  arangodb_data:
```

## Continuous Integration

When setting up CI for this project, ensure the CI environment:

1. Has Python 3.10+
2. Installs all dependencies
3. Sets up ArangoDB (in CI container or as a service)
4. Configures all required environment variables
5. Runs tests in the correct order (imports → validation → functionality → CLI)

The test scripts provided in this guide should be adaptable for CI environments with minimal modifications.