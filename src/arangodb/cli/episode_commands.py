"""
Episode Commands for ArangoDB Memory System CLI

This module provides CLI commands for managing episodes - temporal groupings
of conversations and interactions in the memory system.
"""

import json
from datetime import datetime, timezone
from typing import Optional
import typer
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
from rich.panel import Panel

from .db_connection import get_db_connection
from ..core.memory.episode_manager import EpisodeManager

# Initialize Typer app
app = typer.Typer(name="episode", help="Manage conversation episodes")


@app.command("create")
def create_episode(
    name: str = typer.Argument(..., help="Name/title of the episode"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Episode description"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="User ID for the episode"),
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID for the episode"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """Create a new episode for grouping conversations.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        # Build metadata
        metadata = {}
        if user_id:
            metadata["user_id"] = user_id
        if session_id:
            metadata["session_id"] = session_id
        
        # Create episode
        episode = episode_manager.create_episode(
            name=name,
            description=description,
            metadata=metadata
        )
        
        # Display result
        console.print(format_success(f"Created episode: {episode['_key']}"))
        
        if output_format == "json":
            console.print(format_output(episode, output_format=output_format))
        else:
            headers = ["Field", "Value"]
            rows = [
                ["Key", episode["_key"]],
                ["Name", episode["name"]],
                ["Description", episode.get("description", "")],
                ["Start Time", episode["start_time"]],
                ["User ID", metadata.get("user_id", "")],
                ["Session ID", metadata.get("session_id", "")]
            ]
            
            formatted_output = format_output(
                rows,
                output_format=output_format,
                headers=headers,
                title="Episode Details"
            )
            console.print(formatted_output)
        
        return episode["_key"]
        
    except Exception as e:
        console.print(format_error("Failed to create episode", str(e)))
        raise typer.Exit(code=1)


@app.command("list")
def list_episodes(
    active_only: bool = typer.Option(False, "--active", "-a", help="Show only active episodes"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of episodes to show"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """List episodes with optional filters.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        if active_only:
            episodes = episode_manager.get_active_episodes(user_id=user_id, limit=limit)
            title = "Active Episodes"
        else:
            # For now, we'll use search with empty query to get all episodes
            episodes = episode_manager.search_episodes("", user_id=user_id, limit=limit)
            title = "All Episodes"
        
        if not episodes:
            console.print(format_warning("No episodes found"))
            return
        
        # Display results
        if output_format == "json":
            console.print(format_output(episodes, output_format=output_format))
        else:
            headers = ["Key", "Name", "Status", "Start Time", "Entities", "Relations"]
            rows = []
            
            for episode in episodes:
                status = "Active" if episode.get("end_time") is None else "Ended"
                rows.append([
                    episode["_key"],
                    episode["name"],
                    status,
                    episode["start_time"],
                    str(episode.get("entity_count", 0)),
                    str(episode.get("relationship_count", 0))
                ])
            
            formatted_output = format_output(
                rows,
                output_format=output_format,
                headers=headers,
                title=title
            )
            console.print(formatted_output)
            console.print(format_info(f"Showing {len(episodes)} episodes"))
        
    except Exception as e:
        console.print(format_error("Failed to list episodes", str(e)))
        raise typer.Exit(code=1)


@app.command("search")
def search_episodes(
    query: str = typer.Argument(..., help="Search query for episode names/descriptions"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """Search episodes by text query.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        episodes = episode_manager.search_episodes(
            query_text=query,
            user_id=user_id,
            limit=limit
        )
        
        if not episodes:
            console.print(format_warning(f"No episodes found matching '{query}'"))
            return
        
        # Display results
        if output_format == "json":
            console.print(format_output(episodes, output_format=output_format))
        else:
            headers = ["Key", "Name", "Description", "Start Time"]
            rows = []
            
            for episode in episodes:
                desc = episode.get("description", "")
                desc_preview = desc[:40] + "..." if desc and len(desc) > 40 else desc
                rows.append([
                    episode["_key"],
                    episode["name"],
                    desc_preview,
                    episode["start_time"]
                ])
            
            formatted_output = format_output(
                rows,
                output_format=output_format,
                headers=headers,
                title=f"Search Results for '{query}'"
            )
            console.print(formatted_output)
            console.print(format_info(f"Found {len(episodes)} matching episodes"))
        
    except Exception as e:
        console.print(format_error("Failed to search episodes", str(e)))
        raise typer.Exit(code=1)


@app.command("get")
def get_episode(
    episode_id: str = typer.Argument(..., help="Episode ID or key to retrieve"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """Get detailed information about a specific episode.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        episode = episode_manager.get_episode(episode_id)
        
        if not episode:
            console.print(format_error(f"Episode '{episode_id}' not found"))
            raise typer.Exit(code=1)
        
        # Get linked entities and relationships
        entities = episode_manager.get_episode_entities(episode_id)
        relationships = episode_manager.get_episode_relationships(episode_id)
        
        if output_format == "json":
            # Add entities and relationships to episode for JSON output
            episode["entities"] = entities
            episode["relationships"] = relationships
            console.print(format_output(episode, output_format=output_format))
        else:
            # Display episode details
            headers = ["Field", "Value"]
            rows = [
                ["Key", episode['_key']],
                ["Name", episode['name']],
                ["Description", episode.get('description', '')],
                ["Status", 'Active' if episode.get('end_time') is None else 'Ended'],
                ["Start Time", episode['start_time']],
                ["End Time", episode.get('end_time', 'N/A')],
                ["Entities", str(len(entities))],
                ["Relationships", str(len(relationships))],
                ["Metadata", json.dumps(episode.get('metadata', {}), indent=2)]
            ]
            
            formatted_output = format_output(
                rows,
                output_format=output_format,
                headers=headers,
                title=f"Episode: {episode['_key']}"
            )
            console.print(formatted_output)
            
            # Display entities if any (for table format only)
            if entities and output_format == "table":
                console.print("\n[bold cyan]Linked Entities:[/bold cyan]")
                entity_headers = ["Key", "Name", "Type"]
                entity_rows = []
                
                for entity in entities[:5]:  # Show first 5
                    entity_rows.append([
                        entity["_key"],
                        entity.get("name", ""),
                        entity.get("type", "")
                    ])
                
                entity_output = format_output(
                    entity_rows,
                    output_format=output_format,
                    headers=entity_headers,
                    title="Linked Entities"
                )
                console.print(entity_output)
                
                if len(entities) > 5:
                    console.print(format_info(f"... and {len(entities) - 5} more entities"))
        
    except Exception as e:
        console.print(format_error("Failed to get episode", str(e)))
        raise typer.Exit(code=1)


@app.command("end")
def end_episode(
    episode_id: str = typer.Argument(..., help="Episode ID or key to end"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """Mark an episode as ended.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        episode = episode_manager.end_episode(episode_id)
        
        if output_format == "json":
            console.print(format_output(episode, output_format=output_format))
        else:
            console.print(format_success(f"Ended episode: {episode['_key']}"))
            console.print(format_info(f"End time: {episode['end_time']}"))
        
    except Exception as e:
        console.print(format_error("Failed to end episode", str(e)))
        raise typer.Exit(code=1)


@app.command("delete")
def delete_episode(
    episode_id: str = typer.Argument(..., help="Episode ID or key to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """Delete an episode and all its links.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        # Get episode first to show details
        episode = episode_manager.get_episode(episode_id)
        if not episode:
            console.print(format_error(f"Episode '{episode_id}' not found"))
            raise typer.Exit(code=1)
        
        # Confirm deletion
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to delete episode '{episode['name']}'? "
                f"This will also remove all links to entities and relationships."
            )
            if not confirm:
                console.print(format_warning("Deletion cancelled"))
                return
        
        # Delete episode
        success = episode_manager.delete_episode(episode_id)
        
        if success:
            if output_format == "json":
                console.print(format_output(
                    {"status": "success", "message": f"Deleted episode: {episode['_key']}"},
                    output_format=output_format
                ))
            else:
                console.print(format_success(f"Deleted episode: {episode['_key']}"))
        else:
            console.print(format_error("Failed to delete episode"))
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(format_error("Failed to delete episode", str(e)))
        raise typer.Exit(code=1)


@app.command("link-entity")
def link_entity_to_episode(
    episode_id: str = typer.Argument(..., help="Episode ID or key"),
    entity_id: str = typer.Argument(..., help="Entity ID to link")
):
    """Link an entity to an episode."""
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        success = episode_manager.link_entity_to_episode(episode_id, entity_id)
        
        if success:
            console.print(f"[green]✓[/green] Linked entity '{entity_id}' to episode '{episode_id}'")
        else:
            console.print(f"[red]✗[/red] Failed to link entity to episode")
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to link entity: {str(e)}")
        raise typer.Exit(code=1)


@app.command("link-relationship")
def link_relationship_to_episode(
    episode_id: str = typer.Argument(..., help="Episode ID or key"),
    relationship_id: str = typer.Argument(..., help="Relationship ID to link")
):
    """Link a relationship to an episode."""
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        success = episode_manager.link_relationship_to_episode(episode_id, relationship_id)
        
        if success:
            console.print(f"[green]✓[/green] Linked relationship '{relationship_id}' to episode '{episode_id}'")
        else:
            console.print(f"[red]✗[/red] Failed to link relationship to episode")
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to link relationship: {str(e)}")
        raise typer.Exit(code=1)


# Main entry point for testing
if __name__ == "__main__":
    app()