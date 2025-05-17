# Field Conventions for ArangoDB Search

This document explains the field conventions used in the ArangoDB search modules to ensure maximum flexibility while maintaining consistency.

## Overview

The search modules follow these principles:
1. **Standardized embedding field**: The vector embedding field is always named `embedding`
2. **Flexible text fields**: Text search fields can be customized per collection
3. **Sensible defaults**: When fields aren't specified, reasonable defaults are used

## Standardized Fields

### Embedding Field
- **Field name**: `embedding`
- **Type**: List of floats (vector)
- **Dimensions**: 1024 (for BAAI/bge-large-en-v1.5 model)
- **Required for**: Semantic/vector search

This field is hardcoded across all search modules because:
- It provides consistency for vector operations
- Agents always know where to find embeddings
- Similar to ArangoDB's `_id` and `_key` conventions

```python
# Always use this field name for embeddings
doc["embedding"] = get_embedding(text)
```

## Flexible Text Fields

Text fields can be customized using the `fields_to_search` parameter:

### Default Text Fields
```python
DEFAULT_SEARCH_FIELDS = ["content", "title", "summary", "tags"]
```

### Custom Fields Example
```python
# Search with custom field names
results = bm25_search(
    db=db,
    query_text="python programming",
    fields_to_search=["custom_title", "body_text", "description"]
)
```

## Usage Examples

### 1. Standard Document Structure
```json
{
    "_key": "doc1",
    "title": "Python Guide",
    "content": "Learn Python programming",
    "summary": "A comprehensive guide",
    "tags": ["python", "tutorial"],
    "embedding": [0.1, 0.2, 0.3, ...]
}
```

### 2. Custom Document Structure
```json
{
    "_key": "doc2",
    "custom_title": "Database Systems",
    "body_text": "Understanding databases",
    "description": "Database overview",
    "keywords": ["database", "sql"],
    "embedding": [0.1, 0.2, 0.3, ...]
}
```

### 3. Agent-Specific Structure
```json
{
    "_key": "memory1",
    "thought": "User asked about Python",
    "response": "Python is a programming language",
    "context": "Programming discussion",
    "importance": 0.8,
    "embedding": [0.1, 0.2, 0.3, ...]
}
```

## Search Function Parameters

All text search functions accept a `fields_to_search` parameter:

### Keyword Search
```python
search_keyword(
    db=db,
    search_term="python",
    fields_to_search=["thought", "response", "context"]
)
```

### BM25 Search
```python
bm25_search(
    db=db,
    query_text="database systems",
    fields_to_search=["custom_title", "body_text"]
)
```

### Hybrid Search
```python
hybrid_search(
    db=db,
    query_text="web development",
    fields_to_search=["title", "description", "keywords"]
)
```

## Best Practices

1. **Always include embedding field**: Every searchable document should have an `embedding` field
2. **Use consistent field names**: Within a collection, keep field names consistent
3. **Document field structure**: Keep documentation of your collection's field structure
4. **Test with actual data**: Validate searches work with your specific field names

## View Configuration

When creating ArangoDB views, ensure all text fields are properly indexed:

```javascript
// Create view with custom fields
db._createView("custom_view", "arangosearch", {
    links: {
        "custom_collection": {
            fields: {
                "custom_title": { analyzers: ["text_en"] },
                "body_text": { analyzers: ["text_en"] },
                "description": { analyzers: ["text_en"] }
            }
        }
    }
});
```

## Migration Guide

If migrating from hardcoded fields:

1. **Keep embedding field as-is**: No changes needed for `embedding`
2. **Update search calls**: Add `fields_to_search` parameter
3. **Test thoroughly**: Verify searches return expected results

```python
# Before (hardcoded)
results = bm25_search(db, "query")  # Searches default fields

# After (flexible)
results = bm25_search(
    db, 
    "query",
    fields_to_search=["my_title", "my_content", "my_summary"]
)
```

## Summary

The field convention strikes a balance between:
- **Standardization**: Embedding field is always `embedding`
- **Flexibility**: Text fields can be customized per use case
- **Simplicity**: Sensible defaults when not specified

This approach allows agents and applications to work with various document structures while maintaining consistency for vector operations.