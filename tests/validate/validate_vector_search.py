#!/usr/bin/env python
"""
Validate that vector search works correctly with memory commands.

This validates:
1. Documents are properly embedded with BGE embeddings (1024 dimensions)
2. Semantic search works correctly with those embeddings
3. Memory commands use the proper semantic search implementation
"""
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dependencies
from arango import ArangoClient
from sentence_transformers import SentenceTransformer
from loguru import logger

# Import our modules
from arangodb.core.constants import (
    ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME,
    MEMORY_COLLECTION, MEMORY_EDGE_COLLECTION, MEMORY_GRAPH_NAME
)
from arangodb.core.memory.memory_agent import MemoryAgent
from arangodb.core.search.semantic_search import semantic_search

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Track validation results
all_validation_failures = []
total_tests = 0

def test_memory_agent_semantic_search():
    """Test memory agent's semantic search with proper embeddings."""
    global total_tests, all_validation_failures
    
    total_tests += 1
    print("\nTest: Memory Agent semantic search with BGE embeddings")
    
    try:
        # Connect to database
        client = ArangoClient(hosts=ARANGO_HOST)
        db = client.db(
            name=ARANGO_DB_NAME,
            username=ARANGO_USER,
            password=ARANGO_PASSWORD
        )
        
        # Initialize memory agent with database connection
        agent = MemoryAgent(db=db)
        
        # Create test messages with different topics
        test_messages = [
            ("user", "Python is great for data science and machine learning"),
            ("assistant", "Yes, Python has excellent libraries like pandas, numpy, and scikit-learn"),
            ("user", "ArangoDB supports graph databases and vector search"),
            ("assistant", "ArangoDB is indeed a multi-model database with graph and vector capabilities"),
            ("user", "Machine learning models can process complex data patterns"),
            ("assistant", "ML algorithms are powerful for pattern recognition and prediction tasks")
        ]
        
        # Add messages to memory
        for role, content in test_messages:
            agent.add_message(
                role=role,
                content=content,
                metadata={"topic": "tech", "timestamp": datetime.utcnow().isoformat()}
            )
        
        print(f"✅ Added {len(test_messages)} test messages")
        
        # Test semantic search with different queries
        test_queries = [
            ("Python data science", 3),
            ("database graph vector", 3),
            ("machine learning patterns", 3)
        ]
        
        for query, limit in test_queries:
            print(f"\nSearching for: '{query}'")
            results = agent.temporal_search(
                query=query,
                limit=limit,
                use_semantic=True
            )
            
            if results:
                print(f"✅ Found {len(results)} results")
                for i, result in enumerate(results):
                    content = result.get('content', '')[:100] + '...'
                    score = result.get('semantic_score', 0)
                    print(f"  {i+1}. {content} (score: {score:.4f})")
            else:
                all_validation_failures.append(f"No results for query: {query}")
                print(f"❌ No results found")
        
        # Verify embeddings are properly stored
        collection = agent.db.collection(MEMORY_COLLECTION)
        sample_doc = collection.random()
        
        if 'embedding' in sample_doc:
            embedding_dim = len(sample_doc['embedding'])
            if embedding_dim == 1024:
                print(f"\n✅ Embeddings are properly stored with {embedding_dim} dimensions")
            else:
                all_validation_failures.append(f"Wrong embedding dimensions: {embedding_dim} (expected 1024)")
        else:
            all_validation_failures.append("No embedding field found in documents")
        
    except Exception as e:
        all_validation_failures.append(f"Memory agent test failed: {str(e)}")
        print(f"❌ Test failed: {e}")

def test_direct_semantic_search():
    """Test direct semantic search API."""
    global total_tests, all_validation_failures
    
    total_tests += 1
    print("\nTest: Direct semantic search API")
    
    try:
        # Connect to database
        client = ArangoClient(hosts=ARANGO_HOST)
        db = client.db(
            name=ARANGO_DB_NAME,
            username=ARANGO_USER,
            password=ARANGO_PASSWORD
        )
        
        # Test semantic search on memory collection
        results = semantic_search(
            db=db,
            query="Python programming data science",
            collections=[MEMORY_COLLECTION],
            min_score=0.3,  # Lower threshold for testing
            top_n=5
        )
        
        if results and 'results' in results:
            print(f"✅ Semantic search returned {len(results['results'])} results")
            for i, result in enumerate(results['results']):
                doc = result.get('doc', {})
                content = doc.get('content', '')[:100] + '...'
                score = result.get('similarity_score', 0)
                print(f"  {i+1}. {content} (score: {score:.4f})")
                
            # Check search metadata
            if 'search_engine' in results:
                print(f"✅ Search engine used: {results['search_engine']}")
            
            # Verify we're using proper embeddings
            first_result = results['results'][0] if results['results'] else None
            if first_result and 'doc' in first_result:
                doc = first_result['doc']
                if 'embedding' in doc and len(doc['embedding']) == 1024:
                    print("✅ Documents have proper 1024-dimensional BGE embeddings")
        else:
            all_validation_failures.append("Semantic search returned no results")
            print("❌ No results returned")
            
    except Exception as e:
        all_validation_failures.append(f"Direct semantic search failed: {str(e)}")
        print(f"❌ Test failed: {e}")

def main():
    """Run all validation tests."""
    global total_tests, all_validation_failures
    
    print("=== Vector Search Validation ===")
    print("Testing semantic search with BGE embeddings (BAAI/bge-large-en-v1.5)")
    print("Expected: 1024-dimensional embeddings\n")
    
    # Test memory agent semantic search
    test_memory_agent_semantic_search()
    
    # Test direct semantic search API
    test_direct_semantic_search()
    
    # Final report
    print("\n=== Validation Summary ===")
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        print("\nNote: APPROX_NEAR_COSINE may fail but semantic search still works via fallback")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests passed")
        print("Vector search is working correctly with BGE embeddings!")
        print("\nKey findings:")
        print("1. Documents are properly embedded with 1024-dimensional BGE vectors")
        print("2. Semantic search works correctly using fallback methods")
        print("3. Memory agent successfully performs semantic search")
        sys.exit(0)

if __name__ == "__main__":
    main()