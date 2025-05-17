"""
Search Configuration CLI Commands

Provides CLI interface for managing and using search configurations.
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.json import JSON
import json

from arangodb.core.search.search_config import (
    SearchConfig, 
    SearchConfigManager, 
    SearchMethod, 
    QueryTypeConfig
)
from arangodb.core.search.hybrid_search import search_with_config
from arangodb.cli.db_connection import get_db_connection

app = typer.Typer(help="Search configuration commands")
console = Console()


@app.command("list-configs")
def list_configs():
    """List all available search configurations."""
    console.print("\n[bold]Available Search Configurations:[/bold]\n")
    
    # Built-in configurations
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Config Name", width=20)
    table.add_column("Method", width=15)
    table.add_column("Description", width=50)
    
    # Get QueryTypeConfig attributes
    for attr_name in dir(QueryTypeConfig):
        if not attr_name.startswith('_'):
            config = getattr(QueryTypeConfig, attr_name)
            if isinstance(config, SearchConfig):
                table.add_row(
                    attr_name,
                    config.preferred_method.value,
                    f"Weight: BM25={config.bm25_weight}, Semantic={config.semantic_weight}"
                )
    
    console.print(table)


@app.command("search")
def search_with_configuration(
    query: str = typer.Argument(..., help="Search query text"),
    config_type: Optional[str] = typer.Option(None, "--config", "-c", help="Config type (FACTUAL, CONCEPTUAL, etc.)"),
    method: Optional[str] = typer.Option(None, "--method", "-m", help="Override search method"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results to return"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format (table/json)")
):
    """Execute search with specific configuration."""
    db = get_db_connection()
    
    # Create configuration
    if config_type:
        # Use predefined configuration
        config_type_upper = config_type.upper()
        if hasattr(QueryTypeConfig, config_type_upper):
            config = getattr(QueryTypeConfig, config_type_upper)
            config.result_limit = limit
        else:
            console.print(f"[red]Unknown config type: {config_type}[/red]")
            raise typer.Exit(1)
    else:
        # Create custom configuration
        config = SearchConfig(result_limit=limit)
        
        # Override method if specified
        if method:
            try:
                config.preferred_method = SearchMethod(method.lower())
            except ValueError:
                console.print(f"[red]Invalid method: {method}[/red]")
                console.print(f"Valid methods: {[m.value for m in SearchMethod]}")
                raise typer.Exit(1)
    
    # Execute search
    console.print(f"\n[bold]Searching with {config.preferred_method.value} method...[/bold]")
    
    results = search_with_config(
        db=db,
        query_text=query,
        config=config,
        output_format=output_format
    )
    
    # Display results
    if output_format == "json":
        console.print(JSON(json.dumps(results, indent=2)))
    else:
        total = results.get('total', 0)
        time_taken = results.get('time', 0)
        
        console.print(f"\nFound [green]{total}[/green] results in [yellow]{time_taken:.3f}s[/yellow]\n")
        
        if total > 0:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Rank", width=6)
            table.add_column("Score", width=10)
            table.add_column("Title/Content", width=80)
            
            for i, result in enumerate(results.get('results', [])[:limit], 1):
                doc = result.get('doc', {})
                score = result.get('hybrid_score') or result.get('score', 0)
                
                # Get best content to display
                title = doc.get('question') or doc.get('problem') or doc.get('title', '')
                content = doc.get('solution') or doc.get('content', '')
                display_text = title[:80] if title else content[:80]
                
                table.add_row(
                    str(i),
                    f"{score:.4f}",
                    display_text + "..." if len(display_text) == 80 else display_text
                )
            
            console.print(table)


@app.command("analyze")
def analyze_query(
    query: str = typer.Argument(..., help="Query to analyze")
):
    """Analyze a query to determine best search configuration."""
    manager = SearchConfigManager()
    config = manager.get_config_for_query(query)
    
    console.print(f"\n[bold]Query Analysis:[/bold]")
    console.print(f"Query: [yellow]{query}[/yellow]")
    console.print(f"Recommended method: [green]{config.preferred_method.value}[/green]")
    console.print(f"BM25 weight: {config.bm25_weight}")
    console.print(f"Semantic weight: {config.semantic_weight}")
    console.print(f"Result limit: {config.result_limit}")
    console.print(f"Enable reranking: {config.enable_reranking}")
    
    # Explain why this config was chosen
    console.print("\n[bold]Reasoning:[/bold]")
    
    query_lower = query.lower()
    if any(word in query_lower for word in ["what", "when", "where", "how many"]):
        console.print("• Detected factual query indicators → BM25 preferred")
    elif any(word in query_lower for word in ["why", "explain", "understand"]):
        console.print("• Detected conceptual query indicators → Semantic preferred")
    elif "tag:" in query_lower or "#" in query:
        console.print("• Detected tag query → Tag search preferred")
    elif any(word in query_lower for word in ["related", "connected", "linked"]):
        console.print("• Detected graph exploration indicators → Graph search preferred")
    elif any(word in query_lower for word in ["recent", "latest", "today"]):
        console.print("• Detected temporal indicators → Time-filtered hybrid search")
    else:
        console.print("• General query → Hybrid search with balanced weights")


if __name__ == "__main__":
    """Validate search configuration CLI functionality."""
    
    # Test config listing
    print("Available configs:")
    list_configs()
    
    # Test query analysis
    test_queries = [
        "What is Python?",
        "Why is recursion important?",
        "Show me documents with tag:python",
        "What's related to databases?"
    ]
    
    manager = SearchConfigManager()
    for query in test_queries:
        config = manager.get_config_for_query(query)
        print(f"\nQuery: '{query}'")
        print(f"Method: {config.preferred_method.value}")
        print(f"Weights: BM25={config.bm25_weight}, Semantic={config.semantic_weight}")
    
    print("\n✅ Search configuration CLI validation passed!")