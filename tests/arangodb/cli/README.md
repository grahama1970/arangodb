# CLI Command Tests

This directory contains comprehensive tests for all CLI commands in the ArangoDB project.

## Test Philosophy

- **NO MOCKING**: All tests use real components
- Real database connections
- Real embeddings using `get_embedding`
- Real LiteLLM calls
- Multiple parameter variations
- Tests must actually run successfully

## Test Files

### test_memory_commands.py
Tests all memory-related CLI commands with real database operations:
- `memory create` - Creates new memory entries with embeddings
- `memory list` - Lists memories with various filters
- `memory search` - Searches memories using BM25 (vector search limitations)
- `memory get` - Retrieves specific memories by ID
- `memory history` - Gets conversation history

**Status**: ✅ All 15 tests passing

### test_all_cli_commands.py
Tests CLI consistency across all command modules:
- Help text validation
- JSON/Table output consistency
- Parameter consistency
- Error handling consistency

**Status**: Partial - Help text tests require exact string matching

## Running Tests

Run all CLI tests:
```bash
python -m pytest tests/arangodb/cli/ -xvs
```

Run specific test file:
```bash
python -m pytest tests/arangodb/cli/test_memory_commands.py -xvs
```

## Key Implementation Details

1. **Vector Index Setup**: Tests create vector indexes AFTER inserting documents (ArangoDB requirement)
2. **View Recreation**: Each test recreates the search view, which can cause indexing delays
3. **Search Limitations**: Vector search with APPROX_NEAR_COSINE has limitations; tests use BM25 fallback
4. **Test Data**: Uses MemoryAgent to create realistic test data with proper embeddings
5. **Error Handling**: Tests validate proper error responses with JSON structure

## Troubleshooting

If tests fail due to:
- **Vector search errors**: Check that indexes are created with correct structure (params as sub-object)
- **Empty search results**: View recreation can cause indexing delays
- **Database connection**: Ensure ArangoDB is running on localhost:8529
- **Embedding errors**: Verify BGE model is available and GPU/CPU resources are sufficient

## Future Improvements

1. Add comprehensive tests for all CLI modules
2. Improve vector search reliability 
3. Add performance benchmarks
4. Test edge cases and error conditions
5. Add integration tests for complex workflows