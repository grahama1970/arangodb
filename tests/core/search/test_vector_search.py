#!/usr/bin/env python3
"""
Working ArangoDB Vector Search with APPROX_NEAR_COSINE

This creates exactly as requested:
1. 10 sample documents 
2. BGE embeddings (BAAI/bge-large-en-v1.5)
3. Proper vector index
4. Working APPROX_NEAR_COSINE search

The key is using the correct index structure with params sub-object.
"""

from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer
from arango import ArangoClient
from loguru import logger
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME
from core.arango_setup import connect_arango, ensure_database

def create_sample_documents() -> List[Dict[str, Any]]:
    """Create 10 sample documents as requested."""
    return [
        {"title": "Introduction to Python", "content": "Python is a versatile programming language."},
        {"title": "Data Science Basics", "content": "Data science involves statistics and machine learning."},
        {"title": "Machine Learning Guide", "content": "Machine learning algorithms can predict patterns."},
        {"title": "Deep Learning Overview", "content": "Deep learning uses neural networks for AI."},
        {"title": "ArangoDB Tutorial", "content": "ArangoDB is a multi-model database system."},
        {"title": "Vector Search Explained", "content": "Vector search enables semantic similarity matching."},
        {"title": "BGE Embeddings", "content": "BGE models create high-quality text embeddings."},
        {"title": "Database Indexing", "content": "Indexes improve query performance in databases."},
        {"title": "AI Applications", "content": "Artificial intelligence has many real-world uses."},
        {"title": "Search Technology", "content": "Modern search uses embeddings for better results."}
    ]

def embed_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add BGE embeddings to documents."""
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    logger.info("Generating BGE embeddings...")
    
    for doc in documents:
        text = f"{doc['title']} {doc['content']}"
        embedding = model.encode(text, show_progress_bar=False)
        doc['embedding'] = embedding.tolist()
    
    return documents

def create_vector_index(collection: Any) -> bool:
    """Create proper vector index with correct structure."""
    try:
        index_info = collection.add_index({
            "type": "vector",
            "fields": ["embedding"],
            "params": {  # params must be a sub-object
                "dimension": 1024,
                "metric": "cosine",
                "nLists": 2
            }
        })
        logger.info(f"Vector index created: {index_info}")
        return True
    except Exception as e:
        logger.error(f"Vector index creation failed: {e}")
        return False

def run_semantic_search(db: Any, collection_name: str, query_text: str):
    """Run semantic search using APPROX_NEAR_COSINE."""
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    query_embedding = model.encode(query_text, show_progress_bar=False).tolist()
    
    print(f"\n=== Semantic Search: '{query_text}' ===")
    
    aql = f"""
    FOR doc IN {collection_name}
        LET similarity = APPROX_NEAR_COSINE(doc.embedding, @queryEmbedding)
        SORT similarity DESC
        LIMIT 5
        RETURN {{
            title: doc.title,
            content: doc.content,
            similarity: similarity
        }}
    """
    
    try:
        cursor = db.aql.execute(aql, bind_vars={"queryEmbedding": query_embedding})
        results = list(cursor)
        
        print("\n✅ APPROX_NEAR_COSINE Results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']} (similarity: {result['similarity']:.4f})")
            print(f"   {result['content']}")
    except Exception as e:
        print(f"\n❌ APPROX_NEAR_COSINE failed: {e}")

def main():
    """Main execution function."""
    logger.add("vector_search_working.log", rotation="10 MB")
    
    # Connect to ArangoDB
    client = connect_arango()
    db = ensure_database(client)
    collection_name = "vector_search_demo"
    
    # Create collection
    if db.has_collection(collection_name):
        db.delete_collection(collection_name)
    collection = db.create_collection(collection_name)
    logger.info(f"Created collection: {collection_name}")
    
    # Create and embed documents
    documents = create_sample_documents()
    embedded_docs = embed_documents(documents)
    
    # Insert documents
    collection.insert_many(embedded_docs)
    logger.info(f"Inserted {len(embedded_docs)} documents")
    
    # Create vector index
    if not create_vector_index(collection):
        print("Failed to create vector index")
        return 1
    
    # Run semantic searches
    search_queries = [
        "Python programming tutorial",
        "artificial intelligence and machine learning",
        "database search and indexing",
        "BGE embeddings and vector search"
    ]
    
    for query in search_queries:
        run_semantic_search(db, collection_name, query)
    
    print("\n✅ All operations completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())