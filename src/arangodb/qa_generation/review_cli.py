"""
Q&A Edge Review CLI Module

Provides CLI commands for reviewing low-confidence Q&A edges,
allowing manual inspection and approval/rejection of edges
that require human verification.
"""

import sys
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from arangodb.core.db_connection_wrapper import DatabaseOperations
from arangodb.core.constants import CONFIG

app = typer.Typer(
    help="Commands for reviewing Q&A edges",
    no_args_is_help=True
)

console = Console()


class ReviewAction(str, Enum):
    """Review actions for Q&A edges."""
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    SKIP = "skip"


@app.command()
def list_pending(
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of edges to list"),
    min_confidence: float = typer.Option(0.0, "--min-confidence", "-c", help="Minimum confidence threshold"),
    max_confidence: float = typer.Option(0.7, "--max-confidence", "-C", help="Maximum confidence threshold"),
    collection: str = typer.Option("relationships", "--collection", "-e", help="Edge collection name"),
):
    """
    List pending Q&A edges for review.
    
    Lists edges with review_status = 'pending' and allows filtering by confidence.
    """
    # Initialize database
    db_ops = DatabaseOperations.get_instance()
    
    # Build AQL query
    aql = f"""
    FOR edge IN {collection}
    FILTER edge.type == "qa_derived"
    FILTER edge.review_status == "pending"
    FILTER edge.confidence >= @min_confidence
    FILTER edge.confidence <= @max_confidence
    SORT edge.confidence ASC
    LIMIT @limit
    RETURN {{
        _key: edge._key,
        _id: edge._id,
        _from: edge._from,
        _to: edge._to,
        question: edge.question,
        answer: SUBSTRING(edge.answer, 0, 150) + "...",
        confidence: edge.confidence,
        context_confidence: edge.context_confidence,
        source_document_id: edge.source_document_id
    }}
    """
    
    # Execute query
    bind_vars = {
        "min_confidence": min_confidence,
        "max_confidence": max_confidence,
        "limit": limit
    }
    
    try:
        cursor = db_ops.db.aql.execute(aql, bind_vars=bind_vars)
        edges = list(cursor)
    except Exception as e:
        console.print(f"[bold red]Error listing pending edges: {e}[/bold red]")
        return
    
    # Display results
    if not edges:
        console.print("[yellow]No pending Q&A edges found for review.[/yellow]")
        return
    
    # Create table
    table = Table(title="Pending Q&A Edges for Review", box=box.SIMPLE_HEAVY)
    table.add_column("Key", style="cyan")
    table.add_column("From", style="blue")
    table.add_column("To", style="blue")
    table.add_column("Question", style="green")
    table.add_column("Confidence", style="magenta")
    table.add_column("Context Confidence", style="magenta")
    
    for edge in edges:
        from_parts = edge["_from"].split("/")
        to_parts = edge["_to"].split("/")
        
        from_label = from_parts[1] if len(from_parts) > 1 else edge["_from"]
        to_label = to_parts[1] if len(to_parts) > 1 else edge["_to"]
        
        table.add_row(
            edge["_key"], 
            from_label, 
            to_label, 
            edge["question"][:60] + "...", 
            f"{edge['confidence']:.2f}",
            f"{edge.get('context_confidence', 0):.2f}"
        )
    
    console.print(table)
    console.print(f"\nFound {len(edges)} edges pending review.")
    console.print("Use 'review <edge_key>' to review a specific edge.")


@app.command()
def review(
    edge_key: str = typer.Argument(..., help="Key of the edge to review"),
    collection: str = typer.Option("relationships", "--collection", "-e", help="Edge collection name"),
):
    """
    Review a specific Q&A edge.
    
    Displays detailed information about the edge and allows approving or rejecting it.
    """
    # Initialize database
    db_ops = DatabaseOperations.get_instance()
    
    # Get edge details
    try:
        edge = db_ops.db.collection(collection).get(edge_key)
        if not edge:
            console.print(f"[bold red]Edge with key '{edge_key}' not found.[/bold red]")
            return
    except Exception as e:
        console.print(f"[bold red]Error retrieving edge: {e}[/bold red]")
        return
    
    # Get entity information
    from_entity = _get_entity_by_id(db_ops, edge["_from"])
    to_entity = _get_entity_by_id(db_ops, edge["_to"])
    
    # Display edge details
    console.print(Panel.fit(
        f"[bold cyan]Edge ID:[/bold cyan] {edge['_id']}\n"
        f"[bold cyan]Type:[/bold cyan] {edge.get('type', 'Unknown')}\n"
        f"[bold cyan]From:[/bold cyan] {from_entity.get('name', edge['_from'])}\n"
        f"[bold cyan]To:[/bold cyan] {to_entity.get('name', edge['_to'])}\n"
        f"[bold cyan]Question:[/bold cyan] {edge.get('question', 'N/A')}\n\n"
        f"[bold cyan]Answer:[/bold cyan] {edge.get('answer', 'N/A')}\n\n"
        f"[bold cyan]Thinking:[/bold cyan] {edge.get('thinking', 'N/A')}\n\n"
        f"[bold cyan]Rationale:[/bold cyan] {edge.get('rationale', 'N/A')}\n"
        f"[bold cyan]Context Rationale:[/bold cyan] {edge.get('context_rationale', 'N/A')}\n\n"
        f"[bold cyan]Confidence:[/bold cyan] {edge.get('confidence', 0):.2f}\n"
        f"[bold cyan]Context Confidence:[/bold cyan] {edge.get('context_confidence', 0):.2f}\n"
        f"[bold cyan]Source Document:[/bold cyan] {edge.get('source_document_id', 'Unknown')}\n",
        title="Q&A Edge Details",
        border_style="blue"
    ))
    
    # Get review action
    action = typer.prompt(
        "Review action",
        type=ReviewAction,
        default=ReviewAction.APPROVE
    )
    
    if action == ReviewAction.SKIP:
        console.print("[yellow]Review skipped.[/yellow]")
        return
    
    if action == ReviewAction.EDIT:
        console.print("[yellow]Edge editing is not yet implemented.[/yellow]")
        return
    
    # Apply the review action
    if action == ReviewAction.APPROVE:
        _update_edge_review_status(db_ops, collection, edge_key, "approved")
        console.print("[green]Edge approved successfully.[/green]")
    elif action == ReviewAction.REJECT:
        _update_edge_review_status(db_ops, collection, edge_key, "rejected")
        console.print("[red]Edge rejected.[/red]")


@app.command()
def batch_review(
    min_confidence: float = typer.Option(0.6, "--min-confidence", "-c", help="Minimum confidence threshold"),
    max_confidence: float = typer.Option(0.7, "--max-confidence", "-C", help="Maximum confidence threshold"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of edges to process"),
    collection: str = typer.Option("relationships", "--collection", "-e", help="Edge collection name"),
):
    """
    Batch review of Q&A edges within a confidence range.
    
    Allows reviewing multiple edges in sequence.
    """
    # Initialize database
    db_ops = DatabaseOperations.get_instance()
    
    # Build AQL query
    aql = f"""
    FOR edge IN {collection}
    FILTER edge.type == "qa_derived"
    FILTER edge.review_status == "pending"
    FILTER edge.confidence >= @min_confidence
    FILTER edge.confidence <= @max_confidence
    SORT edge.confidence ASC
    LIMIT @limit
    RETURN edge
    """
    
    # Execute query
    bind_vars = {
        "min_confidence": min_confidence,
        "max_confidence": max_confidence,
        "limit": limit
    }
    
    try:
        cursor = db_ops.db.aql.execute(aql, bind_vars=bind_vars)
        edges = list(cursor)
    except Exception as e:
        console.print(f"[bold red]Error retrieving edges: {e}[/bold red]")
        return
    
    if not edges:
        console.print("[yellow]No matching edges found for batch review.[/yellow]")
        return
    
    console.print(f"[bold]Found {len(edges)} edges for batch review.[/bold]")
    
    # Process edges in sequence
    approved = 0
    rejected = 0
    skipped = 0
    
    for edge in edges:
        console.print(f"\n[bold cyan]===== Reviewing Edge {edge['_key']} =====[/bold cyan]")
        
        # Get entity information
        from_entity = _get_entity_by_id(db_ops, edge["_from"])
        to_entity = _get_entity_by_id(db_ops, edge["_to"])
        
        # Display minimal edge details
        console.print(
            f"[bold]Question:[/bold] {edge.get('question', 'N/A')}\n"
            f"[bold]Answer:[/bold] {edge.get('answer', 'N/A')[:150]}...\n"
            f"[bold]From:[/bold] {from_entity.get('name', edge['_from'])}\n"
            f"[bold]To:[/bold] {to_entity.get('name', edge['_to'])}\n"
            f"[bold]Confidence:[/bold] {edge.get('confidence', 0):.2f}"
        )
        
        # Get review action
        action = typer.prompt(
            "Review action",
            type=ReviewAction,
            default=ReviewAction.APPROVE
        )
        
        if action == ReviewAction.SKIP:
            skipped += 1
            continue
        
        if action == ReviewAction.EDIT:
            console.print("[yellow]Edge editing is not yet implemented. Skipping.[/yellow]")
            skipped += 1
            continue
        
        # Apply the review action
        if action == ReviewAction.APPROVE:
            _update_edge_review_status(db_ops, collection, edge["_key"], "approved")
            approved += 1
        elif action == ReviewAction.REJECT:
            _update_edge_review_status(db_ops, collection, edge["_key"], "rejected")
            rejected += 1
    
    # Display summary
    console.print(f"\n[bold]Batch Review Summary:[/bold]")
    console.print(f"Approved: [green]{approved}[/green]")
    console.print(f"Rejected: [red]{rejected}[/red]")
    console.print(f"Skipped: [yellow]{skipped}[/yellow]")


@app.command()
def generate_review_aql(
    confidence_threshold: float = typer.Option(0.7, "--threshold", "-t", help="Confidence threshold"),
    collection: str = typer.Option("relationships", "--collection", "-e", help="Edge collection name"),
):
    """
    Generate AQL queries for finding problematic connections.
    
    Outputs AQL queries that can be run directly in the ArangoDB web interface
    or arangosh to find edges that need review.
    """
    queries = [
        {
            "description": "Low confidence Q&A edges",
            "query": f"""
            FOR edge IN {collection}
            FILTER edge.type == "qa_derived"
            FILTER edge.confidence < {confidence_threshold}
            SORT edge.confidence ASC
            LIMIT 100
            RETURN {{
                _key: edge._key,
                _id: edge._id,
                from: edge._from,
                to: edge._to,
                question: edge.question,
                confidence: edge.confidence,
                context_confidence: edge.context_confidence
            }}
            """
        },
        {
            "description": "Contradicting Q&A edges",
            "query": f"""
            FOR edge1 IN {collection}
            FILTER edge1.type == "qa_derived"
            FOR edge2 IN {collection}
            FILTER edge2.type == "qa_derived"
            FILTER edge1._from == edge2._from AND edge1._to == edge2._to
            FILTER edge1._key != edge2._key
            FILTER ABS(edge1.confidence - edge2.confidence) > 0.3
            RETURN {{
                edge1: {{
                    _key: edge1._key,
                    question: edge1.question,
                    answer: edge1.answer,
                    confidence: edge1.confidence
                }},
                edge2: {{
                    _key: edge2._key,
                    question: edge2.question,
                    answer: edge2.answer,
                    confidence: edge2.confidence
                }}
            }}
            """
        },
        {
            "description": "Missing context rationale",
            "query": f"""
            FOR edge IN {collection}
            FILTER edge.type == "qa_derived"
            FILTER edge.context_rationale == NULL OR edge.context_rationale == ""
            RETURN {{
                _key: edge._key,
                _id: edge._id,
                question: edge.question,
                confidence: edge.confidence
            }}
            """
        }
    ]
    
    # Display queries
    for query_info in queries:
        console.print(f"\n[bold cyan]{query_info['description']}[/bold cyan]")
        console.print(Panel(query_info['query'], border_style="blue"))


def _get_entity_by_id(db_ops: DatabaseOperations, entity_id: str) -> Dict[str, Any]:
    """Get entity document by ID."""
    try:
        parts = entity_id.split("/")
        if len(parts) != 2:
            return {"name": entity_id}
        
        collection_name, key = parts
        return db_ops.db.collection(collection_name).get(key) or {"name": entity_id}
    except Exception as e:
        logger.error(f"Error retrieving entity {entity_id}: {e}")
        return {"name": entity_id}


def _update_edge_review_status(
    db_ops: DatabaseOperations, 
    collection: str, 
    edge_key: str, 
    status: str
) -> bool:
    """Update edge review status."""
    try:
        db_ops.db.collection(collection).update(
            edge_key, 
            {
                "review_status": status,
                "reviewed_by": "manual_review",
                "review_timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error updating edge review status: {e}")
        return False


if __name__ == "__main__":
    app()