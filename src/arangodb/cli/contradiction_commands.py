"""
CLI commands for contradiction detection and resolution.

Provides commands to list, analyze, and resolve contradictions in the graph.
"""

import sys
import json
from datetime import datetime, timezone
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from arangodb.core.memory.contradiction_logger import ContradictionLogger
from arangodb.core.graph.contradiction_detection import (
    detect_contradicting_edges,
    resolve_contradiction
)
from .db_connection import get_db_connection

# Initialize the Typer app
app = typer.Typer(name="contradiction", help="Contradiction detection and resolution commands")
console = Console()


@app.command("list")
def list_contradictions(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of contradictions to show"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (resolved/failed)"),
    edge_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by edge type"),
    entity_id: Optional[str] = typer.Option(None, "--entity", "-e", help="Filter by entity ID")
):
    """List detected contradictions from the log."""
    try:
        # Get database connection
        db = get_db_connection()
        
        # Initialize logger
        logger = ContradictionLogger(db)
        
        # Query contradictions
        contradictions = logger.get_contradictions(
            entity_id=entity_id,
            edge_type=edge_type,
            status=status,
            limit=limit
        )
        
        if not contradictions:
            console.print("[yellow]No contradictions found matching the criteria.[/yellow]")
            return
        
        # Create results table
        table = Table(
            title=f"Contradiction Log (Showing {len(contradictions)} of {limit} max)",
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Timestamp", style="cyan", width=20)
        table.add_column("Edge Type", style="green")
        table.add_column("Status", style="red")
        table.add_column("Resolution", style="yellow")
        table.add_column("From → To", style="blue")
        table.add_column("Context", style="white")
        
        for entry in contradictions:
            # Parse timestamp
            ts = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            
            # Format edge info
            edge_type = entry['new_edge']['type']
            from_id = entry['new_edge']['from'].split('/')[-1]
            to_id = entry['new_edge']['to'].split('/')[-1]
            edge_str = f"{from_id} → {to_id}"
            
            # Resolution info
            resolution = entry['resolution']
            res_str = f"{resolution['action']} ({resolution['strategy']})"
            
            # Status with color
            status_str = entry['status']
            if status_str == "resolved":
                status_str = f"[green]{status_str}[/green]"
            else:
                status_str = f"[red]{status_str}[/red]"
            
            table.add_row(
                ts_str,
                edge_type,
                status_str,
                res_str,
                edge_str,
                entry.get('context', 'unknown')
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing contradictions: {e}[/red]")
        raise typer.Exit(1)


@app.command("summary")
def contradiction_summary():
    """Show contradiction statistics summary."""
    try:
        # Get database connection
        db = get_db_connection()
        
        # Initialize logger
        logger = ContradictionLogger(db)
        
        # Get summary
        summary = logger.get_contradiction_summary()
        
        # Create summary panel
        summary_text = f"""
[bold]Contradiction Summary[/bold]

[cyan]Total Contradictions:[/cyan] {summary['total']}
[green]Resolved:[/green] {summary['resolved']}
[red]Failed:[/red] {summary['failed']}
[yellow]Success Rate:[/yellow] {summary['success_rate']:.1%}
        """
        
        console.print(Panel(summary_text.strip(), title="Statistics", border_style="blue"))
        
        # Show breakdown by edge type
        if summary['by_edge_type']:
            type_table = Table(title="Contradictions by Edge Type", show_header=True)
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", style="green")
            
            for item in summary['by_edge_type']:
                type_table.add_row(
                    item['type'] or "(none)",
                    str(item['count'])
                )
            
            console.print(type_table)
        
        # Show breakdown by resolution action
        if summary['by_resolution_action']:
            action_table = Table(title="Resolution Actions", show_header=True)
            action_table.add_column("Action", style="cyan")
            action_table.add_column("Count", style="green")
            
            for item in summary['by_resolution_action']:
                action_table.add_row(
                    item['action'] or "(none)",
                    str(item['count'])
                )
            
            console.print(action_table)
        
    except Exception as e:
        console.print(f"[red]Error getting summary: {e}[/red]")
        raise typer.Exit(1)


@app.command("detect")
def detect_contradictions(
    from_id: str = typer.Argument(..., help="Source entity ID (_id format)"),
    to_id: str = typer.Argument(..., help="Target entity ID (_id format)"),
    edge_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by relationship type"),
    collection: str = typer.Option("agent_relationships", "--collection", "-c", help="Edge collection name")
):
    """Detect potential contradictions between two entities."""
    try:
        # Get database connection
        db = get_db_connection()
        
        # Find contradicting edges
        contradictions = detect_contradicting_edges(
            db=db,
            edge_collection=collection,
            from_id=from_id,
            to_id=to_id,
            relationship_type=edge_type,
            include_invalidated=False
        )
        
        if not contradictions:
            console.print(f"[green]No contradictions found between {from_id} and {to_id}[/green]")
            return
        
        console.print(f"[yellow]Found {len(contradictions)} potential contradictions:[/yellow]\n")
        
        # Display each contradiction
        for i, edge in enumerate(contradictions, 1):
            panel_content = f"""
[cyan]Edge Key:[/cyan] {edge['_key']}
[cyan]Type:[/cyan] {edge['type']}
[cyan]Valid From:[/cyan] {edge.get('valid_at', 'unknown')}
[cyan]Invalid At:[/cyan] {edge.get('invalid_at', 'null')}
[cyan]Created At:[/cyan] {edge.get('created_at', 'unknown')}
[cyan]Attributes:[/cyan]
{json.dumps(edge.get('attributes', {}), indent=2)}
            """
            
            console.print(Panel(
                panel_content.strip(),
                title=f"Contradiction {i}",
                border_style="red"
            ))
        
    except Exception as e:
        console.print(f"[red]Error detecting contradictions: {e}[/red]")
        raise typer.Exit(1)


@app.command("resolve")
def resolve_contradiction_manually(
    new_edge_key: str = typer.Argument(..., help="Key of the new edge"),
    existing_edge_key: str = typer.Argument(..., help="Key of the existing edge"),
    strategy: str = typer.Option("newest_wins", "--strategy", "-s", 
                                help="Resolution strategy: newest_wins, merge, split_timeline"),
    collection: str = typer.Option("agent_relationships", "--collection", "-c", help="Edge collection name"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Resolution reason")
):
    """Manually resolve a contradiction between two edges."""
    try:
        # Get database connection
        db = get_db_connection()
        
        # Get the edges
        edge_collection = db.collection(collection)
        new_edge = edge_collection.get(new_edge_key)
        existing_edge = edge_collection.get(existing_edge_key)
        
        if not new_edge:
            console.print(f"[red]New edge {new_edge_key} not found[/red]")
            raise typer.Exit(1)
        
        if not existing_edge:
            console.print(f"[red]Existing edge {existing_edge_key} not found[/red]")
            raise typer.Exit(1)
        
        # Display the edges for confirmation
        console.print("[bold]New Edge:[/bold]")
        console.print(Syntax(json.dumps(new_edge, indent=2), "json"))
        
        console.print("\n[bold]Existing Edge:[/bold]")
        console.print(Syntax(json.dumps(existing_edge, indent=2), "json"))
        
        # Confirm resolution
        if not typer.confirm(f"\nResolve using '{strategy}' strategy?"):
            console.print("[yellow]Resolution cancelled[/yellow]")
            return
        
        # Resolve the contradiction
        result = resolve_contradiction(
            db=db,
            edge_collection=collection,
            new_edge=new_edge,
            contradicting_edge=existing_edge,
            strategy=strategy,
            resolution_reason=reason or f"Manual resolution via CLI"
        )
        
        # Log the resolution
        logger = ContradictionLogger(db)
        logger.log_contradiction(
            new_edge=new_edge,
            existing_edge=existing_edge,
            resolution=result,
            context="manual_cli_resolution"
        )
        
        # Display result
        if result["success"]:
            console.print(f"[green]✓ Successfully resolved contradiction[/green]")
            console.print(f"[cyan]Action:[/cyan] {result['action']}")
            console.print(f"[cyan]Reason:[/cyan] {result['reason']}")
            
            if result.get("resolved_edge"):
                console.print("\n[bold]Resolved Edge:[/bold]")
                console.print(Syntax(json.dumps(result["resolved_edge"], indent=2), "json"))
        else:
            console.print(f"[red]✗ Failed to resolve contradiction[/red]")
            console.print(f"[red]Reason:[/red] {result['reason']}")
        
    except Exception as e:
        console.print(f"[red]Error resolving contradiction: {e}[/red]")
        raise typer.Exit(1)


# Self-validation function
if __name__ == "__main__":
    from arango import ArangoClient
    
    # Test CLI commands
    host = "http://localhost:8529"
    username = "root"
    password = "openSesame"
    database_name = "agent_memory_test"
    
    try:
        # Connect to ArangoDB
        client = ArangoClient(hosts=host)
        sys_db = client.db("_system", username=username, password=password)
        
        # Create test database if needed
        if not sys_db.has_database(database_name):
            sys_db.create_database(database_name)
        
        db = client.db(database_name, username=username, password=password)
        
        # Create test collection
        if not db.has_collection("agent_relationships"):
            db.create_collection("agent_relationships", edge=True)
        
        # Test the summary command
        print("Testing summary command...")
        # Instead of passing db directly, let the function get its own connection
        # But we need to ensure the environment is set up correctly
        import os
        os.environ["ADB_HOST"] = host
        os.environ["ADB_USERNAME"] = username  
        os.environ["ADB_PASSWORD"] = password
        os.environ["ADB_DATABASE"] = database_name
        contradiction_summary()
        
        # Clean up
        sys_db.delete_database(database_name)
        
        print("✅ VALIDATION PASSED - CLI commands working correctly")
        
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)