"""
Document Embedding Validator
Module: embedding_validator.py
Description: Implementation of embedding validator functionality

This module provides utilities for validating and ensuring consistent embeddings
across documents in a collection. It ensures that:

1. All documents have an embedding field with an array
2. All embeddings have the correct dimension
3. All embeddings use the same embedding model
4. Proper logging is provided for empty collections or inconsistent embeddings

This is critical for ensuring APPROX_NEAR_COSINE works correctly.
"""

import time
from typing import Dict, Any, List, Optional, Union, Set
from loguru import logger

from arango.database import StandardDatabase
from arango.collection import StandardCollection
from arango.cursor import Cursor

# Constants
EMBEDDING_FIELD = "embedding"
EMBEDDING_METADATA_FIELD = "embedding_metadata"


class EmbeddingValidator:
    """
    Validates and ensures consistent embeddings across documents in a collection.
    
    This class provides utilities for:
    1. Checking if documents have valid embeddings
    2. Ensuring new documents have embeddings that match the collection
    3. Fixing documents with missing or inconsistent embeddings
    """
    
    def __init__(
        self, 
        db: StandardDatabase,
        collection_name: str,
        embedding_field: str = EMBEDDING_FIELD,
        metadata_field: str = EMBEDDING_METADATA_FIELD,
        default_model: Optional[str] = None,
        default_dimensions: Optional[int] = None
    ):
        """
        Initialize the embedding validator.
        
        Args:
            db: ArangoDB database connection
            collection_name: Name of the collection to validate
            embedding_field: Name of the embedding field
            metadata_field: Name of the embedding metadata field
            default_model: Default embedding model to use
            default_dimensions: Default embedding dimensions
        """
        self.db = db
        self.collection_name = collection_name
        self.embedding_field = embedding_field
        self.metadata_field = metadata_field
        self.default_model = default_model
        self.default_dimensions = default_dimensions
        
        # Initialize current dimensions and model
        self.current_dimensions = default_dimensions
        self.current_model = default_model
        
        # Initialize collection and stats
        self.collection = db.collection(collection_name) if db.has_collection(collection_name) else None
        self.stats = self._get_stats()
    
    def _get_stats(self) -> Dict[str, Any]:
        """Get statistics about embeddings in the collection."""
        stats = {
            "total_documents": 0,
            "documents_with_embeddings": 0,
            "documents_with_metadata": 0,
            "dimensions_found": set(),
            "embedding_models": set(),
            "consistency": False,
            "issues": []
        }
        
        if not self.collection:
            stats["issues"].append(f"Collection {self.collection_name} does not exist")
            return stats
        
        # Get total document count
        stats["total_documents"] = self.collection.count()
        
        # Initialize current dimensions and model
        self.current_dimensions = self.default_dimensions
        self.current_model = self.default_model
        
        if stats["total_documents"] == 0:
            stats["issues"].append(f"Collection {self.collection_name} is empty")
            return stats
        
        # Get documents with embeddings
        aql = f"""
        RETURN {{
            with_embeddings: LENGTH(
                FOR doc IN {self.collection_name}
                FILTER HAS(doc, "{self.embedding_field}")
                RETURN 1
            ),
            with_metadata: LENGTH(
                FOR doc IN {self.collection_name}
                FILTER HAS(doc, "{self.metadata_field}")
                RETURN 1
            ),
            dimensions: (
                FOR doc IN {self.collection_name}
                FILTER HAS(doc, "{self.embedding_field}")
                    AND IS_LIST(doc.{self.embedding_field})
                RETURN LENGTH(doc.{self.embedding_field})
            ),
            models: (
                FOR doc IN {self.collection_name}
                FILTER HAS(doc, "{self.metadata_field}")
                    AND HAS(doc.{self.metadata_field}, "model")
                RETURN DISTINCT doc.{self.metadata_field}.model
            )
        }}
        """
        
        cursor = self.db.aql.execute(aql)
        result = next(cursor)
        
        stats["documents_with_embeddings"] = result["with_embeddings"]
        stats["documents_with_metadata"] = result["with_metadata"]
        stats["dimensions_found"] = set(result["dimensions"])
        stats["embedding_models"] = set(result["models"])
        
        # Check for issues
        if stats["documents_with_embeddings"] < stats["total_documents"]:
            stats["issues"].append(
                f"{stats['total_documents'] - stats['documents_with_embeddings']} documents missing embeddings"
            )
            
        if stats["documents_with_metadata"] < stats["documents_with_embeddings"]:
            stats["issues"].append(
                f"{stats['documents_with_embeddings'] - stats['documents_with_metadata']} documents with embeddings missing metadata"
            )
            
        if len(stats["dimensions_found"]) > 1:
            stats["issues"].append(f"Inconsistent embedding dimensions: {stats['dimensions_found']}")
            
        if len(stats["embedding_models"]) > 1:
            stats["issues"].append(f"Multiple embedding models found: {stats['embedding_models']}")
            
        # Check array format
        aql_check = f"""
        RETURN LENGTH(
            FOR doc IN {self.collection_name}
            FILTER HAS(doc, "{self.embedding_field}")
                AND NOT IS_LIST(doc.{self.embedding_field})
            RETURN 1
        )
        """
        cursor = self.db.aql.execute(aql_check)
        non_array_count = next(cursor)
        
        if non_array_count > 0:
            stats["issues"].append(f"{non_array_count} documents have embeddings that are not in array format")
        
        # Determine if embeddings are consistent
        stats["consistency"] = len(stats["issues"]) == 0 and stats["documents_with_embeddings"] > 0
        
        # Set the dominant model and dimensions if available
        if stats["embedding_models"]:
            self.current_model = next(iter(stats["embedding_models"]))
        else:
            self.current_model = self.default_model
            
        if stats["dimensions_found"]:
            self.current_dimensions = next(iter(stats["dimensions_found"]))
        else:
            self.current_dimensions = self.default_dimensions
        
        return stats
    
    def validate_document_embedding(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and fix a document's embedding if needed.
        
        Args:
            document: Document to validate
            
        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "issues": List[str],
                "fixed": bool,
                "modified_document": Dict (if fixed)
            }
        """
        result = {
            "valid": False,
            "issues": [],
            "fixed": False,
            "modified_document": None
        }
        
        # Skip validation if no embeddings in collection
        if self.stats["documents_with_embeddings"] == 0:
            if not self.current_dimensions or not self.current_model:
                result["issues"].append("No embeddings in collection to establish baseline")
                return result
        
        # Check if embedding exists
        if self.embedding_field not in document:
            result["issues"].append("Missing embedding field")
            return result
        
        embedding = document[self.embedding_field]
        
        # Check embedding type
        if not isinstance(embedding, list):
            result["issues"].append(f"Embedding is not a list (type: {type(embedding)})")
            return result
        
        # Check embedding dimensions
        if self.current_dimensions and len(embedding) != self.current_dimensions:
            result["issues"].append(
                f"Embedding dimension mismatch: got {len(embedding)}, expected {self.current_dimensions}"
            )
            return result
        
        # Check metadata
        if self.metadata_field not in document:
            result["issues"].append("Missing embedding metadata")
            return result
        
        metadata = document[self.metadata_field]
        
        if not isinstance(metadata, dict):
            result["issues"].append("Metadata is not a dictionary")
            return result
        
        if "model" not in metadata:
            result["issues"].append("Metadata missing 'model' field")
            return result
        
        if "dimensions" not in metadata:
            result["issues"].append("Metadata missing 'dimensions' field")
            return result
        
        if self.current_model and metadata["model"] != self.current_model:
            result["issues"].append(
                f"Embedding model mismatch: got {metadata['model']}, expected {self.current_model}"
            )
            return result
        
        if metadata["dimensions"] != len(embedding):
            result["issues"].append(
                f"Metadata dimensions ({metadata['dimensions']}) don't match actual embedding length ({len(embedding)})"
            )
            return result
        
        # If we get here, the embedding is valid
        result["valid"] = True
        
        return result
    
    def log_embedding_status(self):
        """Log the current embedding status of the collection."""
        logger.info(f"Embedding status for collection: {self.collection_name}")
        logger.info(f"Total documents: {self.stats['total_documents']}")
        logger.info(f"Documents with embeddings: {self.stats['documents_with_embeddings']}")
        logger.info(f"Documents with metadata: {self.stats['documents_with_metadata']}")
        logger.info(f"Dimensions found: {self.stats['dimensions_found']}")
        logger.info(f"Embedding models: {self.stats['embedding_models']}")
        
        if self.stats["consistency"]:
            logger.info("Embeddings are consistent across the collection")
        else:
            logger.warning("Embeddings are inconsistent across the collection")
            for issue in self.stats["issues"]:
                logger.warning(f"Issue: {issue}")
    
    def can_perform_semantic_search(self) -> bool:
        """
        Check if the collection can perform semantic search.
        
        Returns:
            True if semantic search can be performed, False otherwise
        """
        # Need at least 2 documents with valid embeddings for APPROX_NEAR_COSINE
        return (
            self.stats["documents_with_embeddings"] >= 2 and
            len(self.stats["dimensions_found"]) == 1 and
            len(self.stats["issues"]) == 0
        )
    
    def get_semantic_search_status(self) -> Dict[str, Any]:
        """
        Get the semantic search status of the collection.
        
        Returns:
            Dict with status information
        """
        status = {
            "can_search": self.can_perform_semantic_search(),
            "issues": self.stats["issues"],
            "embeddings_count": self.stats["documents_with_embeddings"],
            "consistent_dimensions": len(self.stats["dimensions_found"]) <= 1,
            "consistent_models": len(self.stats["embedding_models"]) <= 1,
            "dimensions": self.current_dimensions,
            "model": self.current_model
        }
        
        # Add more detailed information
        if status["can_search"]:
            status["message"] = "Collection is ready for semantic search"
        else:
            if self.stats["documents_with_embeddings"] < 2:
                status["message"] = "Not enough documents with embeddings for semantic search (need at least 2)"
            elif len(self.stats["dimensions_found"]) > 1:
                status["message"] = f"Inconsistent embedding dimensions: {self.stats['dimensions_found']}"
            elif len(self.stats["issues"]) > 0:
                status["message"] = f"Collection has embedding issues: {', '.join(self.stats['issues'])}"
            else:
                status["message"] = "Unknown issue preventing semantic search"
        
        return status


# Decorator for validating document embeddings before insertion
def validate_embedding_before_insert(
    collection_name: str = None,
    embedding_field: str = EMBEDDING_FIELD,
    metadata_field: str = EMBEDDING_METADATA_FIELD
):
    """
    Decorator for validating document embeddings before insertion.
    
    Args:
        collection_name: Name of the collection (if None, use the method's first argument)
        embedding_field: Name of the embedding field
        metadata_field: Name of the embedding metadata field
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get parameters
            db = args[0]  # First argument is typically the database
            coll_name = collection_name or args[1]  # Second argument is typically the collection name
            documents = args[2] if len(args) > 2 else kwargs.get("documents")  # Documents to insert
            
            if not documents:
                logger.warning("No documents provided for insertion")
                return func(*args, **kwargs)
            
            # Create validator
            validator = EmbeddingValidator(
                db, coll_name, embedding_field, metadata_field
            )
            
            # Log collection status
            validator.log_embedding_status()
            
            # Validate each document
            documents_to_insert = []
            for doc in documents:
                validation = validator.validate_document_embedding(doc)
                if validation["valid"]:
                    documents_to_insert.append(doc)
                else:
                    logger.warning(f"Document with invalid embedding: {validation['issues']}")
                    # TODO: Handle invalid documents (skip, fix, or reject)
                    # For now, just skip them
            
            # Update args or kwargs with validated documents
            if len(args) > 2:
                new_args = list(args)
                new_args[2] = documents_to_insert
                return func(*new_args, **kwargs)
            else:
                kwargs["documents"] = documents_to_insert
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Function to check if semantic search is possible for a collection
def check_semantic_search_readiness(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str = EMBEDDING_FIELD,
    metadata_field: str = EMBEDDING_METADATA_FIELD
) -> Dict[str, Any]:
    """
    Check if a collection is ready for semantic search.
    
    Args:
        db: ArangoDB database connection
        collection_name: Name of the collection to check
        embedding_field: Name of the embedding field
        metadata_field: Name of the embedding metadata field
        
    Returns:
        Dict with readiness information
    """
    validator = EmbeddingValidator(
        db, collection_name, embedding_field, metadata_field
    )
    
    return validator.get_semantic_search_status()