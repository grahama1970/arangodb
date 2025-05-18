"""
Stellar CLI Example - Template for Perfect CLI Consistency

This module demonstrates the ideal CLI structure with:
- Consistent parameter patterns
- Uniform output formatting
- LLM-friendly design
- Beautiful human output
"""

import typer
import json
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box
from dataclasses import dataclass, asdict
from loguru import logger

# Import core functionality
from arangodb.core.db_operations import get_db_connection

# CLI utilities that should be centralized
console = Console()

class OutputFormat(str, Enum):
    """Output format options"""
    TABLE = "table"
    JSON = "json"

@dataclass
class CLIResponse:
    """Standard response structure for all commands"""
    success: bool
    data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None

def add_output_option(func):
    """Decorator to add standard output option to commands"""
    return typer.Option(
        OutputFormat.TABLE,
        "--output", "-o",
        help="Output format (table or json)"
    )(func)

def format_output(response: CLIResponse, output_format: OutputFormat):
    """Format response based on output type"""
    if output_format == OutputFormat.JSON:
        console.print_json(data=asdict(response))
    else:
        if response.success:
            if isinstance(response.data, list):
                _print_table(response.data, response.metadata)
            else:
                _print_single_item(response.data, response.metadata)
        else:
            _print_errors(response.errors)

def _print_table(data: List[Dict], metadata: Dict = None):
    """Print data as a Rich table"""
    if not data:
        console.print("[yellow]No results found[/yellow]")
        return
    
    # Create table
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    
    # Add columns based on first item
    for key in data[0].keys():
        if not key.startswith('_'):  # Skip internal fields
            table.add_column(key.replace('_', ' ').title())
    
    # Add rows
    for item in data:
        row = []
        for key in data[0].keys():
            if not key.startswith('_'):
                value = item.get(key, '')
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                elif isinstance(value, bool):
                    value = "✓" if value else "✗"
                row.append(str(value)[:50] + "..." if len(str(value)) > 50 else str(value))
        table.add_row(*row)
    
    # Add metadata footer if available
    if metadata:
        table.caption = f"Showing {metadata.get('count', 0)} of {metadata.get('total', 0)} results"
    
    console.print(table)

def _print_single_item(data: Dict, metadata: Dict = None):
    """Print single item details"""
    table = Table(box=box.MINIMAL, show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    
    for key, value in data.items():
        if not key.startswith('_'):
            table.add_row(
                key.replace('_', ' ').title(),
                str(value)
            )
    
    console.print(table)

def _print_errors(errors: List[Dict]):
    """Print errors in a formatted way"""
    console.print("[red]Error:[/red]")
    for error in errors:
        console.print(f"  • {error['message']}")
        if 'suggestion' in error:
            console.print(f"    [yellow]Suggestion:[/yellow] {error['suggestion']}")

# Create main app and subcommands
app = typer.Typer(help="Stellar CLI Example - Perfect consistency")
documents_app = typer.Typer(help="Document operations")
search_app = typer.Typer(help="Search operations")

app.add_typer(documents_app, name="documents")
app.add_typer(search_app, name="search")

# Document commands
@documents_app.command("list")
def list_documents(
    collection: str = typer.Argument(..., help="Collection name"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    offset: int = typer.Option(0, "--offset", help="Skip this many results"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """
    List documents from a collection.
    
    USAGE:
        arangodb documents list <collection> [OPTIONS]
    
    WHEN TO USE:
        When you need to browse documents in a collection
    
    OUTPUT:
        - TABLE: Formatted table with document summaries
        - JSON: Complete document data with metadata
    
    EXAMPLES:
        arangodb documents list users --limit 20
        arangodb documents list products --output json --tag electronics
    """
    db = get_db_connection()
    
    try:
        # Build query
        query = f"FOR doc IN {collection}"
        bind_vars = {}
        
        if tag:
            query += " FILTER @tag IN doc.tags"
            bind_vars["tag"] = tag
        
        query += " LIMIT @offset, @limit RETURN doc"
        bind_vars.update({"offset": offset, "limit": limit})
        
        # Execute
        start_time = datetime.now()
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Get total count
        count_query = f"FOR doc IN {collection} RETURN COUNT(doc)"
        total = db.aql.execute(count_query).next()
        
        # Format response
        response = CLIResponse(
            success=True,
            data=results,
            metadata={
                "count": len(results),
                "total": total,
                "limit": limit,
                "offset": offset,
                "timing": {
                    "query_ms": round(query_time, 2)
                }
            }
        )
        
        format_output(response, output)
        
    except Exception as e:
        response = CLIResponse(
            success=False,
            errors=[{
                "code": "QUERY_ERROR",
                "message": str(e),
                "suggestion": f"Check if collection '{collection}' exists"
            }]
        )
        format_output(response, output)
        raise typer.Exit(1)

@documents_app.command("create")
def create_document(
    collection: str = typer.Argument(..., help="Collection name"),
    data: str = typer.Argument(..., help="JSON data for the document"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    embed: bool = typer.Option(True, "--embed/--no-embed", help="Generate embeddings"),
):
    """
    Create a new document in a collection.
    
    USAGE:
        arangodb documents create <collection> <json_data> [OPTIONS]
    
    WHEN TO USE:
        When you need to add a new document to any collection
    
    OUTPUT:
        - TABLE: Summary of created document with ID
        - JSON: Complete document with metadata
    
    EXAMPLES:
        arangodb documents create users '{"name": "John", "age": 30}'
        arangodb documents create notes '{"title": "Meeting", "content": "..."}' --embed
    """
    db = get_db_connection()
    
    try:
        # Parse JSON data
        doc_data = json.loads(data)
        
        # Add metadata
        doc_data["created_at"] = datetime.now().isoformat()
        
        # Generate embedding if requested
        if embed and any(isinstance(v, str) for v in doc_data.values()):
            # This would call actual embedding function
            doc_data["_embedding"] = [0.1] * 768  # Placeholder
        
        # Insert document
        start_time = datetime.now()
        collection_obj = db.collection(collection)
        result = collection_obj.insert(doc_data)
        insert_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Get the created document
        created_doc = collection_obj.get(result["_key"])
        
        response = CLIResponse(
            success=True,
            data=created_doc,
            metadata={
                "operation": "create",
                "collection": collection,
                "key": result["_key"],
                "embedded": embed,
                "timing": {
                    "insert_ms": round(insert_time, 2)
                }
            }
        )
        
        format_output(response, output)
        
    except json.JSONDecodeError as e:
        response = CLIResponse(
            success=False,
            errors=[{
                "code": "INVALID_JSON",
                "message": f"Invalid JSON data: {e}",
                "suggestion": "Check your JSON syntax"
            }]
        )
        format_output(response, output)
        raise typer.Exit(1)
    except Exception as e:
        response = CLIResponse(
            success=False,
            errors=[{
                "code": "CREATE_ERROR",
                "message": str(e)
            }]
        )
        format_output(response, output)
        raise typer.Exit(1)

# Search commands
@search_app.command("semantic")
def search_semantic(
    query: str = typer.Argument(..., help="Search query text"),
    collection: str = typer.Option("documents", "--collection", "-c"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l"),
    threshold: float = typer.Option(0.7, "--threshold", "-t", help="Similarity threshold"),
):
    """
    Perform semantic search using embeddings.
    
    USAGE:
        arangodb search semantic <query> [OPTIONS]
    
    WHEN TO USE:
        When searching for conceptually similar content
    
    OUTPUT:
        - TABLE: Results with similarity scores
        - JSON: Complete results with metadata
    
    EXAMPLES:
        arangodb search semantic "machine learning concepts"
        arangodb search semantic "database optimization" --collection articles --threshold 0.8
    """
    # Implementation would follow the same pattern
    response = CLIResponse(
        success=True,
        data=[
            {"title": "Introduction to ML", "score": 0.92},
            {"title": "Deep Learning Basics", "score": 0.87}
        ],
        metadata={
            "count": 2,
            "query": query,
            "threshold": threshold,
            "collection": collection
        }
    )
    
    format_output(response, output)

# Global options
@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    version: bool = typer.Option(False, "--version", help="Show version"),
):
    """
    Stellar CLI Example - A template for perfect CLI consistency
    """
    if version:
        console.print("Stellar CLI v1.0.0")
        raise typer.Exit()
    
    if verbose:
        logger.add(console.print, level="DEBUG")

if __name__ == "__main__":
    app()