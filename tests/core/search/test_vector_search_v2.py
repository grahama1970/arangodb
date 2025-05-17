#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from loguru import logger

# # Add the current directory to the path
# sys.path.insert(0, os.path.abspath("src"))

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")

def create_test_collection():
    # Import required modules
    from arango import ArangoClient
    from sentence_transformers import SentenceTransformer
    
    # Load environment variables
    from arangodb.core.constants import (
        ARANGO_HOST,
        ARANGO_USER,
        ARANGO_PASSWORD,
        ARANGO_DB_NAME,
        DEFAULT_EMBEDDING_DIMENSIONS
    )
    
    # Connect to ArangoDB
    logger.info(f"Connecting to ArangoDB at {ARANGO_HOST}")
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    # Create test collection
    test_collection_name = "vector_test"
    logger.info(f"Creating test collection: {test_collection_name}")
    
    # Drop collection if it exists
    if db.has_collection(test_collection_name):
        logger.info(f"Dropping existing collection: {test_collection_name}")
        db.delete_collection(test_collection_name)
    
    # Create collection
    collection = db.create_collection(test_collection_name)
    
    # Load embedding model
    model_name = "BAAI/bge-large-en-v1.5"
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Create 10 sample documents with proper embeddings
    logger.info("Creating sample documents with embeddings")
    documents = [
        {"title": "Python Programming", "content": "Learn Python basics and programming concepts"},
        {"title": "Machine Learning", "content": "AI and ML fundamentals for beginners"},
        {"title": "Database Systems", "content": "Introduction to database design and implementation"},
        {"title": "Web Development", "content": "HTML, CSS, and JavaScript for building websites"},
        {"title": "Data Science", "content": "Statistical analysis and data visualization techniques"},
        {"title": "Cybersecurity", "content": "Network security and threat protection strategies"},
        {"title": "Cloud Computing", "content": "AWS, Azure, and Google Cloud platform services"},
        {"title": "Mobile App Development", "content": "Building iOS and Android applications"},
        {"title": "DevOps Practices", "content": "Continuous integration and deployment workflows"},
        {"title": "Software Architecture", "content": "Designing scalable and maintainable systems"}
    ]
    
    # Add embeddings to documents
    for doc in documents:
        text = f"{doc['title']} {doc['content']}"
        embedding = model.encode(text, show_progress_bar=False)
        
        # Ensure embedding is a list, not a numpy array
        doc['embedding'] = embedding.tolist()
        
        # Validate embedding format
        assert isinstance(doc['embedding'], list), "Embedding must be a list"
        assert len(doc['embedding']) == DEFAULT_EMBEDDING_DIMENSIONS, f"Embedding dimension mismatch: got {len(doc['embedding'])}, expected {DEFAULT_EMBEDDING_DIMENSIONS}"
    
    # Insert documents
    logger.info(f"Inserting {len(documents)} documents into {test_collection_name}")
    collection.insert_many(documents)
    
    # Create vector index with proper structure
    logger.info("Creating vector index with proper structure")
    index_info = collection.add_index({
        "type": "vector",
        "fields": ["embedding"],
        "params": {  # params MUST be a sub-object
            "dimension": DEFAULT_EMBEDDING_DIMENSIONS,
            "metric": "cosine",
            "nLists": 2  # Use 2 for small datasets (<100 docs)
        }
    })
    
    logger.info(f"Vector index created: {index_info}")
    
    # Test APPROX_NEAR_COSINE
    logger.info("Testing APPROX_NEAR_COSINE against the collection")
    query_text = "python programming tutorial"
    query_embedding = model.encode(query_text, show_progress_bar=False).tolist()
    
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
    
    logger.info(f"APPROX_NEAR_COSINE search returned {len(results)} results")
    
    # Print results
    for i, result in enumerate(results):
        logger.info(f"{i+1}. {result['title']}: {result['similarity']:.4f}")
    
    return True

# Run the test
if __name__ == "__main__":
    try:
        create_test_collection()
        print("\nTest completed successfully! APPROX_NEAR_COSINE is working properly.")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nTest failed! Check the error message above.")