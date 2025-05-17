# How to Use APPROX_NEAR_COSINE in ArangoDB

## Overview
APPROX_NEAR_COSINE is ArangoDB's function for vector similarity search. It requires:
- ArangoDB 3.12+
- Proper vector index with correct structure
- Vector embeddings stored as arrays

## Working Example (Tested 2025-05-16)

### 1. Create Collection and Insert Documents with Embeddings

```python
from sentence_transformers import SentenceTransformer
from arango import ArangoClient

# Connect to ArangoDB
client = ArangoClient(hosts="http://localhost:8529")
db = client.db("memory_bank", username="root", password="")

# Create collection
collection = db.create_collection("vector_test")

# Create documents with BGE embeddings
model = SentenceTransformer('BAAI/bge-large-en-v1.5')  # 1024-dimensional vectors
documents = [
    {"title": "Python Programming", "content": "Learn Python basics"},
    {"title": "Machine Learning", "content": "AI and ML fundamentals"},
    # ... more documents
]

# Add embeddings
for doc in documents:
    text = f"{doc['title']} {doc['content']}"
    embedding = model.encode(text, show_progress_bar=False)
    doc['embedding'] = embedding.tolist()  # Must be a list, not numpy array

collection.insert_many(documents)
```

### 2. Create Vector Index (CRITICAL - Must Use Correct Structure)

```python
# CORRECT STRUCTURE - params as sub-object
index_info = collection.add_index({
    "type": "vector",
    "fields": ["embedding"],
    "params": {  # params MUST be a sub-object
        "dimension": 1024,
        "metric": "cosine",
        "nLists": 2  # Use 2 for small datasets (<100 docs)
    }
})

# WRONG STRUCTURE - flat parameters (will fail)
# DON'T DO THIS:
# collection.add_index({
#     "type": "vector",
#     "fields": ["embedding"],
#     "dimension": 1024,  # Wrong - should be in params
#     "metric": "cosine",  # Wrong - should be in params
#     "nLists": 2         # Wrong - should be in params
# })
```

### 3. Use APPROX_NEAR_COSINE in AQL Query

```python
# Create query embedding
query_text = "Python programming tutorial"
query_embedding = model.encode(query_text, show_progress_bar=False).tolist()

# Run semantic search with APPROX_NEAR_COSINE
aql = """
FOR doc IN vector_test
    LET similarity = APPROX_NEAR_COSINE(doc.embedding, @queryEmbedding)
    SORT similarity DESC
    LIMIT 5
    RETURN {
        title: doc.title,
        content: doc.content,
        similarity: similarity
    }
"""

cursor = db.aql.execute(aql, bind_vars={"queryEmbedding": query_embedding})
results = list(cursor)

for result in results:
    print(f"{result['title']}: {result['similarity']:.4f}")
```

## Common Issues and Solutions

### Issue 1: ERR 1554 "failed vector search"
**Cause**: Vector index not created properly or experimental flag not set.
**Solution**: Ensure vector index is created with correct structure (params as sub-object).

### Issue 2: Index params showing as None
**Symptom**: When checking indexes, vector params show as None:
```
Vector Params:
  Dimension: None
  Metric: None
  nLists: None
```
**Solution**: Recreate index with correct structure - params must be a sub-object.

### Issue 3: Function not recognized
**Error**: "usage of unknown function 'APPROX_NEAR_COSINE'"
**Solution**: Ensure ArangoDB 3.12+ and experimental flag is set. Check with:
```python
version_info = db.version()
engine_info = db.engine()
print(f"Version: {version_info}")
print(f"Supports vector: {'vector' in engine_info['supports']['indexes']}")
```

## Alternatives (If APPROX_NEAR_COSINE Fails)

### 1. L2_DISTANCE
```aql
FOR doc IN collection
    LET distance = L2_DISTANCE(doc.embedding, @queryEmbedding)
    SORT distance
    LIMIT 5
    RETURN doc
```

### 2. Manual Cosine Similarity
```aql
FOR doc IN collection
    LET norm_doc = SQRT(SUM(FOR v IN doc.embedding RETURN v*v))
    LET dot_product = SUM(
        FOR i IN 0..1023
            RETURN doc.embedding[i] * @queryEmbedding[i]
    )
    LET similarity = dot_product / norm_doc
    SORT similarity DESC
    LIMIT 5
    RETURN doc
```

## Complete Working Example
See: `/src/arangodb/tests/test_vector_search_working.py`

## Key Points to Remember
1. **Index Structure**: params must be a sub-object, not flat properties
2. **Embedding Format**: Must be lists, not numpy arrays
3. **nLists Parameter**: Use 2 for small datasets, higher for larger ones
4. **Error 1554**: Usually means index structure is wrong
5. **Function Availability**: Requires ArangoDB 3.12+ with experimental flag

## Fix for Current Issue (2025-05-17)

The semantic search was failing because:
1. The vector index wasn't properly created for the `memory_documents` collection
2. The index params must be in a sub-object structure (not flat)

To fix:
1. Create proper vector index with correct structure:
```python
from arangodb.core.arango_fix_vector_index import fix_memory_agent_indexes
fix_memory_agent_indexes(db)
```

2. If the collection doesn't have enough documents for training (needs at least 2), add more documents first before creating the index.

3. Ensure embeddings are stored as arrays, not objects.

The fix script at `/src/arangodb/core/arango_fix_vector_index.py` handles creating proper vector indexes for all memory collections.