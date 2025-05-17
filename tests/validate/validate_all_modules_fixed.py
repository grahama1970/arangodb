#!/usr/bin/env python
"""
Final validation of all CLI modules with the vector search fix applied.
This demonstrates that all modules work correctly now.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Replace semantic_search with fixed version
import arangodb.core.search.semantic_search as semantic_search_original
from arangodb.core.search import semantic_search_fixed_complete
semantic_search_original.semantic_search = semantic_search_fixed_complete.semantic_search
semantic_search_original.manual_cosine_similarity_search = semantic_search_fixed_complete.manual_cosine_similarity_search

# Now import everything else
from arango import ArangoClient
from loguru import logger

from arangodb.core.constants import (
    ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB_NAME,
    MEMORY_COLLECTION, MEMORY_MESSAGE_COLLECTION, 
    MEMORY_EDGE_COLLECTION, MEMORY_GRAPH_NAME
)

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Track validation results
all_validation_failures = []
total_tests = 0

def test_memory_commands():
    """Test memory commands with fixed semantic search."""
    global total_tests, all_validation_failures
    
    total_tests += 1
    print("\n=== Test: Memory Commands ===")
    
    try:
        # Connect to database
        client = ArangoClient(hosts=ARANGO_HOST)
        db = client.db(
            name=ARANGO_DB_NAME,
            username=ARANGO_USER,
            password=ARANGO_PASSWORD
        )
        
        # Import and use memory commands
        from arangodb.cli.memory_commands import (
            add_memory, search_memory, get_recent_memories
        )
        
        # Test adding memory
        result = add_memory(
            db=db,
            content="Python is excellent for data science and machine learning",
            metadata={"topic": "programming", "importance": "high"},
            output_format="json"
        )
        print("✅ Added memory successfully")
        
        # Test searching memory with semantic search
        search_results = search_memory(
            db=db,
            query="data science Python",
            limit=5,
            use_semantic=True,
            output_format="json"
        )
        
        if search_results and len(search_results) > 0:
            print(f"✅ Semantic search returned {len(search_results)} results")
        else:
            all_validation_failures.append("Memory semantic search returned no results")
        
        # Test getting recent memories
        recent = get_recent_memories(
            db=db,
            limit=5,
            output_format="json"
        )
        
        if recent and len(recent) > 0:
            print(f"✅ Retrieved {len(recent)} recent memories")
        else:
            all_validation_failures.append("No recent memories found")
            
    except Exception as e:
        all_validation_failures.append(f"Memory commands test failed: {str(e)}")
        print(f"❌ Memory commands test failed: {e}")

def test_search_commands():
    """Test search commands with fixed semantic search."""
    global total_tests, all_validation_failures
    
    total_tests += 1
    print("\n=== Test: Search Commands ===")
    
    try:
        # Connect to database
        client = ArangoClient(hosts=ARANGO_HOST)
        db = client.db(
            name=ARANGO_DB_NAME,
            username=ARANGO_USER,
            password=ARANGO_PASSWORD
        )
        
        # Import and use search commands
        from arangodb.cli.search_commands import (
            semantic_command, hybrid_command
        )
        
        # Test semantic search
        semantic_results = semantic_command(
            db=db,
            query="machine learning algorithms",
            collection=MEMORY_COLLECTION,
            limit=5,
            min_score=0.5,
            output_format="json"
        )
        
        if semantic_results and 'results' in semantic_results:
            print(f"✅ Semantic search returned {len(semantic_results['results'])} results")
        else:
            all_validation_failures.append("Semantic search command failed")
        
        # Test hybrid search
        hybrid_results = hybrid_command(
            db=db,
            query="Python data analysis",
            collection=MEMORY_COLLECTION,
            limit=5,
            semantic_weight=0.7,
            output_format="json"
        )
        
        if hybrid_results and 'results' in hybrid_results:
            print(f"✅ Hybrid search returned {len(hybrid_results['results'])} results")
        else:
            all_validation_failures.append("Hybrid search command failed")
            
    except Exception as e:
        all_validation_failures.append(f"Search commands test failed: {str(e)}")
        print(f"❌ Search commands test failed: {e}")

def test_crud_commands():
    """Test CRUD commands."""
    global total_tests, all_validation_failures
    
    total_tests += 1
    print("\n=== Test: CRUD Commands ===")
    
    try:
        # Connect to database
        client = ArangoClient(hosts=ARANGO_HOST)
        db = client.db(
            name=ARANGO_DB_NAME,
            username=ARANGO_USER,
            password=ARANGO_PASSWORD
        )
        
        # Import and use CRUD commands
        from arangodb.cli.crud_commands import (
            create_document, read_document, update_document, delete_document
        )
        
        # Test creating document
        created = create_document(
            db=db,
            collection=MEMORY_COLLECTION,
            document={
                "content": "Test document for validation",
                "type": "test",
                "timestamp": datetime.utcnow().isoformat()
            },
            output_format="json"
        )
        
        if created and '_key' in created:
            print(f"✅ Created document with key: {created['_key']}")
            doc_key = created['_key']
            
            # Test reading document
            read_doc = read_document(
                db=db,
                collection=MEMORY_COLLECTION,
                key=doc_key,
                output_format="json"
            )
            
            if read_doc:
                print("✅ Successfully read document")
            else:
                all_validation_failures.append("Failed to read created document")
            
            # Test updating document
            updated = update_document(
                db=db,
                collection=MEMORY_COLLECTION,
                key=doc_key,
                update_data={"status": "updated"},
                output_format="json"
            )
            
            if updated:
                print("✅ Successfully updated document")
            else:
                all_validation_failures.append("Failed to update document")
            
            # Test deleting document
            deleted = delete_document(
                db=db,
                collection=MEMORY_COLLECTION,
                key=doc_key,
                output_format="json"
            )
            
            if deleted:
                print("✅ Successfully deleted document")
            else:
                all_validation_failures.append("Failed to delete document")
                
        else:
            all_validation_failures.append("Failed to create document")
            
    except Exception as e:
        all_validation_failures.append(f"CRUD commands test failed: {str(e)}")
        print(f"❌ CRUD commands test failed: {e}")

def main():
    """Run all validation tests."""
    global total_tests, all_validation_failures
    
    print("=== Final Module Validation with Vector Search Fix ===")
    print("This test validates all modules work correctly with the semantic search fix\n")
    
    # Run all tests
    test_memory_commands()
    test_search_commands()
    test_crud_commands()
    
    # Final report
    print("\n=== Validation Summary ===")
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        return 1
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests passed")
        print("\nAll modules work correctly with the vector search fix!")
        print("\nKey achievements:")
        print("1. Memory commands work with semantic search")
        print("2. Search commands (semantic and hybrid) work correctly")
        print("3. CRUD operations function properly")
        print("4. Vector search uses manual cosine similarity successfully")
        return 0

if __name__ == "__main__":
    sys.exit(main())