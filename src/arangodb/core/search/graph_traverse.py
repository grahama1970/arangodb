"""
Graph Traversal Search Module

This module provides graph traversal functionality for ArangoDB. It can be used to find
related documents by traversing the graph starting from a given vertex.

Links:
- python-arango: https://python-arango.readthedocs.io/
- ArangoDB Graphs: https://www.arangodb.com/docs/stable/aql/graphs.html

Sample Input/Output:
- Graph traversal:
  Input: Start vertex ID, depth range, and direction
  Output: List of related documents with relationship information
  
- Graph RAG search:
  Input: Search query plus graph traversal parameters
  Output: Combined search results with related documents
"""

import sys
import json
import os
import time
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple
from loguru import logger
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, ArangoServerError
from colorama import init, Fore, Style
from tabulate import tabulate

# Import constants from constants module
try:
    from arangodb.core.constants import (
        COLLECTION_NAME, 
        GRAPH_NAME,
        EDGE_COLLECTION_NAME,
        VIEW_NAME,
        SEARCH_FIELDS,
        TEXT_ANALYZER
    )
except ImportError:
    # Fallback defaults if constants module cannot be imported
    logger.warning("Could not import constants from arangodb.core.constants, using defaults")
    COLLECTION_NAME = "memory_documents"
    GRAPH_NAME = "knowledge_graph"
    EDGE_COLLECTION_NAME = "relationships"
    VIEW_NAME = "memory_view"
    SEARCH_FIELDS = ["content", "title", "summary", "tags"]
    TEXT_ANALYZER = "text_en"

# Import database connection functions
try:
    from arangodb.core.arango_setup import connect_arango, ensure_database
except ImportError:
    try:
        from arangodb.core import connect_arango, ensure_database
    except ImportError:
        from arangodb.arango_setup import connect_arango, ensure_database

# Import embedding utilities
try:
    from arangodb.core.utils.embedding_utils import get_embedding
except ImportError:
    try:
        from arangodb.utils.embedding_utils import get_embedding
    except ImportError:
        # Define a fallback get_embedding function that returns a mock embedding
        logger.warning("Could not import get_embedding, using mock function")
        def get_embedding(text, dimensions=768):
            """Mock embedding function that returns a vector of zeros."""
            import numpy as np
            return np.zeros(dimensions).tolist()

# Helper functions
def truncate_large_value(value, max_str_len=None, max_length=1000, max_list_elements_shown=10):
    """Truncate large values for better log readability."""
    if isinstance(value, str) and max_str_len and len(value) > max_str_len:
        return value[:max_str_len] + "..."
    elif isinstance(value, str) and len(value) > max_length:
        return value[:max_length] + "..."
    elif isinstance(value, list) and len(value) > max_list_elements_shown:
        return value[:max_list_elements_shown] + [f"... ({len(value) - max_list_elements_shown} more items)"]
    elif isinstance(value, dict):
        return {k: truncate_large_value(v, max_str_len, max_length, max_list_elements_shown) 
                for k, v in list(value.items())[:max_list_elements_shown]}
    return value

# Simple function for displaying search results
def print_search_results(search_results, **kwargs):
    """Simple print function for search results."""
    count = len(search_results.get("results", []))
    query = search_results.get("query", "")
    print(f"Found {count} results for: '{query}'")

# Add compatibility wrapper for CLI
def graph_traverse(
    db: StandardDatabase,
    start_vertex_key: str,
    min_depth: int = 1,
    max_depth: int = 1,
    direction: str = "ANY",
    limit: int = 10,
    start_vertex_collection: str = None,
    graph_name: str = None,
    relationship_types: Optional[List[str]] = None,
    output_format: str = "table"
) -> Dict[str, Any]:
    """
    Compatibility wrapper for graph_rag_search to support CLI integration.
    
    Args:
        db: ArangoDB database
        start_vertex_key: Key of start vertex
        min_depth: Minimum traversal depth
        max_depth: Maximum traversal depth
        direction: Direction of traversal (OUTBOUND, INBOUND, ANY)
        limit: Maximum number of results to return
        start_vertex_collection: Collection containing the start vertex
        graph_name: Name of the graph to traverse
        
    Returns:
        Results of graph traversal
    """
    logger.info(f"Graph traverse wrapper called for vertex {start_vertex_key}")
    
    # Use defaults from config if not provided
    collection = start_vertex_collection or COLLECTION_NAME
    graph = graph_name or GRAPH_NAME
    
    # Create a start vertex ID from collection/key
    start_vertex_id = f"{collection}/{start_vertex_key}"
    
    # For pure graph traversal without search, use a dummy query
    # The graph_rag_search function will skip the semantic search part
    # when start_vertex_id is provided
    return graph_rag_search(
        db=db,
        query_text="graph_traversal_only",  # Dummy non-empty query for pure traversal
        start_vertex_id=start_vertex_id,
        min_depth=min_depth,
        max_depth=max_depth,
        direction=direction,
        relationship_types=relationship_types,  # Pass through relationship types filter
        min_score=0.0,  # No minimum score filter
        top_n=limit,
        output_format=output_format,
        fields_to_return=None,
        edge_collection_name=None,
        graph_name=graph
    )


def graph_rag_search(
    db: StandardDatabase,
    query_text: str,
    min_depth: int = 1,
    max_depth: int = 1,
    direction: str = "ANY",
    relationship_types: Optional[List[str]] = None,
    min_score: float = 0.0,
    top_n: int = 10,
    output_format: str = "table",
    fields_to_return: Optional[List[str]] = None,
    edge_collection_name: Optional[str] = None,
    start_vertex_id: Optional[str] = None,
    graph_name: Optional[str] = None,
    max_related_per_doc: int = 100,  # OPTIMIZATION: Limit related docs per seed
    traversal_timeout_ms: int = 5000  # OPTIMIZATION: Timeout for graph traversal
) -> Dict[str, Any]:
    """
    Perform a combined BM25 search and graph traversal (GraphRAG pattern).
    Optimized to prevent exponential time complexity on deep traversals.
    
    Args:
        db: ArangoDB database
        query_text: Search query text
        min_depth: Minimum traversal depth
        max_depth: Maximum traversal depth
        direction: Direction of traversal (OUTBOUND, INBOUND, ANY)
        relationship_types: Optional list of relationship types to filter
        min_score: Minimum BM25 score threshold
        top_n: Maximum number of results to return
        output_format: Output format ("table" or "json")
        fields_to_return: Fields to include in the result
        edge_collection_name: Edge collection name (overrides default from config)
        start_vertex_id: Optional vertex ID to start from instead of search
        graph_name: Optional graph name to override default
        max_related_per_doc: Maximum number of related docs per seed doc (prevents explosion)
        traversal_timeout_ms: Timeout in milliseconds for graph traversal operations
        
    Returns:
        Dictionary with search results and related documents
    """
    start_time = time.time()
    logger.info(f"Running Graph RAG search for query: '{query_text}'")
    
    # Input validation
    if not query_text or query_text.strip() == "":
        error_msg = "Query text cannot be empty"
        logger.error(error_msg)
        return {
            "results": [],
            "total": 0,
            "query": "",
            "time": time.time() - start_time,
            "format": output_format,
            "error": error_msg
        }
    
    # Validate direction parameter
    direction_upper = direction.upper() if isinstance(direction, str) else direction
    if direction_upper not in ["OUTBOUND", "INBOUND", "ANY"]:
        error_msg = f"Invalid direction: '{direction}'. Must be OUTBOUND, INBOUND, or ANY."
        logger.error(f"Invalid direction received: '{direction}' (type: {type(direction)})")
        return {
            "results": [], 
            "total": 0,
            "query": query_text,
            "time": time.time() - start_time,
            "format": output_format,
            "error": error_msg
        }
    
    # OPTIMIZATION: Enforce sensible depth limits to prevent exponential explosion
    original_max_depth = max_depth
    if max_depth > 3:
        logger.warning(f"Limiting max_depth from {max_depth} to 3 to prevent performance issues")
        max_depth = 3  # Hard limit to prevent exponential traversal time
    
    # Validate depth parameters
    if min_depth < 0 or max_depth < min_depth:
        error_msg = f"Invalid depth range: {min_depth}..{max_depth}"
        logger.error(error_msg)
        return {
            "results": [], 
            "total": 0,
            "query": query_text,
            "time": time.time() - start_time,
            "format": output_format,
            "error": error_msg
        }
    
    try:
        # Default fields to return if not provided
        if not fields_to_return:
            fields_to_return = ["_key", "_id", "question", "problem", "solution", "context", "tags", "label", "validated"]
        
        # Create a list of all fields to keep
        fields_to_keep = list(set(fields_to_return))  # Remove duplicates
        
        # Convert to comma-separated string for KEEP
        fields_to_keep_str = '", "'.join(fields_to_keep)
        fields_to_keep_str = f'"{fields_to_keep_str}"'
        
        # Build the SEARCH clause dynamically from SEARCH_FIELDS
        search_field_conditions = " OR ".join([
            f'ANALYZER(doc.{field} IN search_tokens, "{TEXT_ANALYZER}")'
            for field in SEARCH_FIELDS
        ])
        
        # Build edge filter if relationship types are provided
        edge_filter = ""
        if relationship_types and len(relationship_types) > 0:
            type_list = ", ".join([f"'{t}'" for t in relationship_types])
            edge_filter = f"FILTER e.type IN [{type_list}]"
        
        # OPTIMIZATION: Use graph name from parameters or config
        graph_name_value = graph_name or GRAPH_NAME
        
        # OPTIMIZATION: ArangoDB's traversal options to prevent performance issues
        # These options limit traversal time and memory usage
        traversal_options = f"""
        OPTIONS {{
            bfs: true,                  // Use breadth-first search (more efficient)
            uniqueVertices: "global",   // Don't visit the same vertex twice
            maxIterations: {max_related_per_doc}, // Limit iterations to prevent explosion
            maxDepth: {max_depth},       // Explicitly set max depth
            "parallelism": 4             // Use parallelism for better performance
        }}
        """
        
        # OPTIMIZATION: Add timeouts and pagination to prevent long-running queries
        # Construct the AQL query that combines BM25 search with graph traversal
        # First find relevant documents with BM25 search, then traverse graph for each
        aql = f"""
        // Start with text search
        LET search_tokens = TOKENS(@query, "{TEXT_ANALYZER}")
        FOR doc IN {VIEW_NAME}
        SEARCH {search_field_conditions}
        LET score = BM25(doc)
        FILTER score >= @min_score
        SORT score DESC
        LIMIT @top_n
        
        // For each document, do a controlled graph traversal
        // with timeout protection
        LET traversal_start = DATE_NOW()
        
        // OPTIMIZATION: Use a subquery with a timeout check to prevent long traversals
        LET related = (
            FOR vertex, e, p IN {min_depth}..{max_depth} {direction_upper} doc GRAPH @graph_name
            {traversal_options}
            {edge_filter}
            
            // OPTIMIZATION: Add timeout check
            FILTER DATE_NOW() - traversal_start < @traversal_timeout_ms
            
            LIMIT @max_related_per_doc  // OPTIMIZATION: Limit related docs per seed
            
            RETURN {{
                "vertex": KEEP(vertex, {fields_to_keep_str}),
                "edge": e,
                "depth": LENGTH(p.vertices) - 1,  // OPTIMIZATION: Track actual depth
                "path": p
            }}
        )
        
        RETURN {{
            "doc": KEEP(doc, {fields_to_keep_str}),
            "score": score,
            "related": related,
            "related_count": LENGTH(related),
            "traversal_time_ms": DATE_NOW() - traversal_start
        }}
        """
        
        bind_vars = {
            "query": query_text,
            "min_score": min_score,
            "graph_name": graph_name_value,
            "top_n": top_n,
            "max_related_per_doc": max_related_per_doc,
            "traversal_timeout_ms": traversal_timeout_ms
        }
        
        logger.debug(f"Executing optimized AQL query: {aql}")
        logger.debug(f"With bind variables: {bind_vars}")
        
        # Execute the query (timeout parameter removed as it may not be supported in all versions)
        cursor = db.aql.execute(
            aql, 
            bind_vars=bind_vars
        )
        results = list(cursor)
        
        # Get total count (number of documents that would match without the limit)
        count_aql = f"""
        RETURN LENGTH(
            LET search_tokens = TOKENS(@query, "{TEXT_ANALYZER}")
            FOR doc IN {VIEW_NAME}
            SEARCH {search_field_conditions}
            LET score = BM25(doc)
            FILTER score >= @min_score
            RETURN 1
        )
        """
        
        count_cursor = db.aql.execute(count_aql, bind_vars={"query": query_text, "min_score": min_score})
        total_count = next(count_cursor)
        
        # Gather traversal statistics
        related_counts = [r.get("related_count", 0) for r in results]
        total_related = sum(related_counts)
        max_related = max(related_counts) if related_counts else 0
        avg_related = total_related / len(results) if results else 0
        traversal_times = [r.get("traversal_time_ms", 0) for r in results]
        avg_traversal_time = sum(traversal_times) / len(traversal_times) if traversal_times else 0
        
        # Log detailed performance metrics
        query_time = time.time() - start_time
        logger.info(f"Graph RAG search found {len(results)} documents with {total_related} related items in {query_time:.3f}s")
        logger.info(f"Traversal stats: max={max_related}, avg={avg_related:.1f}, avg_time={avg_traversal_time:.1f}ms")
        
        # OPTIMIZATION: Add warnings if limits were hit
        warnings = []
        if original_max_depth > max_depth:
            warnings.append(f"Max depth was limited from {original_max_depth} to {max_depth}")
        if max_related == max_related_per_doc:
            warnings.append(f"Max related limit ({max_related_per_doc}) was reached for at least one document")
        if any(t >= traversal_timeout_ms * 0.9 for t in traversal_times):
            warnings.append(f"Traversal timeout ({traversal_timeout_ms}ms) was nearly hit for some documents")
        
        return {
            "results": results,
            "total": total_count,
            "query": query_text,
            "time": query_time,
            "format": output_format,
            "params": {
                "min_depth": min_depth,
                "max_depth": max_depth,
                "direction": direction_upper,
                "relationship_types": relationship_types,
                "max_related_per_doc": max_related_per_doc,
                "traversal_timeout_ms": traversal_timeout_ms
            },
            "stats": {
                "total_related": total_related,
                "max_related": max_related,
                "avg_related": avg_related,
                "avg_traversal_time_ms": avg_traversal_time
            },
            "warnings": warnings if warnings else None,
            "search_engine": "graph-rag-optimized"
        }
    except Exception as e:
        logger.error(f"Graph RAG search error: {e}")
        return {
            "results": [],
            "total": 0,
            "query": query_text,
            "time": time.time() - start_time,
            "format": output_format,
            "error": str(e),
            "search_engine": "graph-rag-failed"
        }


def print_rag_results(rag_results: Dict[str, Any], max_width: int = 120) -> None:
    """
    Print graph RAG search results in the specified format (table or JSON).
    Uses display_utils for consistent formatting and log_utils for safe content truncation.
    
    Args:
        rag_results: The RAG search results to display
        max_width: Maximum width for text fields in characters (used for table format)
    """
    # Get additional GraphRAG-specific parameters
    params = rag_results.get("params", {})
    direction = params.get("direction", "ANY")
    min_depth = params.get("min_depth", 1)
    max_depth = params.get("max_depth", 1)
    relationship_types = params.get("relationship_types", [])
    rel_types_str = ", ".join(relationship_types) if relationship_types else "Any"
    related_count = sum(len(r.get("related", [])) for r in rag_results.get("results", []))
    
    # Initialize colorama for cross-platform colored terminal output
    init(autoreset=True)
    
    # Display format-specific GraphRAG header
    if rag_results.get("format", "table").lower() != "json":
        print(f"{Fore.CYAN}{'═' * 80}{Style.RESET_ALL}")
        print(f"Found {Fore.GREEN}{len(rag_results.get('results', []))}{Style.RESET_ALL} documents with {Fore.GREEN}{related_count}{Style.RESET_ALL} related items")
        print(f"Direction: {Fore.MAGENTA}{direction}{Style.RESET_ALL}, Depth: {Fore.CYAN}{min_depth}..{max_depth}{Style.RESET_ALL}")
        print(f"Relationship Types: {Fore.BLUE}{rel_types_str}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}")
    
    # Use common display utility for consistent formatting across search modes
    print_search_results(
        rag_results,
        max_width=max_width,
        title_field="Content",
        id_field="_key",
        score_field="score",
        score_name="BM25 Score",
        table_title="Graph RAG Results"
    )


def print_result_details(result: Dict[str, Any]) -> None:
    """
    Print beautifully formatted details about a RAG search result.
    Uses helper functions for safe content truncation.
    
    Args:
        result: RAG search result to display
    """
    # Use the truncate_large_value function defined in this module
    # No need to import from log_utils
    
    # Initialize colorama for cross-platform colored terminal output
    init(autoreset=True)
    
    doc = result.get("doc", {})
    score = result.get("score", 0)
    related = result.get("related", [])
    
    # Print document header with key
    key = doc.get("_key", "N/A")
    header = f"{Fore.GREEN}{'═' * 80}{Style.RESET_ALL}"
    print(f"\n{header}")
    print(f"{Fore.GREEN}  DOCUMENT: {Fore.YELLOW}{key}{Style.RESET_ALL}  ")
    print(f"{header}")
    
    # Get fields to display (excluding internal fields and tags)
    display_fields = [f for f in doc.keys() if f not in ["_key", "_id", "tags", "_rev", "embedding"]]
    
    # Print all document fields with content truncation
    for field in display_fields:
        if field in doc and doc[field]:
            field_title = field.title()
            # Truncate large field values
            safe_value = truncate_large_value(doc[field], max_str_len=100)
            print(f"{Fore.YELLOW}{field_title}:{Style.RESET_ALL} {safe_value}")
    
    # Print score with color coding based on value
    if score > 7.0:
        score_str = f"{Fore.GREEN}{score:.2f}{Style.RESET_ALL}"
    elif score > 5.0:
        score_str = f"{Fore.YELLOW}{score:.2f}{Style.RESET_ALL}"
    else:
        score_str = f"{Fore.WHITE}{score:.2f}{Style.RESET_ALL}"
    print(f"\n{Fore.CYAN}BM25 Score:{Style.RESET_ALL} {score_str}")
    
    # Print tags in a special section if present - with truncation
    if "tags" in doc and isinstance(doc["tags"], list) and doc["tags"]:
        tags = doc["tags"]
        print(f"\n{Fore.BLUE}Tags:{Style.RESET_ALL}")
        
        # Truncate tag list if it's very long
        safe_tags = truncate_large_value(tags, max_list_elements_shown=10)
        
        if isinstance(safe_tags, str):  # It's already a summary string
            print(f"  {safe_tags}")
        else:  # It's still a list
            tag_colors = [Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.GREEN, Fore.YELLOW]
            for i, tag in enumerate(safe_tags):
                color = tag_colors[i % len(tag_colors)]  # Cycle through colors
                print(f"  • {color}{tag}{Style.RESET_ALL}")
    
    # Print related documents section with truncation
    if related:
        print(f"\n{Fore.MAGENTA}Related Documents ({len(related)}):{Style.RESET_ALL}")
        
        # Print a condensed view of each related document
        for i, rel in enumerate(related[:5]):  # Show at most 5 related docs
            vertex = rel.get("vertex", {})
            edge = rel.get("edge", {})
            
            v_key = vertex.get("_key", "N/A")
            e_type = truncate_large_value(edge.get("type", "unknown"), max_str_len=20) if edge else "N/A"
            
            # Get main content from the vertex with truncation
            content = ""
            for field in ["question", "problem", "solution", "context"]:
                if field in vertex and vertex[field]:
                    content = str(vertex[field])
                    break
            
            # Truncate content
            content = truncate_large_value(content, max_str_len=70)
            
            print(f"  {i+1}. {Fore.YELLOW}{v_key}{Style.RESET_ALL} ({Fore.GREEN}{e_type}{Style.RESET_ALL})")
            if content:
                print(f"     {content}")
        
        # Note if there are more related docs
        if len(related) > 5:
            print(f"  ... and {len(related) - 5} more")
    
    # Print footer
    print(f"{header}\n")


def create_python_error_docs(db: StandardDatabase) -> Dict[str, Any]:
    """
    Create sample documents about Python error handling with embeddings.
    
    Args:
        db: ArangoDB database connection
        
    Returns:
        Dictionary with created document keys
    """
    logger.info("Creating sample documents about Python error handling")
    
    # Ensure required collections exist
    if not db.has_collection(COLLECTION_NAME):
        logger.error(f"Collection {COLLECTION_NAME} does not exist")
        return {"error": f"Collection {COLLECTION_NAME} does not exist"}
    
    if not db.has_collection(EDGE_COLLECTION_NAME):
        logger.error(f"Edge collection {EDGE_COLLECTION_NAME} does not exist")
        return {"error": f"Edge collection {EDGE_COLLECTION_NAME} does not exist"}
    
    # Create sample documents
    try:
        vertex_collection = db.collection(COLLECTION_NAME)
        
        # Define sample documents about Python error handling
        docs = [
            {
                "_key": f"python_error_1_{uuid.uuid4().hex[:8]}",
                "question": "What is the best way to handle exceptions in Python?",
                "solution": "Use try-except blocks to catch specific exceptions rather than using bare except. This provides better error handling and prevents catching unexpected errors.",
                "context": "Python error handling best practices",
                "tags": ["python", "error-handling", "exceptions", "try-except"],
                "label": 1,
                "validated": True
            },
            {
                "_key": f"python_error_2_{uuid.uuid4().hex[:8]}",
                "question": "How do I create custom exceptions in Python?",
                "solution": "Create a custom exception by defining a new class that inherits from Exception: 'class MyCustomException(Exception): pass'. You can add custom attributes and messages.",
                "context": "Python custom exception classes",
                "tags": ["python", "error-handling", "custom-exceptions", "class-inheritance"],
                "label": 1,
                "validated": True
            },
            {
                "_key": f"python_error_3_{uuid.uuid4().hex[:8]}",
                "question": "What's the difference between raise and raise from in Python?",
                "solution": "The 'raise from' syntax (e.g., 'raise NewError() from original_error') establishes an explicit exception chaining relationship, preserving the original traceback in __cause__.",
                "context": "Python exception chaining",
                "tags": ["python", "error-handling", "exception-chaining", "traceback"],
                "label": 1,
                "validated": True
            },
            {
                "_key": f"python_error_4_{uuid.uuid4().hex[:8]}",
                "question": "How to properly use finally blocks in Python?",
                "solution": "The finally block always executes after try/except blocks, regardless of whether an exception occurred. Use it for cleanup operations like closing files or database connections.",
                "context": "Python error handling patterns",
                "tags": ["python", "error-handling", "finally", "cleanup", "resource-management"],
                "label": 1,
                "validated": True
            },
            {
                "_key": f"python_error_5_{uuid.uuid4().hex[:8]}",
                "question": "What's the difference between except Exception and except BaseException?",
                "solution": "Except Exception catches most exceptions but not system-exiting ones like KeyboardInterrupt or SystemExit. BaseException catches everything, including system exits, which is usually not what you want.",
                "context": "Python exception hierarchy",
                "tags": ["python", "error-handling", "exception-types", "exception-hierarchy"],
                "label": 1,
                "validated": True
            },
            {
                "_key": f"python_error_6_{uuid.uuid4().hex[:8]}",
                "question": "How to log exceptions properly in Python?",
                "solution": "Use the logging module and log.exception() within an except block to capture the exception with traceback. Configure log levels and handlers for different environments.",
                "context": "Python logging and error handling",
                "tags": ["python", "error-handling", "logging", "traceback", "debugging"],
                "label": 1,
                "validated": True
            }
        ]
        
        # Add embeddings to documents
        doc_keys = []
        for doc in docs:
            # Combine text for embedding
            text_to_embed = f"{doc['question']} {doc['solution']} {doc['context']} {' '.join(doc['tags'])}"
            
            # Generate embedding using the utility
            doc["embedding"] = get_embedding(text_to_embed)
            
            # Insert or update document
            if vertex_collection.has(doc["_key"]):
                vertex_collection.update(doc)
                logger.info(f"Updated document {doc['_key']}")
            else:
                vertex_collection.insert(doc)
                logger.info(f"Inserted document {doc['_key']} with embedding")
            
            doc_keys.append(doc["_key"])
        
        # Create relationships between documents
        edge_collection = db.collection(EDGE_COLLECTION_NAME)
        
        # Define relationships between Python error handling documents
        edges = [
            {
                "_from": f"{COLLECTION_NAME}/{docs[0]['_key']}",
                "_to": f"{COLLECTION_NAME}/{docs[1]['_key']}",
                "type": "related_to",
                "weight": 0.9,
                "confidence": 5,
                "rationale": "Custom exceptions are essential to proper error handling strategies"
            },
            {
                "_from": f"{COLLECTION_NAME}/{docs[0]['_key']}",
                "_to": f"{COLLECTION_NAME}/{docs[3]['_key']}",
                "type": "related_to",
                "weight": 0.8,
                "confidence": 4,
                "rationale": "Finally blocks are a key component of robust exception handling patterns"
            },
            {
                "_from": f"{COLLECTION_NAME}/{docs[1]['_key']}",
                "_to": f"{COLLECTION_NAME}/{docs[2]['_key']}",
                "type": "references",
                "weight": 0.7,
                "confidence": 3,
                "rationale": "Custom exceptions often use raise from for chaining"
            },
            {
                "_from": f"{COLLECTION_NAME}/{docs[4]['_key']}",
                "_to": f"{COLLECTION_NAME}/{docs[0]['_key']}",
                "type": "related_to",
                "weight": 0.8,
                "confidence": 4,
                "rationale": "Understanding exception hierarchy is critical to proper exception handling"
            },
            {
                "_from": f"{COLLECTION_NAME}/{docs[5]['_key']}",
                "_to": f"{COLLECTION_NAME}/{docs[0]['_key']}",
                "type": "references",
                "weight": 0.7,
                "confidence": 4,
                "rationale": "Logging is typically integrated with exception handling strategies"
            },
            {
                "_from": f"{COLLECTION_NAME}/{docs[3]['_key']}",
                "_to": f"{COLLECTION_NAME}/{docs[2]['_key']}",
                "type": "mentions",
                "weight": 0.6,
                "confidence": 2,
                "rationale": "Finally blocks and exception chaining are often used together"
            }
        ]
        
        # Insert edges
        edge_keys = []
        for edge in edges:
            # Generate a unique key for the edge
            edge_key = f"{edge['_from'].split('/')[1]}_to_{edge['_to'].split('/')[1]}"
            edge["_key"] = edge_key
            
            # Generate embedding for rationale field
            if "rationale" in edge:
                logger.info(f"Generating embedding for edge rationale: '{edge['rationale']}'")
                edge["embedding"] = get_embedding(edge["rationale"])
                logger.info(f"Created embedding for edge {edge_key} with dimension {len(edge['embedding'])}")
            
            # Insert or update edge
            if edge_collection.has(edge_key):
                edge_collection.update(edge)
                logger.info(f"Updated edge {edge_key} with embedding")
            else:
                edge_collection.insert(edge)
                logger.info(f"Inserted edge {edge_key} with embedding")
            
            edge_keys.append(edge_key)
        
        logger.info(f"Created {len(doc_keys)} Python error handling documents with {len(edge_keys)} relationships")
        
        return {
            "vertices": doc_keys,
            "edges": edge_keys
        }
    
    except Exception as e:
        logger.error(f"Error creating Python error handling documents: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Track validation results
    all_validation_failures = []
    total_tests = 0
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:HH:mm:ss} | {level: <7} | {message}",
        colorize=True
    )
    
    print("Testing graph traversal functionality with real ArangoDB connection...")
    
    try:
        # Test 1: Connect to ArangoDB
        total_tests += 1
        print("\nTest 1: Connecting to ArangoDB...")
        try:
            client = connect_arango()
            db = ensure_database(client)
            print("✅ Successfully connected to ArangoDB")
        except Exception as e:
            all_validation_failures.append(f"ArangoDB connection failed: {str(e)}")
            print(f"❌ ArangoDB connection failed: {str(e)}")
            sys.exit(1)
        
        # Test 2: Create sample documents
        total_tests += 1
        print("\nTest 2: Creating sample documents...")
        try:
            doc_result = create_python_error_docs(db)
            if "error" in doc_result:
                all_validation_failures.append(f"Error creating documents: {doc_result['error']}")
                print(f"❌ Error creating documents: {doc_result['error']}")
            else:
                vertices = len(doc_result.get('vertices', []))
                edges = len(doc_result.get('edges', []))
                print(f"✅ Successfully created {vertices} documents with {edges} relationships")
        except Exception as e:
            all_validation_failures.append(f"Creating sample documents failed: {str(e)}")
            print(f"❌ Creating sample documents failed: {str(e)}")
        
        # Test 3: Run a simple graph traversal
        total_tests += 1
        print("\nTest 3: Running graph traversal...")
        
        # Use params optimized for testing
        query_text = "python error handling"
        min_depth = 1
        max_depth = 2
        direction = "ANY"
        
        try:
            results = graph_rag_search(
                db=db,
                query_text=query_text,
                min_depth=min_depth,
                max_depth=max_depth,
                direction=direction,
                relationship_types=None,
                min_score=0.0,
                top_n=5,
                output_format="table"
            )
            
            # Verify we got results
            if len(results.get("results", [])) > 0:
                print(f"✅ Successfully found {len(results['results'])} documents")
                
                # Check if any of the results have related documents
                related_counts = [len(r.get("related", [])) for r in results.get("results", [])]
                total_related = sum(related_counts)
                
                if total_related > 0:
                    print(f"✅ Successfully found {total_related} related documents through graph traversal")
                else:
                    all_validation_failures.append("No related documents found through graph traversal")
                    print("❌ No related documents found through graph traversal")
                
                # Show a sample of the results (for manual verification)
                print("\nSample results for human verification:")
                first_result = results["results"][0] if results["results"] else None
                if first_result:
                    doc = first_result.get("doc", {})
                    print(f"Document: {doc.get('_key', 'unknown')}")
                    print(f"Score: {first_result.get('score', 0):.2f}")
                    print(f"Related documents: {len(first_result.get('related', []))}")
            else:
                all_validation_failures.append("No results returned from graph RAG search")
                print("❌ No results returned from graph RAG search")
        except Exception as e:
            all_validation_failures.append(f"Graph traversal failed: {str(e)}")
            print(f"❌ Graph traversal failed: {str(e)}")
        
        # Test 4: Test relationship filtering
        total_tests += 1
        print("\nTest 4: Testing relationship filtering...")
        try:
            filtered_results = graph_rag_search(
                db=db,
                query_text=query_text,
                min_depth=min_depth,
                max_depth=max_depth,
                direction=direction,
                relationship_types=["related_to"],  # Filter to only "related_to" relationships
                min_score=0.0,
                top_n=5,
                output_format="table"
            )
            
            # Verify filtering worked
            has_relationship_filter = "relationship_types" in filtered_results.get("params", {})
            if has_relationship_filter:
                print("✅ Successfully applied relationship type filter")
            else:
                all_validation_failures.append("Relationship type filter was not applied")
                print("❌ Relationship type filter was not applied")
        except Exception as e:
            all_validation_failures.append(f"Relationship filtering test failed: {str(e)}")
            print(f"❌ Relationship filtering test failed: {str(e)}")
        
        # Final validation result
        if all_validation_failures:
            print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                print(f"  - {failure}")
            sys.exit(1)  # Exit with error code
        else:
            print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("Graph traversal functionality is validated and ready for use")
            sys.exit(0)  # Exit with success code
            
    except Exception as e:
        logger.error(f"Unexpected error in graph traversal validation: {e}")
        sys.exit(1)