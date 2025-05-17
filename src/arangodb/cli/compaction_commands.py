"""
ArangoDB CLI Compaction Commands

This module provides command-line interface for conversation compaction operations using
the core business logic layer. It handles conversation compaction, retrieval, and search
over compacted summaries.

Compaction commands include:
- Creating compacted summaries of conversations
- Retrieving compacted summaries
- Searching through compacted content

Each function follows consistent parameter patterns and error handling to
ensure a robust CLI experience.

Sample Input:
- CLI command: arangodb compaction create --conversation-id "abc123" --method "summarize"
- CLI command: arangodb compaction search "database queries" --threshold 0.75

Expected Output:
- Console-formatted tables or JSON output of compaction operations
"""

from arangodb.core.utils.initialize_litellm_cache import initialize_litellm_cache

# Initialize LiteLLM cache
initialize_litellm_cache()
import typer
import json
import sys
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from loguru import logger
from pathlib import Path

# Import CLI utilities
from arangodb.core.utils.cli import (
    console, 
    format_output, 
    add_output_option,
    format_error,
    format_success,
    format_info,
    OutputFormat
)

# Import from core modules
from arangodb.core.memory.compact_conversation import compact_conversation
from arangodb.core.memory.memory_agent import MemoryAgent
from arangodb.core.constants import (
    COMPACTED_SUMMARIES_COLLECTION,
    COMPACTED_SUMMARIES_VIEW,
    COMPACTION_EDGES_COLLECTION,
    EMBEDDING_FIELD,
    CONFIG
)

# Import connection utilities
from arangodb.cli.db_connection import get_db_connection

# Create the compaction app command group
compaction_app = typer.Typer(
    name="compaction",
    help="Tools for creating and managing compacted conversation summaries."
)

@compaction_app.command("create")
def cli_create_compaction(
    conversation_id: Optional[str] = typer.Option(
        None, "--conversation-id", "-c", help="ID of the conversation to compact"
    ),
    episode_id: Optional[str] = typer.Option(
        None, "--episode-id", "-e", help="ID of the episode to compact"
    ),
    compaction_method: str = typer.Option(
        CONFIG["search"]["compaction"]["default_method"], 
        "--method", 
        "-m", 
        help=f"Method for compaction: {', '.join(CONFIG['search']['compaction']['available_methods'])}"
    ),
    max_tokens: int = typer.Option(
        CONFIG["search"]["compaction"]["default_max_tokens"],
        "--max-tokens",
        "-mt",
        help="Maximum number of tokens per chunk for processing"
    ),
    min_overlap: int = typer.Option(
        CONFIG["search"]["compaction"]["default_min_overlap"],
        "--min-overlap",
        "-mo",
        help="Minimum token overlap between chunks"
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON"
    ),
):
    """
    Create a compact representation of a conversation or episode.
    
    WHEN TO USE: Use this command to create more efficient memory storage
    by compacting verbose message exchanges into concise summaries or key points.
    
    WHY: Compacted conversations take less space, are faster to retrieve,
    and can fit more context within LLM token limits.
    
    EXAMPLES:
    
    Summarize a specific conversation:
    arangodb compaction create --conversation-id "conv_123"
    
    Extract key points from all conversations in an episode:
    arangodb compaction create --episode-id "ep_456" --method extract_key_points
    
    Create a topic model with custom token settings:
    arangodb compaction create --conversation-id "conv_789" 
                              --method topic_model
                              --max-tokens 3000 
                              --min-overlap 200
    """
    logger.info(f"CLI: Compacting conversation/episode with method: {compaction_method}")
    
    # Validation
    if not conversation_id and not episode_id:
        console.print("[bold red]Error:[/bold red] Either conversation_id or episode_id must be provided")
        raise typer.Exit(code=1)
    
    # Validate compaction method
    valid_methods = CONFIG["search"]["compaction"]["available_methods"]
    if compaction_method not in valid_methods:
        console.print(f"[bold red]Error:[/bold red] Invalid compaction method: {compaction_method}")
        console.print(f"Valid methods: {', '.join(valid_methods)}")
        raise typer.Exit(code=1)
    
    # Get database connection
    db = get_db_connection()
    
    try:
        # Initialize memory agent
        memory_agent = MemoryAgent(db=db)
        
        # Perform compaction
        result = memory_agent.compact_conversation(
            conversation_id=conversation_id,
            episode_id=episode_id,
            compaction_method=compaction_method,
            max_tokens=max_tokens,
            min_overlap=min_overlap
        )
        
        # Display results
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            console.print("\n[bold green]Conversation Compaction Results:[/bold green]")
            console.print(f"[bold cyan]Compaction ID:[/bold cyan] {result.get('_key', 'N/A')}")
            console.print(f"[bold cyan]Method:[/bold cyan] {compaction_method}")
            console.print(f"[bold cyan]Original Messages:[/bold cyan] {result.get('message_count', 0)}")
            
            # Calculate reduction percentages
            metadata = result.get("metadata", {})
            char_reduction = metadata.get("reduction_ratio", 0) * 100
            
            original_tokens = metadata.get("original_token_count", 0)
            compacted_tokens = metadata.get("compacted_token_count", 0)
            token_reduction = (1 - (compacted_tokens / max(1, original_tokens))) * 100
            
            console.print(f"[bold cyan]Character Reduction:[/bold cyan] {char_reduction:.1f}%")
            console.print(f"[bold cyan]Token Reduction:[/bold cyan] {token_reduction:.1f}%")
            
            # Show workflow summary if available
            workflow = result.get("workflow_summary", {})
            if workflow and not json_output:
                console.print("\n[bold cyan]Workflow Info:[/bold cyan]")
                console.print(f"Total Processing Time: {workflow.get('total_elapsed_time', 0):.2f} seconds")
                console.print(f"Status: {workflow.get('status', 'Unknown')}")
            
            console.print("\n[bold cyan]Compacted Content:[/bold cyan]")
            console.print(result.get('content', 'No content available'))
            
    except Exception as e:
        logger.error(f"Compaction failed: {e}", exc_info=True)
        console.print(f"[bold red]Error during compaction:[/bold red] {e}")
        raise typer.Exit(code=1)

@compaction_app.command("search")
def cli_search_compactions(
    query: str = typer.Argument(..., help="The search query text."),
    threshold: float = typer.Option(
        0.75,
        "--threshold",
        "-th",
        help="Minimum similarity score (0.0-1.0).",
        min=0.0,
        max=1.0,
    ),
    top_n: int = typer.Option(
        5, "--top-n", "-n", help="Number of results to return.", min=1
    ),
    method: Optional[str] = typer.Option(
        None,
        "--method",
        "-m",
        help="Filter by compaction method: summarize, extract_key_points, or topic_model.",
    ),
    conversation_id: Optional[str] = typer.Option(
        None, "--conversation-id", "-c", help="Filter by conversation ID."
    ),
    episode_id: Optional[str] = typer.Option(
        None, "--episode-id", "-e", help="Filter by episode ID."
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON array."
    ),
):
    """
    Search for compacted conversation summaries using semantic similarity.

    WHEN TO USE: Use this command when you need to quickly find relevant
    conversation summaries that match your query conceptually, rather than
    searching through individual messages.

    WHY TO USE: Provides a high-level view of entire conversations that are
    relevant to your query, with links to the original message details.
    
    EXAMPLES:
    
    Search for compacted summaries about a topic:
    arangodb compaction search "database optimization techniques"
    
    Search with higher similarity threshold:
    arangodb compaction search "user authentication flow" --threshold 0.85
    
    Filter by compaction method:
    arangodb compaction search "project timeline" --method extract_key_points
    
    Search within a specific episode:
    arangodb compaction search "API integration" --episode-id "ep_456"
    """
    logger.info(f"CLI: Performing compaction search for '{query}'")
    db = get_db_connection()
    
    # Convert method to list if provided
    methods = [method] if method else None
    
    try:
        # Initialize memory agent
        memory_agent = MemoryAgent(db=db)
        
        # Perform search
        results_data = memory_agent.search_compactions(
            query_text=query,
            min_score=threshold,
            top_n=top_n,
            compaction_methods=methods,
            conversation_id=conversation_id,
            episode_id=episode_id
        )
        
        if json_output:
            print(json.dumps(results_data.get("results", []), indent=2))
        else:
            # Display results in a formatted table
            table = Table(title=f"Compaction Search Results")
            
            table.add_column("ID", style="cyan")
            table.add_column("Method", style="green")
            table.add_column("Content Preview", style="white")
            table.add_column("Score", style="magenta")
            table.add_column("Messages", style="yellow")
            
            for result in results_data.get("results", []):
                # Format content preview (first 100 chars)
                content = result.get("content", "")
                preview = (content[:97] + "...") if len(content) > 100 else content
                
                # Add row to table
                table.add_row(
                    result.get("_key", "N/A"),
                    result.get("compaction_method", "N/A"),
                    preview,
                    f"{result.get('similarity_score', 0):.4f}",
                    str(result.get("message_count", 0))
                )
            
            console.print(table)
            
            # Add summary footer
            footer = f"Found {len(results_data.get('results', []))} results in {results_data.get('time', 0):.2f} seconds"
            console.print(footer)
            
    except Exception as e:
        logger.error(f"Compaction search failed: {e}", exc_info=True)
        console.print(f"[bold red]Error during compaction search:[/bold red] {e}")
        raise typer.Exit(code=1)

@compaction_app.command("get")
def cli_get_compaction(
    compaction_id: str = typer.Argument(
        ..., help="The ID of the compaction to retrieve."
    ),
    include_workflow: bool = typer.Option(
        False, "--include-workflow", "-w", help="Include workflow tracking information."
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON."
    ),
):
    """
    Retrieve a specific compacted conversation summary.
    
    WHEN TO USE: Use this command when you need to view the detailed content 
    and metadata of a previously created compaction.
    
    WHY TO USE: Provides the full content of a compacted summary along with
    its metadata and reference information.
    
    EXAMPLES:
    
    Get a specific compaction by ID:
    arangodb compaction get "cmp_123abc"
    
    Get compaction with workflow details:
    arangodb compaction get "cmp_123abc" --include-workflow
    
    Get compaction as JSON for further processing:
    arangodb compaction get "cmp_123abc" --json-output
    """
    logger.info(f"CLI: Retrieving compaction with ID: {compaction_id}")
    db = get_db_connection()
    
    try:
        # Check if the ID already includes the collection prefix
        if "/" not in compaction_id:
            full_id = f"{COMPACTED_SUMMARIES_COLLECTION}/{compaction_id}"
        else:
            full_id = compaction_id
        
        # Get the compaction document
        compaction = db.document(full_id)
        
        # Get workflow data if requested
        if include_workflow and "metadata" in compaction and "workflow_id" in compaction["metadata"]:
            workflow_id = compaction["metadata"]["workflow_id"]
            # Initialize memory agent
            memory_agent = MemoryAgent(db=db)
            # Get workflow data
            workflow_data = memory_agent.get_workflow_data(workflow_id)
            compaction["workflow_data"] = workflow_data
        
        if json_output:
            print(json.dumps(compaction, indent=2))
        else:
            console.print("\n[bold green]Compacted Conversation Summary:[/bold green]")
            console.print(f"[bold cyan]ID:[/bold cyan] {compaction.get('_key', 'N/A')}")
            console.print(f"[bold cyan]Method:[/bold cyan] {compaction.get('compaction_method', 'N/A')}")
            console.print(f"[bold cyan]Created:[/bold cyan] {compaction.get('created_at', 'N/A')}")
            console.print(f"[bold cyan]Messages:[/bold cyan] {compaction.get('message_count', 0)}")
            
            if "metadata" in compaction:
                metadata = compaction["metadata"]
                console.print("\n[bold cyan]Metadata:[/bold cyan]")
                console.print(f"Original Length: {metadata.get('original_content_length', 'N/A')} characters")
                console.print(f"Compacted Length: {metadata.get('compacted_length', 'N/A')} characters")
                console.print(f"Reduction: {metadata.get('reduction_ratio', 0) * 100:.1f}%")
                
                if "original_token_count" in metadata and "compacted_token_count" in metadata:
                    token_reduction = (1 - (metadata.get("compacted_token_count", 0) / 
                                          max(1, metadata.get("original_token_count", 1)))) * 100
                    console.print(f"Token Reduction: {token_reduction:.1f}%")
            
            if include_workflow and "workflow_data" in compaction:
                workflow = compaction["workflow_data"]
                console.print("\n[bold cyan]Workflow Details:[/bold cyan]")
                console.print(f"Status: {workflow.get('status', 'Unknown')}")
                console.print(f"Started: {workflow.get('start_time', 'N/A')}")
                console.print(f"Completed: {workflow.get('end_time', 'N/A')}")
                console.print(f"Duration: {workflow.get('elapsed_time', 0):.2f} seconds")
                
                steps = workflow.get("steps", [])
                if steps:
                    console.print("\n[bold cyan]Workflow Steps:[/bold cyan]")
                    for i, step in enumerate(steps):
                        status = step.get("status", "Unknown")
                        duration = step.get("elapsed_time", 0)
                        name = step.get("name", f"Step {i+1}")
                        
                        if status == "completed":
                            console.print(f"✅ {name}: {duration:.2f}s")
                        elif status == "failed":
                            console.print(f"❌ {name}: {duration:.2f}s - {step.get('error', 'Unknown error')}")
                        else:
                            console.print(f"⏳ {name}: {status}")
            
            console.print("\n[bold cyan]Content:[/bold cyan]")
            console.print(compaction.get('content', 'No content available'))
            
    except Exception as e:
        logger.error(f"Error retrieving compaction: {e}", exc_info=True)
        console.print(f"[bold red]Error retrieving compaction:[/bold red] {e}")
        raise typer.Exit(code=1)

@compaction_app.command("list")
def cli_list_compactions(
    limit: int = typer.Option(
        10, "--limit", "-lim", help="Maximum number of results to return.", min=1
    ),
    conversation_id: Optional[str] = typer.Option(
        None, "--conversation-id", "-c", help="Filter by conversation ID."
    ),
    episode_id: Optional[str] = typer.Option(
        None, "--episode-id", "-e", help="Filter by episode ID."
    ),
    compaction_method: Optional[str] = typer.Option(
        None, "--method", "-m", help="Filter by compaction method."
    ),
    sort_by: str = typer.Option(
        "created_at", "--sort-by", "-s", 
        help="Field to sort by: created_at, message_count, reduction_ratio."
    ),
    descending: bool = typer.Option(
        True, "--descending/--ascending", help="Sort in descending or ascending order."
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON array."
    ),
):
    """
    List compacted conversation summaries with optional filtering.
    
    WHEN TO USE: Use this command to see all compacted summaries that match 
    your filtering criteria, sorted as specified.
    
    WHY TO USE: Provides an overview of what conversation compactions are available
    and helps you identify the ones you might want to retrieve in full.
    
    EXAMPLES:
    
    List the 10 most recent compactions:
    arangodb compaction list
    
    List compactions for a specific conversation:
    arangodb compaction list --conversation-id "conv_123"
    
    List compactions by reduction ratio (most efficient first):
    arangodb compaction list --sort-by reduction_ratio --descending
    
    List oldest compactions first:
    arangodb compaction list --sort-by created_at --ascending
    """
    logger.info(f"CLI: Listing compactions with filters")
    db = get_db_connection()
    
    try:
        # Build AQL query
        query = f"""
        FOR c IN {COMPACTED_SUMMARIES_COLLECTION}
        """
        
        # Add filters
        filters = []
        bind_vars = {}
        
        if conversation_id:
            filters.append("c.conversation_id == @conversation_id")
            bind_vars["conversation_id"] = conversation_id
            
        if episode_id:
            filters.append("c.episode_id == @episode_id")
            bind_vars["episode_id"] = episode_id
            
        if compaction_method:
            filters.append("c.compaction_method == @compaction_method")
            bind_vars["compaction_method"] = compaction_method
        
        if filters:
            query += f" FILTER {' AND '.join(filters)}"
        
        # Add sorting
        sort_field = "c.created_at"
        if sort_by == "message_count":
            sort_field = "c.message_count"
        elif sort_by == "reduction_ratio":
            sort_field = "c.metadata.reduction_ratio"
            
        sort_direction = "DESC" if descending else "ASC"
        query += f" SORT {sort_field} {sort_direction}"
        
        # Add limit
        query += f" LIMIT @limit"
        bind_vars["limit"] = limit
        
        # Return fields
        query += """
        RETURN {
            _id: c._id,
            _key: c._key,
            conversation_id: c.conversation_id,
            episode_id: c.episode_id,
            compaction_method: c.compaction_method,
            message_count: c.message_count,
            created_at: c.created_at,
            content_preview: LENGTH(c.content) > 100 ? CONCAT(SUBSTRING(c.content, 0, 100), "...") : c.content,
            reduction_ratio: c.metadata.reduction_ratio
        }
        """
        
        # Execute query
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        
        if json_output:
            print(json.dumps(results, indent=2))
        else:
            # Display results in a formatted table
            table = Table(title=f"Compacted Summaries" + (f" ({len(results)} results)" if results else ""))
            
            table.add_column("ID", style="cyan")
            table.add_column("Method", style="green")
            if not conversation_id:
                table.add_column("Conversation", style="blue")
            if not episode_id:
                table.add_column("Episode", style="yellow")
            table.add_column("Messages", style="magenta")
            table.add_column("Created", style="blue")
            table.add_column("Reduction", style="green")
            table.add_column("Preview", style="white")
            
            for item in results:
                row = [
                    item.get("_key", "N/A"),
                    item.get("compaction_method", "N/A"),
                ]
                
                if not conversation_id:
                    row.append(item.get("conversation_id", "N/A"))
                    
                if not episode_id:
                    row.append(item.get("episode_id", "N/A"))
                    
                # Add remaining columns
                created_at = item.get("created_at", "")
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        created_at = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                        
                reduction = item.get("reduction_ratio", 0) * 100
                
                row.extend([
                    str(item.get("message_count", 0)),
                    created_at,
                    f"{reduction:.1f}%",
                    item.get("content_preview", "")[:50]
                ])
                
                table.add_row(*row)
            
            console.print(table)
            
            if not results:
                console.print("\n[bold yellow]No compactions found matching the specified criteria[/bold yellow]")
            
    except Exception as e:
        logger.error(f"Error listing compactions: {e}", exc_info=True)
        console.print(f"[bold red]Error listing compactions:[/bold red] {e}")
        raise typer.Exit(code=1)

def get_compaction_app():
    """Get the compaction app Typer instance for use in the main CLI."""
    return compaction_app
