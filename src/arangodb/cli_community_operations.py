"""
CLI commands for community building and management.

This module provides CLI commands for detecting, creating, and managing communities
in the knowledge graph, building on the community building functionality. These
commands allow users to discover and work with entity clusters.

Key features:
1. Detect communities using graph algorithms
2. Create and manage communities
3. Add/remove community members
4. Search and analyze communities
5. Community visualization tools

For usage information, run 'python -m arangodb.cli memory detect-communities --help'
"""

import json
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from loguru import logger

try:
    # Try absolute import first
    from arangodb.community_building import CommunityBuilder
    from arangodb.arango_setup import get_db_connection as get_db
except ImportError:
    # Fall back to relative import
    from src.arangodb.community_building import CommunityBuilder
    from src.arangodb.arango_setup import get_db_connection as get_db

# Initialize console for rich output
console = Console()

# Initialize CLI app
app = typer.Typer(help="Community operations commands")


@app.command("detect-communities")
def detect_communities(
    algorithm: str = typer.Option(
        "louvain", "--algorithm", "-a", 
        help="Community detection algorithm: louvain, scc, or connected."
    ),
    min_members: int = typer.Option(
        3, "--min-members", "-m", 
        help="Minimum number of members for a valid community."
    ),
    max_communities: int = typer.Option(
        10, "--max-communities", "-n", 
        help="Maximum number of communities to detect."
    ),
    weight_attribute: str = typer.Option(
        "confidence", "--weight", "-w", 
        help="Edge attribute to use as weight for algorithms that support it."
    ),
    create: bool = typer.Option(
        False, "--create", "-c", 
        help="Create communities in the database after detection."
    ),
    group_id: Optional[str] = typer.Option(
        None, "--group-id", "-g", 
        help="Optional group ID to assign to the communities."
    ),
    entity_collection: str = typer.Option(
        "agent_entities", "--entity-collection", 
        help="Name of the entity collection."
    ),
    relationship_collection: str = typer.Option(
        "agent_relationships", "--relationship-collection", 
        help="Name of the relationship collection."
    ),
    community_collection: str = typer.Option(
        "communities", "--community-collection", 
        help="Name of the community collection."
    ),
    community_edge_collection: str = typer.Option(
        "community_edges", "--community-edge-collection", 
        help="Name of the community membership edge collection."
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", 
        help="Output results as JSON."
    )
):
    """
    Detect communities in the knowledge graph.
    
    *WHEN TO USE:* When you want to discover clusters of related entities to find
    patterns and groupings in your knowledge graph.
    
    *HOW TO USE:* Run with default parameters to detect communities. Use --create
    to persist detected communities in the database.
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize community builder
        builder = CommunityBuilder(
            db=db,
            entity_collection=entity_collection,
            relationship_collection=relationship_collection,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection
        )
        
        # Detect communities
        console.print(f"[yellow]Detecting communities using {algorithm} algorithm...[/yellow]")
        
        try:
            communities_data = builder.detect_communities(
                algorithm=algorithm,
                min_members=min_members,
                max_communities=max_communities,
                weight_attribute=weight_attribute,
                group_id=group_id
            )
        except Exception as e:
            if "GRAPH_" in str(e) and "not found" in str(e):
                console.print("[yellow]Graph algorithm not available, using fallback method...[/yellow]")
                communities_data = builder._detect_communities_fallback(
                    min_members=min_members,
                    max_communities=max_communities
                )
            else:
                raise
        
        # Create communities if requested
        created_communities = []
        if create and communities_data:
            console.print("[yellow]Creating communities in database...[/yellow]")
            created_communities = builder.create_communities(
                communities_data=communities_data,
                group_id=group_id,
                auto_generate_tags=True
            )
        
        # Format output
        if json_output:
            if create:
                output = {
                    "detected_communities": len(communities_data),
                    "created_communities": len(created_communities),
                    "communities": created_communities if created_communities else communities_data
                }
            else:
                output = {
                    "detected_communities": len(communities_data),
                    "communities": communities_data
                }
            
            print(json.dumps(output, default=str))
        else:
            # Display as table
            if not communities_data:
                console.print("[yellow]No communities detected.[/yellow]")
                return
            
            console.print(f"[green]Detected {len(communities_data)} communities:[/green]")
            
            table = Table(title="Detected Communities", box=box.ROUNDED)
            
            # Add columns
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Members", style="green", justify="right")
            table.add_column("Homogeneity", style="blue", justify="right")
            table.add_column("Main Types", style="yellow")
            
            # Add rows
            for i, community in enumerate(communities_data):
                # Get the community ID or index
                community_id = community.get("community_id", f"community_{i}")
                
                # Get or generate a name
                name = community.get("name", "Unnamed Community")
                
                # Get member count
                member_count = community.get("member_count", len(community.get("members", [])))
                
                # Get homogeneity
                homogeneity = community.get("homogeneity", 0.0)
                
                # Get main types
                type_counts = {}
                for member in community.get("members", []):
                    member_type = member.get("type", "Unknown")
                    type_counts[member_type] = type_counts.get(member_type, 0) + 1
                
                main_types = ", ".join(
                    [f"{t} ({c})" for t, c in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:2]]
                )
                
                table.add_row(
                    str(community_id),
                    name,
                    str(member_count),
                    f"{homogeneity:.2f}",
                    main_types
                )
            
            console.print(table)
            
            if create:
                console.print(f"[green]Created {len(created_communities)} communities in the database.[/green]")
                if created_communities:
                    console.print("Community IDs:")
                    for community in created_communities:
                        console.print(f"  - {community['_id']}")
    
    except Exception as e:
        logger.error(f"Error detecting communities: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Error detecting communities:[/bold red] {e}")
        return 1
    
    return 0


@app.command("list-communities")
def list_communities(
    query: str = typer.Option(
        "", "--query", "-q", 
        help="Filter communities by name (substring match)."
    ),
    tags: Optional[List[str]] = typer.Option(
        None, "--tags", "-t", 
        help="Filter communities by tags (comma-separated)."
    ),
    min_members: int = typer.Option(
        0, "--min-members", "-m", 
        help="Minimum number of members."
    ),
    max_members: Optional[int] = typer.Option(
        None, "--max-members", "-M", 
        help="Maximum number of members."
    ),
    group_id: Optional[str] = typer.Option(
        None, "--group-id", "-g", 
        help="Filter by group ID."
    ),
    limit: int = typer.Option(
        20, "--limit", "-l", 
        help="Maximum number of communities to return."
    ),
    offset: int = typer.Option(
        0, "--offset", "-o", 
        help="Offset for pagination."
    ),
    community_collection: str = typer.Option(
        "communities", "--community-collection", 
        help="Name of the community collection."
    ),
    community_edge_collection: str = typer.Option(
        "community_edges", "--community-edge-collection", 
        help="Name of the community membership edge collection."
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", 
        help="Output results as JSON."
    )
):
    """
    List and search for communities.
    
    *WHEN TO USE:* When you want to find existing communities based on various criteria.
    
    *HOW TO USE:* Run with default parameters to list all communities. Use filters
    to narrow down the results.
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize community builder
        builder = CommunityBuilder(
            db=db,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection
        )
        
        # Parse tags
        tag_list = None
        if tags:
            if isinstance(tags, str):
                tag_list = [t.strip() for t in tags.split(",")]
            else:
                tag_list = tags
        
        # Search communities
        communities = builder.search_communities(
            query=query,
            tags=tag_list,
            min_members=min_members,
            max_members=max_members,
            group_id=group_id,
            limit=limit,
            offset=offset
        )
        
        # Format output
        if json_output:
            output = {
                "total": len(communities),
                "communities": communities
            }
            
            print(json.dumps(output, default=str))
        else:
            # Display as table
            if not communities:
                console.print("[yellow]No communities found.[/yellow]")
                return
            
            console.print(f"[green]Found {len(communities)} communities:[/green]")
            
            table = Table(title="Communities", box=box.ROUNDED)
            
            # Add columns
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Members", style="green", justify="right")
            table.add_column("Tags", style="yellow")
            table.add_column("Created", style="blue")
            
            # Add rows
            for community in communities:
                # Get community ID
                community_id = community.get("_id", "")
                
                # Get name
                name = community.get("name", "Unnamed Community")
                
                # Get member count
                member_count = community.get("member_count", 0)
                
                # Get tags
                tags_str = ", ".join(community.get("tags", []))
                
                # Get creation time
                created_at = community.get("created_at", "")
                if created_at:
                    # Truncate timestamp for display
                    created_at = created_at.split("T")[0] if "T" in created_at else created_at
                
                table.add_row(
                    community_id,
                    name,
                    str(member_count),
                    tags_str,
                    created_at
                )
            
            console.print(table)
    
    except Exception as e:
        logger.error(f"Error listing communities: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Error listing communities:[/bold red] {e}")
        return 1
    
    return 0


@app.command("view-community")
def view_community(
    community_id: str = typer.Argument(
        ..., help="ID or key of the community to view."
    ),
    include_members: bool = typer.Option(
        True, "--members/--no-members", 
        help="Include member details in the output."
    ),
    analyze: bool = typer.Option(
        False, "--analyze", "-a", 
        help="Perform detailed analysis of the community."
    ),
    community_collection: str = typer.Option(
        "communities", "--community-collection", 
        help="Name of the community collection."
    ),
    community_edge_collection: str = typer.Option(
        "community_edges", "--community-edge-collection", 
        help="Name of the community membership edge collection."
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", 
        help="Output results as JSON."
    )
):
    """
    View details of a specific community.
    
    *WHEN TO USE:* When you want to examine a specific community and its members.
    
    *HOW TO USE:* Provide the community ID or key. Use --analyze for detailed metrics
    about the community structure.
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize community builder
        builder = CommunityBuilder(
            db=db,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection
        )
        
        # Ensure community_id is a full ID
        if "/" not in community_id:
            community_id = f"{community_collection}/{community_id}"
        
        # Get community document
        try:
            community_doc = db.document(community_id)
        except Exception:
            if json_output:
                print(json.dumps({"error": f"Community {community_id} not found", "status": "error"}))
            else:
                console.print(f"[bold red]Error:[/bold red] Community {community_id} not found")
            return 1
        
        # Get members if requested
        members = []
        if include_members:
            members = builder.get_community_members(community_id)
        
        # Perform analysis if requested
        analysis = None
        if analyze:
            analysis = builder.analyze_community(community_id, include_members=False)
        
        # Format output
        if json_output:
            output = {
                "community": community_doc
            }
            
            if include_members:
                output["members"] = members
            
            if analysis:
                output["analysis"] = analysis
            
            print(json.dumps(output, default=str))
        else:
            # Display community details
            console.print(f"[bold cyan]Community:[/bold cyan] {community_doc.get('name', 'Unnamed Community')}")
            console.print(f"[bold]ID:[/bold] {community_id}")
            console.print(f"[bold]Members:[/bold] {community_doc.get('member_count', 0)}")
            console.print(f"[bold]Created:[/bold] {community_doc.get('created_at', '')}")
            
            if "group_id" in community_doc and community_doc["group_id"]:
                console.print(f"[bold]Group:[/bold] {community_doc['group_id']}")
            
            if "tags" in community_doc and community_doc["tags"]:
                console.print(f"[bold]Tags:[/bold] {', '.join(community_doc['tags'])}")
            
            if "homogeneity" in community_doc:
                console.print(f"[bold]Homogeneity:[/bold] {community_doc['homogeneity']:.2f}")
            
            # Display members if requested
            if include_members and members:
                console.print("\n[bold]Members:[/bold]")
                
                member_table = Table(box=box.SIMPLE)
                member_table.add_column("ID", style="cyan")
                member_table.add_column("Name", style="green")
                member_table.add_column("Type", style="yellow")
                
                for member in members:
                    member_table.add_row(
                        member["_id"],
                        member.get("name", "Unnamed"),
                        member.get("type", "Unknown")
                    )
                
                console.print(member_table)
            
            # Display analysis if requested
            if analysis:
                console.print("\n[bold]Community Analysis:[/bold]")
                
                console.print(f"[bold]Type Distribution:[/bold]")
                for type_name, count in analysis.get("type_distribution", {}).items():
                    console.print(f"  - {type_name}: {count}")
                
                console.print(f"[bold]Internal Relationships:[/bold] {analysis.get('internal_relationship_count', 0)}")
                console.print(f"[bold]Cohesion:[/bold] {analysis.get('cohesion', 0):.2f}")
                console.print(f"[bold]Homogeneity:[/bold] {analysis.get('homogeneity', 0):.2f}")
    
    except Exception as e:
        logger.error(f"Error viewing community: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Error viewing community:[/bold red] {e}")
        return 1
    
    return 0


@app.command("add-member")
def add_member(
    community_id: str = typer.Argument(
        ..., help="ID or key of the community."
    ),
    entity_id: str = typer.Argument(
        ..., help="ID or key of the entity to add."
    ),
    community_collection: str = typer.Option(
        "communities", "--community-collection", 
        help="Name of the community collection."
    ),
    community_edge_collection: str = typer.Option(
        "community_edges", "--community-edge-collection", 
        help="Name of the community membership edge collection."
    ),
    entity_collection: str = typer.Option(
        "agent_entities", "--entity-collection", 
        help="Name of the entity collection."
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", 
        help="Output results as JSON."
    )
):
    """
    Add an entity to a community.
    
    *WHEN TO USE:* When you want to manually add an entity to a community.
    
    *HOW TO USE:* Provide the community ID and entity ID. The entity will be
    added as a member of the community.
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize community builder
        builder = CommunityBuilder(
            db=db,
            entity_collection=entity_collection,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection
        )
        
        # Add member to community
        edge = builder.add_member_to_community(community_id, entity_id)
        
        # Format output
        if json_output:
            output = {
                "status": "success",
                "message": f"Entity {entity_id} added to community {community_id}",
                "edge": edge
            }
            
            print(json.dumps(output, default=str))
        else:
            console.print(f"[green]Successfully added entity {entity_id} to community {community_id}[/green]")
    
    except Exception as e:
        logger.error(f"Error adding member to community: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Error adding member to community:[/bold red] {e}")
        return 1
    
    return 0


@app.command("remove-member")
def remove_member(
    community_id: str = typer.Argument(
        ..., help="ID or key of the community."
    ),
    entity_id: str = typer.Argument(
        ..., help="ID or key of the entity to remove."
    ),
    community_collection: str = typer.Option(
        "communities", "--community-collection", 
        help="Name of the community collection."
    ),
    community_edge_collection: str = typer.Option(
        "community_edges", "--community-edge-collection", 
        help="Name of the community membership edge collection."
    ),
    entity_collection: str = typer.Option(
        "agent_entities", "--entity-collection", 
        help="Name of the entity collection."
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", 
        help="Output results as JSON."
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", 
        help="Skip confirmation."
    )
):
    """
    Remove an entity from a community.
    
    *WHEN TO USE:* When you want to remove an entity from a community that it
    should no longer be part of.
    
    *HOW TO USE:* Provide the community ID and entity ID. The entity will be
    removed from the community.
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize community builder
        builder = CommunityBuilder(
            db=db,
            entity_collection=entity_collection,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection
        )
        
        # Confirm removal if not using --yes
        if not yes:
            confirmed = typer.confirm(
                f"Are you sure you want to remove entity {entity_id} from community {community_id}?",
                abort=True
            )
        
        # Remove member from community
        removed = builder.remove_member_from_community(community_id, entity_id)
        
        # Format output
        if json_output:
            output = {
                "status": "success" if removed else "error",
                "message": f"Entity {entity_id} {'removed from' if removed else 'was not a member of'} community {community_id}"
            }
            
            print(json.dumps(output))
        else:
            if removed:
                console.print(f"[green]Successfully removed entity {entity_id} from community {community_id}[/green]")
            else:
                console.print(f"[yellow]Entity {entity_id} was not a member of community {community_id}[/yellow]")
    
    except Exception as e:
        logger.error(f"Error removing member from community: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Error removing member from community:[/bold red] {e}")
        return 1
    
    return 0


@app.command("merge-communities")
def merge_communities(
    community_ids: List[str] = typer.Argument(
        ..., help="IDs or keys of communities to merge (comma-separated)."
    ),
    new_name: Optional[str] = typer.Option(
        None, "--name", "-n", 
        help="Name for the merged community."
    ),
    community_collection: str = typer.Option(
        "communities", "--community-collection", 
        help="Name of the community collection."
    ),
    community_edge_collection: str = typer.Option(
        "community_edges", "--community-edge-collection", 
        help="Name of the community membership edge collection."
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", 
        help="Output results as JSON."
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", 
        help="Skip confirmation."
    )
):
    """
    Merge multiple communities into a single new community.
    
    *WHEN TO USE:* When you have multiple small communities that should be combined
    into a larger, more meaningful group.
    
    *HOW TO USE:* Provide a comma-separated list of community IDs to merge. A new
    community will be created with all members from the source communities.
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize community builder
        builder = CommunityBuilder(
            db=db,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection
        )
        
        # Parse community IDs
        if isinstance(community_ids, str):
            community_ids = [cid.strip() for cid in community_ids.split(",")]
        
        # Check if enough communities provided
        if len(community_ids) < 2:
            if json_output:
                print(json.dumps({
                    "error": "At least two communities are required for merging",
                    "status": "error"
                }))
            else:
                console.print("[bold red]Error:[/bold red] At least two communities are required for merging")
            return 1
        
        # Confirm merge if not using --yes
        if not yes:
            community_list = ", ".join(community_ids)
            confirmed = typer.confirm(
                f"Are you sure you want to merge these communities: {community_list}?",
                abort=True
            )
        
        # Perform merge
        merged_community = builder.merge_communities(community_ids, new_name)
        
        # Format output
        if json_output:
            output = {
                "status": "success",
                "message": f"Successfully merged {len(community_ids)} communities",
                "merged_community": merged_community
            }
            
            print(json.dumps(output, default=str))
        else:
            console.print(f"[green]Successfully merged {len(community_ids)} communities[/green]")
            console.print(f"[bold]New community:[/bold] {merged_community['_id']} - {merged_community['name']}")
            console.print(f"[bold]Members:[/bold] {merged_community['member_count']}")
    
    except Exception as e:
        logger.error(f"Error merging communities: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Error merging communities:[/bold red] {e}")
        return 1
    
    return 0


@app.command("delete-community")
def delete_community(
    community_id: str = typer.Argument(
        ..., help="ID or key of the community to delete."
    ),
    community_collection: str = typer.Option(
        "communities", "--community-collection", 
        help="Name of the community collection."
    ),
    community_edge_collection: str = typer.Option(
        "community_edges", "--community-edge-collection", 
        help="Name of the community membership edge collection."
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", 
        help="Output results as JSON."
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", 
        help="Skip confirmation."
    )
):
    """
    Delete a community.
    
    *WHEN TO USE:* When a community is no longer useful or relevant.
    
    *HOW TO USE:* Provide the community ID. The community and all its membership
    edges will be deleted.
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize community builder
        builder = CommunityBuilder(
            db=db,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection
        )
        
        # Confirm deletion if not using --yes
        if not yes:
            confirmed = typer.confirm(
                f"Are you sure you want to delete community {community_id}? This will remove all membership relationships.",
                abort=True
            )
        
        # Delete community
        deleted = builder.delete_community(community_id)
        
        # Format output
        if json_output:
            output = {
                "status": "success" if deleted else "error",
                "message": f"Community {community_id} {'deleted' if deleted else 'could not be deleted'}"
            }
            
            print(json.dumps(output))
        else:
            if deleted:
                console.print(f"[green]Successfully deleted community {community_id}[/green]")
            else:
                console.print(f"[yellow]Failed to delete community {community_id}[/yellow]")
    
    except Exception as e:
        logger.error(f"Error deleting community: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Error deleting community:[/bold red] {e}")
        return 1
    
    return 0


# Main entry point
if __name__ == "__main__":
    app()