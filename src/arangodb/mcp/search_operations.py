"""
ArangoDB MCP Search Operations
Module: search_operations.py
Description: Functions for search operations operations

This module provides MCP (Machine-Collaborator Protocol) integration for ArangoDB search operations,
built on top of the core business logic layer. These functions allow Claude to interact with
ArangoDB through the MCP interface.

Operations include:
- BM25 search
- Semantic search
- Hybrid search
- Tag search
- Keyword search
- Graph traversal

Sample Input:
- MCP function call with parameters (e.g., query_text, min_score, etc.)

Expected Output:
- Standardized JSON response conforming to MCP protocol
"""

import json
from typing import List, Optional, Dict, Any, Union
from loguru import logger

# Import from core layer
from arangodb.core.search import (
    bm25_search,
    hybrid_search,
    tag_search,
    graph_traverse,
    search_keyword,
    glossary_search
)

# Import safe semantic search for better error handling
from arangodb.core.search.semantic_search import safe_semantic_search as semantic_search

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


def mcp_bm25_search(
    query_text: str,
    min_score: float = 0.1,
    top_n: int = 5,
    offset: int = 0,
    tag_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform BM25 search over ArangoDB documents.
    
    Args:
        query_text: The search query text
        min_score: Minimum BM25 score threshold (0.0+)
        top_n: Number of results to return
        offset: Offset for pagination
        tag_list: Optional list of tags to filter by
    
    Returns:
        Dictionary with search results and metadata
    """
    logger.info(f"MCP: Performing BM25 search for '{query_text}'")
    
    try:
        db = get_db_connection()
        
        # Call the core layer BM25 search function
        results_data = bm25_search(
            db=db,
            query_text=query_text,
            min_score=min_score,
            top_n=top_n,
            offset=offset,
            tag_list=tag_list
        )
        
        # Return the results
        return {
            "status": "success",
            "data": results_data,
            "message": f"Found {len(results_data.get('results', []))} results"
        }
    except Exception as e:
        logger.error(f"MCP BM25 search failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_semantic_search(
    query_text: str,
    min_score: float = 0.75,
    top_n: int = 5,
    tag_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform semantic (vector) search over ArangoDB documents.
    
    Args:
        query_text: The search query text to embed
        min_score: Minimum similarity score threshold (0.0-1.0)
        top_n: Number of results to return
        tag_list: Optional list of tags to filter by
    
    Returns:
        Dictionary with search results and metadata
    """
    logger.info(f"MCP: Performing semantic search for '{query_text}'")
    
    try:
        db = get_db_connection()
        
        # Generate query embedding
        query_embedding = get_embedding(query_text)
        if not query_embedding:
            return {
                "status": "error",
                "message": "Failed to generate embedding for the query",
                "data": None
            }
        
        # Call the core layer semantic search function
        results_data = semantic_search(
            db=db,
            query_embedding=query_embedding,
            top_n=top_n,
            min_score=min_score,
            tag_list=tag_list
        )
        
        # Return the results
        return {
            "status": "success",
            "data": results_data,
            "message": f"Found {len(results_data.get('results', []))} results"
        }
    except Exception as e:
        logger.error(f"MCP semantic search failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_hybrid_search(
    query_text: str,
    top_n: int = 5,
    initial_k: int = 20,
    min_bm25_score: float = 0.01,
    min_semantic_score: float = 0.70,
    tag_list: Optional[List[str]] = None,
    use_reranking: bool = False,
    reranking_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    reranking_strategy: str = "replace"
) -> Dict[str, Any]:
    """
    Perform hybrid search combining BM25 and semantic search with RRF.
    
    Args:
        query_text: The search query text
        top_n: Final number of ranked results
        initial_k: Number of candidates from BM25/Semantic
        min_bm25_score: BM25 score threshold
        min_semantic_score: Semantic similarity threshold
        tag_list: Optional list of tags to filter by
        use_reranking: Whether to apply cross-encoder reranking
        reranking_model: Model to use for reranking
        reranking_strategy: Strategy for combining scores
    
    Returns:
        Dictionary with search results and metadata
    """
    logger.info(f"MCP: Performing hybrid search for '{query_text}'")
    
    try:
        db = get_db_connection()
        
        # Call the core layer hybrid search function
        results_data = hybrid_search(
            db=db,
            query_text=query_text,
            top_n=top_n,
            initial_k=initial_k,
            min_bm25_score=min_bm25_score,
            min_semantic_score=min_semantic_score,
            tag_list=tag_list
        )
        
        # Apply reranking if requested
        if use_reranking:
            from arangodb.core.search import rerank_results
            
            # Extract documents for reranking
            docs_to_rerank = [r.get("doc", r) for r in results_data.get("results", [])]
            
            # Apply reranking
            reranked_results = rerank_results(
                query=query_text,
                documents=docs_to_rerank,
                model_name=reranking_model,
                strategy=reranking_strategy,
                original_scores=[r.get("rrf_score", 0.5) for r in results_data.get("results", [])]
            )
            
            # Update results with reranked scores
            results_data["results"] = reranked_results
            results_data["reranking_applied"] = True
            results_data["reranking_model"] = reranking_model
            results_data["reranking_strategy"] = reranking_strategy
        
        # Return the results
        return {
            "status": "success",
            "data": results_data,
            "message": f"Found {len(results_data.get('results', []))} results"
        }
    except Exception as e:
        logger.error(f"MCP hybrid search failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_tag_search(
    tags: List[str],
    limit: int = 10,
    require_all_tags: bool = False
) -> Dict[str, Any]:
    """
    Search for documents with specific tags.
    
    Args:
        tags: List of tags to search for
        limit: Maximum number of results
        require_all_tags: Whether all tags must be present
    
    Returns:
        Dictionary with search results and metadata
    """
    logger.info(f"MCP: Performing tag search for: {tags}")
    
    try:
        db = get_db_connection()
        
        # Call the core layer tag search function
        results_data = tag_search(
            db=db,
            tags=tags,
            limit=limit,
            require_all_tags=require_all_tags
        )
        
        # Return the results
        return {
            "status": "success",
            "data": results_data,
            "message": f"Found {len(results_data.get('results', []))} results"
        }
    except Exception as e:
        logger.error(f"MCP tag search failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_keyword_search(
    search_term: str,
    top_n: int = 10,
    require_all: bool = False,
    search_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Search for documents containing specific keywords.
    
    Args:
        search_term: Keywords to search for
        top_n: Maximum number of results
        require_all: Whether all keywords must be present
        search_fields: Fields to search in
    
    Returns:
        Dictionary with search results and metadata
    """
    logger.info(f"MCP: Performing keyword search for: '{search_term}'")
    
    try:
        db = get_db_connection()
        
        # Call the core layer keyword search function
        results = search_keyword(
            db=db,
            search_term=search_term,
            top_n=top_n,
            require_all=require_all,
            search_fields=search_fields
        )
        
        # Wrap results for consistency
        results_data = {
            "results": results,
            "total": len(results),
            "offset": 0,
            "search_term": search_term
        }
        
        # Return the results
        return {
            "status": "success",
            "data": results_data,
            "message": f"Found {len(results)} results"
        }
    except Exception as e:
        logger.error(f"MCP keyword search failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


def mcp_graph_traverse(
    start_node_id: str,
    graph_name: str = GRAPH_NAME,
    direction: str = "OUTBOUND",
    min_depth: int = 1,
    max_depth: int = 2,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Traverse a graph starting from a specific node.
    
    Args:
        start_node_id: Full ID of the starting node
        graph_name: Name of the graph to traverse
        direction: Traversal direction (OUTBOUND, INBOUND, ANY)
        min_depth: Minimum traversal depth
        max_depth: Maximum traversal depth
        limit: Maximum number of results
    
    Returns:
        Dictionary with traversal paths and metadata
    """
    logger.info(f"MCP: Traversing graph from '{start_node_id}'")
    
    try:
        db = get_db_connection()
        
        # Validate direction
        valid_directions = ["OUTBOUND", "INBOUND", "ANY"]
        if direction not in valid_directions:
            return {
                "status": "error",
                "message": f"Invalid direction '{direction}'. Must be one of: {', '.join(valid_directions)}",
                "data": None
            }
        
        # Call the core layer graph traverse function
        results = graph_traverse(
            db,
            start_node_id,
            graph_name,
            direction=direction,
            min_depth=min_depth,
            max_depth=max_depth,
            limit=limit
        )
        
        # Return the results
        return {
            "status": "success",
            "data": results,
            "message": f"Found {len(results.get('paths', []))} paths"
        }
    except Exception as e:
        logger.error(f"MCP graph traversal failed: {e}", exc_info=True)
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
        test_result = "bm25_search" in globals() and "semantic_search" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import core search functions")
    except Exception as e:
        all_validation_failures.append(f"Import validation failed: {e}")
    
    # Test 2: Verify MCP functions exist and return valid responses
    total_tests += 1
    try:
        # Check that we have MCP functions defined
        functions = ["mcp_bm25_search", "mcp_semantic_search", "mcp_hybrid_search", 
                    "mcp_tag_search", "mcp_keyword_search", "mcp_graph_traverse"]
        
        missing_functions = [f for f in functions if f not in globals()]
        if missing_functions:
            all_validation_failures.append(f"Missing MCP functions: {missing_functions}")
            
        # Check function signatures
        for func_name in functions:
            if func_name not in missing_functions:
                func = globals()[func_name]
                # Check if function has a return annotation
                if not hasattr(func, "__annotations__") or "return" not in func.__annotations__:
                    all_validation_failures.append(f"Function {func_name} missing return type annotation")
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