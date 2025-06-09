# ArangoDB Memory Bank Beta Testing Guide

## Overview

Welcome to the ArangoDB Memory Bank beta testing program! This guide will help you get started with testing our conversation-centric memory system with bi-temporal data tracking capabilities.

## Current Beta Version

**Version**: 0.1.0-beta  
**Release Date**: January 2025  
**Status**: Limited Beta

## System Requirements

- Python 3.10 or higher
- ArangoDB 3.11+ 
- Redis (for caching)
- 8GB RAM minimum
- GPU recommended for embeddings (but not required)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd arangodb
   ```

2. **Set up virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -e .
   ```

4. **Configure ArangoDB**:
   - Ensure ArangoDB is running on `localhost:8529`
   - Default credentials: `root` / `openSesame`
   - Database: `_system`

5. **Initialize the system**:
   ```bash
   arangodb-cli memory setup
   ```

## Key Features to Test

### 1. Bi-temporal Data Model
Test the temporal tracking capabilities:

```bash
# Store a conversation with temporal data
arangodb-cli memory store \
    --user-message "What's the weather?" \
    --agent-response "It's sunny today" \
    --point-in-time "2024-01-01T12:00:00"

# Search at a specific time
arangodb-cli memory search-at-time "weather" \
    --timestamp "2024-01-01T12:00:00"

# Get conversation history at a point in time
arangodb-cli memory conversation-at-time <conversation_id> \
    --timestamp "2024-01-01T12:00:00"
```

### 2. Search Functionality
Test different search types:

```bash
# Semantic search
arangodb-cli search semantic "machine learning concepts"

# BM25 search
arangodb-cli search bm25 "python programming"

# Hybrid search
arangodb-cli search hybrid "database optimization"

# Vector search (using embeddings)
arangodb-cli search vector "similar content"
```

### 3. Memory Operations
Test core memory functionality:

```bash
# Store conversation
arangodb-cli memory store \
    --user-message "Tell me about pandas" \
    --agent-response "Pandas are black and white bears"

# Retrieve messages
arangodb-cli memory get <conversation_id>

# List recent conversations
arangodb-cli memory list --limit 10

# Export conversations
arangodb-cli memory export --format json > conversations.json
```

### 4. Entity and Relationship Management
Test graph operations:

```bash
# Extract entities
arangodb-cli graph extract-entities --text "Python is a programming language"

# Create relationships
arangodb-cli graph link-entities --source "Python" --target "Programming" --type "IS_A"

# Query relationships
arangodb-cli graph query --entity "Python" --depth 2
```

## Testing Scenarios

### Scenario 1: Temporal Data Consistency
1. Store multiple conversations at different timestamps
2. Query data at various points in time
3. Verify temporal consistency and ordering
4. Test invalid_at functionality

### Scenario 2: Search Accuracy
1. Store diverse content with different topics
2. Test each search type (semantic, BM25, hybrid, vector)
3. Verify search result relevance
4. Test search with filters and constraints

### Scenario 3: Performance Testing
1. Store large volumes of conversations (1000+)
2. Measure query response times
3. Test concurrent operations
4. Monitor resource usage

### Scenario 4: Edge Cases
1. Test with empty or null inputs
2. Test with very long messages
3. Test with special characters and unicode
4. Test error handling and recovery

## Reporting Issues

When reporting issues, please include:

1. **System Information**:
   - OS and version
   - Python version
   - ArangoDB version
   - GPU availability

2. **Steps to Reproduce**:
   - Exact commands used
   - Input data (if applicable)
   - Expected vs actual behavior

3. **Error Messages**:
   - Full error stack trace
   - Log files from `logs/` directory

4. **Context**:
   - What you were trying to accomplish
   - Any workarounds you've tried

## Known Limitations (Beta)

Please be aware of these limitations in the current beta:

1. **Edge Invalidation**: Not yet implemented (Task 027)
2. **Contradiction Detection**: Pending implementation
3. **Episode Flexibility**: Graphiti-style episodes not yet integrated
4. **Performance**: Not optimized for very large datasets (>1M records)
5. **Deprecation Warnings**: Some Pydantic V1 style warnings (non-breaking)

## Feedback Channels

- **GitHub Issues**: For bug reports and feature requests
- **Discord**: For real-time discussions (link TBD)
- **Email**: beta-feedback@arangodb-memory.com (TBD)

## Best Practices

1. **Start Small**: Begin with simple operations before complex scenarios
2. **Use Test Data**: Don't use production or sensitive data during beta
3. **Regular Backups**: Export your data regularly during testing
4. **Check Logs**: Review logs in `logs/` for detailed information
5. **Document Everything**: Keep notes on your testing experience

## Performance Tips

1. **Batch Operations**: Use batch imports for large datasets
2. **Index Usage**: Ensure proper indexes are created
3. **Resource Monitoring**: Watch CPU and memory usage
4. **GPU Acceleration**: Enable GPU for faster embeddings if available

## Security Considerations

1. **Credentials**: Never commit credentials to version control
2. **API Keys**: Secure your LLM API keys properly
3. **Network**: Use secure connections for remote databases
4. **Data Privacy**: Be mindful of data privacy regulations

## Next Steps

After initial testing:

1. Review the [API Documentation](/docs/api/python_api.md)
2. Check the [CLI Reference](/docs/usage/cli_reference_guide.md)
3. Explore [Advanced Features](/docs/guides/TEMPORAL_MODEL_GUIDE.md)
4. Join the community discussions

## Thank You!

Thank you for participating in the ArangoDB Memory Bank beta program. Your feedback is invaluable in helping us improve the system.

Happy Testing! 🚀