"""
CLI command implementation for manual entity resolution in ArangoDB.

This module provides a Typer command for the ArangoDB CLI to manually resolve
and merge entities. It allows users to identify potentially duplicate entities
and merge them with different strategies.

Usage:
    arangodb memory resolve-entity [OPTIONS]
"""

import typer
import json
from typing import Optional, List, Dict, Any
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.json import JSON
from datetime import datetime, timezone

# Import necessary modules
try:
    # Try standalone package imports first
    from arangodb.enhanced_entity_resolution import (
        find_exact_entity_matches,
        find_similar_entity_matches,
        calculate_entity_match_confidence,
        merge_entity_attributes,
        resolve_entity
    )
    from arangodb.config import COLLECTION_NAME
    from arangodb.utils.embedding_utils import get_embedding
except ImportError:
    # Fall back to relative imports
    from src.arangodb.enhanced_entity_resolution import (
        find_exact_entity_matches,
        find_similar_entity_matches,
        calculate_entity_match_confidence,
        merge_entity_attributes,
        resolve_entity
    )
    from src.arangodb.config import COLLECTION_NAME
    from src.arangodb.utils.embedding_utils import get_embedding

# Rich console for output formatting
console = Console()

def display_entities(entities, title="Entities"):
    """
    Display a list of entities in a rich table format.
    
    Args:
        entities: List of entity documents
        title: Title for the table
    """
    if not entities:
        console.print("[yellow]No entities found.[/yellow]")
        return
        
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title=title
    )
    
    table.add_column("Key", style="cyan")
    table.add_column("Name", style="blue")
    table.add_column("Type", style="green")
    table.add_column("Attributes", style="yellow")
    table.add_column("Confidence", style="bright_magenta")
    
    for entity in entities:
        # Format attributes as a compact JSON string
        attrs = entity.get("attributes", {})
        if not isinstance(attrs, dict):
            attrs = {}
        
        attributes_str = json.dumps(attrs, sort_keys=True)
        if len(attributes_str) > 40:
            attributes_str = attributes_str[:37] + "..."
        
        table.add_row(
            entity.get("_key", ""),
            entity.get("name", ""),
            entity.get("type", ""),
            attributes_str,
            f"{entity.get('_confidence', 0):.2f}" if "_confidence" in entity else ""
        )
    
    console.print(table)

def display_entity_details(entity, title="Entity Details"):
    """
    Display detailed information about an entity.
    
    Args:
        entity: Entity document
        title: Title for the output
    """
    if not entity:
        console.print("[yellow]No entity data to display.[/yellow]")
        return
        
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print(f"[bold]Key:[/bold] {entity.get('_key', '')}")
    console.print(f"[bold]Name:[/bold] {entity.get('name', '')}")
    console.print(f"[bold]Type:[/bold] {entity.get('type', '')}")
    
    if "created_at" in entity:
        console.print(f"[bold]Created:[/bold] {entity['created_at']}")
    
    if "attributes" in entity and isinstance(entity["attributes"], dict):
        console.print("[bold]Attributes:[/bold]")
        for key, value in entity["attributes"].items():
            console.print(f"  [cyan]{key}:[/cyan] {value}")
    
    if "_merge_history" in entity and isinstance(entity["_merge_history"], list):
        console.print("[bold]Merge History:[/bold]")
        for merge in entity["_merge_history"]:
            console.print(f"  [cyan]Merged with:[/cyan] {merge.get('merged_with', 'unknown')}")
            console.print(f"  [cyan]Strategy:[/cyan] {merge.get('strategy', 'unknown')}")
            console.print(f"  [cyan]Timestamp:[/cyan] {merge.get('timestamp', 'unknown')}")
            console.print("")
    
    console.print("")

def find_potential_entity_matches(
    db,
    entity_collection: str,
    search_term: str,
    entity_type: Optional[str] = None,
    embedding_field: str = "embedding",
    exact_match_only: bool = False,
    min_similarity: float = 0.7,
    max_results: int = 10,
    json_output: bool = False
):
    """
    Find potential entity matches using name search and/or semantic similarity.
    
    Args:
        db: ArangoDB database handle
        entity_collection: Name of the entity collection
        search_term: Term to search for (name or description)
        entity_type: Optional type filter
        embedding_field: Name of the embedding field
        exact_match_only: If True, only return exact name matches
        min_similarity: Minimum similarity threshold
        max_results: Maximum number of results to return
        json_output: If True, output results as JSON
        
    Returns:
        List of matching entities if json_output is True, otherwise None
    """
    try:
        # Step 1: Build AQL query for name search
        type_filter = f"FILTER doc.type == @entity_type" if entity_type else ""
        
        aql = f"""
        FOR doc IN {entity_collection}
        FILTER LOWER(doc.name) LIKE CONCAT('%', LOWER(@search_term), '%')
        {type_filter}
        SORT LOWER(doc.name) ASC
        LIMIT @max_results
        RETURN doc
        """
        
        bind_vars = {
            "search_term": search_term,
            "max_results": max_results
        }
        
        if entity_type:
            bind_vars["entity_type"] = entity_type
        
        # Execute query
        cursor = db.aql.execute(aql, bind_vars=bind_vars)
        name_matches = list(cursor)
        
        if not exact_match_only and len(name_matches) < max_results:
            # Step 2: Try semantic search if we have room for more results
            remaining_slots = max_results - len(name_matches)
            
            # Create a temporary entity document for semantic matching
            entity_doc = {
                "name": search_term,
                "type": entity_type or "Entity"
            }
            
            # Generate embedding for the entity
            entity_text = f"{search_term} {entity_type or ''}"
            entity_doc[embedding_field] = get_embedding(entity_text)
            
            # Find similar entities
            semantic_matches = find_similar_entity_matches(
                db, 
                entity_doc, 
                entity_collection, 
                embedding_field=embedding_field,
                min_similarity=min_similarity,
                max_results=remaining_slots
            )
            
            # Combine results, avoiding duplicates
            seen_keys = {match["_key"] for match in name_matches}
            for match in semantic_matches:
                if match["_key"] not in seen_keys:
                    name_matches.append(match)
                    seen_keys.add(match["_key"])
            
            # Ensure we don't exceed max_results
            name_matches = name_matches[:max_results]
        
        # If nothing found, show appropriate message
        if not name_matches:
            if json_output:
                return []
            else:
                console.print(f"[yellow]No entities found matching '{search_term}'[/yellow]")
                return None
        
        # Display or return the results
        if json_output:
            return name_matches
        else:
            display_entities(name_matches, title=f"Entities Matching '{search_term}'")
            return None
            
    except Exception as e:
        logger.error(f"Error finding potential entity matches: {e}")
        if json_output:
            return []
        else:
            console.print(f"[bold red]Error finding entities:[/bold red] {e}")
            return None

def resolve_entities_command(
    db,
    entity_collection: str,
    entity1_key: str,
    entity2_key: str,
    merge_strategy: str = "union",
    keep_entity: str = "1",
    embedding_field: str = "embedding",
    yes: bool = False,
    json_output: bool = False
):
    """
    CLI command implementation to resolve and merge two entities.
    
    Args:
        db: ArangoDB database handle
        entity_collection: Name of the entity collection
        entity1_key: Key of the first entity
        entity2_key: Key of the second entity
        merge_strategy: Strategy for merging attributes
        keep_entity: Which entity to keep ("1", "2", or "new")
        embedding_field: Name of the embedding field
        yes: If True, automatically confirm merge
        json_output: If True, output results as JSON
        
    Returns:
        Merged entity if json_output is True, otherwise None
    """
    try:
        # Get both entities
        entity1 = db.collection(entity_collection).get(entity1_key)
        entity2 = db.collection(entity_collection).get(entity2_key)
        
        if not entity1:
            if json_output:
                return {"status": "error", "message": f"Entity with key '{entity1_key}' not found"}
            else:
                console.print(f"[bold red]Error:[/bold red] Entity with key '{entity1_key}' not found")
                return None
        
        if not entity2:
            if json_output:
                return {"status": "error", "message": f"Entity with key '{entity2_key}' not found"}
            else:
                console.print(f"[bold red]Error:[/bold red] Entity with key '{entity2_key}' not found")
                return None
        
        # Display entity details for confirmation
        if not json_output:
            display_entity_details(entity1, title="Entity 1")
            display_entity_details(entity2, title="Entity 2")
            
            # Calculate confidence
            confidence = calculate_entity_match_confidence(entity1, entity2, embedding_field=embedding_field)
            console.print(f"Calculated match confidence: [bold]{confidence:.2f}[/bold]")
            
            # Confirm merge if not auto-confirmed
            if not yes:
                confirmed = typer.confirm(
                    f"Merge these entities using '{merge_strategy}' strategy and keeping " + 
                    (f"entity {keep_entity}" if keep_entity in ["1", "2"] else "a new entity"),
                    abort=True
                )
        
        # Determine which entity to keep as the base
        base_entity = None
        merge_entity = None
        
        if keep_entity == "1":
            base_entity = entity1
            merge_entity = entity2
        elif keep_entity == "2":
            base_entity = entity2
            merge_entity = entity1
        else:  # "new"
            # Create a new entity with basic info from entity1
            base_entity = {
                "name": entity1["name"],
                "type": entity1["type"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # If entity1 has an embedding, use it
            if embedding_field in entity1:
                base_entity[embedding_field] = entity1[embedding_field]
            
            # Insert the new entity
            result = db.collection(entity_collection).insert(base_entity)
            base_entity["_key"] = result["_key"]
            base_entity["_id"] = result["_id"]
            
            # First merge entity1's attributes into the new entity
            base_entity = merge_entity_attributes(entity1, base_entity, strategy=merge_strategy)
            merge_entity = entity2
        
        # Merge the entities
        merged_entity = merge_entity_attributes(merge_entity, base_entity, strategy=merge_strategy)
        
        # Update the base entity with the merged attributes
        db.collection(entity_collection).update(base_entity["_key"], merged_entity)
        
        # If keep_entity is not "new", we should invalidate the merged entity
        if keep_entity in ["1", "2"]:
            now = datetime.now(timezone.utc).isoformat()
            merged_key = entity2_key if keep_entity == "1" else entity1_key
            
            # Mark as merged rather than deleted
            db.collection(entity_collection).update(
                merged_key,
                {
                    "merged_into": base_entity["_key"],
                    "merged_at": now,
                    "merge_strategy": merge_strategy
                }
            )
        
        # Get the final merged entity
        final_entity = db.collection(entity_collection).get(base_entity["_key"])
        
        # Display results
        if json_output:
            return final_entity
        else:
            console.print(f"[green]Successfully merged entities into '{final_entity['_key']}'[/green]")
            display_entity_details(final_entity, title="Merged Entity")
            return None
            
    except Exception as e:
        logger.error(f"Error resolving entities: {e}")
        if json_output:
            return {"status": "error", "message": str(e)}
        else:
            console.print(f"[bold red]Error resolving entities:[/bold red] {e}")
            return None

def add_entity_command(
    db,
    entity_collection: str,
    name: str,
    entity_type: str,
    attributes_str: Optional[str] = None,
    attributes_file: Optional[str] = None,
    auto_resolve: bool = True,
    merge_strategy: str = "union",
    min_confidence: float = 0.8,
    embedding_field: str = "embedding",
    json_output: bool = False
):
    """
    CLI command implementation to add a new entity with resolution.
    
    Args:
        db: ArangoDB database handle
        entity_collection: Name of the entity collection
        name: Name of the entity
        entity_type: Type of the entity
        attributes_str: JSON string of attributes
        attributes_file: Path to JSON file with attributes
        auto_resolve: Whether to automatically resolve duplicates
        merge_strategy: Strategy for merging attributes
        min_confidence: Minimum confidence threshold for auto-merge
        embedding_field: Name of the embedding field
        json_output: If True, output results as JSON
        
    Returns:
        Entity document if json_output is True, otherwise None
    """
    try:
        # Parse attributes
        attributes = {}
        
        if attributes_str and attributes_file:
            if json_output:
                return {"status": "error", "message": "Cannot specify both attributes_str and attributes_file"}
            else:
                console.print("[bold red]Error:[/bold red] Cannot specify both --attributes and --attributes-file")
                return None
        
        if attributes_str:
            try:
                attributes = json.loads(attributes_str)
                if not isinstance(attributes, dict):
                    raise ValueError("Attributes must be a JSON object")
            except json.JSONDecodeError as e:
                if json_output:
                    return {"status": "error", "message": f"Invalid JSON in attributes: {e}"}
                else:
                    console.print(f"[bold red]Error:[/bold red] Invalid JSON in attributes: {e}")
                    return None
        
        if attributes_file:
            try:
                with open(attributes_file, "r") as f:
                    attributes = json.load(f)
                if not isinstance(attributes, dict):
                    raise ValueError("Attributes in file must be a JSON object")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                if json_output:
                    return {"status": "error", "message": f"Error reading attributes file: {e}"}
                else:
                    console.print(f"[bold red]Error:[/bold red] Error reading attributes file: {e}")
                    return None
        
        # Create entity document
        entity_doc = {
            "name": name,
            "type": entity_type,
            "attributes": attributes,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Generate embedding for the entity
        entity_text = f"{name} {entity_type} {json.dumps(attributes)}"
        entity_doc[embedding_field] = get_embedding(entity_text)
        
        # Resolve entity
        resolved_entity, matches, merged = resolve_entity(
            db,
            entity_doc,
            entity_collection,
            embedding_field=embedding_field,
            min_confidence=min_confidence,
            merge_strategy=merge_strategy,
            auto_merge=auto_resolve
        )
        
        # Display results
        if json_output:
            result = {
                "entity": resolved_entity,
                "merged": merged,
                "matches": matches if matches else []
            }
            return result
        else:
            if merged:
                console.print(f"[green]Entity merged with existing entity '{resolved_entity['_key']}'[/green]")
            else:
                console.print(f"[green]Created new entity with key '{resolved_entity['_key']}'[/green]")
            
            display_entity_details(resolved_entity, title="Entity Details")
            
            if matches:
                console.print("\n[bold]Similar entities found:[/bold]")
                display_entities(matches, title="Similar Entities")
            
            return None
            
    except Exception as e:
        logger.error(f"Error adding entity: {e}")
        if json_output:
            return {"status": "error", "message": str(e)}
        else:
            console.print(f"[bold red]Error adding entity:[/bold red] {e}")
            return None