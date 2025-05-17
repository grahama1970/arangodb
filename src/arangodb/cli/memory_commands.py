"""
ArangoDB CLI Memory Commands

This module provides command-line interface for memory agent operations using
the core business logic layer. It handles conversation storage, retrieval,
and search over the memory agent's database.

Memory commands include:
- Storing conversations with metadata
- Retrieving conversation history
- Searching conversations with temporal constraints
- Managing memory relationships

Each function follows consistent parameter patterns and error handling to
ensure a robust CLI experience.

Sample Input:
- CLI command: arangodb memory store --conversation-id "abc123" --user-message "Hello" --agent-response "Hi"
- CLI command: arangodb memory search "database queries" --point-in-time "2023-01-01T12:00:00"

Expected Output:
- Console-formatted tables or JSON output of memory operations
"""

import typer
import json
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from loguru import logger

# Import dependency checker for graceful handling of missing dependencies
from arangodb.core.utils.dependency_checker import (
    HAS_ARANGO,
    check_dependency
)

# Check for UI dependencies
HAS_RICH = "rich" in sys.modules
HAS_TYPER = "typer" in sys.modules

# Import UI components if available
if HAS_RICH:
    from rich.console import Console
    from rich.table import Table
    from rich.json import JSON
    
    # Initialize Rich console
    console = Console()
else:
    # Create a simple fallback console
    class SimpleConsole:
        def print(self, message, **kwargs):
            # Strip any rich formatting if present
            # This is a simplified approach - real implementation would be more robust
            import re
            clean_message = re.sub(r'\[.*?\]', '', message)
            print(clean_message)
    
    console = SimpleConsole()

# Import memory agent and related functions - dependency checked in functions
from arangodb.core.memory.memory_agent import (
    MemoryAgent,
)

# Import memory-related utility functions if needed
# These will be imported conditionally within functions if available

# Import constants from core
from arangodb.core.constants import (
    MEMORY_MESSAGE_COLLECTION,
    MEMORY_COLLECTION,
    MEMORY_EDGE_COLLECTION,
    MEMORY_VIEW_NAME,
    MEMORY_GRAPH_NAME
)

# Import connection utilities
from arangodb.cli.db_connection import get_db_connection

# Create the Memory app command group
memory_app = typer.Typer(
    name="memory", 
    help="Manage agent memory, conversations, and temporal search."
)


@memory_app.command("store")
def cli_store_conversation(
    conversation_id: Optional[str] = typer.Option(
        None, "--conversation-id", "-cid", help="ID for the conversation (generated if not provided)."
    ),
    user_message: str = typer.Option(
        ..., "--user-message", "-u", help="The user's message to store."
    ),
    agent_response: str = typer.Option(
        ..., "--agent-response", "-a", help="The agent's response to store."
    ),
    timestamp: Optional[str] = typer.Option(
        None, 
        "--timestamp", 
        "-t", 
        help="When the conversation occurred (ISO-8601 format, e.g., 2023-01-01T12:00:00). Defaults to now."
    ),
    metadata: Optional[str] = typer.Option(
        None,
        "--metadata",
        "-m",
        help="Additional metadata as a JSON string (e.g., '{\"source\": \"chat\", \"topic\": \"databases\"}').",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output result as JSON."
    ),
):
    """
    Store a user-agent message exchange in the memory database.

    *WHEN TO USE:* Use when you want to save a conversation exchange between
    a user and an agent for future reference and search. The system will automatically
    generate embeddings and create relationships between related memories.

    *HOW TO USE:* Provide the user message and agent response, with an optional
    conversation ID to group messages together. You can also provide a timestamp
    and additional metadata.
    """
    logger.info(f"CLI: Storing conversation" + (f" with ID '{conversation_id}'" if conversation_id else ""))
    
    # Check for ArangoDB availability
    if not HAS_ARANGO:
        error_msg = "Cannot store conversation: ArangoDB is not available"
        logger.error(error_msg)
        console.print(
            f"[bold red]Error:[/bold red] {error_msg}. "
            f"Please install python-arango to use memory features."
        )
        raise typer.Exit(code=1)
    
    # Get database connection
    db = get_db_connection()
    
    # Parse reference_time if provided
    reference_time = None
    if timestamp:
        try:
            reference_time = datetime.fromisoformat(timestamp)
            logger.debug(f"Using provided reference time: {reference_time.isoformat()}")
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] Invalid timestamp format: {e}")
            console.print("[yellow]Hint:[/yellow] Use ISO-8601 format, e.g., 2023-01-01T12:00:00")
            raise typer.Exit(code=1)
    
    # Parse metadata if provided
    meta_dict = {}
    if metadata:
        try:
            meta_dict = json.loads(metadata)
            if not isinstance(meta_dict, dict):
                console.print("[bold red]Error:[/bold red] Metadata must be a valid JSON object.")
                raise typer.Exit(code=1)
            logger.debug(f"Using provided metadata: {meta_dict}")
        except json.JSONDecodeError as e:
            console.print(f"[bold red]Error parsing metadata JSON:[/bold red] {e}")
            raise typer.Exit(code=1)
    
    try:
        # Initialize the memory agent - this requires ArangoDB
        memory_agent = MemoryAgent(db)
        
        # Store the conversation
        result = memory_agent.store_conversation(
            conversation_id=conversation_id,
            user_message=user_message,
            agent_response=agent_response,
            metadata=meta_dict,
            reference_time=reference_time
        )
        
        if result:
            if json_output:
                print(json.dumps(result))
            else:
                console.print("[green]Success:[/green] Conversation stored successfully.")
                console.print(f"  Conversation ID: [cyan]{result.get('conversation_id')}[/cyan]")
                console.print(f"  User Message Key: [cyan]{result.get('user_key')}[/cyan]")
                console.print(f"  Agent Response Key: [cyan]{result.get('agent_key')}[/cyan]")
                console.print(f"  Memory Record Key: [cyan]{result.get('memory_key')}[/cyan]")
        else:
            console.print(
                "[bold red]Error:[/bold red] Failed to store conversation (check logs for details)."
            )
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Store conversation failed in CLI: {e}", exc_info=True)
        console.print(f"[bold red]Error during store operation:[/bold red] {e}")
        raise typer.Exit(code=1)


@memory_app.command("get-history")
def cli_get_conversation_history(
    conversation_id: str = typer.Argument(
        ..., help="The ID of the conversation to retrieve."
    ),
    limit: int = typer.Option(
        20, "--limit", "-lim", help="Maximum number of messages to retrieve.", min=1
    ),
    include_embeddings: bool = typer.Option(
        False, "--include-embeddings", "-e", help="Include embedding vectors in the output."
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output as JSON array."
    ),
):
    """
    Retrieve the message history for a specific conversation.

    *WHEN TO USE:* Use when you need to see the full conversation history for a
    specific conversation ID.

    *HOW TO USE:* Provide the conversation ID and optional limit.
    """
    logger.info(f"CLI: Retrieving conversation history for ID '{conversation_id}'")
    
    # Check for ArangoDB availability
    if not HAS_ARANGO:
        error_msg = "Cannot retrieve conversation history: ArangoDB is not available"
        logger.error(error_msg)
        console.print(
            f"[bold red]Error:[/bold red] {error_msg}. "
            f"Please install python-arango to use memory features."
        )
        raise typer.Exit(code=1)
    
    # Get database connection
    db = get_db_connection()
    
    # Check if Rich is available for table output (when not using JSON)
    if not HAS_RICH and not json_output:
        logger.warning("Rich library not available, table formatting will be limited")
    
    try:
        # Initialize the memory agent
        memory_agent = MemoryAgent(db)
        
        # Get the conversation history
        messages = memory_agent.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit,
            include_embeddings=include_embeddings
        )
        
        if not messages:
            if json_output:
                print(json.dumps([]))
            else:
                console.print(f"[yellow]No messages found:[/yellow] No history for conversation ID '{conversation_id}'.")
            raise typer.Exit(code=0)
        
        if json_output:
            print(json.dumps(messages, indent=2))
        else:
            console.print(f"[bold green]Conversation History[/bold green] (found {len(messages)} messages)")
            console.print(f"Conversation ID: [cyan]{conversation_id}[/cyan]")
            
            # Create and display table conditionally based on Rich availability
            if HAS_RICH:
                # Use Rich table formatting
                table = Table(title=f"Conversation Messages")
                table.add_column("Type", style="cyan")
                table.add_column("Timestamp", style="yellow")
                table.add_column("Content", style="green")
                
                # Add each message to the table
                for msg in messages:
                    msg_type = msg.get("message_type", "Unknown")
                    timestamp = msg.get("timestamp", "Unknown")
                    content = msg.get("content", "No content")
                    
                    # Truncate content if it's too long
                    if len(content) > 100:
                        content = content[:97] + "..."
                    
                    table.add_row(msg_type, timestamp, content)
                
                console.print(table)
            else:
                # Simple text output without Rich formatting
                for i, msg in enumerate(messages):
                    msg_type = msg.get("message_type", "Unknown")
                    timestamp = msg.get("timestamp", "Unknown")
                    content = msg.get("content", "No content")
                    
                    # Truncate content if it's too long
                    if len(content) > 100:
                        content = content[:97] + "..."
                    
                    print(f"Message {i+1}:")
                    print(f"  Type: {msg_type}")
                    print(f"  Time: {timestamp}")
                    print(f"  Content: {content}")
                    print("")
    except Exception as e:
        logger.error(f"Get conversation history failed in CLI: {e}", exc_info=True)
        console.print(f"[bold red]Error retrieving conversation history:[/bold red] {e}")
        raise typer.Exit(code=1)


@memory_app.command("search")
def cli_search_memory(
    query: str = typer.Argument(..., help="The search query text."),
    point_in_time: Optional[str] = typer.Option(
        None, 
        "--point-in-time", 
        "-t", 
        help="When the memories should be valid (ISO-8601 format). Defaults to now."
    ),
    top_n: int = typer.Option(
        10, "--top-n", "-n", help="Number of results to return.", min=1
    ),
    include_messages: bool = typer.Option(
        False, "--include-messages", "-m", help="Include individual messages in search."
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON array."
    ),
):
    """
    Search for memories valid at a specific point in time.

    *WHEN TO USE:* Use when you need to find relevant past conversations
    that were valid at a specific point in time. The search uses semantic
    similarity to find conceptually related content.

    *HOW TO USE:* Provide the search query text and an optional point in time
    in ISO-8601 format (e.g., 2023-01-01T12:00:00).
    """
    logger.info(f"CLI: Performing memory search for '{query}'")
    
    # Check for ArangoDB availability
    if not HAS_ARANGO:
        error_msg = "Cannot perform memory search: ArangoDB is not available"
        logger.error(error_msg)
        console.print(
            f"[bold red]Error:[/bold red] {error_msg}. "
            f"Please install python-arango to use memory features."
        )
        raise typer.Exit(code=1)
    
    # Get database connection
    db = get_db_connection()
    
    # Check if Rich is available for table output (when not using JSON)
    if not HAS_RICH and not json_output:
        logger.warning("Rich library not available, table formatting will be limited")
    
    # Parse point_in_time if provided
    search_time = None
    if point_in_time:
        try:
            search_time = datetime.fromisoformat(point_in_time)
            logger.debug(f"Using provided search time: {search_time.isoformat()}")
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] Invalid timestamp format: {e}")
            console.print("[yellow]Hint:[/yellow] Use ISO-8601 format, e.g., 2023-01-01T12:00:00")
            raise typer.Exit(code=1)
    
    try:
        # Initialize the memory agent
        memory_agent = MemoryAgent(db)
        
        # Determine which collections to search
        collections = [MEMORY_COLLECTION]
        if include_messages:
            collections.append(MEMORY_MESSAGE_COLLECTION)
        
        # Perform the temporal search
        results = memory_agent.temporal_search(
            query_text=query,
            point_in_time=search_time,
            collections=collections,
            top_n=top_n
        )
        
        if json_output:
            print(json.dumps(results, indent=2))
        else:
            # Display results in a readable format
            all_results = results.get("results", [])
            if not all_results:
                console.print("[yellow]No results found.[/yellow]")
                raise typer.Exit(code=0)
            
            console.print(f"[bold green]Memory Search Results[/bold green] (found {len(all_results)} matches)")
            console.print(f"Query: [cyan]{query}[/cyan]")
            console.print(f"Point in time: [cyan]{results.get('point_in_time', 'now')}[/cyan]")
            console.print(f"Search time: [cyan]{results.get('time', 0):.2f} seconds[/cyan]")
            
            # Display results conditionally based on Rich availability
            if HAS_RICH:
                # Create a rich table for the results
                table = Table(title=f"Memory Search Results")
                table.add_column("Collection", style="cyan")
                table.add_column("Score", style="yellow")
                table.add_column("Valid At", style="green")
                table.add_column("Content", style="white")
                
                # Add each result to the table
                for result in all_results:
                    doc = result.get("doc", {})
                    collection = result.get("collection", "Unknown")
                    score = result.get("score", 0)
                    valid_at = doc.get("valid_at", "Unknown")
                    
                    # Get content based on collection type
                    if collection == MEMORY_COLLECTION:
                        content = doc.get("summary", doc.get("content", "No content"))
                    else:  # Message collection
                        content = doc.get("content", "No content")
                    
                    # Truncate content if it's too long
                    if len(content) > 80:
                        content = content[:77] + "..."
                    
                    table.add_row(collection.split("/")[-1], f"{score:.4f}", valid_at, content)
                
                console.print(table)
            else:
                # Simple text output without Rich formatting
                for i, result in enumerate(all_results):
                    doc = result.get("doc", {})
                    collection = result.get("collection", "Unknown").split("/")[-1]
                    score = result.get("score", 0)
                    valid_at = doc.get("valid_at", "Unknown")
                    
                    # Get content based on collection type
                    if collection == MEMORY_COLLECTION.split("/")[-1]:
                        content = doc.get("summary", doc.get("content", "No content"))
                    else:  # Message collection
                        content = doc.get("content", "No content")
                    
                    # Truncate content if it's too long
                    if len(content) > 80:
                        content = content[:77] + "..."
                    
                    print(f"Result {i+1}:")
                    print(f"  Collection: {collection}")
                    print(f"  Score: {score:.4f}")
                    print(f"  Valid At: {valid_at}")
                    print(f"  Content: {content}")
                    print("")
    except Exception as e:
        logger.error(f"Memory search failed in CLI: {e}", exc_info=True)
        console.print(f"[bold red]Error during memory search:[/bold red] {e}")
        raise typer.Exit(code=1)


# Expose the Memory app for use in the main CLI
def get_memory_app():
    """Get the Memory app Typer instance for use in the main CLI."""
    return memory_app


if __name__ == "__main__":
    """
    Self-validation tests for the memory_commands module.
    
    This validation checks for dependencies and performs appropriate tests
    regardless of whether ArangoDB and other dependencies are available.
    """
    import sys
    
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List of validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Check dependency checker imports
    total_tests += 1
    try:
        test_result = "HAS_ARANGO" in globals() and "check_dependency" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import dependency checker flags")
        else:
            print(f"✓ Dependency flags: HAS_ARANGO = {HAS_ARANGO}")
    except Exception as e:
        all_validation_failures.append(f"Dependency checker validation failed: {e}")
    
    # Test 2: Check UI dependency detection
    total_tests += 1
    try:
        test_result = "HAS_RICH" in globals() and "HAS_TYPER" in globals()
        if not test_result:
            all_validation_failures.append("Failed to check UI dependencies")
        else:
            print(f"✓ UI dependency flags: HAS_RICH = {HAS_RICH}, HAS_TYPER = {HAS_TYPER}")
    except Exception as e:
        all_validation_failures.append(f"UI dependency validation failed: {e}")
    
    # Test 3: Check core memory function imports
    total_tests += 1
    try:
        # Test import paths
        test_result = "MemoryAgent" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import core memory functions")
        else:
            print("✓ Core memory agent imported successfully")
    except Exception as e:
        all_validation_failures.append(f"Import validation failed: {e}")
    
    # Test 4: Verify Typer setup
    total_tests += 1
    try:
        # Check that we have commands registered
        commands = [c.name for c in memory_app.registered_commands]
        expected_commands = ["store", "get-history", "search"]
        
        missing_commands = [cmd for cmd in expected_commands if cmd not in commands]
        if missing_commands:
            all_validation_failures.append(f"Missing commands: {missing_commands}")
        else:
            print(f"✓ All required commands ({', '.join(expected_commands)}) are registered")
    except Exception as e:
        all_validation_failures.append(f"Typer command validation failed: {e}")
    
    # Test 5: Check SimpleConsole fallback
    total_tests += 1
    try:
        if not HAS_RICH:
            # Check that we defined SimpleConsole for fallback
            if 'SimpleConsole' not in globals():
                all_validation_failures.append("SimpleConsole fallback not defined despite Rich being unavailable")
            else:
                print("✓ SimpleConsole fallback is defined as expected")
        else:
            # Check Rich import and console initialization
            if not isinstance(console, Console):
                all_validation_failures.append("Rich is available but console is not a Rich Console instance")
            else:
                print("✓ Rich Console is properly initialized")
    except Exception as e:
        all_validation_failures.append(f"Console fallback validation failed: {e}")
    
    # Display validation results
    if all_validation_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Module validated and ready for use")
        sys.exit(0)