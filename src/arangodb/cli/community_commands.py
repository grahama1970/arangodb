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

# Import CLI utilities
from arangodb.core.utils.cli.formatters import (
    console, 
    format_output, 
    add_output_option,
    format_error,
    format_success,
    OutputFormat
)

# Import database and community detection
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.graph.community_detection import CommunityDetector

# Initialize app
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
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """
    Detect communities in the entity graph using the Louvain algorithm.
    
    Communities are groups of closely related entities based on their 
    relationships. This helps organize knowledge into meaningful clusters.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    logger.info(f"CLI: Detecting communities with min_size={min_size}, resolution={resolution}")
    
    try:
        # Get database connection
        db = get_db_connection()
        
        # Initialize community detector
        detector = CommunityDetector(db)
        
        # Clear existing communities if rebuild requested
        if rebuild:
            if output_format != "json":
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
        
        # Get stored communities for additional metadata
        stored_communities = detector.get_all_communities()
        community_metadata = {c["original_id"]: c for c in stored_communities}
        
        # Filter out communities smaller than min_size (just in case the merge didn't work perfectly)
        filtered_groups = {cid: entities for cid, entities in community_groups.items() 
                          if len(entities) >= min_size}
        
        # Prepare data for output
        if output_format == "json":
            # JSON format - full data structure
            result = {
                "total_entities": sum(len(entities) for entities in filtered_groups.values()),
                "total_communities": len(filtered_groups),
                "communities": []
            }
            
            for community_id, entities in filtered_groups.items():
                metadata = community_metadata.get(community_id, {})
                result["communities"].append({
                    "id": metadata.get("_key", community_id),
                    "size": len(entities),
                    "entities": entities,
                    "modularity": metadata.get("metadata", {}).get("modularity_score", 0)
                })
            
            console.print(format_output(result, output_format=output_format))
        else:
            # Table/CSV/Text format - prepare rows
            headers = ["Community ID", "Size", "Key Entities", "Modularity"]
            rows = []
            
            for community_id, entities in filtered_groups.items():
                key_entities = ", ".join(entities[:3])
                if len(entities) > 3:
                    key_entities += f" (+{len(entities)-3} more)"
                
                metadata = community_metadata.get(community_id, {})
                modularity = metadata.get("metadata", {}).get("modularity_score", 0)
                
                rows.append([
                    metadata.get("_key", community_id),
                    str(len(entities)),
                    key_entities,
                    f"{modularity:.3f}"
                ])
            
            formatted_output = format_output(
                rows,
                output_format=output_format,
                headers=headers,
                title="Community Detection Results"
            )
            console.print(formatted_output)
            
            # Add summary for table format
            if output_format == "table":
                console.print(format_success(
                    f"Total communities: {len(community_groups)}, Total entities: {len(communities)}"
                ))
    
    except Exception as e:
        logger.error(f"Community detection failed: {e}", exc_info=True)
        console.print(format_error("Community detection failed", str(e)))
        raise typer.Exit(code=1)


@app.command("show")
def show_community(
    community_id: str = typer.Argument(
        ...,
        help="Community ID to display"
    ),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """
    Show detailed information about a specific community.
    
    Displays all members of the community, their relationships,
    and community metadata like creation time and modularity score.
    
    Use --output/-o to choose between table, json, csv, or text formats.
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
            console.print(format_error(f"Community '{community_id}' not found"))
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
        
        if output_format == "json":
            # Output as JSON
            result = {
                "id": community["_key"],
                "member_count": community.get("member_count", 0),
                "entities": entities,
                "metadata": community.get("metadata", {}),
                "created_at": community.get("created_at"),
                "sample_members": community.get("sample_members", [])
            }
            console.print(format_output(result, output_format=output_format))
        else:
            # For table/CSV/text formats
            
            # Community info
            info_rows = [
                ["Community ID", community["_key"]],
                ["Members", str(community.get("member_count", 0))],
                ["Created", community.get("created_at", "Unknown")]
            ]
            
            if community.get("metadata"):
                info_rows.append(["Algorithm", community["metadata"].get("algorithm", "Unknown")])
                info_rows.append(["Modularity Score", f"{community['metadata'].get('modularity_score', 0):.3f}"])
            
            # Output community info
            info_output = format_output(
                info_rows,
                output_format=output_format,
                headers=["Property", "Value"],
                title=f"Community: {community['_key']}"
            )
            console.print(info_output)
            
            # Output entities if available
            if entities and output_format != OutputFormat.TEXT:
                console.print("")  # Add spacing
                
                entity_rows = []
                for entity in entities:
                    entity_rows.append([
                        entity["id"],
                        entity["name"],
                        entity["type"]
                    ])
                
                entity_output = format_output(
                    entity_rows,
                    output_format=output_format,
                    headers=["Entity ID", "Name", "Type"],
                    title="Community Members"
                )
                console.print(entity_output)
    
    except Exception as e:
        if "not found" not in str(e):
            logger.error(f"Show community failed: {e}", exc_info=True)
            console.print(format_error("Show community failed", str(e)))
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
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")
):
    """
    List all communities with their basic information.
    
    Shows a summary of all detected communities including size,
    key members, and quality metrics like modularity score.
    
    Use --output/-o to choose between table, json, csv, or text formats.
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
        
        if output_format == "json":
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
            console.print(format_output(result, output_format=output_format))
        else:
            # Prepare rows for table/CSV/text formats
            headers = ["ID", "Size", "Sample Members", "Modularity", "Created"]
            rows = []
            
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
                
                rows.append([
                    community["_key"],
                    str(community.get("member_count", 0)),
                    sample_members,
                    f"{community.get('metadata', {}).get('modularity_score', 0):.3f}",
                    created
                ])
            
            formatted_output = format_output(
                rows,
                output_format=output_format,
                headers=headers,
                title=f"Communities (Total: {len(communities)})"
            )
            console.print(formatted_output)
    
    except Exception as e:
        logger.error(f"List communities failed: {e}", exc_info=True)
        console.print(format_error("List communities failed", str(e)))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()