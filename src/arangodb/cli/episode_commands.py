"""
Episode Commands for ArangoDB Memory System CLI

This module provides CLI commands for managing episodes - temporal groupings
of conversations and interactions in the memory system.
"""

import json
from datetime import datetime, timezone
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from loguru import logger

from .db_connection import get_db_connection
from ..core.memory.episode_manager import EpisodeManager

# Initialize Typer app and console
app = typer.Typer(name="episode", help="Manage conversation episodes")
console = Console()


@app.command("create")
def create_episode(
    name: str = typer.Argument(..., help="Name/title of the episode"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Episode description"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="User ID for the episode"),
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID for the episode")
):
    """Create a new episode for grouping conversations."""
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
        console.print(f"[green]✓[/green] Created episode: {episode['_key']}")
        
        table = Table(title="Episode Details", show_header=True, header_style="bold cyan")
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        table.add_row("Key", episode["_key"])
        table.add_row("Name", episode["name"])
        table.add_row("Description", episode.get("description", ""))
        table.add_row("Start Time", episode["start_time"])
        table.add_row("User ID", metadata.get("user_id", ""))
        table.add_row("Session ID", metadata.get("session_id", ""))
        
        console.print(table)
        return episode["_key"]
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create episode: {str(e)}")
        raise typer.Exit(code=1)


@app.command("list")
def list_episodes(
    active_only: bool = typer.Option(False, "--active", "-a", help="Show only active episodes"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of episodes to show")
):
    """List episodes with optional filters."""
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
            console.print(f"[yellow]No episodes found[/yellow]")
            return
        
        # Display results
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Key", style="cyan", width=20)
        table.add_column("Name", style="white", width=30)
        table.add_column("Status", style="green", width=10)
        table.add_column("Start Time", style="yellow", width=25)
        table.add_column("Entities", style="blue", width=10)
        table.add_column("Relations", style="blue", width=10)
        
        for episode in episodes:
            status = "Active" if episode.get("end_time") is None else "Ended"
            table.add_row(
                episode["_key"],
                episode["name"],
                status,
                episode["start_time"],
                str(episode.get("entity_count", 0)),
                str(episode.get("relationship_count", 0))
            )
        
        console.print(table)
        console.print(f"\nShowing {len(episodes)} episodes")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list episodes: {str(e)}")
        raise typer.Exit(code=1)


@app.command("search")
def search_episodes(
    query: str = typer.Argument(..., help="Search query for episode names/descriptions"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results")
):
    """Search episodes by text query."""
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        episodes = episode_manager.search_episodes(
            query_text=query,
            user_id=user_id,
            limit=limit
        )
        
        if not episodes:
            console.print(f"[yellow]No episodes found matching '{query}'[/yellow]")
            return
        
        # Display results
        table = Table(title=f"Search Results for '{query}'", show_header=True, header_style="bold cyan")
        table.add_column("Key", style="cyan", width=20)
        table.add_column("Name", style="white", width=30)
        table.add_column("Description", style="white", width=40)
        table.add_column("Start Time", style="yellow", width=25)
        
        for episode in episodes:
            table.add_row(
                episode["_key"],
                episode["name"],
                episode.get("description", "")[:40] + "..." if episode.get("description", "") else "",
                episode["start_time"]
            )
        
        console.print(table)
        console.print(f"\nFound {len(episodes)} matching episodes")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to search episodes: {str(e)}")
        raise typer.Exit(code=1)


@app.command("get")
def get_episode(
    episode_id: str = typer.Argument(..., help="Episode ID or key to retrieve")
):
    """Get detailed information about a specific episode."""
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        episode = episode_manager.get_episode(episode_id)
        
        if not episode:
            console.print(f"[red]Episode '{episode_id}' not found[/red]")
            raise typer.Exit(code=1)
        
        # Get linked entities and relationships
        entities = episode_manager.get_episode_entities(episode_id)
        relationships = episode_manager.get_episode_relationships(episode_id)
        
        # Display episode details
        panel = Panel.fit(
            f"[bold cyan]Episode: {episode['_key']}[/bold cyan]\n\n"
            f"[bold]Name:[/bold] {episode['name']}\n"
            f"[bold]Description:[/bold] {episode.get('description', '')}\n"
            f"[bold]Status:[/bold] {'Active' if episode.get('end_time') is None else 'Ended'}\n"
            f"[bold]Start Time:[/bold] {episode['start_time']}\n"
            f"[bold]End Time:[/bold] {episode.get('end_time', 'N/A')}\n"
            f"[bold]Entities:[/bold] {len(entities)}\n"
            f"[bold]Relationships:[/bold] {len(relationships)}\n"
            f"[bold]Metadata:[/bold] {json.dumps(episode.get('metadata', {}), indent=2)}",
            title="Episode Details",
            border_style="cyan"
        )
        console.print(panel)
        
        # Display entities if any
        if entities:
            console.print("\n[bold cyan]Linked Entities:[/bold cyan]")
            entity_table = Table(show_header=True, header_style="bold")
            entity_table.add_column("Key", style="cyan")
            entity_table.add_column("Name", style="white")
            entity_table.add_column("Type", style="yellow")
            
            for entity in entities[:5]:  # Show first 5
                entity_table.add_row(
                    entity["_key"],
                    entity.get("name", ""),
                    entity.get("type", "")
                )
            
            console.print(entity_table)
            if len(entities) > 5:
                console.print(f"... and {len(entities) - 5} more entities")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to get episode: {str(e)}")
        raise typer.Exit(code=1)


@app.command("end")
def end_episode(
    episode_id: str = typer.Argument(..., help="Episode ID or key to end")
):
    """Mark an episode as ended."""
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        episode = episode_manager.end_episode(episode_id)
        
        console.print(f"[green]✓[/green] Ended episode: {episode['_key']}")
        console.print(f"End time: {episode['end_time']}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to end episode: {str(e)}")
        raise typer.Exit(code=1)


@app.command("delete")
def delete_episode(
    episode_id: str = typer.Argument(..., help="Episode ID or key to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete an episode and all its links."""
    try:
        db = get_db_connection()
        episode_manager = EpisodeManager(db)
        
        # Get episode first to show details
        episode = episode_manager.get_episode(episode_id)
        if not episode:
            console.print(f"[red]Episode '{episode_id}' not found[/red]")
            raise typer.Exit(code=1)
        
        # Confirm deletion
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to delete episode '{episode['name']}'? "
                f"This will also remove all links to entities and relationships."
            )
            if not confirm:
                console.print("[yellow]Deletion cancelled[/yellow]")
                return
        
        # Delete episode
        success = episode_manager.delete_episode(episode_id)
        
        if success:
            console.print(f"[green]✓[/green] Deleted episode: {episode['_key']}")
        else:
            console.print(f"[red]✗[/red] Failed to delete episode")
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to delete episode: {str(e)}")
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