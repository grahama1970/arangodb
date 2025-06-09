"""CLI commands for D3.js visualization integration
Module: visualization_commands.py
Description: Functions for visualization commands operations

This module provides CLI commands for generating D3.js visualizations from ArangoDB queries.

Sample input: ArangoDB query results
Expected output: HTML visualizations saved to files or served via browser
"""

import json
import webbrowser
from pathlib import Path
from typing import Optional, List
import typer
from loguru import logger
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Import visualization components
from ..visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig
from ..visualization.core.data_transformer import DataTransformer
from ..visualization.core.table_engine import TableEngine
from ..core.arango_setup import connect_arango, ensure_database

# Create Typer app
app = typer.Typer(name="visualize", help="Generate D3.js visualizations from ArangoDB data")
console = Console()

# Default output directory
DEFAULT_OUTPUT_DIR = Path("/home/graham/workspace/experiments/arangodb/visualizations")
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.command()
def generate(
    query: str = typer.Argument(..., help="AQL query to fetch graph data"),
    layout: str = typer.Option("force", help="Layout type: force, tree, radial, sankey"),
    output: Optional[Path] = typer.Option(None, help="Output file path (default: auto-generated)"),
    title: Optional[str] = typer.Option(None, help="Visualization title"),
    open_browser: bool = typer.Option(True, help="Open visualization in browser"),
    use_llm: bool = typer.Option(True, help="Use LLM for layout recommendation"),
    width: int = typer.Option(1200, help="Visualization width"),
    height: int = typer.Option(800, help="Visualization height"),
    db_name: str = typer.Option("epistemic_test", help="Database name"),
    collection: Optional[str] = typer.Option(None, help="Collection name for context")
):
    """Generate a visualization from an AQL query"""
    try:
        console.print(f"[bold blue]Executing query:[/bold blue] {query}")
        
        # Initialize database connection
        client = connect_arango()
        if db_name == "epistemic_test":
            db = ensure_database(client)
        else:
            # Use specified database directly with credentials
            db = client.db(db_name, username='root', password='password')
        
        # Execute query
        cursor = db.aql.execute(query)
        result = list(cursor)
        
        if not result:
            console.print("[red]Query returned no results[/red]")
            return
        
        # Transform data for visualization
        transformer = DataTransformer()
        
        # Handle different result formats
        if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict):
            # Single result object - check if it's already in graph format
            if "nodes" in result[0] and ("links" in result[0] or "edges" in result[0]):
                graph_data = result[0]
                # Convert "edges" to "links" if needed
                if "edges" in graph_data and "links" not in graph_data:
                    graph_data["links"] = graph_data.pop("edges")
            else:
                # Convert single documents to nodes
                graph_data = {
                    "nodes": [{"id": doc.get("_key", str(i)), "name": doc.get("name", f"Node {i}")} 
                              for i, doc in enumerate(result)],
                    "links": []
                }
        elif isinstance(result, list):
            # Multiple documents - convert to nodes
            graph_data = {
                "nodes": [{"id": doc.get("_key", str(i)), "name": doc.get("name", f"Node {i}")} 
                          for i, doc in enumerate(result)],
                "links": []
            }
        else:
            console.print("[red]Could not transform results to graph format[/red]")
            return
        
        console.print(f"[green]Transformed data: {len(graph_data['nodes'])} nodes, {len(graph_data['links'])} links[/green]")
        
        # Initialize visualization engine
        engine = D3VisualizationEngine(use_llm=use_llm)
        
        # Create configuration
        config = VisualizationConfig(
            layout=layout,
            title=title or f"Visualization from {collection or 'query'}",
            width=width,
            height=height
        )
        
        # Generate visualization
        if use_llm and engine.llm_recommender:
            console.print("[bold yellow]Getting LLM recommendation...[/bold yellow]")
            recommendation = engine.recommend_visualization(graph_data, query)
            
            if recommendation:
                console.print(f"[green]LLM recommended: {recommendation.layout_type}[/green]")
                console.print(f"[dim]{recommendation.reasoning}[/dim]")
                
                # Update config with recommendation
                config.layout = recommendation.layout_type
                config.title = recommendation.title
                
                # Ask user to confirm
                if not typer.confirm(f"Use recommended layout '{recommendation.layout_type}'?"):
                    config.layout = layout
        
        # Generate HTML
        console.print(f"[bold blue]Generating {config.layout} visualization...[/bold blue]")
        html = engine.generate_visualization(graph_data, layout=config.layout, config=config)
        
        # Save to file
        if not output:
            timestamp = Path().name
            output = DEFAULT_OUTPUT_DIR / f"{config.layout}_{len(graph_data['nodes'])}nodes_{timestamp}.html"
        
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(html)
        
        console.print(f"[green]Visualization saved to: {output}[/green]")
        
        # Open in browser
        if open_browser:
            webbrowser.open(f"file://{output.absolute()}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Visualization generation failed: {e}")
        raise typer.Exit(1)


@app.command()
def from_file(
    input_file: Path = typer.Argument(..., help="JSON file with graph data"),
    layout: str = typer.Option("force", help="Layout type: force, tree, radial, sankey"),
    output: Optional[Path] = typer.Option(None, help="Output file path"),
    title: Optional[str] = typer.Option(None, help="Visualization title"),
    open_browser: bool = typer.Option(True, help="Open visualization in browser"),
    use_llm: bool = typer.Option(True, help="Use LLM for layout recommendation"),
    width: int = typer.Option(1200, help="Visualization width"),
    height: int = typer.Option(800, help="Visualization height")
):
    """Generate a visualization from a JSON file"""
    try:
        if not input_file.exists():
            console.print(f"[red]File not found: {input_file}[/red]")
            raise typer.Exit(1)
        
        # Load graph data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if data is in D3 format or ArangoDB format
        if isinstance(data, dict):
            if "nodes" in data and "links" in data:
                # Already in D3 format
                graph_data = data
            elif "vertices" in data and "edges" in data:
                # ArangoDB format - convert to D3
                console.print("[yellow]Converting ArangoDB format to D3 format...[/yellow]")
                transformer = DataTransformer()
                graph_data = transformer.transform_graph_data(data)
            else:
                console.print("[red]Invalid graph data format. Expected {nodes: [], links: []} or {vertices: [], edges: []}[/red]")
                raise typer.Exit(1)
        else:
            console.print("[red]Invalid JSON format. Expected dictionary[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]Loaded data: {len(graph_data['nodes'])} nodes, {len(graph_data['links'])} links[/green]")
        
        # Initialize visualization engine
        engine = D3VisualizationEngine(use_llm=use_llm)
        
        # Create configuration
        config = VisualizationConfig(
            layout=layout,
            title=title or f"Visualization from {input_file.name}",
            width=width,
            height=height
        )
        
        # Generate visualization with potential LLM recommendation
        if use_llm and engine.llm_recommender:
            console.print("[bold yellow]Getting LLM recommendation...[/bold yellow]")
            html = engine.generate_with_recommendation(graph_data, base_config=config)
        else:
            html = engine.generate_visualization(graph_data, layout=config.layout, config=config)
        
        # Save to file
        if not output:
            output = input_file.with_suffix('.html')
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(html)
        
        console.print(f"[green]Visualization saved to: {output}[/green]")
        
        # Open in browser
        if open_browser:
            webbrowser.open(f"file://{output.absolute()}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Visualization from file failed: {e}")
        raise typer.Exit(1)


@app.command()
def server(
    graph_data: Optional[Path] = typer.Option(None, help="JSON file with graph data"),
    query: Optional[str] = typer.Option(None, help="User query for LLM context"),
    layout: str = typer.Option("force", help="Layout type"),
    use_llm: bool = typer.Option(True, help="Use LLM recommendation"),
    server_url: str = typer.Option("http://localhost:8000", help="Visualization server URL")
):
    """Send visualization request to server"""
    try:
        if not graph_data and not query:
            console.print("[red]Please provide either graph data file or query[/red]")
            raise typer.Exit(1)
        
        # Prepare request data
        if graph_data:
            with open(graph_data, 'r', encoding='utf-8') as f:
                graph_json = json.load(f)
        else:
            # Use sample data for demo
            graph_json = {
                "nodes": [
                    {"id": "1", "name": "Sample Node 1"},
                    {"id": "2", "name": "Sample Node 2"},
                    {"id": "3", "name": "Sample Node 3"}
                ],
                "links": [
                    {"source": "1", "target": "2"},
                    {"source": "2", "target": "3"}
                ]
            }
        
        request_data = {
            "graph_data": graph_json,
            "layout": layout,
            "use_llm": use_llm,
            "query": query
        }
        
        console.print(f"[bold blue]Sending request to server: {server_url}[/bold blue]")
        
        # Send request
        with httpx.Client() as client:
            response = client.post(
                f"{server_url}/visualize",
                json=request_data,
                timeout=30.0
            )
        
        if response.status_code != 200:
            console.print(f"[red]Server error: {response.status_code}[/red]")
            console.print(response.text)
            raise typer.Exit(1)
        
        result = response.json()
        
        # Display result
        table = Table(title="Visualization Result")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Layout", result.get("layout", "N/A"))
        table.add_row("Title", result.get("title", "N/A"))
        table.add_row("Cache Hit", str(result.get("cache_hit", False)))
        
        if result.get("recommendation"):
            rec = result["recommendation"]
            table.add_row("LLM Layout", rec.get("layout", "N/A"))
            table.add_row("Confidence", f"{rec.get('confidence', 0):.2f}")
        
        console.print(table)
        
        # Save HTML to file
        output = DEFAULT_OUTPUT_DIR / f"server_{result.get('layout', 'unknown')}_{Path().name}.html"
        with open(output, 'w', encoding='utf-8') as f:
            f.write(result["html"])
        
        console.print(f"[green]Visualization saved to: {output}[/green]")
        
        # Open in browser
        webbrowser.open(f"file://{output.absolute()}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Server request failed: {e}")
        raise typer.Exit(1)


@app.command()
def table(
    query: str = typer.Argument(..., help="AQL query to fetch data for table"),
    output: Optional[Path] = typer.Option(None, help="Output file path (default: auto-generated)"),
    title: Optional[str] = typer.Option(None, help="Table title"),
    page_size: int = typer.Option(10, help="Number of rows per page"),
    open_browser: bool = typer.Option(True, help="Open table in browser"),
    db_name: str = typer.Option("epistemic_test", help="Database name"),
    collection: Optional[str] = typer.Option(None, help="Collection name for context"),
    columns: Optional[str] = typer.Option(None, help="Comma-separated list of columns to display")
):
    """Generate an interactive table from an AQL query"""
    try:
        console.print(f"[bold blue]Executing query:[/bold blue] {query}")
        
        # Initialize database connection
        client = connect_arango()
        if db_name == "epistemic_test":
            db = ensure_database(client)
        else:
            db = client.db(db_name, username='root', password='password')
        
        # Execute query
        cursor = db.aql.execute(query)
        result = list(cursor)
        
        if not result:
            console.print("[red]Query returned no results[/red]")
            return
        
        console.print(f"[green]Query returned {len(result)} rows[/green]")
        
        # Initialize table engine
        engine = TableEngine()
        
        # Parse columns if provided
        custom_columns = None
        if columns:
            column_names = [c.strip() for c in columns.split(',')]
            custom_columns = [{"key": col, "label": col.replace('_', ' ').title(), "type": "string"} 
                            for col in column_names]
        
        # Generate table HTML
        html = engine.generate_table(
            data=result,
            columns=custom_columns,
            title=title or f"Table: {collection or 'Query Results'}",
            page_size=page_size,
            collection_name=collection
        )
        
        # Save to file
        if not output:
            timestamp = Path().name
            output = DEFAULT_OUTPUT_DIR / f"table_{len(result)}rows_{timestamp}.html"
        
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(html)
        
        console.print(f"[green]Table saved to: {output}[/green]")
        
        # Open in browser
        if open_browser:
            webbrowser.open(f"file://{output.absolute()}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Table generation failed: {e}")
        raise typer.Exit(1)


@app.command()
def layouts():
    """List available visualization layouts"""
    table = Table(title="Available Visualization Layouts")
    table.add_column("Layout", style="cyan", width=10)
    table.add_column("Description", style="green", width=40)
    table.add_column("Best For", style="yellow", width=30)
    
    layouts_info = [
        ("force", "Force-directed layout with physics simulation", "Networks, clusters, general graphs"),
        ("tree", "Hierarchical tree layout", "Hierarchies, taxonomies, org charts"),
        ("radial", "Radial tree layout", "Centered hierarchies, circular organization"),
        ("sankey", "Flow diagram for weighted paths", "Flows, processes, resource allocation")
    ]
    
    for layout, desc, best_for in layouts_info:
        table.add_row(layout, desc, best_for)
    
    console.print(table)


@app.command()
def examples():
    """Show example AQL queries for visualization"""
    # Graph visualization examples
    graph_examples = [
        {
            "title": "Find all document relationships",
            "query": "FOR doc IN documents\n  FOR v, e IN 1..3 OUTBOUND doc relationships\n  RETURN {nodes: UNION([doc], v), links: e}",
            "layout": "force"
        },
        {
            "title": "Show concept hierarchy",
            "query": "FOR concept IN concepts\n  FILTER concept.type == 'root'\n  FOR v, e, p IN 1..5 OUTBOUND concept parent_of\n  RETURN {nodes: p.vertices, links: p.edges}",
            "layout": "tree"
        },
        {
            "title": "Analyze information flow",
            "query": "FOR source IN sources\n  FOR target, flow IN 1..3 OUTBOUND source flows_to\n  RETURN {source: source, target: target, value: flow.weight}",
            "layout": "sankey"
        }
    ]
    
    # Table visualization examples
    table_examples = [
        {
            "title": "List all memories with details",
            "query": "FOR m IN memories\n  LIMIT 100\n  RETURN m",
            "command": "arangodb visualize table"
        },
        {
            "title": "Show entities with relationships count",
            "query": "FOR e IN entities\n  LET rel_count = LENGTH(FOR v IN 1..1 ANY e relationships RETURN 1)\n  RETURN {name: e.name, type: e.type, relationships: rel_count, created: e.created_at}",
            "command": "arangodb visualize table --columns name,type,relationships,created"
        },
        {
            "title": "Recent memories sorted by confidence",
            "query": "FOR m IN memories\n  FILTER m.created_at > DATE_SUBTRACT(DATE_NOW(), 7, 'days')\n  SORT m.confidence DESC\n  LIMIT 50\n  RETURN m",
            "command": "arangodb visualize table --page-size 25"
        }
    ]
    
    console.print("[bold cyan]Graph Visualization Examples:[/bold cyan]\n")
    for i, example in enumerate(graph_examples, 1):
        panel = Panel(
            f"[bold]{example['title']}[/bold]\n\n"
            f"[cyan]Query:[/cyan]\n{example['query']}\n\n"
            f"[yellow]Recommended layout:[/yellow] {example['layout']}",
            title=f"Graph Example {i}",
            expand=False
        )
        console.print(panel)
        console.print()
    
    console.print("[bold cyan]Table Visualization Examples:[/bold cyan]\n")
    for i, example in enumerate(table_examples, 1):
        panel = Panel(
            f"[bold]{example['title']}[/bold]\n\n"
            f"[cyan]Query:[/cyan]\n{example['query']}\n\n"
            f"[yellow]Command:[/yellow] {example['command']}",
            title=f"Table Example {i}",
            expand=False
        )
        console.print(panel)
        console.print()


if __name__ == "__main__":
    app()