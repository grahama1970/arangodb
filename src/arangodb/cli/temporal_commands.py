"""
Temporal Commands for ArangoDB Memory System CLI
Module: temporal_commands.py
Description: Functions for temporal commands operations

This module provides CLI commands for temporal operations including
point-in-time queries, historical views, and temporal validation.
"""

import typer
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from arangodb.core.utils.cli.formatters import (
    console,
    format_output,
    add_output_option,
    format_error,
    format_success,
    format_info,
    OutputFormat
)

from arangodb.cli.db_connection import get_db_connection
from arangodb.core.memory.memory_agent import MemoryAgent
from arangodb.core.temporal_operations import (
    get_entity_history,
    validate_temporal_consistency,
    create_temporal_indexes
)

# Initialize Typer app
app = typer.Typer(name="temporal", help="Temporal operations and queries")

@app.command("search-at-time")
def search_at_time(
    query: str = typer.Argument(..., help="Search query"),
    timestamp: str = typer.Argument(..., help="ISO timestamp to search at"),
    search_type: str = typer.Option("hybrid", "--type", "-t", help="Search type"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results"),
    conversation_id: Optional[str] = typer.Option(None, "--conversation", "-c", help="Filter by conversation"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """
    Search for messages valid at a specific point in time.
    
    USAGE:
        arangodb temporal search-at-time "AI discussion" "2024-01-01T12:00:00Z"
    
    WHEN TO USE:
        When you need to see what information was available at a specific moment
    
    OUTPUT:
        - TABLE: Results showing messages valid at that time
        - JSON: Full temporal search results
    
    EXAMPLES:
        arangodb temporal search-at-time "project status" "2024-06-01T00:00:00Z"
        arangodb temporal search-at-time "budget" "2024-03-15T14:30:00Z" --type semantic
    """
    try:
        db = get_db_connection()
        memory_agent = MemoryAgent(db)
        
        # Parse timestamp
        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Build filters
        filters = {}
        if conversation_id:
            filters['conversation_id'] = conversation_id
        
        # Perform temporal search
        results = memory_agent.search_at_time(
            query=query,
            timestamp=ts,
            search_type=search_type,
            filters=filters,
            limit=limit
        )
        
        # Format results
        if output_format == "json":
            console.print_json(data={
                "query": query,
                "timestamp": timestamp,
                "results": results,
                "count": len(results)
            })
        else:
            if results:
                headers = ["Time", "Type", "Content", "Score", "Valid At"]
                rows = []
                
                for result in results:
                    rows.append([
                        result.get('timestamp', ''),
                        result.get('type', ''),
                        result.get('content', '')[:50] + "...",
                        f"{result.get('score', 0):.3f}",
                        result.get('valid_at', '')
                    ])
                
                formatted_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=headers,
                    title=f"Search at {timestamp}"
                )
                console.print(formatted_output)
            else:
                console.print("[yellow]No results found at this point in time[/yellow]")
        
    except Exception as e:
        console.print(format_error("Temporal search failed", str(e)))
        raise typer.Exit(code=1)

@app.command("conversation-at-time")
def conversation_at_time(
    conversation_id: str = typer.Argument(..., help="Conversation ID"),
    timestamp: str = typer.Argument(..., help="ISO timestamp"),
    include_invalid: bool = typer.Option(False, "--invalid", help="Include invalidated messages"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """
    Get the state of a conversation at a specific point in time.
    
    USAGE:
        arangodb temporal conversation-at-time conv_123 "2024-01-01T12:00:00Z"
    
    WHEN TO USE:
        To see a conversation as it existed at a particular moment
    
    EXAMPLES:
        arangodb temporal conversation-at-time conv_abc "2024-06-01T00:00:00Z"
        arangodb temporal conversation-at-time conv_xyz "2024-03-15T14:30:00Z" --invalid
    """
    try:
        db = get_db_connection()
        memory_agent = MemoryAgent(db)
        
        # Parse timestamp
        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Get conversation at time
        messages = memory_agent.get_conversation_at_time(
            conversation_id=conversation_id,
            timestamp=ts,
            include_invalid=include_invalid
        )
        
        # Format results
        if output_format == "json":
            console.print_json(data={
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "messages": messages,
                "count": len(messages)
            })
        else:
            if messages:
                headers = ["Time", "Type", "Content", "Valid At", "Invalid At"]
                rows = []
                
                for msg in messages:
                    rows.append([
                        msg.get('timestamp', ''),
                        msg.get('type', ''),
                        msg.get('content', '')[:60] + "...",
                        msg.get('valid_at', ''),
                        msg.get('invalid_at', 'Active')
                    ])
                
                formatted_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=headers,
                    title=f"Conversation {conversation_id} at {timestamp}"
                )
                console.print(formatted_output)
            else:
                console.print("[yellow]No messages found at this point in time[/yellow]")
        
    except Exception as e:
        console.print(format_error("Failed to get conversation", str(e)))
        raise typer.Exit(code=1)

@app.command("range")
def temporal_range(
    start_time: str = typer.Argument(..., help="Start time (ISO format)"),
    end_time: str = typer.Argument(..., help="End time (ISO format)"),
    conversation_id: Optional[str] = typer.Option(None, "--conversation", "-c", help="Filter by conversation"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """
    Get messages within a temporal range.
    
    USAGE:
        arangodb temporal range "2024-01-01T00:00:00Z" "2024-01-31T23:59:59Z"
    
    EXAMPLES:
        arangodb temporal range "2024-06-01T00:00:00Z" "2024-06-30T23:59:59Z"
        arangodb temporal range "2024-01-01T00:00:00Z" "2024-12-31T23:59:59Z" -c conv_123
    """
    try:
        db = get_db_connection()
        memory_agent = MemoryAgent(db)
        
        # Parse timestamps
        start_ts = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_ts = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Get messages in range
        messages = memory_agent.get_temporal_range(
            start_time=start_ts,
            end_time=end_ts,
            conversation_id=conversation_id
        )
        
        # Format results
        if output_format == "json":
            console.print_json(data={
                "start_time": start_time,
                "end_time": end_time,
                "messages": messages,
                "count": len(messages)
            })
        else:
            if messages:
                headers = ["Timestamp", "Conversation", "Type", "Content"]
                rows = []
                
                for msg in messages:
                    rows.append([
                        msg.get('timestamp', ''),
                        msg.get('conversation_id', ''),
                        msg.get('type', ''),
                        msg.get('content', '')[:50] + "..."
                    ])
                
                formatted_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=headers,
                    title=f"Messages from {start_time} to {end_time}"
                )
                console.print(formatted_output)
                console.print(format_info(f"Total messages: {len(messages)}"))
            else:
                console.print("[yellow]No messages found in this time range[/yellow]")
        
    except Exception as e:
        console.print(format_error("Failed to get temporal range", str(e)))
        raise typer.Exit(code=1)

@app.command("history")
def entity_history(
    collection: str = typer.Argument(..., help="Collection name"),
    entity_key: str = typer.Argument(..., help="Entity key"),
    include_invalidated: bool = typer.Option(True, "--include-invalid", help="Include invalidated versions"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """
    Get the complete temporal history of an entity.
    
    USAGE:
        arangodb temporal history messages msg_123
    
    EXAMPLES:
        arangodb temporal history entities entity_456
        arangodb temporal history memories mem_789 --no-include-invalid
    """
    try:
        db = get_db_connection()
        
        # Get entity history
        history = get_entity_history(
            db,
            collection,
            entity_key,
            include_invalidated=include_invalidated
        )
        
        # Format results
        if output_format == "json":
            console.print_json(data={
                "entity_key": entity_key,
                "collection": collection,
                "history": history,
                "versions": len(history)
            })
        else:
            if history:
                headers = ["Version", "Valid At", "Created At", "Invalid At", "Status"]
                rows = []
                
                for idx, version in enumerate(history):
                    rows.append([
                        f"v{idx + 1}",
                        version.get('valid_at', ''),
                        version.get('created_at', ''),
                        version.get('invalid_at', 'N/A'),
                        "Invalid" if version.get('invalid_at') else "Active"
                    ])
                
                formatted_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=headers,
                    title=f"History of {collection}/{entity_key}"
                )
                console.print(formatted_output)
            else:
                console.print(f"[yellow]No history found for {entity_key}[/yellow]")
        
    except Exception as e:
        console.print(format_error("Failed to get entity history", str(e)))
        raise typer.Exit(code=1)

@app.command("validate")
def validate_temporal(
    collection: str = typer.Argument(..., help="Collection name"),
    entity_key: str = typer.Argument(..., help="Entity key")
):
    """
    Validate temporal consistency of an entity.
    
    USAGE:
        arangodb temporal validate messages msg_123
    
    EXAMPLES:
        arangodb temporal validate entities entity_456
    """
    try:
        db = get_db_connection()
        
        # Validate temporal consistency
        validation = validate_temporal_consistency(
            db,
            collection,
            entity_key
        )
        
        if validation['is_valid']:
            console.print(format_success(f"Entity {entity_key} has valid temporal state"))
        else:
            console.print(format_error(
                f"Entity {entity_key} has temporal issues",
                "\n".join(validation['errors'])
            ))
        
    except Exception as e:
        console.print(format_error("Validation failed", str(e)))
        raise typer.Exit(code=1)

@app.command("create-indexes")
def create_indexes(
    collection: str = typer.Argument(..., help="Collection name")
):
    """
    Create temporal indexes for a collection.
    
    USAGE:
        arangodb temporal create-indexes messages
    
    EXAMPLES:
        arangodb temporal create-indexes entities
    """
    try:
        db = get_db_connection()
        
        # Create temporal indexes
        create_temporal_indexes(db, collection)
        
        console.print(format_success(f"Created temporal indexes for {collection}"))
        
    except Exception as e:
        console.print(format_error("Failed to create indexes", str(e)))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()