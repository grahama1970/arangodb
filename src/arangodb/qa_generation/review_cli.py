"""
Q&A Edge Review CLI Module
Module: review_cli.py

Provides CLI commands for reviewing QA-derived edges,
allowing manual inspection and approval/rejection of edges
created from Q&A pairs in the knowledge graph.
"""

import sys
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from ..core.db_connection_wrapper import DatabaseOperations
from ..core.constants import CONFIG
from .edge_generator import RELATIONSHIP_TYPE_QA_DERIVED

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


class ReviewStatus(str, Enum):
    """Review status options for QA edges."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ALL = "all"


class ConfidenceLevel(str, Enum):
    """Confidence level filters for QA edges."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ALL = "all"


def get_db_connection() -> DatabaseOperations:
    """Get a connection to ArangoDB."""
    from arango import ArangoClient
    
    # Get connection details from config
    hosts = CONFIG.get("database", {}).get("hosts", "http://localhost:8529")
    db_name = CONFIG.get("database", {}).get("name", "_system")
    username = CONFIG.get("database", {}).get("username", "root")
    password = CONFIG.get("database", {}).get("password", "")
    
    # Connect to ArangoDB
    client = ArangoClient(hosts=hosts)
    db = client.db(db_name, username=username, password=password)
    
    return DatabaseOperations(db)


def get_edge_collection() -> str:
    """Get the edge collection name from config."""
    try:
        return CONFIG["graph"]["edge_collections"][0]
    except (KeyError, IndexError):
        return "relationships"


def confidence_filter(level: ConfidenceLevel) -> str:
    """Generate AQL filter condition for confidence level."""
    filters = {
        ConfidenceLevel.LOW: "edge.confidence < 0.7",
        ConfidenceLevel.MEDIUM: "edge.confidence >= 0.7 AND edge.confidence < 0.9",
        ConfidenceLevel.HIGH: "edge.confidence >= 0.9",
        ConfidenceLevel.ALL: "true"
    }
    return filters[level]


@app.command("list")
def list_qa_edges(
    status: ReviewStatus = typer.Option(
        ReviewStatus.PENDING,
        "--status",
        "-s",
        help="Filter by review status"
    ),
    confidence: ConfidenceLevel = typer.Option(
        ConfidenceLevel.ALL,
        "--confidence",
        "-c",
        help="Filter by confidence level"
    ),
    document_id: Optional[str] = typer.Option(
        None,
        "--document",
        "-d",
        help="Filter by source document ID"
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-n",
        help="Maximum number of edges to list"
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        "-o",
        help="Offset for pagination"
    ),
    collection: str = typer.Option(
        "",
        "--collection",
        "-e",
        help="Edge collection name (overrides config)"
    )
):
    """
    List Q&A-derived edges with filtering options.
    
    This command displays a list of QA edges and their properties,
    with options to filter by status, confidence, and source document.
    """
    console.print("[bold blue]Listing QA-derived edges[/]")
    
    # Get database connection
    db = get_db_connection()
    collection_name = collection or get_edge_collection()
    
    # Build filter conditions
    filter_conditions = [f"edge.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'"]
    bind_vars = {
        "limit": limit,
        "offset": offset
    }
    
    # Add status filter
    if status != ReviewStatus.ALL:
        filter_conditions.append("edge.review_status == @status")
        bind_vars["status"] = status.value
    
    # Add confidence filter
    filter_conditions.append(confidence_filter(confidence))
    
    # Add document filter
    if document_id:
        filter_conditions.append("edge.source_document_id == @document_id")
        bind_vars["document_id"] = document_id
    
    # Combine filter conditions
    filter_clause = " AND ".join(filter_conditions)
    
    # Execute query
    query = f"""
    FOR edge IN {collection_name}
        FILTER {filter_clause}
        LET from_entity = DOCUMENT(edge._from)
        LET to_entity = DOCUMENT(edge._to)
        SORT edge.created_at DESC
        LIMIT @offset, @limit
        RETURN {{
            edge: edge,
            from_entity: from_entity,
            to_entity: to_entity
        }}
    """
    
    # Execute query with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Fetching QA edges...", total=None)
        
        # Try to execute query
        try:
            cursor = db.db.aql.execute(query, bind_vars=bind_vars)
            results = list(cursor)
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            return
        
        progress.update(task, completed=True, description="Complete")
    
    # Display results
    if not results:
        console.print("[yellow]No QA edges found matching the criteria[/]")
        return
    
    # Create table
    table = Table(title=f"QA-Derived Edges ({len(results)} results)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Relationship", style="magenta")
    table.add_column("Question", style="blue")
    table.add_column("Confidence", style="green")
    table.add_column("Status", style="yellow")
    
    # Add rows
    for result in results:
        edge = result["edge"]
        from_entity = result.get("from_entity", {})
        to_entity = result.get("to_entity", {})
        
        # Format relationship
        relationship = f"{from_entity.get('name', '?')} → {to_entity.get('name', '?')}"
        
        # Format question
        question = edge.get("question", "")
        if len(question) > 50:
            question = question[:47] + "..."
        
        # Format confidence
        confidence = edge.get("confidence", 0)
        confidence_str = f"{confidence:.2f}"
        
        # Format status
        status = edge.get("review_status", "pending")
        
        # Add row
        table.add_row(
            edge.get("_key", ""),
            relationship,
            question,
            confidence_str,
            status
        )
    
    # Display table
    console.print(table)
    
    # Get total count
    count_query = f"""
    RETURN LENGTH(
        FOR edge IN {collection_name}
            FILTER {filter_clause}
            RETURN 1
    )
    """
    
    try:
        count_cursor = db.db.aql.execute(count_query, bind_vars=bind_vars)
        total_count = list(count_cursor)[0]
        
        # Show pagination info if needed
        if total_count > limit:
            console.print(f"Showing {offset+1}-{min(offset+limit, total_count)} of {total_count} QA edges")
            console.print("Use --offset and --limit to navigate")
    except Exception as e:
        console.print(f"[bold yellow]Warning:[/] Could not get total count: {str(e)}")


@app.command("view")
def view_qa_edge(
    edge_id: str = typer.Argument(
        ...,
        help="Edge ID or key to view"
    ),
    collection: str = typer.Option(
        "",
        "--collection",
        "-e",
        help="Edge collection name (overrides config)"
    )
):
    """
    View detailed information about a QA-derived edge.
    
    Displays complete information about a specific QA edge,
    including its source entities, question/answer content,
    and contextual information.
    """
    console.print(f"[bold blue]Viewing QA edge: {edge_id}[/]")
    
    # Get database connection
    db = get_db_connection()
    collection_name = collection or get_edge_collection()
    
    # Add collection prefix if ID is a key
    if "/" not in edge_id:
        edge_id = f"{collection_name}/{edge_id}"
    
    # Get edge details
    query = """
    LET edge = DOCUMENT(@edge_id)
    LET from_entity = DOCUMENT(edge._from)
    LET to_entity = DOCUMENT(edge._to)
    LET source_doc = edge.source_document_id ? DOCUMENT(edge.source_document_id) : null
    
    RETURN {
        edge: edge,
        from_entity: from_entity,
        to_entity: to_entity,
        source_doc: source_doc
    }
    """
    
    # Execute query
    try:
        cursor = db.db.aql.execute(query, bind_vars={"edge_id": edge_id})
        results = list(cursor)
        
        if not results:
            console.print(f"[bold red]Error:[/] Edge {edge_id} not found")
            return
        
        # Get result
        result = results[0]
        edge = result["edge"]
        from_entity = result["from_entity"]
        to_entity = result["to_entity"]
        source_doc = result["source_doc"]
        
        # Print edge details
        console.print("\n[bold]Edge Information:[/]")
        console.print(f"ID: {edge['_id']}")
        console.print(f"Type: {edge.get('type', 'Unknown')}")
        console.print(f"Created: {edge.get('created_at', 'Unknown')}")
        console.print(f"Review Status: {edge.get('review_status', 'pending')}")
        
        # Print entities
        console.print("\n[bold]Entities:[/]")
        console.print(f"From: {from_entity.get('name', '?')} ({from_entity.get('type', '?')})")
        console.print(f"To: {to_entity.get('name', '?')} ({to_entity.get('type', '?')})")
        
        # Print Q&A content
        console.print("\n[bold]Q&A Content:[/]")
        console.print(f"Question: {edge.get('question', 'N/A')}")
        console.print(f"Answer: {edge.get('answer', 'N/A')}")
        console.print(f"Thinking: {edge.get('thinking', 'N/A')}")
        console.print(f"Question Type: {edge.get('question_type', 'N/A')}")
        
        # Print confidence metrics
        console.print("\n[bold]Confidence Metrics:[/]")
        console.print(f"Edge Confidence: {edge.get('confidence', 0):.2f}")
        console.print(f"Context Confidence: {edge.get('context_confidence', 0):.2f}")
        console.print(f"Weight: {edge.get('weight', 0):.2f}")
        
        # Print context information
        console.print("\n[bold]Context Information:[/]")
        console.print(f"Source Document: {source_doc.get('title', source_doc.get('_id', 'Unknown')) if source_doc else 'Unknown'}")
        console.print(f"Source Section: {edge.get('source_section', 'N/A')}")
        console.print(f"Evidence Blocks: {len(edge.get('evidence_blocks', []))}")
        console.print(f"Context Rationale: {edge.get('context_rationale', 'N/A')}")
        
        # Print hierarchical context as JSON
        if edge.get("hierarchical_context"):
            console.print("\n[bold]Hierarchical Context:[/]")
            console.print(json.dumps(edge["hierarchical_context"], indent=2))
        
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        return


@app.command("update-status")
def update_status(
    edge_id: str = typer.Argument(
        ...,
        help="Edge ID or key to update"
    ),
    status: ReviewStatus = typer.Option(
        ...,
        "--status",
        "-s",
        help="New review status"
    ),
    notes: Optional[str] = typer.Option(
        None,
        "--notes",
        "-n",
        help="Review notes or reason for decision"
    ),
    collection: str = typer.Option(
        "",
        "--collection",
        "-e",
        help="Edge collection name (overrides config)"
    )
):
    """
    Update the review status of a QA-derived edge.
    
    Changes the review status of a specific QA edge to approved,
    rejected, or pending, with optional notes about the decision.
    """
    console.print(f"[bold blue]Updating status for QA edge: {edge_id}[/]")
    
    # Skip "all" status
    if status == ReviewStatus.ALL:
        console.print("[bold red]Error:[/] Cannot set status to 'all'")
        return
    
    # Get database connection
    db = get_db_connection()
    collection_name = collection or get_edge_collection()
    
    # Add collection prefix if ID is a key
    if "/" not in edge_id:
        edge_id = f"{collection_name}/{edge_id}"
    
    # Update edge
    update_doc = {
        "review_status": status.value,
        "reviewed_by": "cli_user",
        "review_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Add notes if provided
    if notes:
        update_doc["review_notes"] = notes
    
    # Execute update
    try:
        # First check if edge exists
        edge = db.db.document(edge_id)
        if edge.get("type") != RELATIONSHIP_TYPE_QA_DERIVED:
            console.print(f"[bold red]Error:[/] Edge {edge_id} is not a QA-derived edge")
            return
        
        # Update edge
        db.db.update_document(edge_id, update_doc)
        console.print(f"[bold green][/] Updated status to {status.value}")
        
        # Get updated edge
        updated_edge = db.db.document(edge_id)
        console.print(f"Edge {edge_id}: {updated_edge.get('_from')} → {updated_edge.get('_to')}")
        console.print(f"Question: {updated_edge.get('question', '')[:50]}...")
        console.print(f"Status: {updated_edge.get('review_status', '')}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        return


@app.command("batch-review")
def batch_review(
    confidence: ConfidenceLevel = typer.Option(
        ConfidenceLevel.MEDIUM,
        "--confidence",
        "-c",
        help="Filter by confidence level"
    ),
    document_id: Optional[str] = typer.Option(
        None,
        "--document",
        "-d",
        help="Filter by source document ID"
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Maximum number of edges to process"
    ),
    collection: str = typer.Option(
        "",
        "--collection",
        "-e",
        help="Edge collection name (overrides config)"
    )
):
    """
    Interactive batch review of QA edges.
    
    Allows reviewing multiple QA edges in sequence with
    options to approve, reject, or skip each edge.
    """
    console.print("[bold blue]Batch review of QA edges[/]")
    
    # Get database connection
    db = get_db_connection()
    collection_name = collection or get_edge_collection()
    
    # Build filter conditions
    filter_conditions = [
        f"edge.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'",
        "edge.review_status == 'pending'"
    ]
    bind_vars = {
        "limit": limit
    }
    
    # Add confidence filter
    filter_conditions.append(confidence_filter(confidence))
    
    # Add document filter
    if document_id:
        filter_conditions.append("edge.source_document_id == @document_id")
        bind_vars["document_id"] = document_id
    
    # Combine filter conditions
    filter_clause = " AND ".join(filter_conditions)
    
    # Execute query
    query = f"""
    FOR edge IN {collection_name}
        FILTER {filter_clause}
        LET from_entity = DOCUMENT(edge._from)
        LET to_entity = DOCUMENT(edge._to)
        SORT edge.created_at DESC
        LIMIT @limit
        RETURN {{
            edge: edge,
            from_entity: from_entity,
            to_entity: to_entity
        }}
    """
    
    # Execute query with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Fetching QA edges...", total=None)
        
        # Try to execute query
        try:
            cursor = db.db.aql.execute(query, bind_vars=bind_vars)
            results = list(cursor)
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            return
        
        progress.update(task, completed=True, description="Complete")
    
    # Display results
    if not results:
        console.print("[yellow]No pending QA edges found matching the criteria[/]")
        return
    
    console.print(f"[bold]Found {len(results)} edges for batch review.[/]")
    
    # Process edges in sequence
    approved = 0
    rejected = 0
    skipped = 0
    
    for result in results:
        edge = result["edge"]
        from_entity = result["from_entity"]
        to_entity = result["to_entity"]
        
        console.print(f"\n[bold cyan]===== Reviewing Edge {edge['_key']} =====[/bold cyan]")
        
        # Display minimal edge details
        console.print(Panel.fit(
            f"[bold]Question:[/bold] {edge.get('question', 'N/A')}\n\n"
            f"[bold]Answer:[/bold] {edge.get('answer', 'N/A')[:200]}...\n\n"
            f"[bold]From:[/bold] {from_entity.get('name', edge['_from'])}\n"
            f"[bold]To:[/bold] {to_entity.get('name', edge['_to'])}\n"
            f"[bold]Confidence:[/bold] {edge.get('confidence', 0):.2f}\n"
            f"[bold]Context Confidence:[/bold] {edge.get('context_confidence', 0):.2f}",
            title="QA Edge",
            border_style="blue"
        ))
        
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
        
        # Update edge based on action
        update_doc = {
            "review_status": "approved" if action == ReviewAction.APPROVE else "rejected",
            "reviewed_by": "cli_user",
            "review_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            db.db.update_document(edge["_id"], update_doc)
            
            if action == ReviewAction.APPROVE:
                approved += 1
                console.print("[green] Approved[/green]")
            else:
                rejected += 1
                console.print("[red] Rejected[/red]")
        except Exception as e:
            console.print(f"[bold red]Error updating edge: {str(e)}[/bold red]")
            skipped += 1
    
    # Display summary
    console.print(f"\n[bold]Batch Review Summary:[/bold]")
    console.print(f"Approved: [green]{approved}[/green]")
    console.print(f"Rejected: [red]{rejected}[/red]")
    console.print(f"Skipped: [yellow]{skipped}[/yellow]")


@app.command("bulk-update")
def bulk_update(
    status: ReviewStatus = typer.Option(
        ...,
        "--status",
        "-s",
        help="New review status"
    ),
    confidence: ConfidenceLevel = typer.Option(
        ConfidenceLevel.ALL,
        "--confidence",
        "-c",
        help="Filter by confidence level"
    ),
    document_id: Optional[str] = typer.Option(
        None,
        "--document",
        "-d",
        help="Filter by source document ID"
    ),
    current_status: ReviewStatus = typer.Option(
        ReviewStatus.PENDING,
        "--current-status",
        "-cs",
        help="Current status to filter by"
    ),
    limit: int = typer.Option(
        100,
        "--limit",
        "-n",
        help="Maximum number of edges to update"
    ),
    notes: Optional[str] = typer.Option(
        None,
        "--notes",
        "--reason",
        help="Review notes or reason for decision"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be updated without making changes"
    ),
    collection: str = typer.Option(
        "",
        "--collection",
        "-e",
        help="Edge collection name (overrides config)"
    )
):
    """
    Update review status for multiple QA edges in bulk.
    
    Updates the status of multiple QA edges matching the filter
    criteria, with options for limiting the scope of changes and
    dry-run mode to preview the updates.
    """
    console.print("[bold blue]Bulk updating QA edges[/]")
    
    # Skip "all" status
    if status == ReviewStatus.ALL:
        console.print("[bold red]Error:[/] Cannot set status to 'all'")
        return
    
    # Get database connection
    db = get_db_connection()
    collection_name = collection or get_edge_collection()
    
    # Build filter conditions
    filter_conditions = [f"edge.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'"]
    bind_vars = {
        "limit": limit,
        "new_status": status.value,
        "reviewer": "cli_user",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Add current status filter
    if current_status != ReviewStatus.ALL:
        filter_conditions.append("edge.review_status == @current_status")
        bind_vars["current_status"] = current_status.value
    
    # Add confidence filter
    filter_conditions.append(confidence_filter(confidence))
    
    # Add document filter
    if document_id:
        filter_conditions.append("edge.source_document_id == @document_id")
        bind_vars["document_id"] = document_id
    
    # Add notes if provided
    if notes:
        bind_vars["notes"] = notes
    
    # Combine filter conditions
    filter_clause = " AND ".join(filter_conditions)
    
    # Get count of edges to update
    count_query = f"""
    RETURN LENGTH(
        FOR edge IN {collection_name}
            FILTER {filter_clause}
            LIMIT @limit
            RETURN 1
    )
    """
    
    try:
        count_cursor = db.db.aql.execute(count_query, bind_vars=bind_vars)
        update_count = list(count_cursor)[0]
        
        if update_count == 0:
            console.print("[yellow]No QA edges found matching the criteria[/]")
            return
        
        # Confirm update
        if not dry_run:
            confirm_message = f"Update {update_count} QA edges to status '{status.value}'?"
            if not typer.confirm(confirm_message):
                console.print("[yellow]Update cancelled[/]")
                return
        
        # Execute update
        update_query = f"""
        FOR edge IN {collection_name}
            FILTER {filter_clause}
            LIMIT @limit
            UPDATE edge WITH {{
                review_status: @new_status,
                reviewed_by: @reviewer,
                review_timestamp: @timestamp
                {', review_notes: @notes' if notes else ''}
            }} IN {collection_name}
            RETURN OLD._key
        """
        
        if dry_run:
            console.print(f"[bold yellow]Dry run:[/] Would update {update_count} QA edges to '{status.value}'")
            console.print(f"Filter conditions: {filter_clause}")
        else:
            # Update with progress indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Updating QA edges...", total=None)
                
                # Execute update
                cursor = db.db.aql.execute(update_query, bind_vars=bind_vars)
                updated_keys = list(cursor)
                
                progress.update(task, completed=True, description="Complete")
            
            console.print(f"[bold green][/] Updated {len(updated_keys)} QA edges to '{status.value}'")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        return


@app.command("stats")
def qa_edge_stats(
    document_id: Optional[str] = typer.Option(
        None,
        "--document",
        "-d",
        help="Filter by source document ID"
    ),
    collection: str = typer.Option(
        "",
        "--collection",
        "-e",
        help="Edge collection name (overrides config)"
    )
):
    """
    Show statistics about QA-derived edges.
    
    Displays summary statistics for QA edges, including counts by
    status, confidence levels, and question types.
    """
    console.print("[bold blue]QA Edge Statistics[/]")
    
    # Get database connection
    db = get_db_connection()
    collection_name = collection or get_edge_collection()
    
    # Build filter clause
    filter_clause = f"edge.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'"
    bind_vars = {}
    
    # Add document filter
    if document_id:
        filter_clause += " AND edge.source_document_id == @document_id"
        bind_vars["document_id"] = document_id
    
    # Get overall statistics
    stats_query = f"""
    LET all_edges = (
        FOR edge IN {collection_name}
            FILTER {filter_clause}
            RETURN edge
    )
    
    LET status_counts = (
        FOR edge IN all_edges
            COLLECT status = edge.review_status INTO groups
            RETURN {{
                "status": status || "unknown",
                "count": LENGTH(groups)
            }}
    )
    
    LET confidence_buckets = (
        FOR edge IN all_edges
            LET bucket = edge.confidence < 0.7 ? "low" :
                        edge.confidence < 0.9 ? "medium" : "high"
            COLLECT b = bucket INTO groups
            RETURN {{
                "bucket": b,
                "count": LENGTH(groups)
            }}
    )
    
    LET question_types = (
        FOR edge IN all_edges
            COLLECT type = edge.question_type INTO groups
            RETURN {{
                "type": type || "unknown",
                "count": LENGTH(groups)
            }}
    )
    
    LET documents = (
        FOR edge IN all_edges
            COLLECT doc = edge.source_document_id INTO groups
            RETURN {{
                "doc": doc,
                "count": LENGTH(groups)
            }}
    )
    
    RETURN {{
        "total": LENGTH(all_edges),
        "status_counts": status_counts,
        "confidence_buckets": confidence_buckets,
        "question_types": question_types,
        "documents": documents
    }}
    """
    
    # Execute query with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Computing statistics...", total=None)
        
        try:
            cursor = db.db.aql.execute(stats_query, bind_vars=bind_vars)
            stats = list(cursor)[0]
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            return
        
        progress.update(task, completed=True, description="Complete")
    
    # Display overall statistics
    total = stats["total"]
    console.print(f"Total QA edges: {total}")
    
    if total == 0:
        console.print("[yellow]No QA edges found matching the criteria[/]")
        return
    
    # Display status distribution
    console.print("\n[bold]Review Status Distribution:[/]")
    status_table = Table()
    status_table.add_column("Status", style="cyan")
    status_table.add_column("Count", style="magenta")
    status_table.add_column("Percentage", style="green")
    
    for status in stats["status_counts"]:
        status_name = status["status"]
        count = status["count"]
        percentage = count / total if total > 0 else 0
        
        status_table.add_row(
            status_name,
            str(count),
            f"{percentage:.1%}"
        )
    
    console.print(status_table)
    
    # Display confidence distribution
    console.print("\n[bold]Confidence Level Distribution:[/]")
    confidence_table = Table()
    confidence_table.add_column("Confidence", style="cyan")
    confidence_table.add_column("Count", style="magenta")
    confidence_table.add_column("Percentage", style="green")
    
    for bucket in stats["confidence_buckets"]:
        bucket_name = bucket["bucket"]
        count = bucket["count"]
        percentage = count / total if total > 0 else 0
        
        confidence_table.add_row(
            bucket_name,
            str(count),
            f"{percentage:.1%}"
        )
    
    console.print(confidence_table)
    
    # Display question type distribution
    console.print("\n[bold]Question Type Distribution:[/]")
    type_table = Table()
    type_table.add_column("Type", style="cyan")
    type_table.add_column("Count", style="magenta")
    type_table.add_column("Percentage", style="green")
    
    for type_info in stats["question_types"]:
        type_name = type_info["type"]
        count = type_info["count"]
        percentage = count / total if total > 0 else 0
        
        type_table.add_row(
            type_name,
            str(count),
            f"{percentage:.1%}"
        )
    
    console.print(type_table)
    
    # Display document distribution if not filtered
    if not document_id and stats["documents"]:
        console.print("\n[bold]Document Distribution:[/]")
        doc_table = Table()
        doc_table.add_column("Document", style="cyan")
        doc_table.add_column("Count", style="magenta")
        doc_table.add_column("Percentage", style="green")
        
        for doc_info in stats["documents"]:
            doc_id = doc_info["doc"] or "Unknown"
            count = doc_info["count"]
            percentage = count / total if total > 0 else 0
            
            doc_table.add_row(
                doc_id,
                str(count),
                f"{percentage:.1%}"
            )
        
        console.print(doc_table)


@app.command("generate-aql")
def generate_review_aql(
    confidence_threshold: float = typer.Option(
        0.7,
        "--threshold",
        "-t",
        help="Confidence threshold"
    ),
    collection: str = typer.Option(
        "",
        "--collection",
        "-e",
        help="Edge collection name (overrides config)"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for AQL queries"
    )
):
    """
    Generate AQL queries for finding problematic connections.
    
    Outputs AQL queries that can be run directly in the ArangoDB web interface
    or arangosh to find edges that need review.
    """
    collection_name = collection or get_edge_collection()
    
    queries = [
        {
            "description": "Low confidence Q&A edges",
            "query": f"""
            FOR edge IN {collection_name}
            FILTER edge.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'
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
            FOR edge1 IN {collection_name}
            FILTER edge1.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'
            FOR edge2 IN {collection_name}
            FILTER edge2.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'
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
            FOR edge IN {collection_name}
            FILTER edge.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'
            FILTER edge.context_rationale == NULL OR edge.context_rationale == ""
            RETURN {{
                _key: edge._key,
                _id: edge._id,
                question: edge.question,
                confidence: edge.confidence
            }}
            """
        },
        {
            "description": "Entities with most QA edges",
            "query": f"""
            FOR edge IN {collection_name}
            FILTER edge.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'
            COLLECT entity = edge._from WITH COUNT INTO count
            SORT count DESC
            LIMIT 20
            LET entity_doc = DOCUMENT(entity)
            RETURN {{
                entity: entity,
                name: entity_doc.name,
                type: entity_doc.type,
                edge_count: count
            }}
            """
        },
        {
            "description": "Unapproved high confidence edges",
            "query": f"""
            FOR edge IN {collection_name}
            FILTER edge.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'
            FILTER edge.confidence >= 0.9
            FILTER edge.review_status == 'pending'
            RETURN {{
                _key: edge._key,
                _id: edge._id,
                question: edge.question,
                confidence: edge.confidence,
                from: edge._from,
                to: edge._to
            }}
            """
        }
    ]
    
    # If output file provided, write queries to file
    if output:
        with open(output, "w") as f:
            for query_info in queries:
                f.write(f"// {query_info['description']}\n")
                f.write(query_info['query'].strip() + "\n\n")
        
        console.print(f"[bold green][/] Wrote {len(queries)} AQL queries to {output}")
    else:
        # Display queries to console
        for query_info in queries:
            console.print(f"\n[bold cyan]{query_info['description']}[/bold cyan]")
            console.print(Panel(query_info['query'], border_style="blue"))


@app.command("export")
def export_qa_edges(
    output_path: Path = typer.Argument(
        ...,
        help="Output file path (.json or .jsonl)"
    ),
    status: ReviewStatus = typer.Option(
        ReviewStatus.APPROVED,
        "--status",
        "-s",
        help="Filter by review status"
    ),
    confidence: ConfidenceLevel = typer.Option(
        ConfidenceLevel.ALL,
        "--confidence",
        "-c",
        help="Filter by confidence level"
    ),
    document_id: Optional[str] = typer.Option(
        None,
        "--document",
        "-d",
        help="Filter by source document ID"
    ),
    format: str = typer.Option(
        "jsonl",
        "--format",
        "-f",
        help="Output format (json or jsonl)"
    ),
    limit: int = typer.Option(
        1000,
        "--limit",
        "-n",
        help="Maximum number of edges to export"
    ),
    include_entities: bool = typer.Option(
        True,
        "--include-entities/--no-entities",
        help="Include entity information in export"
    ),
    collection: str = typer.Option(
        "",
        "--collection",
        "-e",
        help="Edge collection name (overrides config)"
    )
):
    """
    Export QA edges to a file.
    
    Exports QA edges to a JSON or JSONL file, with options for
    filtering by status, confidence, and document ID.
    """
    console.print(f"[bold blue]Exporting QA edges to {output_path}[/]")
    
    # Validate format
    if format not in ["json", "jsonl"]:
        console.print("[bold red]Error:[/] Format must be 'json' or 'jsonl'")
        return
    
    # Ensure correct extension
    if format == "json" and output_path.suffix.lower() != ".json":
        output_path = output_path.with_suffix(".json")
    elif format == "jsonl" and output_path.suffix.lower() != ".jsonl":
        output_path = output_path.with_suffix(".jsonl")
    
    # Get database connection
    db = get_db_connection()
    collection_name = collection or get_edge_collection()
    
    # Build filter conditions
    filter_conditions = [f"edge.type == '{RELATIONSHIP_TYPE_QA_DERIVED}'"]
    bind_vars = {
        "limit": limit
    }
    
    # Add status filter
    if status != ReviewStatus.ALL:
        filter_conditions.append("edge.review_status == @status")
        bind_vars["status"] = status.value
    
    # Add confidence filter
    filter_conditions.append(confidence_filter(confidence))
    
    # Add document filter
    if document_id:
        filter_conditions.append("edge.source_document_id == @document_id")
        bind_vars["document_id"] = document_id
    
    # Combine filter conditions
    filter_clause = " AND ".join(filter_conditions)
    
    # Build query
    query = f"""
    FOR edge IN {collection_name}
        FILTER {filter_clause}
        LIMIT @limit
    """
    
    if include_entities:
        query += """
        LET from_entity = DOCUMENT(edge._from)
        LET to_entity = DOCUMENT(edge._to)
        RETURN {
            "edge": edge,
            "from_entity": from_entity,
            "to_entity": to_entity
        }
        """
    else:
        query += """
        RETURN {
            "edge": edge
        }
        """
    
    # Execute query with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Fetching QA edges...", total=None)
        
        try:
            cursor = db.db.aql.execute(query, bind_vars=bind_vars)
            results = list(cursor)
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            return
        
        progress.update(task, description=f"Exporting {len(results)} edges...")
        
        # Export edges
        try:
            if format == "json":
                with open(output_path, "w") as f:
                    json.dump(results, f, indent=2)
            else:  # jsonl
                with open(output_path, "w") as f:
                    for result in results:
                        f.write(json.dumps(result) + "\n")
            
            progress.update(task, completed=True, description="Complete")
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            return
    
    console.print(f"[bold green][/] Exported {len(results)} QA edges to {output_path}")


if __name__ == "__main__":
    import sys
    
    # Initialize validation testing
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: CLI commands defined
    total_tests += 1
    try:
        # Check all commands are defined
        expected_commands = ["list", "view", "update-status", "batch-review", 
                           "bulk-update", "stats", "generate-aql", "export"]
        for cmd in expected_commands:
            assert cmd in app.registered_commands, f"Command '{cmd}' not defined"
        print(" All commands defined correctly")
    except Exception as e:
        all_validation_failures.append(f"Command definition test failed: {str(e)}")
    
    # Final validation result
    if all_validation_failures:
        print(f"\n VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"\n VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("QA Review CLI is validated and ready for use")
        sys.exit(0)  # Exit with success code
    
    # Run CLI
    app()