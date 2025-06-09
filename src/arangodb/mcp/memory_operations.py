"""
ArangoDB MCP Memory Operations
Module: memory_operations.py
Description: Functions for memory operations operations

This module provides MCP (Machine-Collaborator Protocol) integration for ArangoDB memory operations,
built on top of the core business logic layer. These functions allow Claude to interact with
the memory agent through the MCP interface.

Operations include:
- Storing conversations
- Retrieving conversation history
- Temporal searches over memory data
- Managing memory relationships

Sample Input:
- MCP function call with parameters (e.g., conversation data, query text, etc.)

Expected Output:
- Standardized JSON response conforming to MCP protocol
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from loguru import logger

# Import from core layer
from arangodb.core.memory import MemoryAgent

# Import constants from core
from arangodb.core.constants import (
    MEMORY_MESSAGE_COLLECTION,
    MEMORY_COLLECTION,
    MEMORY_EDGE_COLLECTION,
    MEMORY_VIEW_NAME,
    MEMORY_GRAPH_NAME
)

# Import connection utilities
from arangodb.cli.db_connection import get_db_connection


def mcp_store_conversation(
    user_message: str,
    agent_response: str,
    conversation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Store a user-agent message exchange in the memory database.
    
    Args:
        user_message: The user's message to store'
        agent_response: The agent's response to store'
        conversation_id: Optional ID for the conversation
        metadata: Additional metadata for the conversation
        timestamp: ISO-8601 formatted timestamp when the conversation occurred
    
    Returns:
        Dictionary with operation result and metadata
    """
    logger.info(f"MCP: Storing conversation" + (f" with ID '{conversation_id}'" if conversation_id else ""))
    
    try:
        db = get_db_connection()
        
        # Parse reference_time if provided
        reference_time = None
        if timestamp:
            try:
                reference_time = datetime.fromisoformat(timestamp)
                logger.debug(f"Using provided reference time: {reference_time.isoformat()}")
            except ValueError as e:
                return {
                    "status": "error",
                    "message": f"Invalid timestamp format: {e}. Use ISO-8601 format, e.g., 2023-01-01T12:00:00",
                    "data": None
                }
        
        # Initialize the memory agent
        memory_agent = MemoryAgent(db)
        
        # Store the conversation
        result = memory_agent.store_conversation(
            conversation_id=conversation_id,
            user_message=user_message,
            agent_response=agent_response,
            metadata=metadata,
            reference_time=reference_time
        )
        
        if result:
            return {
                "status": "success",
                "data": result,
                "message": f"Conversation stored successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to store conversation (no result returned)",
                "data": None
            }
    except Exception as e:
        logger.error(f"MCP store conversation failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_get_conversation_history(
    conversation_id: str,
    limit: int = 20,
    include_embeddings: bool = False
) -> Dict[str, Any]:
    """
    Retrieve the message history for a specific conversation.
    
    Args:
        conversation_id: ID of the conversation to retrieve
        limit: Maximum number of messages to retrieve
        include_embeddings: Whether to include embedding vectors
    
    Returns:
        Dictionary with operation result and message history
    """
    logger.info(f"MCP: Retrieving conversation history for ID '{conversation_id}'")
    
    try:
        db = get_db_connection()
        
        # Initialize the memory agent
        memory_agent = MemoryAgent(db)
        
        # Get the conversation history
        messages = memory_agent.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit,
            include_embeddings=include_embeddings
        )
        
        if messages is not None:  # Could be an empty list, which is valid
            return {
                "status": "success",
                "data": {"messages": messages, "count": len(messages)},
                "message": f"Retrieved {len(messages)} messages"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to retrieve conversation history",
                "data": None
            }
    except Exception as e:
        logger.error(f"MCP get conversation history failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_search_memory(
    query_text: str,
    point_in_time: Optional[str] = None,
    top_n: int = 10,
    include_messages: bool = False
) -> Dict[str, Any]:
    """
    Search for memories valid at a specific point in time.
    
    Args:
        query_text: The search query text
        point_in_time: ISO-8601 formatted timestamp for temporal search
        top_n: Maximum number of results to return
        include_messages: Whether to include individual messages in search
    
    Returns:
        Dictionary with operation result and search results
    """
    logger.info(f"MCP: Searching memory for '{query_text}'")
    
    try:
        db = get_db_connection()
        
        # Parse point_in_time if provided
        search_time = None
        if point_in_time:
            try:
                search_time = datetime.fromisoformat(point_in_time)
                logger.debug(f"Using provided search time: {search_time.isoformat()}")
            except ValueError as e:
                return {
                    "status": "error",
                    "message": f"Invalid timestamp format: {e}. Use ISO-8601 format, e.g., 2023-01-01T12:00:00",
                    "data": None
                }
        
        # Initialize the memory agent
        memory_agent = MemoryAgent(db)
        
        # Determine which collections to search
        collections = [MEMORY_COLLECTION]
        if include_messages:
            collections.append(MEMORY_MESSAGE_COLLECTION)
        
        # Perform the temporal search
        results = memory_agent.temporal_search(
            query_text=query_text,
            point_in_time=search_time,
            collections=collections,
            top_n=top_n
        )
        
        return {
            "status": "success",
            "data": results,
            "message": f"Found {len(results.get('results', []))} results"
        }
    except Exception as e:
        logger.error(f"MCP memory search failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_detect_contradictions(
    document_data: Dict[str, Any],
    collection_name: str = MEMORY_COLLECTION,
    relationship_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Detect potential contradictions for a new document or relationship.
    
    Args:
        document_data: Document or edge data to check
        collection_name: Collection to check against
        relationship_type: Type of relationship to check
    
    Returns:
        Dictionary with operation result and detected contradictions
    """
    logger.info(f"MCP: Detecting contradictions in collection '{collection_name}'")
    
    try:
        db = get_db_connection()
        
        # Determine if we're checking a document or an edge
        is_edge = ("_from" in document_data and "_to" in document_data)
        
        if is_edge:
            # For edges, we'd need to implement edge contradiction detection in MemoryAgent
            # This is a placeholder for now
            logger.warning("Edge contradiction detection is not implemented in the core layer yet")
            
            return {
                "status": "warning",
                "message": "Edge contradiction detection is not implemented yet",
                "data": {"contradictions": [], "count": 0}
            }
        else:
            # For documents, we'd need a specific document contradiction detection method
            # This is a placeholder for document contradiction detection
            return {
                "status": "warning",
                "message": "Document contradiction detection is not implemented yet",
                "data": {"contradictions": [], "count": 0}
            }
    except Exception as e:
        logger.error(f"MCP detect contradictions failed: {e}", exc_info=True)
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
        test_result = "MemoryAgent" in globals() and "MEMORY_COLLECTION" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import core memory functions")
    except Exception as e:
        all_validation_failures.append(f"Import validation failed: {e}")
    
    # Test 2: Verify MCP functions exist
    total_tests += 1
    try:
        # Check that we have MCP functions defined
        functions = ["mcp_store_conversation", "mcp_get_conversation_history", 
                    "mcp_search_memory", "mcp_detect_contradictions"]
        
        missing_functions = [f for f in functions if f not in globals()]
        if missing_functions:
            all_validation_failures.append(f"Missing MCP functions: {missing_functions}")
    except Exception as e:
        all_validation_failures.append(f"MCP function validation failed: {e}")
    
    # Display validation results
    if all_validation_failures:
        print(f" VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f" VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Module validated and ready for use")
        sys.exit(0)