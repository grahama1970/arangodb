"""
Fixed Memory Commands with Consistent Interface

This module provides standardized memory commands following the stellar CLI template.
All commands use consistent parameter patterns for LLM-friendly usage.
"""

import typer
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger

from arangodb.core.db_operations import get_db_connection
from arangodb.core.utils.cli import (
    console,
    format_output,
    add_output_option,
    OutputFormat,
    format_error,
    format_success
)

# Initialize memory app
memory_app = typer.Typer(help="Memory operations with consistent interface")

# Standard response structure
def create_response(success: bool, data: Any = None, metadata: Dict = None, errors: List = None):
    """Create standardized response structure"""
    return {
        "success": success,
        "data": data,
        "metadata": metadata or {},
        "errors": errors or []
    }

@memory_app.command("create")
@add_output_option
def create_memory(
    user_message: str = typer.Option(..., "--user", "-u", help="User's message"),
    agent_response: str = typer.Option(..., "--agent", "-a", help="Agent's response"),
    conversation_id: Optional[str] = typer.Option(None, "--conversation-id", "-c", help="Conversation ID for grouping"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    timestamp: Optional[str] = typer.Option(None, "--timestamp", "-t", help="ISO-8601 timestamp"),
    metadata: Optional[str] = typer.Option(None, "--metadata", "-m", help="Additional metadata as JSON"),
):
    """
    Create a new memory from user-agent conversation.
    
    USAGE:
        arangodb memory create --user "What is ArangoDB?" --agent "ArangoDB is..." [OPTIONS]
    
    WHEN TO USE:
        When storing conversation exchanges for future retrieval and search
    
    OUTPUT:
        - TABLE: Summary of created memory with ID
        - JSON: Complete memory data with metadata
    
    EXAMPLES:
        arangodb memory create --user "Question" --agent "Answer"
        arangodb memory create --user "Query" --agent "Response" --conversation-id "chat123" --output json
    """
    logger.info(f"Creating memory: conversation_id={conversation_id}")
    
    try:
        db = get_db_connection()
        
        # Parse metadata if provided
        meta_dict = {}
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid metadata JSON: {e}")
        
        # Parse timestamp
        ref_time = None
        if timestamp:
            ref_time = datetime.fromisoformat(timestamp)
        else:
            ref_time = datetime.now()
        
        # Import memory agent
        from arangodb.core.memory.memory_agent import MemoryAgent
        
        # Store the conversation
        memory_agent = MemoryAgent(db=db)
        start_time = datetime.now()
        result = memory_agent.add_message(
            message_type="user",
            content=user_message,
            conversation_id=conversation_id,
            reference_time=ref_time,
            metadata=meta_dict
        )
        
        # Store agent response
        agent_result = memory_agent.add_message(
            message_type="agent",
            content=agent_response,
            conversation_id=result.get("conversation_id"),
            reference_time=ref_time,
            metadata=meta_dict
        )
        
        operation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = create_response(
            success=True,
            data={
                "user_memory": result,
                "agent_memory": agent_result,
                "conversation_id": result.get("conversation_id")
            },
            metadata={
                "operation": "create",
                "timing": {"create_ms": round(operation_time, 2)}
            }
        )
        
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_success(
                f"Memory created successfully. Conversation ID: {result.get('conversation_id')}"
            ))
        
    except Exception as e:
        logger.error(f"Memory creation failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "CREATE_ERROR",
                "message": str(e),
                "suggestion": "Check your input format and database connection"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("Memory Creation Failed", str(e)))
        raise typer.Exit(1)

@memory_app.command("list")
@add_output_option
def list_memories(
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    offset: int = typer.Option(0, "--offset", help="Skip this many results"),
    conversation_id: Optional[str] = typer.Option(None, "--conversation-id", "-c", help="Filter by conversation"),
):
    """
    List stored memories.
    
    USAGE:
        arangodb memory list [OPTIONS]
    
    WHEN TO USE:
        When browsing stored conversations and memories
    
    OUTPUT:
        - TABLE: Summary of memories with timestamps
        - JSON: Complete memory data
    
    EXAMPLES:
        arangodb memory list --limit 20
        arangodb memory list --conversation-id "chat123" --output json
    """
    logger.info("Listing memories")
    
    try:
        db = get_db_connection()
        
        # Build query
        query = """
        FOR doc IN memories
        """
        bind_vars = {}
        
        if conversation_id:
            query += " FILTER doc.conversation_id == @conversation_id"
            bind_vars["conversation_id"] = conversation_id
        
        query += " SORT doc.timestamp DESC"
        query += " LIMIT @offset, @limit"
        query += " RETURN doc"
        
        bind_vars.update({"offset": offset, "limit": limit})
        
        # Execute query
        start_time = datetime.now()
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Get total count
        count_query = "FOR doc IN memories RETURN COUNT(doc)"
        total = db.aql.execute(count_query).next()
        
        response = create_response(
            success=True,
            data=results,
            metadata={
                "count": len(results),
                "total": total,
                "limit": limit,
                "offset": offset,
                "conversation_id": conversation_id,
                "timing": {"query_ms": round(query_time, 2)}
            }
        )
        
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            if results:
                from rich.table import Table
                table = Table(title="Memories")
                table.add_column("ID", style="cyan")
                table.add_column("Type", style="magenta")
                table.add_column("Conversation", style="blue")
                table.add_column("Content", style="white")
                table.add_column("Timestamp", style="green")
                
                for memory in results:
                    content = memory.get("content", "")
                    content_preview = content[:50] + "..." if len(content) > 50 else content
                    
                    table.add_row(
                        memory.get("_key", ""),
                        memory.get("message_type", ""),
                        memory.get("conversation_id", "")[:12] + "...",
                        content_preview,
                        memory.get("timestamp", "")[:19]
                    )
                
                table.caption = f"Showing {len(results)} of {total} memories"
                console.print(table)
            else:
                console.print("[yellow]No memories found[/yellow]")
        
    except Exception as e:
        logger.error(f"List memories failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "LIST_ERROR",
                "message": str(e),
                "suggestion": "Check database connection and permissions"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("List Failed", str(e)))
        raise typer.Exit(1)

@memory_app.command("search")
@add_output_option
def search_memories(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    conversation_id: Optional[str] = typer.Option(None, "--conversation-id", "-c", help="Filter by conversation"),
    point_in_time: Optional[str] = typer.Option(None, "--time", "-t", help="Point in time (ISO-8601)"),
):
    """
    Search memories by content.
    
    USAGE:
        arangodb memory search --query "database concepts" [OPTIONS]
    
    WHEN TO USE:
        When finding specific conversations or topics in memory
    
    OUTPUT:
        - TABLE: Matching memories with relevance scores
        - JSON: Complete search results with metadata
    
    EXAMPLES:
        arangodb memory search --query "ArangoDB features"
        arangodb memory search --query "optimization" --conversation-id "chat456" --output json
    """
    logger.info(f"Searching memories: query='{query}'")
    
    try:
        db = get_db_connection()
        
        # Parse point in time
        ref_time = None
        if point_in_time:
            ref_time = datetime.fromisoformat(point_in_time)
        else:
            ref_time = datetime.now()
        
        # Import memory agent
        from arangodb.core.memory.memory_agent import MemoryAgent
        
        memory_agent = MemoryAgent(db=db)
        start_time = datetime.now()
        
        # Search memories
        results = memory_agent.search(
            query=query,
            conversation_id=conversation_id,
            n_results=limit,
            point_in_time=ref_time
        )
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = create_response(
            success=True,
            data=results,
            metadata={
                "query": query,
                "count": len(results),
                "limit": limit,
                "conversation_id": conversation_id,
                "point_in_time": ref_time.isoformat() if ref_time else None,
                "timing": {"search_ms": round(search_time, 2)}
            }
        )
        
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            if results:
                from rich.table import Table
                table = Table(title=f"Search Results for '{query}'")
                table.add_column("ID", style="cyan")
                table.add_column("Type", style="magenta")
                table.add_column("Content", style="white")
                table.add_column("Score", style="yellow")
                table.add_column("Timestamp", style="green")
                
                for result in results:
                    content = result.get("content", "")
                    content_preview = content[:60] + "..." if len(content) > 60 else content
                    
                    table.add_row(
                        result.get("_key", ""),
                        result.get("message_type", ""),
                        content_preview,
                        f"{result.get('score', 0):.3f}",
                        result.get("timestamp", "")[:19]
                    )
                
                table.caption = f"Found {len(results)} matching memories"
                console.print(table)
            else:
                console.print("[yellow]No memories found matching query[/yellow]")
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "SEARCH_ERROR",
                "message": str(e),
                "suggestion": "Check query syntax and database connection"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("Search Failed", str(e)))
        raise typer.Exit(1)

@memory_app.command("get")
@add_output_option
def get_memory(
    memory_id: str = typer.Argument(..., help="Memory ID to retrieve"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
):
    """
    Get a specific memory by ID.
    
    USAGE:
        arangodb memory get <memory_id> [OPTIONS]
    
    WHEN TO USE:
        When retrieving a specific memory record
    
    OUTPUT:
        - TABLE: Memory details in formatted table
        - JSON: Complete memory document
    
    EXAMPLES:
        arangodb memory get memory123
        arangodb memory get memory456 --output json
    """
    logger.info(f"Getting memory: id={memory_id}")
    
    try:
        db = get_db_connection()
        
        # Get memory document
        collection = db.collection("memories")
        memory = collection.get(memory_id)
        
        if not memory:
            raise ValueError(f"Memory '{memory_id}' not found")
        
        response = create_response(
            success=True,
            data=memory,
            metadata={
                "id": memory_id,
                "found": True
            }
        )
        
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            from rich.table import Table
            table = Table(title=f"Memory: {memory_id}", show_header=False)
            table.add_column("Field", style="cyan")
            table.add_column("Value")
            
            for key, value in memory.items():
                if not key.startswith('_'):
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, indent=2)
                    table.add_row(key.replace('_', ' ').title(), str(value))
            
            console.print(table)
        
    except Exception as e:
        logger.error(f"Get memory failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "GET_ERROR",
                "message": str(e),
                "suggestion": f"Verify memory ID '{memory_id}' exists"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("Get Failed", str(e)))
        raise typer.Exit(1)

@memory_app.command("history")
@add_output_option
def get_history(
    conversation_id: str = typer.Option(..., "--conversation-id", "-c", help="Conversation ID"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(50, "--limit", "-l", help="Number of messages"),
    chronological: bool = typer.Option(True, "--chronological/--reverse", help="Sort order"),
):
    """
    Get conversation history.
    
    USAGE:
        arangodb memory history --conversation-id "chat123" [OPTIONS]
    
    WHEN TO USE:
        When retrieving complete conversation threads
    
    OUTPUT:
        - TABLE: Conversation in readable format
        - JSON: Complete conversation data
    
    EXAMPLES:
        arangodb memory history --conversation-id "chat789"
        arangodb memory history --conversation-id "chat456" --limit 100 --output json
    """
    logger.info(f"Getting history: conversation_id={conversation_id}")
    
    try:
        db = get_db_connection()
        
        # Import memory agent
        from arangodb.core.memory.memory_agent import MemoryAgent
        
        memory_agent = MemoryAgent(db=db)
        results = memory_agent.get_conversation_history(
            conversation_id=conversation_id,
            n_results=limit,
            chronological=chronological
        )
        
        response = create_response(
            success=True,
            data=results,
            metadata={
                "conversation_id": conversation_id,
                "count": len(results),
                "limit": limit,
                "chronological": chronological
            }
        )
        
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            if results:
                console.print(f"\n[bold]Conversation: {conversation_id}[/bold]\n")
                
                for msg in results:
                    msg_type = msg.get("message_type", "unknown")
                    content = msg.get("content", "")
                    timestamp = msg.get("timestamp", "")[:19]
                    
                    if msg_type == "user":
                        console.print(f"[blue]User ({timestamp}):[/blue]")
                        console.print(f"  {content}\n")
                    else:
                        console.print(f"[green]Agent ({timestamp}):[/green]")
                        console.print(f"  {content}\n")
            else:
                console.print("[yellow]No conversation history found[/yellow]")
        
    except Exception as e:
        logger.error(f"Get history failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "HISTORY_ERROR",
                "message": str(e),
                "suggestion": f"Check conversation ID '{conversation_id}'"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("History Failed", str(e)))
        raise typer.Exit(1)

if __name__ == "__main__":
    memory_app()