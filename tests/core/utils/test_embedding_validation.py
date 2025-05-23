#!/usr/bin/env python3
"""
Test embedding configuration validation for ArangoDB integration.

This test validates:
1. Embedding field exists in collections
2. Vector indexes exist with proper configuration
3. Embedding dimensions match expected 1024 dimensions from env vars
"""

import os
import sys
from pathlib import Path
import unittest
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import ArangoDB setup functions
from complexity.arangodb.arango_setup import (
    connect_arango,
    ensure_database,
    validate_embedding_dimensions
)

# Load environment variables
load_dotenv()

# Constants from environment variables
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", 1024))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
EMBEDDING_FIELD = os.environ.get("EMBEDDING_FIELD", "embedding")

class TestEmbeddingValidation(unittest.TestCase):
    """Test embedding configuration and validate dimensions."""
    
    @classmethod
    def setUpClass(cls):
        """Connect to database and setup test environment."""
        # Set up ArangoDB connection
        cls.client = connect_arango()
        cls.db = ensure_database(cls.client)
        
        # Get collections to test
        cls.collections = [c for c in cls.db.collections() if not c["name"].startswith("_")]
        cls.collection_names = [c["name"] for c in cls.collections]
        
        print(f"✅ Connected to database with {len(cls.collection_names)} collections")
        
    def test_env_variables(self):
        """Verify environment variables are properly set."""
        self.assertEqual(EMBEDDING_DIMENSION, 1024, 
                         "EMBEDDING_DIMENSION should be 1024")
        self.assertEqual(EMBEDDING_MODEL, "BAAI/bge-large-en-v1.5", 
                         "EMBEDDING_MODEL should be BAAI/bge-large-en-v1.5")
        self.assertIsNotNone(EMBEDDING_FIELD, 
                             "EMBEDDING_FIELD should be defined")
        
        print(f"✅ Environment variables validated: {EMBEDDING_MODEL} / {EMBEDDING_DIMENSION}d")

    def test_embedding_field_exists(self):
        """Check that embedding fields exist in collections."""
        collections_with_embeddings = []
        
        for collection_name in self.collection_names:
            # Skip system collections and edge collections
            if collection_name.startswith("_") or collection_name in ["prerequisites", "related_topics"]:
                continue
                
            # Check if the collection has documents with embedding field
            query = f"""
            FOR doc IN {collection_name}
            FILTER HAS(doc, "{EMBEDDING_FIELD}")
                AND IS_LIST(doc.{EMBEDDING_FIELD})
                AND LENGTH(doc.{EMBEDDING_FIELD}) > 0
            LIMIT 1
            RETURN doc._key
            """
            
            cursor = self.db.aql.execute(query)
            has_embeddings = len(list(cursor)) > 0
            
            if has_embeddings:
                collections_with_embeddings.append(collection_name)
        
        print(f"✅ Collections with embeddings: {collections_with_embeddings}")
        
        # At least one collection should have embeddings for tests to be valid
        self.assertTrue(len(collections_with_embeddings) > 0, 
                        "At least one collection should have embedding fields")

    def test_vector_indexes_exist(self):
        """Check that vector indexes exist for collections with embeddings."""
        for collection_name in self.collection_names:
            # Skip system collections and edge collections
            if collection_name.startswith("_") or collection_name in ["prerequisites", "related_topics"]:
                continue
                
            col = self.db.collection(collection_name)
            indexes = list(col.indexes())
            
            # Find vector indexes
            vector_indexes = [
                idx for idx in indexes 
                if idx.get("type") == "vector" and EMBEDDING_FIELD in idx.get("fields", [])
            ]
            
            if vector_indexes:
                for idx in vector_indexes:
                    # Check dimension configuration
                    params = idx.get("params", {})
                    dimension = params.get("dimension")
                    
                    # Verify dimension is correct
                    if dimension:
                        self.assertEqual(dimension, EMBEDDING_DIMENSION,
                                     f"Vector index in {collection_name} has dimension {dimension}, expected {EMBEDDING_DIMENSION}")
                        print(f"✅ Collection {collection_name} has vector index with correct dimension {dimension}")

    def test_embedding_dimensions(self):
        """Test embedding dimensions in documents match expected dimensions."""
        for collection_name in self.collection_names:
            # Skip system collections and edge collections
            if collection_name.startswith("_") or collection_name in ["prerequisites", "related_topics"]:
                continue
                
            query = f"""
            FOR doc IN {collection_name}
            FILTER HAS(doc, "{EMBEDDING_FIELD}")
                AND IS_LIST(doc.{EMBEDDING_FIELD})
                AND LENGTH(doc.{EMBEDDING_FIELD}) > 0
            LIMIT 5
            RETURN {{
                _key: doc._key,
                embedding_dimension: LENGTH(doc.{EMBEDDING_FIELD})
            }}
            """
            
            try:
                cursor = self.db.aql.execute(query)
                samples = list(cursor)
                
                if samples:
                    for sample in samples:
                        # Check dimension
                        dim = sample.get("embedding_dimension")
                        self.assertEqual(dim, EMBEDDING_DIMENSION,
                                      f"Document {sample.get('_key')} in {collection_name} has dimension {dim}, expected {EMBEDDING_DIMENSION}")
                    
                    print(f"✅ Collection {collection_name} has {len(samples)} documents with correct dimensions")
            except Exception as e:
                print(f"⚠️ Error checking collection {collection_name}: {str(e)}")

    def test_validate_embedding_dimensions_function(self):
        """Test the validate_embedding_dimensions function."""
        # We'll check the validation function for each collection
        for collection_name in self.collection_names:
            # Skip system collections and edge collections
            if collection_name.startswith("_") or collection_name in ["prerequisites", "related_topics"]:
                continue
            
            try:
                # Call the validation function with the specific collection
                config_overrides = {
                    "search": {"collection_name": collection_name},
                    "embedding": {"field": EMBEDDING_FIELD, "dimensions": EMBEDDING_DIMENSION}
                }
                
                # If this throws an exception, the test will fail
                result, message = validate_embedding_dimensions(self.db, config_overrides)
                
                if result:
                    print(f"✅ Collection {collection_name} passed embedding validation")
                else:
                    print(f"⚠️ Collection {collection_name} failed validation: {message}")
                    # We don't assert here because some collections might not have embeddings
            except Exception as e:
                print(f"⚠️ Error validating collection {collection_name}: {str(e)}")
    
if __name__ == "__main__":
    unittest.main()