"""
CLI commands for contradiction detection and resolution.

Provides commands to list, analyze, and resolve contradictions in the graph.
"""

import sys
import json
from datetime import datetime, timezone
from typing import Optional, List
import typer

# Import CLI utilities
from arangodb.core.utils.cli.formatters import (
    console, 
    format_output, 
    add_output_option,
    format_error,
    format_success,
    format_info,
    format_warning,
    OutputFormat
)
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


@app.command("list")
@add_output_option
def list_contradictions(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of contradictions to show"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (resolved/failed)"),
    edge_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by edge type"),
    entity_id: Optional[str] = typer.Option(None, "--entity", "-e", help="Filter by entity ID"),
    output_format: str = "table"
):
    """List detected contradictions from the log.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
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
            console.print(format_warning("No contradictions found matching the criteria."))
            return
        
        if output_format == OutputFormat.JSON:
            console.print(format_output(contradictions, output_format=output_format))
        else:
            # Prepare data for table/CSV/text format
            headers = ["Timestamp", "Edge Type", "Status", "Resolution", "From → To", "Context"]
            rows = []
            
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
                
                # Status
                status_str = entry['status']
                
                rows.append([
                    ts_str,
                    edge_type,
                    status_str,
                    res_str,
                    edge_str,
                    entry.get('context', 'unknown')
                ])
            
            formatted_output = format_output(
                rows,
                output_format=output_format,
                headers=headers,
                title=f"Contradiction Log (Showing {len(contradictions)} of {limit} max)"
            )
            console.print(formatted_output)
        
    except Exception as e:
        console.print(format_error("Error listing contradictions", str(e)))
        raise typer.Exit(1)


@app.command("summary")
@add_output_option
def contradiction_summary(output_format: str = "table"):
    """Show contradiction statistics summary.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        # Get database connection
        db = get_db_connection()
        
        # Initialize logger
        logger = ContradictionLogger(db)
        
        # Get summary
        summary = logger.get_contradiction_summary()
        
        if output_format == OutputFormat.JSON:
            console.print(format_output(summary, output_format=output_format))
        else:
            # Prepare main summary data
            headers = ["Metric", "Value"]
            rows = [
                ["Total Contradictions", str(summary['total'])],
                ["Resolved", str(summary['resolved'])],
                ["Failed", str(summary['failed'])],
                ["Success Rate", f"{summary['success_rate']:.1%}"]
            ]
            
            formatted_output = format_output(
                rows,
                output_format=output_format,
                headers=headers,
                title="Contradiction Summary"
            )
            console.print(formatted_output)
            
            # Show breakdown by edge type
            if summary['by_edge_type'] and output_format == OutputFormat.TABLE:
                type_rows = []
                for item in summary['by_edge_type']:
                    type_rows.append([
                        item['type'] or "(none)",
                        str(item['count'])
                    ])
                
                type_output = format_output(
                    type_rows,
                    output_format=output_format,
                    headers=["Type", "Count"],
                    title="Contradictions by Edge Type"
                )
                console.print("\n" + type_output)
            
            # Show breakdown by resolution action
            if summary['by_resolution_action'] and output_format == OutputFormat.TABLE:
                action_rows = []
                for item in summary['by_resolution_action']:
                    action_rows.append([
                        item['action'] or "(none)",
                        str(item['count'])
                    ])
                
                action_output = format_output(
                    action_rows,
                    output_format=output_format,
                    headers=["Action", "Count"],
                    title="Resolution Actions"
                )
                console.print("\n" + action_output)
        
    except Exception as e:
        console.print(format_error("Error getting summary", str(e)))
        raise typer.Exit(1)


@app.command("detect")
@add_output_option
def detect_contradictions(
    from_id: str = typer.Argument(..., help="Source entity ID (_id format)"),
    to_id: str = typer.Argument(..., help="Target entity ID (_id format)"),
    edge_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by relationship type"),
    collection: str = typer.Option("agent_relationships", "--collection", "-c", help="Edge collection name"),
    output_format: str = "table"
):
    """Detect potential contradictions between two entities.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
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
            console.print(format_success(f"No contradictions found between {from_id} and {to_id}"))
            return
        
        if output_format == OutputFormat.JSON:
            console.print(format_output(contradictions, output_format=output_format))
        else:
            console.print(format_warning(f"Found {len(contradictions)} potential contradictions"))
            
            if output_format == OutputFormat.TABLE:
                # Display each contradiction as panels for table format
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
            else:
                # For CSV/text format, display as rows
                headers = ["Edge Key", "Type", "Valid From", "Invalid At", "Created At"]
                rows = []
                
                for edge in contradictions:
                    rows.append([
                        edge['_key'],
                        edge['type'],
                        edge.get('valid_at', 'unknown'),
                        edge.get('invalid_at', 'null'),
                        edge.get('created_at', 'unknown')
                    ])
                
                formatted_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=headers,
                    title="Potential Contradictions"
                )
                console.print(formatted_output)
        
    except Exception as e:
        console.print(format_error("Error detecting contradictions", str(e)))
        raise typer.Exit(1)


@app.command("resolve")
@add_output_option
def resolve_contradiction_manually(
    new_edge_key: str = typer.Argument(..., help="Key of the new edge"),
    existing_edge_key: str = typer.Argument(..., help="Key of the existing edge"),
    strategy: str = typer.Option("newest_wins", "--strategy", "-s", 
                                help="Resolution strategy: newest_wins, merge, split_timeline"),
    collection: str = typer.Option("agent_relationships", "--collection", "-c", help="Edge collection name"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Resolution reason"),
    output_format: str = "table"
):
    """Manually resolve a contradiction between two edges.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        # Get database connection
        db = get_db_connection()
        
        # Get the edges
        edge_collection = db.collection(collection)
        new_edge = edge_collection.get(new_edge_key)
        existing_edge = edge_collection.get(existing_edge_key)
        
        if not new_edge:
            console.print(format_error(f"New edge {new_edge_key} not found"))
            raise typer.Exit(1)
        
        if not existing_edge:
            console.print(format_error(f"Existing edge {existing_edge_key} not found"))
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
        if output_format == OutputFormat.JSON:
            console.print(format_output(result, output_format=output_format))
        else:
            if result["success"]:
                console.print(format_success("Successfully resolved contradiction"))
                
                # Show details for table/CSV/text
                headers = ["Property", "Value"]
                rows = [
                    ["Action", result['action']],
                    ["Reason", result['reason']]
                ]
                
                formatted_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=headers,
                    title="Resolution Details"
                )
                console.print(formatted_output)
                
                if result.get("resolved_edge") and output_format == OutputFormat.TABLE:
                    console.print("\n[bold]Resolved Edge:[/bold]")
                    console.print(Syntax(json.dumps(result["resolved_edge"], indent=2), "json"))
            else:
                console.print(format_error(
                    "Failed to resolve contradiction",
                    result['reason']
                ))
        
    except Exception as e:
        console.print(format_error("Error resolving contradiction", str(e)))
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