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

# Import CLI utilities
from arangodb.core.utils.cli.formatters import (
    console, 
    format_output, 
    add_output_option,
    format_error,
    format_success,
    format_warning,
    format_info,
    OutputFormat
)

# Import dependency checker for graceful handling of missing dependencies
from arangodb.core.utils.dependency_checker import (
    HAS_ARANGO,
    check_dependency
)

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
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """
    Create a link (edge) between two lessons.

    *WHEN TO USE:* Use after analysis suggests a meaningful connection exists 
    between two lessons. Choose the correct `relationship_type` and provide 
    a clear `rationale`.

    *HOW TO USE:* Provide the source and target document keys, relationship type,
    and rationale. Optionally add additional attributes as a JSON string.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    logger.info(f"CLI: Creating relationship from '{from_key}' to '{to_key}' of type '{relationship_type}'")
    db = get_db_connection()
    
    # Parse attributes if provided
    edge_attributes = {}
    if attributes:
        try:
            edge_attributes = json.loads(attributes)
            if not isinstance(edge_attributes, dict):
                console.print(format_error("Attributes must be a valid JSON object."))
                raise typer.Exit(code=1)
        except json.JSONDecodeError as e:
            console.print(format_error("Error parsing attributes JSON", str(e)))
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
            if output_format == "json":
                console.print(format_output(meta, output_format=output_format))
            else:
                console.print(format_success("Relationship created successfully."))
                
                # Prepare table data
                headers = ["Property", "Value"]
                rows = [
                    ["From", from_key],
                    ["To", to_key],
                    ["Type", relationship_type],
                    ["Edge Key", meta.get('_key', 'Unknown')]
                ]
                
                formatted_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=headers,
                    title="Relationship Details"
                )
                console.print(formatted_output)
        else:
            console.print(format_error("Failed to create relationship (check logs for details)."))
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Add relationship failed in CLI: {e}", exc_info=True)
        console.print(format_error("Error during add-relationship operation", str(e)))
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
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """
    Remove a specific link (edge) between lessons.

    *WHEN TO USE:* Use when a previously established relationship is found to be 
    incorrect or no longer relevant.

    *HOW TO USE:* Provide the `_key` of the relationship edge document.
    Use the `--yes` flag to skip the confirmation prompt.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    logger.info(f"CLI: Attempting to delete relationship with key '{edge_key}'")
    db = get_db_connection()
    
    # Get the edge first to confirm it exists and show info
    try:
        edge = get_edge(db, EDGE_COLLECTION_NAME, edge_key)
        if not edge:
            message = f"Relationship with key '{edge_key}' not found in collection '{EDGE_COLLECTION_NAME}'."
            if output_format == "json":
                console.print(format_output({"status": "error", "message": message}, output_format=output_format))
            else:
                console.print(format_warning(message))
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Error checking edge before delete: {e}", exc_info=True)
        if output_format == "json":
            console.print(format_output({"status": "error", "message": str(e)}, output_format=output_format))
        else:
            console.print(format_error(str(e)))
        raise typer.Exit(code=1)
    
    # Confirm deletion
    if not yes:
        # Extract information for confirmation
        from_id = edge.get("_from", "unknown")
        to_id = edge.get("_to", "unknown")
        rel_type = edge.get("type", "unknown")
        
        console.print(format_warning("\nYou are about to delete this relationship:"))
        console.print(f"Edge Key: [cyan]{edge_key}[/cyan]")
        console.print(f"From: [cyan]{from_id}[/cyan]")
        console.print(f"To: [cyan]{to_id}[/cyan]")
        console.print(f"Type: [cyan]{rel_type}[/cyan]")
        console.print("\nThis action [bold red]cannot be undone[/bold red].")
        
        confirmation = typer.confirm("Are you sure you want to proceed?")
        if not confirmation:
            if output_format == "json":
                console.print(format_output({"status": "cancelled", "message": "Deletion cancelled by user."}, output_format=output_format))
            else:
                console.print(format_warning("Operation cancelled."))
            raise typer.Exit(code=0)
    
    # Proceed with deletion
    try:
        # Call the core layer delete_relationship_by_key function
        result = delete_relationship_by_key(db, edge_key, EDGE_COLLECTION_NAME)
        
        if result:
            if output_format == "json":
                console.print(format_output({"status": "success", "message": "Relationship deleted successfully."}, output_format=output_format))
            else:
                console.print(format_success(f"Relationship with key '{edge_key}' has been deleted."))
        else:
            if output_format == "json":
                console.print(format_output({"status": "error", "message": "Failed to delete relationship."}, output_format=output_format))
            else:
                console.print(format_error("Failed to delete relationship (check logs for details)."))
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Delete relationship failed in CLI: {e}", exc_info=True)
        if output_format == "json":
            console.print(format_output({"status": "error", "message": str(e)}, output_format=output_format))
        else:
            console.print(format_error("Error during delete operation", str(e)))
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
    output_format: str = "json"
):
    """
    Explore relationships starting from a specific node.

    *WHEN TO USE:* Use to discover connected lessons and understand the context 
    or dependencies around a specific lesson. Essential for navigating the 
    knowledge graph. Requires edges to exist.

    *HOW TO USE:* Provide the starting node ID and traversal parameters like
    direction and depth.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    logger.info(f"CLI: Traversing graph from '{start_node_id}'")
    db = get_db_connection()
    
    # Validate direction
    valid_directions = ["OUTBOUND", "INBOUND", "ANY"]
    if direction not in valid_directions:
        console.print(format_error(f"Invalid direction '{direction}'. Must be one of: {', '.join(valid_directions)}"))
        raise typer.Exit(code=1)
    
    try:
        # Call the core layer graph_traverse function
        results = graph_traverse(
            db,
            start_node_id,
            min_depth=min_depth,
            max_depth=max_depth,
            direction=direction,
            limit=limit,
            graph_name=graph_name
        )
        
        if output_format == "json":
            console.print(format_output(results, output_format=output_format))
        else:
            # Display results in a readable format
            paths = results.get("paths", [])
            if not paths:
                console.print(format_warning("No paths found. Check if the starting node exists and has connections."))
                raise typer.Exit(code=0)
            
            # For table format, show path summaries
            if output_format == "table":
                console.print(format_info(f"Graph Traversal Results (found {len(paths)} paths)"))
                console.print(format_info(f"Starting from: {start_node_id}"))
                console.print(format_info(f"Direction: {direction}, Depth: {min_depth}-{max_depth}"))
                
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
            else:
                # For CSV/text, create tabular summary
                headers = ["Path", "Vertices", "Depth", "Start", "End"]
                rows = []
                
                for i, path in enumerate(paths):
                    vertices = path.get("vertices", [])
                    start_vertex = vertices[0] if vertices else {}
                    end_vertex = vertices[-1] if vertices else {}
                    
                    rows.append([
                        f"Path {i+1}",
                        str(len(vertices)),
                        str(len(path.get("edges", []))),
                        start_vertex.get("_id", "unknown"),
                        end_vertex.get("_id", "unknown")
                    ])
                
                formatted_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=headers,
                    title="Graph Traversal Summary"
                )
                console.print(formatted_output)
            
    except Exception as e:
        logger.error(f"Graph traversal failed in CLI: {e}", exc_info=True)
        if output_format == "json":
            console.print(format_output({"status": "error", "message": str(e)}, output_format=output_format))
        else:
            console.print(format_error("Error during traversal", str(e)))
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