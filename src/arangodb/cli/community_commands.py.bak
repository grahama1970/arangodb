"""
Community Detection CLI Commands for ArangoDB

This module provides command-line interface for community detection operations
within the knowledge graph. It uses the community detection algorithm to identify
and manage clusters of related entities.

Key Commands:
- detect: Run community detection on the entity graph
- show: Display information about a specific community
- list: List all communities with basic stats
- rebuild: Force rebuild of all communities

External Documentation:
- Typer: https://typer.tiangolo.com/
- Rich: https://rich.readthedocs.io/
"""

import typer
import json
from datetime import datetime
from typing import Optional
from loguru import logger

# Import UI components
from rich.console import Console
from rich.table import Table
from rich import print_json

# Import database and community detection
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.graph.community_detection import CommunityDetector

# Initialize UI components
console = Console()
app = typer.Typer()


@app.command("detect", no_args_is_help=False)
def detect_communities(
    min_size: int = typer.Option(
        2,
        "--min-size",
        "-m",
        help="Minimum community size to keep"
    ),
    resolution: float = typer.Option(
        1.0,
        "--resolution",
        "-r",
        help="Resolution parameter (higher = more communities)"
    ),
    rebuild: bool = typer.Option(
        False,
        "--rebuild",
        "-R",
        help="Force rebuild all communities"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output results as JSON"
    )
):
    """
    Detect communities in the entity graph using the Louvain algorithm.
    
    Communities are groups of closely related entities based on their 
    relationships. This helps organize knowledge into meaningful clusters.
    """
    logger.info(f"CLI: Detecting communities with min_size={min_size}, resolution={resolution}")
    
    try:
        # Get database connection
        db = get_db_connection()
        
        # Initialize community detector
        detector = CommunityDetector(db)
        
        # Clear existing communities if rebuild requested
        if rebuild:
            console.print("[yellow]Rebuilding all communities...[/yellow]")
            try:
                db.collection("agent_communities").truncate()
            except:
                pass  # Collection might not exist
        
        # Run community detection
        communities = detector.detect_communities(
            min_size=min_size,
            resolution=resolution
        )
        
        # Group entities by community
        community_groups = {}
        for entity, community in communities.items():
            if community not in community_groups:
                community_groups[community] = []
            community_groups[community].append(entity)
        
        if json_output:
            # Output as JSON
            result = {
                "total_entities": len(communities),
                "total_communities": len(community_groups),
                "communities": []
            }
            
            # Get stored communities for additional metadata
            stored_communities = detector.get_all_communities()
            community_metadata = {c["original_id"]: c for c in stored_communities}
            
            for community_id, entities in community_groups.items():
                metadata = community_metadata.get(community_id, {})
                result["communities"].append({
                    "id": metadata.get("_key", community_id),
                    "size": len(entities),
                    "entities": entities,
                    "modularity": metadata.get("metadata", {}).get("modularity_score", 0)
                })
            
            print_json(data=result)
        else:
            # Display as table
            table = Table(title="Community Detection Results")
            table.add_column("Community ID", style="cyan")
            table.add_column("Size", style="green", justify="center")
            table.add_column("Key Entities", style="yellow")
            table.add_column("Modularity", style="magenta", justify="center")
            
            # Get stored communities for modularity scores
            stored_communities = detector.get_all_communities()
            community_metadata = {c["original_id"]: c for c in stored_communities}
            
            for community_id, entities in community_groups.items():
                key_entities = ", ".join(entities[:3])
                if len(entities) > 3:
                    key_entities += f" (+{len(entities)-3} more)"
                
                metadata = community_metadata.get(community_id, {})
                modularity = metadata.get("metadata", {}).get("modularity_score", 0)
                
                table.add_row(
                    metadata.get("_key", community_id),
                    str(len(entities)),
                    key_entities,
                    f"{modularity:.3f}"
                )
            
            console.print(table)
            console.print(f"\n[green]Total communities: {len(community_groups)}[/green]")
            console.print(f"[green]Total entities: {len(communities)}[/green]")
    
    except Exception as e:
        logger.error(f"Community detection failed: {e}", exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("show")
def show_community(
    community_id: str = typer.Argument(
        ...,
        help="Community ID to display"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON"
    )
):
    """
    Show detailed information about a specific community.
    
    Displays all members of the community, their relationships,
    and community metadata like creation time and modularity score.
    """
    logger.info(f"CLI: Showing community {community_id}")
    
    try:
        # Get database connection
        db = get_db_connection()
        
        # Get community document
        communities_col = db.collection("agent_communities")
        
        try:
            community = communities_col.get(community_id)
        except:
            console.print(f"[bold red]Error:[/bold red] Community '{community_id}' not found")
            raise typer.Exit(code=1)
        
        # Get entity details
        entities_col = db.collection("agent_entities")
        entities = []
        
        for entity_id in community.get("member_ids", []):
            try:
                entity = entities_col.get(entity_id)
                if entity:
                    entities.append({
                        "id": entity["_key"],
                        "name": entity.get("name", entity["_key"]),
                        "type": entity.get("type", "unknown")
                    })
            except:
                pass
        
        if json_output:
            # Output as JSON
            result = {
                "id": community["_key"],
                "member_count": community.get("member_count", 0),
                "entities": entities,
                "metadata": community.get("metadata", {}),
                "created_at": community.get("created_at"),
                "sample_members": community.get("sample_members", [])
            }
            print_json(data=result)
        else:
            # Display as formatted output
            console.print(f"\n[bold cyan]Community: {community['_key']}[/bold cyan]")
            console.print(f"Members: {community.get('member_count', 0)}")
            console.print(f"Created: {community.get('created_at', 'Unknown')}")
            
            if community.get("metadata"):
                console.print(f"Algorithm: {community['metadata'].get('algorithm', 'Unknown')}")
                console.print(f"Modularity Score: {community['metadata'].get('modularity_score', 0):.3f}")
            
            # Create entities table
            if entities:
                table = Table(title="Community Members")
                table.add_column("Entity ID", style="cyan")
                table.add_column("Name", style="yellow")
                table.add_column("Type", style="green")
                
                for entity in entities:
                    table.add_row(
                        entity["id"],
                        entity["name"],
                        entity["type"]
                    )
                
                console.print("\n")
                console.print(table)
    
    except Exception as e:
        if "not found" not in str(e):
            logger.error(f"Show community failed: {e}", exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("list")
def list_communities(
    min_size: Optional[int] = typer.Option(
        None,
        "--min-size",
        "-m",
        help="Filter communities by minimum size"
    ),
    sort_by: str = typer.Option(
        "size",
        "--sort",
        "-s",
        help="Sort by: size, modularity, or created"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j", 
        help="Output as JSON"
    )
):
    """
    List all communities with their basic information.
    
    Shows a summary of all detected communities including size,
    key members, and quality metrics like modularity score.
    """
    logger.info("CLI: Listing all communities")
    
    try:
        # Get database connection
        db = get_db_connection()
        
        # Get all communities
        detector = CommunityDetector(db)
        communities = detector.get_all_communities()
        
        # Filter by size if requested
        if min_size:
            communities = [c for c in communities if c.get("member_count", 0) >= min_size]
        
        # Sort communities
        if sort_by == "size":
            communities.sort(key=lambda c: c.get("member_count", 0), reverse=True)
        elif sort_by == "modularity":
            communities.sort(key=lambda c: c.get("metadata", {}).get("modularity_score", 0), reverse=True)
        elif sort_by == "created":
            communities.sort(key=lambda c: c.get("created_at", ""), reverse=True)
        
        if json_output:
            # Output as JSON
            result = {
                "total": len(communities),
                "communities": [
                    {
                        "id": c["_key"],
                        "size": c.get("member_count", 0),
                        "sample_members": c.get("sample_members", []),
                        "modularity": c.get("metadata", {}).get("modularity_score", 0),
                        "created_at": c.get("created_at")
                    }
                    for c in communities
                ]
            }
            print_json(data=result)
        else:
            # Display as table
            table = Table(title=f"Communities (Total: {len(communities)})")
            table.add_column("ID", style="cyan")
            table.add_column("Size", style="green", justify="center")
            table.add_column("Sample Members", style="yellow")
            table.add_column("Modularity", style="magenta", justify="center")
            table.add_column("Created", style="blue")
            
            for community in communities:
                sample_members = ", ".join(community.get("sample_members", [])[:3])
                if len(community.get("sample_members", [])) > 3:
                    sample_members += "..."
                
                created = community.get("created_at", "Unknown")
                if created != "Unknown":
                    try:
                        dt = datetime.fromisoformat(created)
                        created = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                table.add_row(
                    community["_key"],
                    str(community.get("member_count", 0)),
                    sample_members,
                    f"{community.get('metadata', {}).get('modularity_score', 0):.3f}",
                    created
                )
            
            console.print(table)
    
    except Exception as e:
        logger.error(f"List communities failed: {e}", exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()