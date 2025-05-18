"""
Fixed Search Commands with Consistent Interface

This module provides standardized search commands following the stellar CLI template.
All commands use consistent parameter patterns for LLM-friendly usage.
"""

import typer
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from arangodb.cli.db_connection import get_db_connection
from arangodb.core.utils.cli.formatters import (
    console,
    format_output,
    add_output_option,
    OutputFormat,
    format_error,
    format_success,
    CLIResponse,
    format_search_results
)

# Initialize search app
search_app = typer.Typer(help="Search operations with consistent interface")

# Add consistent output format handling
def standard_output_handler(results: List[Dict], metadata: Dict, output_format: OutputFormat):
    """Standard output handler for all search commands"""
    response = {
        "success": True,
        "data": {"results": results},  # Wrap results in a dict
        "metadata": metadata,
        "errors": []
    }
    
    if output_format == OutputFormat.JSON:
        console.print_json(data=response)
    else:
        # Table format
        if results:
            from rich.table import Table
            table = Table(title=f"{metadata.get('type', 'Search')} Results")
            
            # Add columns based on first result
            for key in results[0].keys():
                if not key.startswith('_'):
                    table.add_column(key.replace('_', ' ').title())
            
            # Add rows
            for result in results:
                row = []
                for key in results[0].keys():
                    if not key.startswith('_'):
                        value = str(result.get(key, ''))
                        row.append(value[:50] + "..." if len(value) > 50 else value)
                table.add_row(*row)
            
            table.caption = f"Found {len(results)} results"
            console.print(table)
        else:
            console.print("[yellow]No results found[/yellow]")

@search_app.command("bm25")
def search_bm25(
    query: str = typer.Option(..., "--query", "-q", help="Search query text"),
    collection: str = typer.Option("documents", "--collection", "-c", help="Collection to search"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    offset: int = typer.Option(0, "--offset", help="Skip this many results"),
    threshold: float = typer.Option(0.0, "--threshold", "-t", help="Minimum BM25 score"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Filter by tags (comma-separated)"),
):
    """
    Find documents using BM25 keyword search algorithm.
    
    USAGE:
        arangodb search bm25 --query "database optimization" [OPTIONS]
    
    WHEN TO USE:
        When you need traditional keyword matching with relevance scoring
    
    OUTPUT:
        - TABLE: Formatted results with BM25 scores
        - JSON: Complete results with metadata
    
    EXAMPLES:
        arangodb search bm25 --query "python tutorial" --collection articles
        arangodb search bm25 --query "ArangoDB" --output json --limit 20
    """
    logger.info(f"BM25 search: query='{query}', collection={collection}")
    
    try:
        db = get_db_connection()
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        
        # Import actual search function
        from arangodb.core.search.bm25_search import bm25_search
        
        start_time = datetime.now()
        results = bm25_search(
            db=db,
            query_text=query,
            collections=[collection],  # Function expects list of collections
            top_n=limit,
            offset=offset,
            tag_list=tag_list,
            min_score=threshold,
            output_format="json"  # We need raw data for our formatter
        )
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        metadata = {
            "type": "BM25",
            "query": query,
            "collection": collection,
            "count": len(results),
            "limit": limit,
            "offset": offset,
            "threshold": threshold,
            "timing": {"search_ms": round(search_time, 2)}
        }
        
        standard_output_handler(results, metadata, output_format)
        
    except Exception as e:
        logger.error(f"BM25 search failed: {e}")
        error_response = {
            "success": False,
            "data": None,
            "metadata": {},
            "errors": [{
                "code": "SEARCH_ERROR",
                "message": str(e),
                "suggestion": "Check collection exists and query syntax"
            }]
        }
        if output_format == OutputFormat.JSON:
            console.print_json(data=error_response)
        else:
            console.print(format_error("BM25 Search Failed", str(e)))
        raise typer.Exit(1)

@search_app.command("semantic")

def search_semantic(
    query: str = typer.Option(..., "--query", "-q", help="Search query text (will be embedded)"),
    collection: str = typer.Option("documents", "--collection", "-c", help="Collection to search"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    threshold: float = typer.Option(0.75, "--threshold", "-t", help="Minimum similarity score (0-1)"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Filter by tags (comma-separated)"),
):
    """
    Find documents based on semantic similarity using embeddings.
    
    USAGE:
        arangodb search semantic --query "machine learning concepts" [OPTIONS]
    
    WHEN TO USE:
        When searching for conceptually similar content regardless of exact keywords
    
    OUTPUT:
        - TABLE: Results with similarity scores
        - JSON: Complete results with embeddings metadata
    
    EXAMPLES:
        arangodb search semantic --query "AI applications" --threshold 0.8
        arangodb search semantic --query "database theory" --collection research --output json
    """
    logger.info(f"Semantic search: query='{query}', collection={collection}")
    
    try:
        db = get_db_connection()
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        
        # Import actual search function
        from arangodb.core.search.semantic_search import semantic_search
        
        start_time = datetime.now()
        results = semantic_search(
            db=db,
            query=query,
            collections=[collection],
            min_score=threshold,
            top_n=limit,
            tag_list=tag_list,
            output_format="json",
            validate_before_search=False,  # Skip validation for testing
            auto_fix_embeddings=False
        )
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Extract the actual results from the response
        actual_results = results.get("results", [])
        
        metadata = {
            "type": "Semantic",
            "query": query,
            "collection": collection,
            "count": len(actual_results),
            "limit": limit,
            "threshold": threshold,
            "timing": {"search_ms": round(search_time, 2)}
        }
        
        standard_output_handler(actual_results, metadata, output_format)
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        error_response = {
            "success": False,
            "data": None,
            "metadata": {},
            "errors": [{
                "code": "SEARCH_ERROR", 
                "message": str(e),
                "suggestion": "Ensure collection has embeddings and query is valid"
            }]
        }
        if output_format == OutputFormat.JSON:
            console.print_json(data=error_response)
        else:
            console.print(format_error("Semantic Search Failed", str(e)))
        raise typer.Exit(1)

@search_app.command("keyword")

def search_keyword(
    query: str = typer.Option(..., "--query", "-q", help="Keywords to search (space-separated)"),
    collection: str = typer.Option("documents", "--collection", "-c", help="Collection to search"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    field: str = typer.Option("content", "--field", "-f", help="Field to search in"),
):
    """
    Find documents containing specific keywords in a field.
    
    USAGE:
        arangodb search keyword --query "python database" --field content [OPTIONS]
    
    WHEN TO USE:
        When you need exact keyword matching in specific document fields
    
    OUTPUT:
        - TABLE: Documents containing the keywords
        - JSON: Complete matching documents
    
    EXAMPLES:
        arangodb search keyword --query "ArangoDB graph" --field title
        arangodb search keyword --query "optimization" --collection blog --output json
    """
    logger.info(f"Keyword search: query='{query}', field={field}")
    
    try:
        db = get_db_connection()
        keywords = query.split()
        
        # Import actual search function
        from arangodb.core.search.keyword_search import keyword_search
        
        start_time = datetime.now()
        results = keyword_search(
            db=db,
            search_term=query,  # Function expects single search term, not array
            collection_name=collection,
            fields_to_search=[field],  # Function expects list of fields
            view_name="memory_view",  # Add required view name
            top_n=limit,
            output_format="json"  # We need raw data for our formatter
        )
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        metadata = {
            "type": "Keyword",
            "query": query,
            "keywords": keywords,
            "collection": collection,
            "field": field,
            "count": len(results),
            "limit": limit,
            "timing": {"search_ms": round(search_time, 2)}
        }
        
        standard_output_handler(results, metadata, output_format)
        
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        error_response = {
            "success": False,
            "data": None,
            "metadata": {},
            "errors": [{
                "code": "SEARCH_ERROR",
                "message": str(e),
                "suggestion": f"Check that field '{field}' exists in collection"
            }]
        }
        if output_format == OutputFormat.JSON:
            console.print_json(data=error_response)
        else:
            console.print(format_error("Keyword Search Failed", str(e)))
        raise typer.Exit(1)

@search_app.command("tag")

def search_tag(
    tags: str = typer.Option(..., "--tags", "-t", help="Tags to search for (comma-separated)"),
    collection: str = typer.Option("documents", "--collection", "-c", help="Collection to search"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    match_all: bool = typer.Option(False, "--match-all", help="Require all tags to match"),
):
    """
    Find documents by tags.
    
    USAGE:
        arangodb search tag --tags "python,tutorial" [OPTIONS]
    
    WHEN TO USE:
        When filtering documents by predefined tags
    
    OUTPUT:
        - TABLE: Documents with matching tags
        - JSON: Complete document data
    
    EXAMPLES:
        arangodb search tag --tags "beginner,python" --match-all
        arangodb search tag --tags "advanced" --collection tutorials --output json
    """
    logger.info(f"Tag search: tags='{tags}', match_all={match_all}")
    
    try:
        db = get_db_connection()
        tag_list = [tag.strip() for tag in tags.split(",")]
        
        # Import actual search function
        from arangodb.core.search.tag_search import tag_search
        
        start_time = datetime.now()
        results = tag_search(
            db=db,
            tags=tag_list,
            collections=[collection],  # Function expects list of collections
            require_all_tags=match_all,  # Correct parameter name
            limit=limit,
            output_format="json"  # We need raw data for our formatter
        )
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        metadata = {
            "type": "Tag",
            "tags": tag_list,
            "collection": collection,
            "match_all": match_all,
            "count": len(results),
            "limit": limit,
            "timing": {"search_ms": round(search_time, 2)}
        }
        
        standard_output_handler(results, metadata, output_format)
        
    except Exception as e:
        logger.error(f"Tag search failed: {e}")
        error_response = {
            "success": False,
            "data": None,
            "metadata": {},
            "errors": [{
                "code": "SEARCH_ERROR",
                "message": str(e),
                "suggestion": "Ensure documents have 'tags' field"
            }]
        }
        if output_format == OutputFormat.JSON:
            console.print_json(data=error_response)
        else:
            console.print(format_error("Tag Search Failed", str(e)))
        raise typer.Exit(1)

@search_app.command("graph")

def search_graph(
    start_id: str = typer.Option(..., "--start-id", "-s", help="Starting node ID for traversal"),
    collection: str = typer.Option("documents", "--collection", "-c", help="Collection to traverse"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    max_depth: int = typer.Option(2, "--max-depth", "-d", help="Maximum traversal depth"),
    direction: str = typer.Option("outbound", "--direction", help="Traversal direction: outbound, inbound, any"),
):
    """
    Traverse graph relationships from a starting point.
    
    USAGE:
        arangodb search graph --start-id "doc/123" --max-depth 3 [OPTIONS]
    
    WHEN TO USE:
        When exploring connected documents through relationships
    
    OUTPUT:
        - TABLE: Related documents with depth and path
        - JSON: Complete traversal data with metadata
    
    EXAMPLES:
        arangodb search graph --start-id "user/456" --direction any
        arangodb search graph --start-id "post/789" --max-depth 1 --output json
    """
    logger.info(f"Graph search: start_id={start_id}, depth={max_depth}")
    
    try:
        db = get_db_connection()
        
        # Import actual search function
        from arangodb.core.search.graph_traverse import graph_traverse
        
        # Extract the key from the ID (format: collection/key)
        if "/" in start_id:
            collection_name, start_key = start_id.split("/", 1)
        else:
            start_key = start_id
            collection_name = collection
        
        start_time = datetime.now()
        results = graph_traverse(
            db=db,
            start_vertex_key=start_key,
            min_depth=1,  # Minimum depth
            max_depth=max_depth,
            direction=direction.upper(),  # Ensure uppercase
            limit=limit,
            start_vertex_collection=collection_name,
            output_format="json"  # We need raw data for our formatter
        )
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        metadata = {
            "type": "Graph",
            "start_id": start_id,
            "direction": direction,
            "max_depth": max_depth,
            "collection": collection,
            "count": len(results),
            "limit": limit,
            "timing": {"search_ms": round(search_time, 2)}
        }
        
        standard_output_handler(results, metadata, output_format)
        
    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        error_response = {
            "success": False,
            "data": None,
            "metadata": {},
            "errors": [{
                "code": "SEARCH_ERROR",
                "message": str(e),
                "suggestion": f"Check that node '{start_id}' exists"
            }]
        }
        if output_format == OutputFormat.JSON:
            console.print_json(data=error_response)
        else:
            console.print(format_error("Graph Search Failed", str(e)))
        raise typer.Exit(1)

if __name__ == "__main__":
    search_app()