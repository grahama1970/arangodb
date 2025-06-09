"""
Example CLI Command using the formatters module with output format support.
Module: cli_command.py
Description: Functions for cli command operations

This module demonstrates how to integrate the CLI formatters module into a Typer command,
making it easy to switch between output formats with the --output option.
"""

import typer
from typing import List, Dict, Any, Optional
from loguru import logger

# Import CLI utilities
from arangodb.core.utils.cli import (
    console, 
    format_success, 
    format_error, 
    format_output,
    add_output_option
)

# Import business logic
from arangodb.core.memory.memory_agent import MemoryAgent
from arangodb.cli.db_connection import get_db_connection

# Create a Typer app for the CLI command
app = typer.Typer(help="Example command using formatters")

@app.command("list")
@add_output_option  # This adds the --output/-o option automatically
def list_items(
    limit: int = typer.Option(
        10, "--limit", "-n", help="Maximum number of items to return.", min=1
    ),
    filter_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter by item type."
    ),
    output_format: str = "table",  # Added by the add_output_option decorator
):
    """
    List items with support for multiple output formats.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        # Get database connection
        db = get_db_connection()
        
        # Initialize memory agent
        memory_agent = MemoryAgent(db)
        
        # Get items (this is just an example implementation)
        items = memory_agent.get_items(limit=limit, item_type=filter_type)
        
        # Define custom metadata for different output formats
        title = f"Items{f' of type {filter_type}' if filter_type else ''}"
        headers = ["ID", "Type", "Created At", "Content Preview"]
        
        # Format the items for display
        rows = []
        for item in items:
            # Extract item data
            item_id = item.get("_key", "N/A")
            item_type = item.get("type", "unknown")
            created_at = item.get("created_at", "N/A")
            
            # Create content preview
            content = item.get("content", "")
            preview = (content[:47] + "...") if len(content) > 50 else content
            
            # Add row
            rows.append([item_id, item_type, created_at, preview])
        
        # Format output according to requested format
        formatted_output = format_output(
            rows,
            output_format=output_format,
            headers=headers,
            title=title
        )
        
        # Print the formatted output
        console.print(formatted_output)
        
    except Exception as e:
        logger.error(f"Error listing items: {e}", exc_info=True)
        console.print(format_error(
            "Failed to list items",
            str(e)
        ))
        raise typer.Exit(code=1)


@app.command("get")
@add_output_option
def get_item(
    item_id: str = typer.Argument(..., help="ID of the item to retrieve."),
    include_metadata: bool = typer.Option(
        False, "--metadata", "-m", help="Include metadata in the output."
    ),
    output_format: str = "table",  # Added by the add_output_option decorator
):
    """
    Get details of a specific item.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        # Get database connection
        db = get_db_connection()
        
        # Initialize memory agent
        memory_agent = MemoryAgent(db)
        
        # Get the item
        item = memory_agent.get_item(item_id)
        
        if not item:
            console.print(format_error(f"Item not found: {item_id}"))
            raise typer.Exit(code=1)
        
        # Handle different output formats
        if output_format == "json":
            # For JSON, return the entire item
            console.print(format_output(item, output_format="json"))
        elif output_format == "text":
            # For text, show a simplified view
            console.print(f"Item ID: {item.get('_key', 'N/A')}")
            console.print(f"Type: {item.get('type', 'unknown')}")
            console.print(f"Created: {item.get('created_at', 'N/A')}")
            console.print(f"Content: {item.get('content', '')}")
            
            if include_metadata and "metadata" in item:
                console.print("\nMetadata:")
                for key, value in item["metadata"].items():
                    console.print(f"  {key}: {value}")
        else:
            # For table and CSV, structure the data
            if include_metadata and "metadata" in item:
                # Create rows from metadata
                rows = []
                for key, value in item["metadata"].items():
                    rows.append([key, str(value)])
                
                metadata_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=["Property", "Value"],
                    title=f"Item {item_id} Metadata"
                )
                
                # First show the item details
                item_data = [
                    ["ID", item.get("_key", "N/A")],
                    ["Type", item.get("type", "unknown")],
                    ["Created At", item.get("created_at", "N/A")],
                    ["Content", item.get("content", "")]
                ]
                
                item_output = format_output(
                    item_data,
                    output_format=output_format,
                    headers=["Property", "Value"],
                    title=f"Item {item_id} Details"
                )
                
                console.print(item_output)
                console.print("\n")
                console.print(metadata_output)
            else:
                # Just show the item details
                item_data = [
                    ["ID", item.get("_key", "N/A")],
                    ["Type", item.get("type", "unknown")],
                    ["Created At", item.get("created_at", "N/A")],
                    ["Content", item.get("content", "")]
                ]
                
                console.print(format_output(
                    item_data,
                    output_format=output_format,
                    headers=["Property", "Value"],
                    title=f"Item {item_id} Details"
                ))
        
    except Exception as e:
        logger.error(f"Error retrieving item: {e}", exc_info=True)
        console.print(format_error(
            f"Failed to retrieve item: {item_id}",
            str(e)
        ))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    """Direct execution for testing."""
    app()
