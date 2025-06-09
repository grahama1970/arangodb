# ArangoDB Python API Documentation

## Overview

The ArangoDB Python interface provides a comprehensive API for interacting with ArangoDB databases. The API is organized into three layers:

1. **Core Layer**: Direct Python functions for database operations
2. **CLI Layer**: Command-line interface with JSON and table output formats
3. **MCP Layer**: Model Context Protocol integration for Claude

## Installation

```bash
git clone https://github.com/yourusername/arangodb-python
cd arangodb-python
uv sync
```

## Core Layer API

### Database Connection

```python
from arangodb.core.arango_setup import connect_arango, ensure_database

# Connect to ArangoDB
client = connect_arango(
    host='localhost',
    port=8529,
    username='root',
    password='password'
)

# Ensure database exists
db = ensure_database(client, db_name='your_database')
```

### Document Operations

```python
from arangodb.core.db_operations import (
    add_document,
    get_document,
    update_document,
    delete_document,
    search_documents
)
from arangodb.core.constants import COLLECTION_NAME

# Add a document
doc = {
    "_key": "unique_key",
    "title": "Document Title",
    "content": "Document content",
    "tags": ["tag1", "tag2"]
}
result = add_document(db, COLLECTION_NAME, doc)

# Get a document
document = get_document(db, COLLECTION_NAME, "unique_key")

# Update a document
updates = {"content": "Updated content"}
update_result = update_document(db, COLLECTION_NAME, "unique_key", updates)

# Delete a document
delete_result = delete_document(db, COLLECTION_NAME, "unique_key")

# Search documents
results = search_documents(db, query="search text", limit=10)
```

### Search Operations

```python
from arangodb.core.search.hybrid_search import hybrid_search
from arangodb.core.search.semantic_search import semantic_search
from arangodb.core.search.bm25_search import bm25_search

# BM25 text search
bm25_results = bm25_search(
    db=db,
    query="python programming",
    limit=10,
    search_fields=["content", "title"],
    filter_expression=None
)

# Semantic search (vector similarity)
semantic_results = semantic_search(
    db=db,
    query="how to implement algorithms",
    top_n=10,
    min_score=0.5
)

# Hybrid search (combines multiple methods)
hybrid_results = hybrid_search(
    db=db,
    query="python tutorials",
    search_type=2,  # 0=text, 1=semantic, 2=combined
    top_n=10,
    tag_list=["python", "tutorial"]
)
```

### Graph Operations

```python
from arangodb.core.graph.graph_operations import (
    create_relationship,
    traverse_relationships,
    get_relationship,
    update_relationship,
    delete_relationship
)

# Create a relationship
relationship = create_relationship(
    db=db,
    from_key="doc1",
    to_key="doc2",
    relationship_type="references",
    rationale="Document 1 references Document 2",
    edge_attributes={"weight": 0.8}
)

# Traverse relationships
connections = traverse_relationships(
    db=db,
    start_key="doc1",
    direction="outbound",  # "inbound", "outbound", or "any"
    edge_types=["references", "related_to"],
    max_depth=2
)

# Get a specific relationship
edge = get_relationship(db, edge_key="edge_12345")

# Update relationship
update_relationship(db, edge_key="edge_12345", {"weight": 0.9})

# Delete relationship
delete_relationship(db, edge_key="edge_12345")
```

### Memory Operations

```python
from arangodb.core.memory.memory_agent import MemoryAgent

# Initialize memory agent
memory_agent = MemoryAgent(db=db)

# Add memories to runtime
memory_agent.messages_runtime.add({
    "conversation_id": "conv_001",
    "role": "user",
    "content": "How do I use Python?",
    "context": {"topic": "programming"}
})

memory_agent.messages_runtime.add({
    "conversation_id": "conv_001",
    "role": "assistant",
    "content": "Python is a high-level programming language...",
    "context": {"topic": "programming"}
})

# Process and store memories
memories = [{
    "conversation_id": "conv_001",
    "topics": ["python", "programming"],
    "importance": 0.8,
    "memory_text": "User learning Python programming basics",
    "metadata": {"session": "tutorial"}
}]
memory_agent.add_memories_workflow(memories)

# Search memories
results = memory_agent.search_memories_workflow(
    query="Python programming",
    top_n=10,
    include_calendar=False
)

# Get conversation history
history = memory_agent.get_messages(
    conversation_id="conv_001",
    limit=10
)
```

## CLI Reference

The CLI provides command-line access to all API functions with JSON output support.

### Basic Usage

```bash
python -m arangodb.cli.main [COMMAND] [OPTIONS]
```

### Available Commands

#### CRUD Operations
```bash
# Add document
python -m arangodb.cli.main crud add-lesson \
  --data '{"title": "Test", "content": "Content"}' \
  --json-output

# Get document
python -m arangodb.cli.main crud get-lesson KEY --json-output

# Update document
python -m arangodb.cli.main crud update-lesson KEY \
  --data '{"content": "Updated"}' \
  --json-output

# Delete document
python -m arangodb.cli.main crud delete-lesson KEY --yes --json-output
```

#### Search Operations
```bash
# Keyword search
python -m arangodb.cli.main search keyword \
  --query "search text" \
  --limit 10 \
  --json-output

# Semantic search
python -m arangodb.cli.main search semantic \
  --query "find similar documents" \
  --limit 5 \
  --json-output

# Tag search
python -m arangodb.cli.main search tag \
  --tags "python,tutorial" \
  --json-output
```

#### Graph Operations
```bash
# Add relationship
python -m arangodb.cli.main graph add-relationship \
  --from DOC1 \
  --to DOC2 \
  --type "related_to" \
  --rationale "Documents are related" \
  --json-output

# Traverse graph
python -m arangodb.cli.main graph traverse \
  --start DOC1 \
  --max-depth 2 \
  --json-output
```

#### Memory Operations
```bash
# Store memory
python -m arangodb.cli.main memory store \
  --content "Important information" \
  --tags "important,reference" \
  --json-output

# Search memories
python -m arangodb.cli.main memory search \
  --query "find important info" \
  --limit 10 \
  --json-output

# Get messages
python -m arangodb.cli.main memory get-messages \
  --conversation-id "conv_001" \
  --limit 10 \
  --json-output
```

## Response Formats

### JSON Output

All CLI commands support `--json-output` flag for machine-readable output:

```json
{
  "status": "success",
  "data": {
    "_key": "doc_123",
    "title": "Document Title",
    "content": "Document content",
    "timestamp": "2025-01-16T12:00:00Z"
  }
}
```

### Error Format

```json
{
  "status": "error",
  "message": "Document not found",
  "error_code": "NOT_FOUND"
}
```

## Error Handling

All functions include comprehensive error handling:

```python
from arangodb.core.db_operations import get_document
from arangodb.core.constants import COLLECTION_NAME

try:
    doc = get_document(db, COLLECTION_NAME, "key")
except DocumentNotFoundError:
    print("Document not found")
except ArangoError as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration

### Environment Variables

```bash
# ArangoDB connection
ARANGO_HOST=localhost
ARANGO_PORT=8529
ARANGO_USERNAME=root
ARANGO_PASSWORD=password
ARANGO_DATABASE=default_db

# Model configuration
OPENAI_API_KEY=your_api_key
EMBEDDING_MODEL=text-embedding-ada-002
DEFAULT_TEMPERATURE=0.7
```

### Configuration File

Create `config.py`:

```python
# Database settings
ARANGO_HOST = "localhost"
ARANGO_PORT = 8529
ARANGO_USERNAME = "root"
ARANGO_PASSWORD = "password"
DEFAULT_DATABASE = "pdf_extractor"

# Collection names
COLLECTION_NAME = "memory_documents"
EDGE_COLLECTION_NAME = "memory_relationships"
MEMORY_COLLECTION = "agent_memories"

# Search settings
DEFAULT_LIMIT = 10
MIN_SCORE = 0.5
EMBEDDING_DIMENSIONS = 1024
```

## Examples

See the `docs/examples/` directory for complete working examples:

- `python_api_usage.py`: Python API usage examples
- `cli_json_output.sh`: CLI with JSON output examples
- `advanced_search.py`: Advanced search techniques
- `graph_analysis.py`: Graph traversal and analysis

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test module
python -m pytest tests/arangodb/test_db_operations.py

# Run with coverage
python -m pytest --cov=arangodb tests/
```

## Performance Considerations

1. **Connection Pooling**: The client maintains a connection pool
2. **Batch Operations**: Use batch operations for bulk inserts
3. **Index Creation**: Ensure proper indexes for search performance
4. **Caching**: Results are cached with configurable TTL

## Support

For issues and questions:
- GitHub Issues: [github.com/yourusername/arangodb-python/issues](https://github.com/yourusername/arangodb-python/issues)
- Documentation: [docs.yourdomain.com](https://docs.yourdomain.com)
- Email: support@yourdomain.com