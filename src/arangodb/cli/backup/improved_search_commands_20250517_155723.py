"""
Improved Search Commands with Consistent Interface

This module provides a more consistent command-line interface for search operations.
All search commands now follow the same pattern with --query and --collection options.
"""

import typer
import json
from typing import Optional, List
from rich.console import Console
from rich.table import Table

from arangodb.core.db_operations import get_db_connection
from arangodb.core.search.bm25_search import search_bm25_documents
from arangodb.core.search.semantic_search import semantic_search  
from arangodb.core.search.keyword_search import search_keywords
from arangodb.core.search.tag_search import search_by_tags
from arangodb.core.search.graph_traverse import traverse_relationships
from arangodb.core.search.glossary_search import search_glossary

app = typer.Typer(help="Improved search commands with consistent interface")
console = Console()


def format_results(results: List[dict], output_format: str = "table", search_type: str = "Search") -> str:
    """Format search results for display"""
    if output_format == "json":
        return json.dumps(results, indent=2)
    
    if not results:
        return f"No results found for {search_type} search."
    
    # Create table
    table = Table(title=f"{search_type} Results")
    
    # Add columns dynamically based on first result
    if results:
        for key in results[0].keys():
            if not key.startswith('_'):  # Skip internal fields
                table.add_column(key.title(), style="cyan")
        
        # Add rows
        for result in results:
            row = []
            for key in results[0].keys():
                if not key.startswith('_'):
                    value = result.get(key, '')
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, indent=2)
                    row.append(str(value))
            table.add_row(*row)
    
    return table


@app.command("bm25")
def search_bm25(
    query: str = typer.Option(..., "--query", "-q", help="Search query text"),
    collection: str = typer.Option("documents", "--collection", "-c", help="Collection to search"),
    top_n: int = typer.Option(10, "--top-n", "-n", help="Number of results"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """
    Perform BM25 (Best Match 25) keyword search.
    
    BM25 is a probabilistic ranking function used for full-text search.
    It's effective for finding documents that contain specific keywords.
    """
    try:
        # Get database connection
        db = get_db_connection()
        
        # Perform search
        results = search_bm25_documents(
            db=db,
            query=query,
            collection_name=collection,
            top_n=top_n
        )
        
        # Format and display results
        formatted = format_results(results, output, "BM25")
        console.print(formatted)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command("semantic")
def search_semantic(
    query: str = typer.Option(..., "--query", "-q", help="Search query text"),
    collection: str = typer.Option("documents", "--collection", "-c", help="Collection to search"),
    threshold: float = typer.Option(0.75, "--threshold", "-t", help="Similarity threshold (0-1)"),
    top_n: int = typer.Option(10, "--top-n", "-n", help="Number of results"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """
    Perform semantic search using vector embeddings.
    
    Finds documents based on conceptual similarity rather than exact keywords.
    Uses AI embeddings to understand meaning and context.
    """
    try:
        # Get database connection
        db = get_db_connection()
        
        # Perform search
        results = semantic_search(
            db=db,
            query=query,
            collection_name=collection,
            similarity_threshold=threshold,
            top_n=top_n
        )
        
        # Format and display results
        formatted = format_results(results, output, "Semantic")
        console.print(formatted)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command("keyword")
def search_keyword(
    query: str = typer.Option(..., "--query", "-q", help="Keywords to search for"),
    collection: str = typer.Option("documents", "--collection", "-c", help="Collection to search"),
    field: str = typer.Option("content", "--field", "-f", help="Field to search in"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """
    Perform keyword search in specific fields.
    
    Searches for exact keyword matches in specified document fields.
    """
    try:
        # Get database connection
        db = get_db_connection()
        
        # Perform search
        results = search_keywords(
            db=db,
            keywords=query.split(),
            collection_name=collection,
            field_name=field
        )
        
        # Format and display results
        formatted = format_results(results, output, "Keyword")
        console.print(formatted)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command("tag")
def search_tag(
    tags: str = typer.Option(..., "--tags", "-t", help="Comma-separated tags"),
    collection: str = typer.Option("documents", "--collection", "-c", help="Collection to search"),
    mode: str = typer.Option("any", "--mode", "-m", help="Match mode: any or all"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """
    Search documents by tags.
    
    Find documents that have specific tags assigned to them.
    """
    try:
        # Get database connection
        db = get_db_connection()
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")]
        
        # Perform search
        results = search_by_tags(
            db=db,
            tags=tag_list,
            collection_name=collection,
            match_all=(mode == "all")
        )
        
        # Format and display results
        formatted = format_results(results, output, "Tag")
        console.print(formatted)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command("graph")
def search_graph(
    start_id: str = typer.Option(..., "--start-id", "-s", help="Starting node ID"),
    direction: str = typer.Option("outbound", "--direction", "-d", help="Traversal direction: outbound, inbound, any"),
    max_depth: int = typer.Option(2, "--max-depth", "-m", help="Maximum traversal depth"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """
    Traverse graph relationships from a starting point.
    
    Explore connected nodes in the knowledge graph.
    """
    try:
        # Get database connection
        db = get_db_connection()
        
        # Perform traversal
        results = traverse_relationships(
            db=db,
            start_node_id=start_id,
            direction=direction,
            max_depth=max_depth
        )
        
        # Format and display results
        formatted = format_results(results, output, "Graph")
        console.print(formatted)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()