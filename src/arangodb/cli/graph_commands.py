"""
ArangoDB CLI Graph Commands

This module provides command-line interface for graph operations using
the core business logic layer. It handles CLI argument parsing, validation,
and presentation of results for graph traversal and relationship management.

Graph commands include:
- Adding relationships between documents
- Deleting relationships
- Graph traversal from a starting node
- Graph visualization helpers

Each function follows consistent parameter patterns and error handling to
ensure a robust CLI experience.

Sample Input:
- CLI command: arangodb graph add-relationship doc123 doc456 --type RELATED --rationale "Similar topics"
- CLI command: arangodb graph traverse lessons_learned/doc123 --direction ANY --max-depth 2

Expected Output:
- Console-formatted tables or JSON output of graph operations
"""

import typer
import json
import sys
from typing import List, Optional, Dict, Any, Union
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.json import JSON

# Import dependency checker for graceful handling of missing dependencies
from arangodb.core.utils.dependency_checker import (
    HAS_ARANGO,
    check_dependency
)

# Check for UI dependencies
HAS_RICH = "rich" in sys.modules
HAS_TYPER = "typer" in sys.modules

# Import from core layer - note how we now use the core layer directly
from arangodb.core.graph import (
    create_relationship,
    delete_relationship_by_key,
    graph_traverse
)

# Import constants from core
from arangodb.core.constants import (
    COLLECTION_NAME,
    EDGE_COLLECTION_NAME,
    GRAPH_NAME
)

# Import connection utilities
from arangodb.cli.db_connection import get_db_connection

# Initialize Rich console
console = Console()

# Create the Graph app command group
graph_app = typer.Typer(
    name="graph", 
    help="Manage relationships and graph traversal operations."
)


@graph_app.command("add-relationship")
def cli_add_relationship(
    from_key: str = typer.Argument(..., help="The _key of the source lesson document."),
    to_key: str = typer.Argument(..., help="The _key of the target lesson document."),
    rationale: str = typer.Option(
        ..., "--rationale", "-r", help="Explanation of why these lessons are linked."
    ),
    relationship_type: str = typer.Option(
        ..., "--type", "-typ", help="The category of the relationship (e.g., RELATED, DUPLICATE, PREREQUISITE, CAUSAL)."
    ),
    attributes: Optional[str] = typer.Option(
        None,
        "--attributes",
        "-a",
        help="Additional properties as a JSON string (e.g., '{\"confidence\": 0.9}').",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output metadata as JSON."
    ),
):
    """
    Create a link (edge) between two lessons.

    *WHEN TO USE:* Use after analysis suggests a meaningful connection exists 
    between two lessons. Choose the correct `relationship_type` and provide 
    a clear `rationale`.

    *HOW TO USE:* Provide the source and target document keys, relationship type,
    and rationale. Optionally add additional attributes as a JSON string.
    """
    logger.info(f"CLI: Creating relationship from '{from_key}' to '{to_key}' of type '{relationship_type}'")
    db = get_db_connection()
    
    # Parse attributes if provided
    edge_attributes = {}
    if attributes:
        try:
            edge_attributes = json.loads(attributes)
            if not isinstance(edge_attributes, dict):
                console.print("[bold red]Error:[/bold red] Attributes must be a valid JSON object.")
                raise typer.Exit(code=1)
        except json.JSONDecodeError as e:
            console.print(f"[bold red]Error parsing attributes JSON:[/bold red] {e}")
            raise typer.Exit(code=1)
    
    try:
        # Call the core layer create_relationship function with correct parameters
        meta = create_relationship(
            db,
            from_key,  # Pass the key directly, not the full ID 
            to_key,    # Pass the key directly, not the full ID
            relationship_type,
            rationale, 
            edge_attributes  # Additional attributes (optional)
        )
        
        if meta:
            output = meta
            if json_output:
                print(json.dumps(output))
            else:
                console.print(
                    f"[green]Success:[/green] Relationship created successfully."
                )
                console.print(f"  From: [cyan]{from_key}[/cyan]")
                console.print(f"  To: [cyan]{to_key}[/cyan]")
                console.print(f"  Type: [cyan]{relationship_type}[/cyan]")
                console.print(f"  Edge Key: [cyan]{meta.get('_key', 'Unknown')}[/cyan]")
        else:
            console.print(
                "[bold red]Error:[/bold red] Failed to create relationship (check logs for details)."
            )
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Add relationship failed in CLI: {e}", exc_info=True)
        console.print(f"[bold red]Error during add-relationship operation:[/bold red] {e}")
        raise typer.Exit(code=1)


@graph_app.command("delete-relationship")
def cli_delete_relationship(
    edge_key: str = typer.Argument(..., help="The _key of the relationship edge document."),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt and delete immediately.",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output result as JSON."
    ),
):
    """
    Remove a specific link (edge) between lessons.

    *WHEN TO USE:* Use when a previously established relationship is found to be 
    incorrect or no longer relevant.

    *HOW TO USE:* Provide the `_key` of the relationship edge document.
    Use the `--yes` flag to skip the confirmation prompt.
    """
    logger.info(f"CLI: Attempting to delete relationship with key '{edge_key}'")
    db = get_db_connection()
    
    # Get the edge first to confirm it exists and show info
    try:
        edge = get_edge(db, EDGE_COLLECTION_NAME, edge_key)
        if not edge:
            message = f"Relationship with key '{edge_key}' not found in collection '{EDGE_COLLECTION_NAME}'."
            if json_output:
                print(json.dumps({"status": "error", "message": message}))
            else:
                console.print(f"[yellow]Not Found:[/yellow] {message}")
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Error checking edge before delete: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    
    # Confirm deletion
    if not yes:
        # Extract information for confirmation
        from_id = edge.get("_from", "unknown")
        to_id = edge.get("_to", "unknown")
        rel_type = edge.get("type", "unknown")
        
        console.print("\n[bold yellow]Warning:[/bold yellow] You are about to delete this relationship:")
        console.print(f"Edge Key: [cyan]{edge_key}[/cyan]")
        console.print(f"From: [cyan]{from_id}[/cyan]")
        console.print(f"To: [cyan]{to_id}[/cyan]")
        console.print(f"Type: [cyan]{rel_type}[/cyan]")
        console.print("\nThis action [bold red]cannot be undone[/bold red].")
        
        confirmation = typer.confirm("Are you sure you want to proceed?")
        if not confirmation:
            if json_output:
                print(json.dumps({"status": "cancelled", "message": "Deletion cancelled by user."}))
            else:
                console.print("[yellow]Operation cancelled.[/yellow]")
            raise typer.Exit(code=0)
    
    # Proceed with deletion
    try:
        # Call the core layer delete_relationship_by_key function
        result = delete_relationship_by_key(db, EDGE_COLLECTION_NAME, edge_key)
        
        if result:
            if json_output:
                print(json.dumps({"status": "success", "message": "Relationship deleted successfully."}))
            else:
                console.print(f"[green]Success:[/green] Relationship with key '{edge_key}' has been deleted.")
        else:
            if json_output:
                print(json.dumps({"status": "error", "message": "Failed to delete relationship."}))
            else:
                console.print("[bold red]Error:[/bold red] Failed to delete relationship (check logs for details).")
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Delete relationship failed in CLI: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]Error during delete operation:[/bold red] {e}")
        raise typer.Exit(code=1)


@graph_app.command("traverse")
def cli_traverse_graph(
    start_node_id: str = typer.Argument(
        ..., help="The full _id of the starting node (e.g., 'lessons_learned/123')."
    ),
    graph_name: str = typer.Option(
        GRAPH_NAME, "--graph-name", "-g", help="Name of the graph to traverse."
    ),
    min_depth: int = typer.Option(
        1, "--min-depth", help="Minimum traversal depth.", min=0
    ),
    max_depth: int = typer.Option(
        2, "--max-depth", help="Maximum traversal depth.", min=1
    ),
    direction: str = typer.Option(
        "OUTBOUND",
        "--direction",
        "-dir",
        help="Traversal direction (OUTBOUND, INBOUND, ANY).",
    ),
    limit: int = typer.Option(
        100, "--limit", "-lim", help="Maximum number of results.", min=1
    ),
    json_output: bool = typer.Option(
        True, "--json-output", "-j", help="Output as JSON (default for traverse)."
    ),
):
    """
    Explore relationships starting from a specific node.

    *WHEN TO USE:* Use to discover connected lessons and understand the context 
    or dependencies around a specific lesson. Essential for navigating the 
    knowledge graph. Requires edges to exist.

    *HOW TO USE:* Provide the starting node ID and traversal parameters like
    direction and depth.
    """
    logger.info(f"CLI: Traversing graph from '{start_node_id}'")
    db = get_db_connection()
    
    # Validate direction
    valid_directions = ["OUTBOUND", "INBOUND", "ANY"]
    if direction not in valid_directions:
        console.print(
            f"[bold red]Error:[/bold red] Invalid direction '{direction}'. Must be one of: {', '.join(valid_directions)}"
        )
        raise typer.Exit(code=1)
    
    try:
        # Call the core layer graph_traverse function
        results = graph_traverse(
            db,
            start_node_id,
            graph_name,
            direction=direction,
            min_depth=min_depth,
            max_depth=max_depth,
            limit=limit
        )
        
        if json_output:
            print(json.dumps(results, indent=2))
        else:
            # Display results in a readable format
            paths = results.get("paths", [])
            if not paths:
                console.print("[yellow]No paths found.[/yellow] Check if the starting node exists and has connections.")
                raise typer.Exit(code=0)
            
            console.print(f"[bold green]Graph Traversal Results[/bold green] (found {len(paths)} paths)")
            console.print(f"Starting from: [cyan]{start_node_id}[/cyan]")
            console.print(f"Direction: [cyan]{direction}[/cyan], Depth: [cyan]{min_depth}-{max_depth}[/cyan]")
            
            # Display each path
            for i, path in enumerate(paths):
                console.print(f"\n[bold]Path {i+1}:[/bold]")
                
                # Display vertices and edges in the path
                vertices = path.get("vertices", [])
                edges = path.get("edges", [])
                
                for j, vertex in enumerate(vertices):
                    # Extract vertex info
                    v_id = vertex.get("_id", "unknown")
                    v_title = vertex.get("title", vertex.get("summary", "No title"))
                    
                    console.print(f"  [cyan]Vertex {j+1}:[/cyan] {v_id} - {v_title}")
                    
                    # Display connecting edge if there is one
                    if j < len(edges):
                        edge = edges[j]
                        e_type = edge.get("type", "unknown")
                        e_rationale = edge.get("rationale", "No rationale")
                        
                        console.print(f"  └─ [yellow]Edge:[/yellow] {e_type} - {e_rationale}")
            
    except Exception as e:
        logger.error(f"Graph traversal failed in CLI: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]Error during traversal:[/bold red] {e}")
        raise typer.Exit(code=1)


# Helper function to get edge by key
def get_edge(db, edge_collection, edge_key):
    """Get an edge document by its key."""
    try:
        return db.collection(edge_collection).get(edge_key)
    except Exception as e:
        logger.error(f"Failed to get edge '{edge_key}': {e}")
        return None


# Expose the Graph app for use in the main CLI
def get_graph_app():
    """Get the Graph app Typer instance for use in the main CLI."""
    return graph_app


if __name__ == "__main__":
    """
    Self-validation tests for the graph_commands module.
    
    This validation checks for dependencies and performs appropriate tests
    regardless of whether ArangoDB and other dependencies are available.
    """
    import sys
    
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List of validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Check dependency checker imports
    total_tests += 1
    try:
        test_result = "HAS_ARANGO" in globals() and "check_dependency" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import dependency checker flags")
        else:
            print(f"✓ Dependency flags: HAS_ARANGO = {HAS_ARANGO}")
    except Exception as e:
        all_validation_failures.append(f"Dependency checker validation failed: {e}")
    
    # Test 2: Check UI dependency detection
    total_tests += 1
    try:
        test_result = "HAS_RICH" in globals() and "HAS_TYPER" in globals()
        if not test_result:
            all_validation_failures.append("Failed to check UI dependencies")
        else:
            print(f"✓ UI dependency flags: HAS_RICH = {HAS_RICH}, HAS_TYPER = {HAS_TYPER}")
    except Exception as e:
        all_validation_failures.append(f"UI dependency validation failed: {e}")
    
    # Test 3: Check core graph function imports
    total_tests += 1
    try:
        # Test import paths
        test_result = "create_relationship" in globals() and "delete_relationship_by_key" in globals() and "graph_traverse" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import core graph functions")
        else:
            print("✓ Core graph functions imported successfully")
    except Exception as e:
        all_validation_failures.append(f"Import validation failed: {e}")
    
    # Test 4: Verify Typer setup
    total_tests += 1
    try:
        # Check that we have commands registered
        commands = [c.name for c in graph_app.registered_commands]
        expected_commands = ["add-relationship", "delete-relationship", "traverse"]
        
        missing_commands = [cmd for cmd in expected_commands if cmd not in commands]
        if missing_commands:
            all_validation_failures.append(f"Missing commands: {missing_commands}")
        else:
            print(f"✓ All required commands ({', '.join(expected_commands)}) are registered")
    except Exception as e:
        all_validation_failures.append(f"Typer command validation failed: {e}")
    
    # Display validation results
    if all_validation_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Module validated and ready for use")
        sys.exit(0)