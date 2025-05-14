"""
CLI command implementation for manually resolving contradictions in ArangoDB relationships.

This module provides a Typer command for the ArangoDB CLI to detect and resolve contradictions
in graph relationships. It allows users to identify potentially contradicting relationships
and apply different resolution strategies.

Usage:
    arangodb graph resolve-contradictions [OPTIONS]
"""

import typer
import json
from typing import Optional, List
from loguru import logger
from rich.console import Console
from rich.table import Table

# Import necessary modules
try:
    # Try standalone package imports first
    from arangodb.contradiction_detection import (
        detect_contradicting_edges,
        detect_temporal_contradictions,
        resolve_contradiction,
        resolve_all_contradictions
    )
    from arangodb.config import EDGE_COLLECTION_NAME
except ImportError:
    # Fall back to relative imports
    from src.arangodb.contradiction_detection import (
        detect_contradicting_edges,
        detect_temporal_contradictions,
        resolve_contradiction,
        resolve_all_contradictions
    )
    from src.arangodb.config import EDGE_COLLECTION_NAME

# Rich console for output formatting
console = Console()

def display_edges(edges, title="Edges"):
    """
    Display a list of edges in a rich table format.
    
    Args:
        edges: List of edge documents
        title: Title for the table
    """
    if not edges:
        console.print("[yellow]No edges found.[/yellow]")
        return
        
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title=title
    )
    
    table.add_column("Key", style="cyan")
    table.add_column("From", style="blue")
    table.add_column("To", style="blue")
    table.add_column("Type", style="green")
    table.add_column("Valid From", style="yellow")
    table.add_column("Valid Until", style="yellow")
    table.add_column("Created At", style="dim")
    
    for edge in edges:
        # Extract the document keys from the _from and _to fields (remove collection prefix)
        from_parts = edge.get("_from", "").split("/")
        to_parts = edge.get("_to", "").split("/")
        from_key = from_parts[-1] if len(from_parts) > 1 else edge.get("_from", "")
        to_key = to_parts[-1] if len(to_parts) > 1 else edge.get("_to", "")
        
        table.add_row(
            edge.get("_key", ""),
            from_key,
            to_key,
            edge.get("type", ""),
            edge.get("valid_at", ""),
            edge.get("invalid_at", "None") if edge.get("invalid_at") is None else edge.get("invalid_at", ""),
            edge.get("created_at", "")
        )
    
    console.print(table)

def display_resolution_results(resolutions):
    """
    Display results of contradiction resolution.
    
    Args:
        resolutions: List of resolution result dictionaries
    """
    if not resolutions:
        console.print("[yellow]No resolutions performed.[/yellow]")
        return
        
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title="Contradiction Resolution Results"
    )
    
    table.add_column("Action", style="cyan")
    table.add_column("Success", style="green")
    table.add_column("Edge Key", style="blue")
    table.add_column("Reason", style="yellow")
    
    for res in resolutions:
        # Get the edge key if available
        edge_key = ""
        if res.get("resolved_edge") and isinstance(res["resolved_edge"], dict):
            edge_key = res["resolved_edge"].get("_key", "")
            
        table.add_row(
            res.get("action", "unknown"),
            "✅" if res.get("success") else "❌",
            edge_key,
            res.get("reason", "")
        )
    
    console.print(table)

def resolve_contradictions_command(
    db,
    from_key: str,
    to_key: str,
    collection_name: str,
    edge_collection: str,
    relationship_type: Optional[str] = None,
    strategy: str = "newest_wins",
    show_only: bool = False,
    yes: bool = False,
    json_output: bool = False,
):
    """
    CLI command implementation to detect and resolve contradictions.
    
    Args:
        db: ArangoDB database handle
        from_key: Key of the source document
        to_key: Key of the target document
        collection_name: Name of the vertex collection
        edge_collection: Name of the edge collection
        relationship_type: Optional type of relationship to filter by
        strategy: Resolution strategy (newest_wins, merge, split_timeline)
        show_only: If True, only show contradictions without resolving
        yes: If True, resolve without confirmation
        json_output: If True, output results as JSON
        
    Returns:
        Result dictionary or None
    """
    try:
        # Construct full IDs
        from_id = f"{collection_name}/{from_key}"
        to_id = f"{collection_name}/{to_key}"
        
        # Find all potentially contradicting edges
        logger.info(f"Searching for potentially contradicting edges between {from_id} and {to_id}")
        edges = detect_contradicting_edges(
            db=db,
            edge_collection=edge_collection,
            from_id=from_id,
            to_id=to_id,
            relationship_type=relationship_type,
            include_invalidated=False
        )
        
        if not edges:
            message = f"No active relationships found between {from_key} and {to_key}"
            if relationship_type:
                message += f" with type '{relationship_type}'"
                
            if json_output:
                return {
                    "status": "info",
                    "message": message,
                    "edges": []
                }
            else:
                console.print(f"[yellow]{message}[/yellow]")
                return None
        
        # Display the edges
        if not json_output:
            title = f"Relationships between {from_key} and {to_key}"
            if relationship_type:
                title += f" of type '{relationship_type}'"
            display_edges(edges, title=title)
        
        # If only showing contradictions, stop here
        if show_only or len(edges) < 2:
            if len(edges) < 2:
                message = "Only one relationship found. Need at least two relationships to check for contradictions."
                if json_output:
                    return {
                        "status": "info",
                        "message": message,
                        "edges": edges
                    }
                else:
                    console.print(f"[yellow]{message}[/yellow]")
            elif json_output:
                return {
                    "status": "info",
                    "message": "Found potentially contradicting edges (show-only mode)",
                    "edges": edges
                }
            return None
        
        # Check for temporal contradictions
        # Use the latest edge as reference
        sorted_edges = sorted(edges, key=lambda e: e.get("created_at", ""), reverse=True)
        latest_edge = sorted_edges[0]
        
        temporal_contradictions = detect_temporal_contradictions(
            db=db,
            edge_collection=edge_collection,
            edge_doc=latest_edge
        )
        
        if not temporal_contradictions:
            message = "No temporal contradictions found between these relationships."
            if json_output:
                return {
                    "status": "info",
                    "message": message,
                    "edges": edges
                }
            else:
                console.print(f"[yellow]{message}[/yellow]")
                return None
        
        # Display temporal contradictions
        if not json_output:
            console.print(f"\n[bold blue]Found {len(temporal_contradictions)} temporal contradictions:[/bold blue]")
            display_edges(temporal_contradictions, title="Temporally Contradicting Edges")
        
        # Confirm resolution if not auto-confirmed
        if not yes:
            confirmed = typer.confirm(
                f"Resolve {len(temporal_contradictions)} contradictions using '{strategy}' strategy?",
                abort=True
            )
        
        # Resolve contradictions
        logger.info(f"Resolving {len(temporal_contradictions)} contradictions with '{strategy}' strategy")
        resolutions, success = resolve_all_contradictions(
            db=db,
            edge_collection=edge_collection,
            edge_doc=latest_edge,
            strategy=strategy
        )
        
        # Display results
        if json_output:
            return {
                "status": "success" if success else "error",
                "message": f"Resolved {len(resolutions)} contradictions with '{strategy}' strategy",
                "latest_edge": latest_edge,
                "contradictions": temporal_contradictions,
                "resolutions": resolutions,
                "success": success
            }
        else:
            if success:
                console.print(f"[green]Successfully resolved {len(resolutions)} contradictions using '{strategy}' strategy[/green]")
            else:
                console.print(f"[bold red]Some contradictions could not be resolved[/bold red]")
                
            display_resolution_results(resolutions)
            return None
            
    except Exception as e:
        logger.error(f"Error in contradiction resolution command: {e}", exc_info=True)
        if json_output:
            return {
                "status": "error",
                "message": f"Error resolving contradictions: {str(e)}"
            }
        else:
            console.print(f"[bold red]Error resolving contradictions:[/bold red] {e}")
            return None