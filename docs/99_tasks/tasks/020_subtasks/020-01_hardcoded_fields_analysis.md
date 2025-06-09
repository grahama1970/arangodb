# Task 020-01: Hardcoded Fields Analysis

## Summary of Hardcoded Fields in Search Modules

### 1. semantic_search.py
- **Line 60**: `EMBEDDING_FIELD = "embedding"`
- **Line 679**: Direct use of `EMBEDDING_FIELD` constant
- **Issue**: Forces all documents to have "embedding" field

### 2. keyword_search.py
- **Line 116**: `fields_to_search = ["problem", "solution", "context"]`
- **Issue**: Defaults to fields that don't exist in standard documents

### 3. bm25_search.py
- **Line 100**: Uses `SEARCH_FIELDS` from constants
- **Status**: Already flexible, uses constants properly

### 4. hybrid_search.py
- **Uses**: Calls other search functions, inherits their limitations
- **Issue**: Limited by hardcoded fields in semantic_search

### 5. graph_traverse.py
- **Line 645**: `doc["embedding"] = get_embedding(text_to_embed)`
- **Line 722**: `edge["embedding"] = get_embedding(edge["rationale"])`
- **Issue**: Hardcodes "embedding" field for documents and edges

### 6. cross_encoder_reranking.py
- **Line 132**: Filters out "embedding" field in clean_doc
- **Status**: Reasonable, but should be configurable

### 7. tag_search.py
- **Status**: No hardcoded fields, already flexible

### 8. glossary_search.py
- **Status**: Not found in directory

## Required Changes

### Priority 1: semantic_search.py
- Add `embedding_field` parameter with default from constants
- Pass through all function calls
- Remove hardcoded `EMBEDDING_FIELD`

### Priority 2: keyword_search.py
- Change default `fields_to_search` to use `SEARCH_FIELDS` from constants
- Already has parameter, just needs better default

### Priority 3: graph_traverse.py
- Add `embedding_field` parameter to functions
- Use configurable field name for embeddings

### Priority 4: hybrid_search.py
- Pass `embedding_field` parameter to semantic_search calls
- Ensure flexibility propagates through

### Priority 5: cross_encoder_reranking.py
- Make filtered fields configurable
- Add parameter for fields to exclude

## Constants.py Current Values
```python
"embedding": {
    "field": "embedding",  # This should be default, not hardcoded
},
"search": {
    "fields": ["content", "title", "summary", "tags"],  # Good default
}
```

## Next Steps
1. Update semantic_search.py first (most critical)
2. Fix keyword_search.py defaults
3. Update remaining modules
4. Create comprehensive tests