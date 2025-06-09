# Task 020: Search Flexibility Improvements

## Overview
Make text search functions in `src/arangodb/core/search/` flexible and agent-friendly by removing hardcoded text field names while keeping the embedding field standardized.

## Standardization Decision
- **Embedding Field**: Remains hardcoded as "embedding" - this is a standard convention
- **Text Fields**: Should be configurable to work with different document structures

## Current Issues

### 1. Hardcoded Text Search Fields
- `keyword_search.py` defaults to `["problem", "solution", "context"]`
- Should use configurable fields from constants or parameters
- Doesn't match actual document structure (e.g., "content", "title", etc.)

### 2. Inflexible BM25 Search
- `bm25_search.py` may hardcode field assumptions
- Should allow specifying which fields to search

### 3. Limited Search Field Options
- Many functions don't allow overriding search fields
- Should allow agents to specify exactly which fields to search

## Required Changes

### 1. Update keyword_search.py
```python
def search_keyword(
    db: StandardDatabase,
    search_term: str,
    fields_to_search: Optional[List[str]] = None,  # ADD THIS PARAMETER
    ...
) -> Dict[str, Any]:
    # Use default from constants if not provided
    if not fields_to_search:
        fields_to_search = ["content", "title", "summary"]  # Better defaults
```

### 2. Update bm25_search.py
```python
def bm25_search(
    db: StandardDatabase,
    query: str,
    fields_to_search: Optional[List[str]] = None,  # ADD THIS PARAMETER  
    ...
) -> Dict[str, Any]:
    # Allow flexible field specification
    if not fields_to_search:
        fields_to_search = ["content", "title", "summary"]
```

### 3. Update hybrid_search.py
- Pass through field configuration to component search functions
- Keep embedding field as standard "embedding"
- Allow text field flexibility

### 4. Update constants.py
```python
# Default text search fields (agents can override)
DEFAULT_SEARCH_FIELDS = ["content", "title", "summary", "tags"]

# Standard field conventions (not configurable)
EMBEDDING_FIELD = "embedding"  # Always use this for vector embeddings
```

## Implementation Steps

1. Update keyword_search.py to accept fields_to_search parameter
2. Update bm25_search.py to accept fields_to_search parameter
3. Update hybrid_search.py to pass through field parameters
4. Use sensible defaults that match actual document structure
5. Add validation tests with different field configurations

## Success Criteria

- [ ] Text search functions accept configurable field names
- [ ] Embedding field remains standardized as "embedding"
- [ ] Agent can specify custom text fields for any search
- [ ] Tests pass with different text field configurations
- [ ] Documentation clearly explains field conventions

## Benefits

1. Agents can search different text fields based on document structure
2. Embedding field standardization makes vector operations consistent
3. Flexible text search without sacrificing vector search simplicity
4. Clear conventions: standardized embedding, flexible text

## Next Steps

- Task 021: Add default field discovery for collections
- Task 022: Create field mapping configuration
- Task 023: Add collection-specific search profiles