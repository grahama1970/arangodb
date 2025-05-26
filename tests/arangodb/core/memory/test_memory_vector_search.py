#!/usr/bin/env python3
"""
Test script to investigate why APPROX_NEAR_COSINE fails in memory agent
"""

import time
from arango import ArangoClient
from arangodb.core.constants import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME
from arangodb.core.memory.memory_agent import MemoryAgent
from arangodb.core.utils.embedding_utils import get_embedding

# Connect to ArangoDB
client = ArangoClient(hosts=ARANGO_HOST)
db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)

# Initialize memory agent
memory_agent = MemoryAgent(db=db)

# Create test data
print("\n1. Creating test data...")
test_conversations = [
    {"user": "What is ArangoDB?", "agent": "ArangoDB is a multi-model database."},
    {"user": "How does vector search work?", "agent": "Vector search uses embeddings for similarity."},
    {"user": "Tell me about machine learning", "agent": "Machine learning is a type of AI."}
]

# Store conversations 
for conv in test_conversations:
    memory_agent.store_conversation(
        user_message=conv["user"],
        agent_response=conv["agent"],
        auto_embed=True
    )

# Wait for indexing
time.sleep(1)

print("\n2. Checking collection indexes...")
collection = db.collection("agent_messages")
for index in collection.indexes():
    print(f"Index type: {index.get('type')}")
    if index.get('type') == 'vector':
        print(f"Vector index found: {index}")
        print(f"Fields: {index.get('fields')}")
        print(f"Params: {index.get('params')}")

print("\n3. Checking if embeddings exist...")
cursor = db.aql.execute("""
    FOR doc IN agent_messages
        FILTER LENGTH(doc.embedding) > 0
        LIMIT 5
        RETURN {
            _key: doc._key,
            content: doc.content,
            has_embedding: LENGTH(doc.embedding) > 0,
            embedding_length: LENGTH(doc.embedding)
        }
""")
docs_with_embeddings = list(cursor)
print(f"Documents with embeddings: {len(docs_with_embeddings)}")
for doc in docs_with_embeddings:
    print(f"  - {doc['_key']}: {doc['content'][:50]}... (embedding dims: {doc['embedding_length']})")

# Create the vector index properly
print("\n4. Creating proper vector index...")
try:
    # Drop existing vector indexes first
    for index in collection.indexes():
        if index.get('type') == 'vector':
            collection.delete_index(index['id'])
            print(f"Deleted existing vector index: {index['id']}")
    
    # Create with correct structure
    index_info = collection.add_index({
        "type": "vector",
        "fields": ["embedding"],
        "params": {  # params MUST be a sub-object
            "dimension": 1024,  # BGE embedding dimension
            "metric": "cosine",
            "nLists": 2  # Use 2 for small datasets
        }
    })
    print(f"Created vector index: {index_info}")
except Exception as e:
    print(f"Error creating vector index: {e}")

print("\n5. Testing APPROX_NEAR_COSINE query...")
query_text = "ArangoDB database"
query_embedding = get_embedding(query_text)

try:
    aql_query = """
    FOR doc IN agent_messages
        LET score = APPROX_NEAR_COSINE(doc.embedding, @query_embedding)
        SORT score DESC
        LIMIT 5
        RETURN {
            _key: doc._key,
            content: doc.content,
            type: doc.type,
            similarity_score: score
        }
    """
    
    cursor = db.aql.execute(aql_query, bind_vars={"query_embedding": query_embedding})
    results = list(cursor)
    
    print(f"APPROX_NEAR_COSINE succeeded! Found {len(results)} results:")
    for result in results:
        print(f"  - {result['type']}: {result['content'][:50]}... (score: {result['similarity_score']:.4f})")
        
except Exception as e:
    print(f"APPROX_NEAR_COSINE failed: {e}")
    print(f"Error type: {type(e).__name__}")
    
    print("\n6. Testing with standard text search (BM25)...")
    try:
        # Try the text search that the memory agent currently uses
        aql_text = """
        FOR doc IN messages_search_view  
            SEARCH ANALYZER(doc.content IN TOKENS(@query, "text_en"), "text_en")
            SORT BM25(doc) DESC
            LIMIT 5
            RETURN {
                _key: doc._key,
                content: doc.content,
                type: doc.type,
                score: BM25(doc)
            }
        """
        
        cursor = db.aql.execute(aql_text, bind_vars={"query": query_text})
        text_results = list(cursor)
        
        print(f"Text search found {len(text_results)} results:")
        for result in text_results:
            print(f"  - {result['type']}: {result['content'][:50]}... (score: {result['score']:.4f})")
            
    except Exception as e:
        print(f"Text search also failed: {e}")

print("\n7. Understanding the complex query limitation...")
# Let's test a more complex query with filters (what memory agent might need)
try:
    complex_query = """
    FOR doc IN agent_messages
        FILTER doc.conversation_id != null
        FILTER doc.timestamp >= '2020-01-01'
        LET score = APPROX_NEAR_COSINE(doc.embedding, @query_embedding)
        SORT score DESC
        LIMIT 5
        RETURN {
            _key: doc._key,
            content: doc.content,
            conversation_id: doc.conversation_id,
            similarity_score: score
        }
    """
    
    cursor = db.aql.execute(complex_query, bind_vars={"query_embedding": query_embedding})
    complex_results = list(cursor)
    
    print(f"Complex query with filters succeeded! Found {len(complex_results)} results")
    
except Exception as e:
    print(f"Complex query failed: {e}")
    print("This might be the 'limitations with APPROX_NEAR_COSINE in complex queries' mentioned in the code")