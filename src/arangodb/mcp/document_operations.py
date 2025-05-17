"""
ArangoDB MCP Document Operations

This module provides MCP (Machine-Collaborator Protocol) integration for ArangoDB document operations,
built on top of the core business logic layer. These functions allow Claude to interact with
ArangoDB through the MCP interface for CRUD operations on documents.

Operations include:
- Creating documents
- Reading documents
- Updating documents
- Deleting documents
- Creating relationships
- Deleting relationships

Sample Input:
- MCP function call with parameters (e.g., document data, document key, etc.)

Expected Output:
- Standardized JSON response conforming to MCP protocol
"""

import json
from typing import List, Optional, Dict, Any, Union
from loguru import logger

# Import from core layer
from arangodb.core.db_operations import (
    create_document,
    get_document,
    update_document,
    delete_document,
    query_documents
)

from arangodb.core.graph import (
    create_relationship,
    delete_relationship_by_key
)

# Import utilities for embedding generation
from arangodb.core.utils.embedding_utils import get_embedding

# Import constants from core
from arangodb.core.constants import (
    COLLECTION_NAME,
    EDGE_COLLECTION_NAME,
    GRAPH_NAME
)

# Import connection utilities
from arangodb.cli.db_connection import get_db_connection


def mcp_create_document(
    document_data: Dict[str, Any],
    collection_name: str = COLLECTION_NAME,
    generate_embedding: bool = True
) -> Dict[str, Any]:
    """
    Create a new document in ArangoDB.
    
    Args:
        document_data: Dictionary with document fields
        collection_name: Collection to store the document in
        generate_embedding: Whether to generate embeddings for the document
    
    Returns:
        Dictionary with operation result and metadata
    """
    logger.info(f"MCP: Creating new document in collection '{collection_name}'")
    
    try:
        db = get_db_connection()
        
        # Generate embedding if requested and not already present
        if generate_embedding and 'embedding' not in document_data:
            # Extract text from relevant fields
            text_fields = ['problem', 'solution', 'context', 'content', 'title', 'summary']
            text_to_embed = " ".join([document_data.get(field, "") for field in text_fields if field in document_data])
            
            if text_to_embed.strip():
                embedding = get_embedding(text_to_embed)
                if embedding:
                    document_data['embedding'] = embedding
                    logger.debug("Embedding generated and added to document data")
        
        # Call the core layer create_document function
        meta = create_document(db, collection_name, document_data)
        
        if meta:
            return {
                "status": "success",
                "data": meta,
                "message": f"Document created successfully with key: {meta.get('_key')}"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to create document (no metadata returned)",
                "data": None
            }
    except Exception as e:
        logger.error(f"MCP create document failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_get_document(
    document_key: str,
    collection_name: str = COLLECTION_NAME
) -> Dict[str, Any]:
    """
    Retrieve a document from ArangoDB by key.
    
    Args:
        document_key: Key of the document to retrieve
        collection_name: Collection to retrieve the document from
    
    Returns:
        Dictionary with operation result and document data
    """
    logger.info(f"MCP: Retrieving document '{document_key}' from collection '{collection_name}'")
    
    try:
        db = get_db_connection()
        
        # Call the core layer get_document function
        doc = get_document(db, collection_name, document_key)
        
        if doc:
            return {
                "status": "success",
                "data": doc,
                "message": f"Document retrieved successfully"
            }
        else:
            return {
                "status": "not_found",
                "message": f"Document with key '{document_key}' not found in collection '{collection_name}'",
                "data": None
            }
    except Exception as e:
        logger.error(f"MCP get document failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_update_document(
    document_key: str,
    update_data: Dict[str, Any],
    collection_name: str = COLLECTION_NAME,
    regenerate_embedding: bool = True
) -> Dict[str, Any]:
    """
    Update an existing document in ArangoDB.
    
    Args:
        document_key: Key of the document to update
        update_data: Dictionary with fields to update
        collection_name: Collection containing the document
        regenerate_embedding: Whether to regenerate embeddings if certain fields change
    
    Returns:
        Dictionary with operation result and metadata
    """
    logger.info(f"MCP: Updating document '{document_key}' in collection '{collection_name}'")
    
    try:
        db = get_db_connection()
        
        # Check if document exists first
        current_doc = get_document(db, collection_name, document_key)
        if not current_doc:
            return {
                "status": "not_found",
                "message": f"Document with key '{document_key}' not found in collection '{collection_name}'",
                "data": None
            }
        
        # Check if we need to regenerate embedding
        if regenerate_embedding:
            embedding_fields = ['problem', 'solution', 'context', 'content', 'title', 'summary']
            needs_embedding_update = any(field in update_data for field in embedding_fields)
            
            if needs_embedding_update:
                # Merge current and update data for embedding generation
                merged_doc = {**current_doc, **update_data}
                text_to_embed = " ".join([merged_doc.get(field, "") for field in embedding_fields if field in merged_doc])
                
                if text_to_embed.strip():
                    embedding = get_embedding(text_to_embed)
                    if embedding:
                        update_data['embedding'] = embedding
                        logger.debug("Embedding regenerated and added to update data")
        
        # Call the core layer update_document function
        meta = update_document(db, collection_name, document_key, update_data)
        
        if meta:
            return {
                "status": "success",
                "data": meta,
                "message": f"Document updated successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to update document (no metadata returned)",
                "data": None
            }
    except Exception as e:
        logger.error(f"MCP update document failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_delete_document(
    document_key: str,
    collection_name: str = COLLECTION_NAME
) -> Dict[str, Any]:
    """
    Delete a document from ArangoDB.
    
    Args:
        document_key: Key of the document to delete
        collection_name: Collection containing the document
    
    Returns:
        Dictionary with operation result
    """
    logger.info(f"MCP: Deleting document '{document_key}' from collection '{collection_name}'")
    
    try:
        db = get_db_connection()
        
        # Call the core layer delete_document function
        result = delete_document(db, collection_name, document_key)
        
        if result:
            return {
                "status": "success",
                "data": {"deleted": True},
                "message": f"Document deleted successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to delete document",
                "data": None
            }
    except Exception as e:
        logger.error(f"MCP delete document failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_create_relationship(
    from_id: str,
    to_id: str,
    edge_attributes: Dict[str, Any],
    edge_collection: str = EDGE_COLLECTION_NAME
) -> Dict[str, Any]:
    """
    Create a relationship (edge) between two documents.
    
    Args:
        from_id: ID of the source document
        to_id: ID of the target document
        edge_attributes: Attributes for the edge (must include 'type')
        edge_collection: Collection to store the edge in
    
    Returns:
        Dictionary with operation result and metadata
    """
    logger.info(f"MCP: Creating relationship from '{from_id}' to '{to_id}'")
    
    try:
        db = get_db_connection()
        
        # Validate edge attributes
        if not edge_attributes or not isinstance(edge_attributes, dict):
            return {
                "status": "error",
                "message": "Edge attributes must be a non-empty dictionary",
                "data": None
            }
        
        if 'type' not in edge_attributes:
            return {
                "status": "error",
                "message": "Edge attributes must include a 'type' field",
                "data": None
            }
        
        # Call the core layer create_relationship function
        meta = create_relationship(
            db,
            from_id,
            to_id,
            edge_collection,
            edge_attributes
        )
        
        if meta:
            return {
                "status": "success",
                "data": meta,
                "message": f"Relationship created successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to create relationship (no metadata returned)",
                "data": None
            }
    except Exception as e:
        logger.error(f"MCP create relationship failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_delete_relationship(
    edge_key: str,
    edge_collection: str = EDGE_COLLECTION_NAME
) -> Dict[str, Any]:
    """
    Delete a relationship (edge) from ArangoDB.
    
    Args:
        edge_key: Key of the edge to delete
        edge_collection: Collection containing the edge
    
    Returns:
        Dictionary with operation result
    """
    logger.info(f"MCP: Deleting relationship '{edge_key}' from collection '{edge_collection}'")
    
    try:
        db = get_db_connection()
        
        # Call the core layer delete_relationship_by_key function
        result = delete_relationship_by_key(db, edge_collection, edge_key)
        
        if result:
            return {
                "status": "success",
                "data": {"deleted": True},
                "message": f"Relationship deleted successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to delete relationship",
                "data": None
            }
    except Exception as e:
        logger.error(f"MCP delete relationship failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


if __name__ == "__main__":
    """Test function for this module alone."""
    import sys
    
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List of validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Check imports work correctly
    total_tests += 1
    try:
        # Test import paths
        test_result = "create_document" in globals() and "get_document" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import core document functions")
    except Exception as e:
        all_validation_failures.append(f"Import validation failed: {e}")
    
    # Test 2: Verify MCP functions exist
    total_tests += 1
    try:
        # Check that we have MCP functions defined
        functions = ["mcp_create_document", "mcp_get_document", "mcp_update_document", 
                    "mcp_delete_document", "mcp_create_relationship", "mcp_delete_relationship"]
        
        missing_functions = [f for f in functions if f not in globals()]
        if missing_functions:
            all_validation_failures.append(f"Missing MCP functions: {missing_functions}")
    except Exception as e:
        all_validation_failures.append(f"MCP function validation failed: {e}")
    
    # Display validation results
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Module validated and ready for use")
        sys.exit(0)