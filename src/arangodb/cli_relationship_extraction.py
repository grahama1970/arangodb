"""
CLI commands for advanced relationship extraction.

This module provides CLI commands for extracting, managing, and visualizing
relationships in the knowledge graph, building on the advanced relationship
extraction capabilities.

Key features:
1. Extract relationships from text
2. Add relationships between entities
3. Find and view existing relationships
4. Validate relationship quality
5. Input/output formatting for CLI friendly display

For usage information, run 'python -m arangodb.cli extract-relationships --help'
"""

import json
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union

import typer
from rich.console import Console
from rich.table import Table
from loguru import logger
from arango.database import StandardDatabase

try:
    # Try absolute import first
    from arangodb.advanced_relationship_extraction import RelationshipExtractor, RelationshipType
    from arangodb.arango_setup import get_db
except ImportError:
    # Fall back to relative import
    from src.arangodb.advanced_relationship_extraction import RelationshipExtractor, RelationshipType
    from src.arangodb.arango_setup import get_db

# Initialize console for rich output
console = Console()

# Initialize CLI app
app = typer.Typer(help="Relationship extraction commands")


def format_relationship_for_display(
    relationship: Dict[str, Any],
    include_metadata: bool = False
) -> Dict[str, Any]:
    """Format a relationship document for CLI display."""
    display_rel = {
        "source": relationship.get("source", ""),
        "target": relationship.get("target", ""),
        "type": relationship.get("type", ""),
        "confidence": f"{relationship.get('confidence', 0.0):.2f}",
        "rationale": relationship.get("rationale", "")
    }
    
    # Add temporal information if available
    if "valid_at" in relationship:
        display_rel["valid_from"] = relationship["valid_at"]
    
    if "invalid_at" in relationship:
        display_rel["valid_until"] = relationship["invalid_at"] or "Present"
    
    # Add metadata if requested
    if include_metadata and "metadata" in relationship:
        display_rel["metadata"] = relationship["metadata"]
    
    return display_rel


def display_relationships_table(relationships: List[Dict[str, Any]]):
    """Display relationships in a formatted table."""
    if not relationships:
        console.print("[yellow]No relationships found.[/yellow]")
        return
    
    table = Table(title=f"Relationships ({len(relationships)} found)")
    
    # Add columns
    table.add_column("Source", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Target", style="cyan")
    table.add_column("Confidence", style="yellow")
    table.add_column("Temporal Validity", style="blue")
    table.add_column("Rationale", style="white", no_wrap=False)
    
    # Add rows
    for rel in relationships:
        # Handle different possible formats
        source = rel.get("source", "") or rel.get("_from", "")
        target = rel.get("target", "") or rel.get("_to", "")
        
        # Extract entity names from full IDs if needed
        if "/" in source:
            source = source.split("/")[-1]
        if "/" in target:
            target = target.split("/")[-1]
        
        # Format temporal validity
        valid_from = rel.get("valid_at", rel.get("valid_from", ""))
        valid_until = rel.get("invalid_at", rel.get("valid_until", "")) or "Present"
        
        # Truncate datetime strings for display
        if valid_from and len(valid_from) > 10:
            valid_from = valid_from[:10]
        if valid_until and valid_until != "Present" and len(valid_until) > 10:
            valid_until = valid_until[:10]
            
        temporal = f"{valid_from} → {valid_until}"
        
        # Format confidence
        confidence = rel.get("confidence", 0.0)
        if isinstance(confidence, (int, float)):
            confidence_str = f"{confidence:.2f}"
        else:
            confidence_str = str(confidence)
        
        # Format rationale (truncate if too long)
        rationale = rel.get("rationale", "")
        if len(rationale) > 80:
            rationale = rationale[:77] + "..."
        
        table.add_row(
            source,
            rel.get("type", ""),
            target,
            confidence_str,
            temporal,
            rationale
        )
    
    console.print(table)


@app.command("extract-from-text")
def extract_relationships_from_text(
    text: str = typer.Argument(..., help="Text to extract relationships from."),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for extracted relationships."),
    use_llm: bool = typer.Option(False, "--llm", help="Use LLM-based extraction (requires LLM client)."),
    relationship_types: Optional[List[str]] = typer.Option(
        None, "--types", "-t", help="Types of relationships to extract. Default is all types."
    ),
    min_confidence: float = typer.Option(0.7, "--min-confidence", help="Minimum confidence score for relationships."),
    edge_collection: str = typer.Option("agent_relationships", help="Edge collection name."),
    entity_collection: str = typer.Option("agent_entities", help="Entity collection name."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
):
    """
    Extract relationships from text using pattern-based or LLM-based extraction.
    
    Examples:
        extract-from-text "ArangoDB is a multi-model database system. It supports graphs, documents, and key-value pairs." --types SIMILAR,PREREQUISITE
        extract-from-text "Before using ArangoDB, you should understand graph theory." --llm --output relationships.json
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize relationship extractor
        extractor = RelationshipExtractor(
            db=db,
            edge_collection_name=edge_collection,
            entity_collection_name=entity_collection
        )
        
        # Validate relationship types
        valid_types = [r.value for r in RelationshipType]
        if relationship_types:
            for rel_type in relationship_types:
                if rel_type not in valid_types:
                    console.print(f"[red]Warning: Invalid relationship type '{rel_type}'. Valid types are: {', '.join(valid_types)}[/red]")
        else:
            relationship_types = valid_types
        
        # Extract relationships
        if use_llm:
            # Use LLM-based extraction if requested
            console.print("[yellow]Using LLM-based relationship extraction (async operation)...[/yellow]")
            
            # Create a simple async function runner
            import asyncio
            relationships = asyncio.run(
                extractor.extract_relationships_with_llm(
                    text=text,
                    relationship_types=relationship_types,
                    min_confidence=min_confidence
                )
            )
        else:
            # Use pattern-based extraction
            console.print("[yellow]Using pattern-based relationship extraction...[/yellow]")
            relationships = extractor.extract_relationships_from_text(
                text=text,
                relationship_types=relationship_types,
                confidence_threshold=min_confidence
            )
        
        # Output results
        if json_output:
            # Format for JSON output
            output = {
                "total": len(relationships),
                "relationships": [format_relationship_for_display(r, include_metadata=True) for r in relationships]
            }
            
            # Save to file if requested
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(output, f, indent=2)
                console.print(f"[green]Extracted {len(relationships)} relationships. Results saved to {output_file}[/green]")
            else:
                # Print as JSON
                console.print(json.dumps(output, indent=2))
        else:
            # Display as table
            console.print(f"[green]Extracted {len(relationships)} relationships:[/green]")
            display_relationships_table(relationships)
            
            # Save to file if requested
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(relationships, f, indent=2)
                console.print(f"[green]Results saved to {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error extracting relationships: {e}[/red]")
        return 1
    
    return 0


@app.command("add-relationship")
def add_relationship(
    source: str = typer.Argument(..., help="Source entity ID or name."),
    target: str = typer.Argument(..., help="Target entity ID or name."),
    relationship_type: str = typer.Argument(..., help="Type of relationship to create."),
    rationale: str = typer.Option(..., "--rationale", "-r", help="Rationale for the relationship (min 50 chars)."),
    confidence: float = typer.Option(0.8, "--confidence", "-c", help="Confidence score (0.0 to 1.0)."),
    valid_from: Optional[str] = typer.Option(None, "--valid-from", help="When the relationship became valid (ISO format)."),
    valid_until: Optional[str] = typer.Option(None, "--valid-until", help="When the relationship stopped being valid (ISO format)."),
    edge_collection: str = typer.Option("agent_relationships", help="Edge collection name."),
    entity_collection: str = typer.Option("agent_entities", help="Entity collection name."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
):
    """
    Create a relationship between two entities with enhanced metadata.
    
    Examples:
        add-relationship "entities/1234" "entities/5678" SIMILAR --rationale "Both documents discuss graph database performance optimization techniques in detail." --confidence 0.9
        add-relationship "ArangoDB" "Graph Theory" PREREQUISITE --rationale "Understanding graph theory concepts is essential before working with ArangoDB graph features."
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize relationship extractor
        extractor = RelationshipExtractor(
            db=db,
            edge_collection_name=edge_collection,
            entity_collection_name=entity_collection
        )
        
        # Validate relationship type
        valid_types = [r.value for r in RelationshipType]
        if relationship_type not in valid_types:
            console.print(f"[yellow]Warning: '{relationship_type}' is not a standard relationship type. Valid types are: {', '.join(valid_types)}[/yellow]")
            
            # Ask for confirmation
            if not typer.confirm(f"Continue with custom relationship type '{relationship_type}'?"):
                return 0
        
        # Validate rationale length
        if len(rationale) < 50:
            console.print(f"[red]Error: Rationale must be at least 50 characters (current: {len(rationale)})[/red]")
            return 1
        
        # Resolve entity IDs if names were provided
        source_id = source
        target_id = target
        
        # Check if IDs are in the correct format (collection/key)
        if "/" not in source_id:
            # Try to find entity by name
            aql = """
            FOR doc IN @@collection
            FILTER doc.name == @name
            LIMIT 1
            RETURN doc
            """
            
            cursor = db.aql.execute(
                aql,
                bind_vars={
                    "@collection": entity_collection,
                    "name": source
                }
            )
            
            results = list(cursor)
            if results:
                source_id = results[0]["_id"]
            else:
                console.print(f"[red]Error: Entity '{source}' not found. Please provide a valid entity ID or name.[/red]")
                return 1
        
        if "/" not in target_id:
            # Try to find entity by name
            aql = """
            FOR doc IN @@collection
            FILTER doc.name == @name
            LIMIT 1
            RETURN doc
            """
            
            cursor = db.aql.execute(
                aql,
                bind_vars={
                    "@collection": entity_collection,
                    "name": target
                }
            )
            
            results = list(cursor)
            if results:
                target_id = results[0]["_id"]
            else:
                console.print(f"[red]Error: Entity '{target}' not found. Please provide a valid entity ID or name.[/red]")
                return 1
        
        # Parse dates if provided
        valid_from_dt = None
        valid_until_dt = None
        
        if valid_from:
            try:
                valid_from_dt = datetime.fromisoformat(valid_from.replace("Z", "+00:00"))
            except ValueError:
                console.print(f"[red]Error: Invalid date format for valid_from. Use ISO format (YYYY-MM-DDTHH:MM:SS+00:00).[/red]")
                return 1
        
        if valid_until:
            try:
                valid_until_dt = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            except ValueError:
                console.print(f"[red]Error: Invalid date format for valid_until. Use ISO format (YYYY-MM-DDTHH:MM:SS+00:00).[/red]")
                return 1
        
        # Create the relationship
        relationship = extractor.create_document_relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            rationale=rationale,
            confidence=confidence,
            valid_from=valid_from_dt,
            valid_until=valid_until_dt
        )
        
        # Output results
        if json_output:
            # Format for JSON output
            output = format_relationship_for_display(relationship, include_metadata=True)
            console.print(json.dumps(output, indent=2))
        else:
            console.print(f"[green]Successfully created {relationship_type} relationship between {source_id} and {target_id}[/green]")
            
            # Display as table
            display_relationships_table([relationship])
        
    except Exception as e:
        console.print(f"[red]Error creating relationship: {e}[/red]")
        return 1
    
    return 0


@app.command("find-similar-documents")
def find_similar_documents(
    document_id: str = typer.Argument(..., help="Document ID to find similar documents for."),
    collection_name: str = typer.Option("agent_memories", help="Collection to search in."),
    min_similarity: float = typer.Option(0.75, "--min-similarity", help="Minimum similarity score."),
    max_results: int = typer.Option(5, "--max-results", "-n", help="Maximum number of results."),
    create_relationships: bool = typer.Option(False, "--create-relationships", help="Create SIMILAR relationships."),
    edge_collection: str = typer.Option("agent_relationships", help="Edge collection for new relationships."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
):
    """
    Find documents similar to a given document and optionally create relationships.
    
    Examples:
        find-similar-documents "agent_memories/12345" --min-similarity 0.8
        find-similar-documents "agent_memories/12345" --create-relationships --max-results 10
    """
    try:
        # Get database connection
        db = get_db()
        
        # Initialize relationship extractor
        extractor = RelationshipExtractor(
            db=db,
            edge_collection_name=edge_collection
        )
        
        # Get the source document
        try:
            collection_name, key = document_id.split("/")
            source_doc = db.collection(collection_name).get(key)
            if not source_doc:
                console.print(f"[red]Error: Document {document_id} not found.[/red]")
                return 1
        except ValueError:
            console.print(f"[red]Error: Invalid document ID format. Use 'collection/key'.[/red]")
            return 1
        
        # Check for embedding
        if "embedding" not in source_doc:
            console.print(f"[red]Error: Document {document_id} does not have an embedding field.[/red]")
            return 1
        
        # Find similar documents using ArangoDB vector search
        console.print(f"[yellow]Finding documents similar to {document_id}...[/yellow]")
        
        # Use ArangoDB's vector search capability
        aql = """
        FOR doc IN @@collection
        FILTER doc._id != @doc_id
        FILTER doc.embedding != null
        LET score = APPROX_NEAR_COSINE(doc.embedding, @embedding)
        FILTER score > @min_similarity
        SORT score DESC
        LIMIT @max_results
        RETURN {
            doc: doc,
            score: score
        }
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                "@collection": collection_name,
                "doc_id": document_id,
                "embedding": source_doc["embedding"],
                "min_similarity": min_similarity,
                "max_results": max_results
            }
        )
        
        results = list(cursor)
        
        # Format results for display
        similar_docs = []
        for result in results:
            doc = result["doc"]
            score = result["score"]
            
            similar_docs.append({
                "id": doc["_id"],
                "name": doc.get("name", doc.get("title", doc["_id"])),
                "score": score,
                "type": doc.get("type", "Unknown")
            })
        
        # Create relationships if requested
        created_relationships = []
        if create_relationships and similar_docs:
            console.print(f"[yellow]Creating SIMILAR relationships...[/yellow]")
            
            for doc_info in similar_docs:
                target_id = doc_info["id"]
                
                # Generate a meaningful rationale
                source_name = source_doc.get("name", source_doc.get("title", source_doc["_id"]))
                target_name = doc_info["name"]
                similarity = doc_info["score"]
                
                rationale = f"Documents '{source_name}' and '{target_name}' are semantically similar with a cosine similarity score of {similarity:.2f}. They likely cover related topics and concepts that would be helpful to consider together."
                
                try:
                    # Create the relationship
                    relationship = extractor.create_document_relationship(
                        source_id=document_id,
                        target_id=target_id,
                        relationship_type="SIMILAR",
                        rationale=rationale,
                        confidence=similarity,
                        metadata={"similarity_score": similarity}
                    )
                    
                    created_relationships.append(relationship)
                except Exception as e:
                    console.print(f"[red]Error creating relationship to {target_id}: {e}[/red]")
        
        # Output results
        if json_output:
            # Format for JSON output
            output = {
                "query_document": document_id,
                "total_results": len(similar_docs),
                "similar_documents": similar_docs
            }
            
            if created_relationships:
                output["created_relationships"] = len(created_relationships)
            
            console.print(json.dumps(output, indent=2))
        else:
            # Display as table
            if similar_docs:
                table = Table(title=f"Similar Documents ({len(similar_docs)} found)")
                
                # Add columns
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Type", style="yellow")
                table.add_column("Similarity", style="blue")
                
                # Add rows
                for doc in similar_docs:
                    table.add_row(
                        doc["id"],
                        doc["name"],
                        doc["type"],
                        f"{doc['score']:.3f}"
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No similar documents found.[/yellow]")
            
            # Show created relationships
            if created_relationships:
                console.print(f"[green]Created {len(created_relationships)} SIMILAR relationships:[/green]")
                display_relationships_table(created_relationships)
        
    except Exception as e:
        console.print(f"[red]Error finding similar documents: {e}[/red]")
        return 1
    
    return 0


@app.command("find-relationships")
def find_relationships(
    entity_id: str = typer.Argument(..., help="Entity ID to find relationships for."),
    direction: str = typer.Option("both", "--direction", "-d", help="Relationship direction (outbound, inbound, both)."),
    relationship_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by relationship type."),
    min_confidence: float = typer.Option(0.0, "--min-confidence", help="Minimum confidence score."),
    edge_collection: str = typer.Option("agent_relationships", help="Edge collection name."),
    include_invalid: bool = typer.Option(False, "--include-invalid", help="Include invalidated relationships."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
):
    """
    Find relationships for a given entity.
    
    Examples:
        find-relationships "agent_memories/12345" --direction outbound
        find-relationships "agent_entities/user123" --type SIMILAR --min-confidence 0.8
    """
    try:
        # Get database connection
        db = get_db()
        
        # Validate direction
        valid_directions = ["outbound", "inbound", "both"]
        if direction.lower() not in valid_directions:
            console.print(f"[red]Error: Invalid direction '{direction}'. Valid options are: {', '.join(valid_directions)}[/red]")
            return 1
        
        # Build AQL query based on parameters
        aql_direction = direction.lower()
        
        # Base query
        if aql_direction == "outbound":
            aql = """
            FOR v, e IN OUTBOUND @entity_id GRAPH @graph_name
            """
        elif aql_direction == "inbound":
            aql = """
            FOR v, e IN INBOUND @entity_id GRAPH @graph_name
            """
        else:  # both
            aql = """
            FOR v, e IN ANY @entity_id GRAPH @graph_name
            """
        
        # Add filters
        filters = []
        
        # Filter by relationship type
        if relationship_type:
            filters.append("e.type == @relationship_type")
        
        # Filter by confidence
        if min_confidence > 0:
            filters.append("e.confidence >= @min_confidence")
        
        # Filter out invalid relationships unless requested
        if not include_invalid:
            filters.append("(e.invalid_at == null OR e.invalid_at == '')")
        
        # Add filters to query
        if filters:
            aql += "\nFILTER " + " AND ".join(filters)
        
        # Add sort and return
        aql += """
        SORT e.confidence DESC
        RETURN {
            edge: e,
            vertex: v
        }
        """
        
        # Execute query
        bind_vars = {
            "entity_id": entity_id,
            "graph_name": "knowledge_graph"  # This should match your graph name
        }
        
        if relationship_type:
            bind_vars["relationship_type"] = relationship_type
        
        if min_confidence > 0:
            bind_vars["min_confidence"] = min_confidence
        
        cursor = db.aql.execute(aql, bind_vars=bind_vars)
        
        # Process results
        results = []
        for item in cursor:
            edge = item["edge"]
            vertex = item["vertex"]
            
            # Format relationship for output
            relationship = {
                "_id": edge["_id"],
                "_key": edge["_key"],
                "source": edge["_from"],
                "target": edge["_to"],
                "type": edge.get("type", ""),
                "confidence": edge.get("confidence", 0.0),
                "rationale": edge.get("rationale", ""),
                "created_at": edge.get("created_at", ""),
                "valid_at": edge.get("valid_at", ""),
                "invalid_at": edge.get("invalid_at", ""),
                "related_entity": {
                    "_id": vertex["_id"],
                    "name": vertex.get("name", vertex.get("title", vertex["_id"])),
                    "type": vertex.get("type", "Unknown")
                }
            }
            
            results.append(relationship)
        
        # Output results
        if json_output:
            # Format for JSON output
            output = {
                "entity_id": entity_id,
                "direction": direction,
                "total_relationships": len(results),
                "relationships": results
            }
            
            console.print(json.dumps(output, indent=2))
        else:
            # Display as table
            if results:
                console.print(f"[green]Found {len(results)} relationships for {entity_id} ({direction}):[/green]")
                display_relationships_table(results)
            else:
                console.print(f"[yellow]No relationships found for {entity_id} ({direction}).[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error finding relationships: {e}[/red]")
        return 1
    
    return 0


@app.command("validate-relationship")
def validate_relationship(
    relationship_key: str = typer.Argument(..., help="Relationship key or ID to validate."),
    llm_validation: bool = typer.Option(False, "--llm", help="Use LLM for validation (requires LLM client)."),
    edge_collection: str = typer.Option("agent_relationships", help="Edge collection name."),
    update_confidence: bool = typer.Option(False, "--update-confidence", help="Update confidence score based on validation."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
):
    """
    Validate a relationship for quality and correctness.
    
    Examples:
        validate-relationship "12345" --edge-collection agent_relationships
        validate-relationship "agent_relationships/12345" --llm-validation --update-confidence
    """
    try:
        # Get database connection
        db = get_db()
        
        # Parse relationship key/ID
        if "/" in relationship_key:
            collection, key = relationship_key.split("/")
        else:
            collection = edge_collection
            key = relationship_key
        
        # Get relationship document
        relationship = db.collection(collection).get(key)
        if not relationship:
            console.print(f"[red]Error: Relationship {collection}/{key} not found.[/red]")
            return 1
        
        # Perform validation checks
        validation_results = []
        
        # Basic validation checks
        if "type" not in relationship or not relationship["type"]:
            validation_results.append(("Type", "Missing or empty", "ERROR"))
        else:
            validation_results.append(("Type", relationship["type"], "OK"))
        
        if "rationale" not in relationship or not relationship["rationale"]:
            validation_results.append(("Rationale", "Missing or empty", "ERROR"))
        elif len(relationship["rationale"]) < 50:
            validation_results.append(("Rationale", f"Too short ({len(relationship['rationale'])} chars)", "WARNING"))
        else:
            validation_results.append(("Rationale", f"{len(relationship['rationale'])} chars", "OK"))
        
        if "confidence" not in relationship:
            validation_results.append(("Confidence", "Missing", "ERROR"))
        elif not isinstance(relationship["confidence"], (int, float)):
            validation_results.append(("Confidence", f"Invalid type: {type(relationship['confidence'])}", "ERROR"))
        elif relationship["confidence"] < 0 or relationship["confidence"] > 1:
            validation_results.append(("Confidence", f"Out of range: {relationship['confidence']}", "ERROR"))
        else:
            validation_results.append(("Confidence", f"{relationship['confidence']:.2f}", "OK"))
        
        # Check temporal metadata
        if "valid_at" not in relationship:
            validation_results.append(("Temporal", "Missing valid_at", "WARNING"))
        else:
            validation_results.append(("Temporal", "Has valid_at", "OK"))
        
        # Validate relationship source and target exist
        source_id = relationship["_from"]
        target_id = relationship["_to"]
        
        source_collection, source_key = source_id.split("/")
        target_collection, target_key = target_id.split("/")
        
        source_exists = db.collection(source_collection).has(source_key)
        target_exists = db.collection(target_collection).has(target_key)
        
        if not source_exists:
            validation_results.append(("Source", f"{source_id} does not exist", "ERROR"))
        else:
            validation_results.append(("Source", f"{source_id} exists", "OK"))
        
        if not target_exists:
            validation_results.append(("Target", f"{target_id} does not exist", "ERROR"))
        else:
            validation_results.append(("Target", f"{target_id} exists", "OK"))
        
        # Calculate overall validation status
        errors = sum(1 for _, _, status in validation_results if status == "ERROR")
        warnings = sum(1 for _, _, status in validation_results if status == "WARNING")
        
        if errors > 0:
            overall_status = "INVALID"
        elif warnings > 0:
            overall_status = "WARNING"
        else:
            overall_status = "VALID"
        
        # Output results
        if json_output:
            # Format for JSON output
            output = {
                "relationship_id": f"{collection}/{key}",
                "status": overall_status,
                "errors": errors,
                "warnings": warnings,
                "checks": [
                    {"field": field, "value": value, "status": status}
                    for field, value, status in validation_results
                ],
                "relationship": format_relationship_for_display(relationship, include_metadata=True)
            }
            
            console.print(json.dumps(output, indent=2))
        else:
            # Display as table
            table = Table(title=f"Relationship Validation: {collection}/{key}")
            
            # Add columns
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")
            table.add_column("Status", style="yellow")
            
            # Add rows
            for field, value, status in validation_results:
                color = "green" if status == "OK" else "yellow" if status == "WARNING" else "red"
                table.add_row(field, str(value), f"[{color}]{status}[/{color}]")
            
            console.print(table)
            
            # Display overall status
            status_color = "green" if overall_status == "VALID" else "yellow" if overall_status == "WARNING" else "red"
            console.print(f"Overall status: [{status_color}]{overall_status}[/{status_color}]")
            console.print(f"Errors: {errors}, Warnings: {warnings}")
        
    except Exception as e:
        console.print(f"[red]Error validating relationship: {e}[/red]")
        return 1
    
    return 0


# Main entry point
if __name__ == "__main__":
    app()