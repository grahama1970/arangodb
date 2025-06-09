"""
Module: setup_test_db.py
Description: Test suite for setup_db functionality

External Dependencies:
- arango: https://docs.python-arango.com/
- loguru: https://loguru.readthedocs.io/

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from arangodb.core.arango_setup import connect_arango, ensure_database
from arangodb.cli.db_connection import get_db_connection
from loguru import logger

def setup_test_database():
    """Setup the test database with required collections and indexes"""
    print("Setting up test database...")
    
    # Use test database
    os.environ["ARANGODB_DATABASE"] = "test_memory_db"
    
    try:
        # Connect to ArangoDB
        client = connect_arango()
        
        # Temporarily set the database name
        original_db = os.environ.get("ARANGODB_DATABASE", "memory_agent_db")
        os.environ["ARANGODB_DATABASE"] = "test_memory_db"
        
        db = ensure_database(client)
        
        # Get database connection through CLI layer
        db = get_db_connection()
        
        # Required collections
        required_collections = [
            "documents",
            "conversations", 
            "episodes",
            "communities",
            "edges",
            "message_history",
            "compaction_history",
            "test_products",
            "test_users",
            "test_documents",
            "test_nodes",
            "test_search_collection"
        ]
        
        # Create collections if they don't exist
        for collection_name in required_collections:
            if not db.has_collection(collection_name):
                print(f"Creating collection: {collection_name}")
                db.create_collection(collection_name)
            else:
                print(f"Collection exists: {collection_name}")
        
        # Ensure edge collections are properly configured
        from arangodb.core.arango_setup import ensure_edge_collections
        ensure_edge_collections(db)
        
        # Create necessary indexes
        from arangodb.core.arango_setup import ensure_vector_index
        # Create vector indexes for collections that need them
        collections_with_embeddings = ["documents", "conversations", "test_documents"]
        for collection_name in collections_with_embeddings:
            if db.has_collection(collection_name):
                ensure_vector_index(db, collection_name, "embedding", 768)
        
        print("\n Test database setup complete!")
        print(f"Database: {db.name}")
        print(f"Collections: {len(db.collections())}")
        
        return True
        
    except Exception as e:
        print(f"\n Error setting up test database: {e}")
        logger.error(f"Database setup failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test data from previous runs"""
    print("\nCleaning up old test data...")
    
    try:
        db = get_db_connection()
        
        # Collections to clean
        test_collections = [
            "test_products",
            "test_users", 
            "test_documents",
            "test_nodes",
            "test_search_collection"
        ]
        
        for collection_name in test_collections:
            if db.has_collection(collection_name):
                collection = db.collection(collection_name)
                collection.truncate()
                print(f"Cleaned: {collection_name}")
        
        print(" Cleanup complete!")
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("ArangoDB CLI Test Database Setup")
    print("=" * 50)
    
    # Setup database
    if setup_test_database():
        cleanup_test_data()
        print("\n Ready to run tests!")
        print("Run: python test_all_cli_commands.py")
    else:
        print("\n⚠️  Setup failed. Please check your ArangoDB connection.")
        # sys.exit() removed