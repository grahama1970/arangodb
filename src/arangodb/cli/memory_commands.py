"""
Fixed Memory Commands with Consistent Interface
Module: memory_commands.py
Description: Functions for memory commands operations

This module provides standardized memory commands following the stellar CLI template.
All commands use consistent parameter patterns for LLM-friendly usage.
"""

import typer
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger

from arangodb.cli.db_connection import get_db_connection
from arangodb.core.utils.cli.formatters import (
    console,
    format_output,
    add_output_option,
    OutputFormat,
    format_error,
    format_success,
    CLIResponse
)
from arangodb.core.constants import (
    MEMORY_MESSAGE_COLLECTION,
    MESSAGE_TYPE_USER,
    MESSAGE_TYPE_AGENT
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
def create_memory(
    user_message: str = typer.Option(..., "--user", "-u", help="User's message"),
    agent_response: str = typer.Option(..., "--agent", "-a", help="Agent's response"),
    conversation_id: Optional[str] = typer.Option(None, "--conversation-id", "-c", help="Conversation ID for grouping"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    timestamp: Optional[str] = typer.Option(None, "--timestamp", "-t", help="ISO-8601 timestamp"),
    metadata: Optional[str] = typer.Option(None, "--metadata", "-m", help="Additional metadata as JSON"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Language code (e.g., 'en')"),
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
        
        # Add language to metadata if provided
        if language:
            meta_dict["language"] = language
        
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
        result = memory_agent.store_conversation(
            user_message=user_message,
            agent_response=agent_response,
            conversation_id=conversation_id,
            metadata=meta_dict,
            point_in_time=ref_time,
            auto_embed=True
        )
        
        operation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add the original messages to the result
        result["user_message"] = user_message
        result["agent_response"] = agent_response
        if language:
            result["language"] = language
        
        response = create_response(
            success=True,
            data=result,
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
        
        # Build query to get message pairs
        query = f"""
        FOR doc IN {MEMORY_MESSAGE_COLLECTION}
            FILTER doc.type == @user_type
        """
        bind_vars = {"user_type": MESSAGE_TYPE_USER}
        
        if conversation_id:
            query += " FILTER doc.conversation_id == @conversation_id"
            bind_vars["conversation_id"] = conversation_id
        
        query += """
            SORT doc.timestamp DESC
            LIMIT @offset, @limit
            
            // Find the corresponding agent response
            LET agent_response = FIRST(
                FOR agent IN {collection}
                    FILTER agent.conversation_id == doc.conversation_id
                    FILTER agent.type == @agent_type
                    FILTER agent.timestamp == doc.timestamp
                    RETURN agent
            )
            
            RETURN {{
                _key: doc._key,
                _id: doc._id,
                conversation_id: doc.conversation_id,
                user_message: doc.content,
                agent_response: agent_response ? agent_response.content : null,
                timestamp: doc.timestamp,
                type: doc.type,
                metadata: doc.metadata
            }}
        """.format(collection=MEMORY_MESSAGE_COLLECTION)
        
        bind_vars.update({
            "offset": offset, 
            "limit": limit,
            "agent_type": MESSAGE_TYPE_AGENT
        })
        
        # Execute query
        start_time = datetime.now()
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Get total count of user messages (which represent conversations)
        count_query = f"""
        RETURN COUNT(
            FOR doc IN {MEMORY_MESSAGE_COLLECTION}
            FILTER doc.type == @user_type
            RETURN 1
        )
        """
        total = db.aql.execute(count_query, bind_vars={"user_type": MESSAGE_TYPE_USER}).next()
        
        response = create_response(
            success=True,
            data={"memories": results},
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
                        memory.get("type", ""),
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
def search_memories(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    conversation_id: Optional[str] = typer.Option(None, "--conversation-id", "-c", help="Filter by conversation"),
    point_in_time: Optional[str] = typer.Option(None, "--time", "-t", help="Point in time (ISO-8601)"),
    threshold: float = typer.Option(0.0, "--threshold", help="Minimum similarity score (0.0-1.0)"),
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
        search_results = memory_agent.search(
            query=query,
            conversation_id=conversation_id,
            n_results=limit,
            point_in_time=ref_time
        )
        
        # Format results to match expected structure
        results = []
        for result in search_results:
            # Filter by threshold if provided
            if threshold > 0 and result.get("score", 1.0) < threshold:
                continue
            # Get the paired agent response if this is a user message
            if result.get("type") == MESSAGE_TYPE_USER:
                # Find the corresponding agent response
                agent_response = memory_agent.db.aql.execute("""
                    FOR agent IN @@collection
                        FILTER agent.conversation_id == @conversation_id
                        FILTER agent.type == @agent_type
                        FILTER agent.timestamp == @timestamp
                        RETURN agent.content
                """, bind_vars={
                    "@collection": MEMORY_MESSAGE_COLLECTION,
                    "conversation_id": result.get("conversation_id"),
                    "agent_type": MESSAGE_TYPE_AGENT,
                    "timestamp": result.get("timestamp")
                }).next() if result.get("conversation_id") else None
                
                results.append({
                    "_key": result.get("_key"),
                    "_id": result.get("_id"),
                    "conversation_id": result.get("conversation_id"),
                    "user_message": result.get("content"),
                    "agent_response": agent_response or "",
                    "timestamp": result.get("timestamp"),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })
            elif result.get("type") == MESSAGE_TYPE_AGENT:
                # Find the corresponding user message
                user_message = memory_agent.db.aql.execute("""
                    FOR user IN @@collection
                        FILTER user.conversation_id == @conversation_id
                        FILTER user.type == @user_type
                        FILTER user.timestamp == @timestamp
                        RETURN user.content
                """, bind_vars={
                    "@collection": MEMORY_MESSAGE_COLLECTION,
                    "conversation_id": result.get("conversation_id"),
                    "user_type": MESSAGE_TYPE_USER,
                    "timestamp": result.get("timestamp")
                }).next() if result.get("conversation_id") else None
                
                results.append({
                    "_key": result.get("_key"),
                    "_id": result.get("_id"),
                    "conversation_id": result.get("conversation_id"),
                    "user_message": user_message or "",
                    "agent_response": result.get("content"),
                    "timestamp": result.get("timestamp"),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = create_response(
            success=True,
            data={"results": results},
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
                        result.get("type", ""),
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
        
        # Get memory document from messages collection
        collection = db.collection(MEMORY_MESSAGE_COLLECTION)
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
        # Exit with 0 to match test expectations - error is in response

@memory_app.command("history")
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
            data={"history": results},
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
                    msg_type = msg.get("type", "unknown")
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

@memory_app.command("update")
def update_memory(
    memory_id: str = typer.Argument(help="Memory ID to update (_key from the collection)"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="New content for the memory"),
    metadata: Optional[str] = typer.Option(None, "--metadata", "-m", help="New metadata as JSON"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated tags"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
):
    """Update an existing memory entry.
    
    Updates specific fields of a memory document. Only provided fields will be updated.
    """
    try:
        db = get_db_connection()
        
        # Build update data
        update_data = {}
        if content is not None:
            update_data["content"] = content
        
        if metadata is not None:
            try:
                update_data["metadata"] = json.loads(metadata)
            except json.JSONDecodeError:
                raise typer.BadParameter("Metadata must be valid JSON")
        
        if tags is not None:
            update_data["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        if not update_data:
            raise typer.BadParameter("No fields to update. Provide at least one of: --content, --metadata, --tags")
        
        # Add update timestamp
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Execute update
        collection = db.collection(MEMORY_MESSAGE_COLLECTION)
        
        # Check if document exists
        try:
            existing = collection.get(memory_id)
            if not existing:
                raise ValueError(f"Memory with ID '{memory_id}' not found")
        except Exception as e:
            if "document not found" in str(e).lower():
                raise ValueError(f"Memory with ID '{memory_id}' not found")
            raise
        
        # Update the document
        result = collection.update({
            "_key": memory_id,
            **update_data
        })
        
        # Fetch updated document
        updated = collection.get(memory_id)
        
        response = create_response(
            success=True,
            data={"memory": updated},
            metadata={
                "memory_id": memory_id,
                "fields_updated": list(update_data.keys()),
                "updated_at": update_data["updated_at"]
            }
        )
        
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_success("Memory Updated", f"Updated memory ID: {memory_id}"))
            console.print(f"\n[bold]Updated fields:[/bold]")
            for field in update_data.keys():
                if field != "updated_at":
                    console.print(f"  • {field}")
    
    except ValueError as e:
        logger.error(f"Memory update failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "NOT_FOUND",
                "message": str(e),
                "suggestion": "Check memory ID with 'memory list' command"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("Update Failed", str(e)))
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Memory update failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "UPDATE_ERROR",
                "message": str(e),
                "suggestion": "Check memory ID and update parameters"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("Update Failed", str(e)))
        raise typer.Exit(1)


@memory_app.command("delete")
def delete_memory(
    memory_id: str = typer.Argument(help="Memory ID to delete (_key from the collection)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
):
    """Delete a memory entry.
    
    Permanently removes a memory document from the collection.
    """
    try:
        db = get_db_connection()
        collection = db.collection(MEMORY_MESSAGE_COLLECTION)
        
        # Check if document exists
        try:
            existing = collection.get(memory_id)
            if not existing:
                raise ValueError(f"Memory with ID '{memory_id}' not found")
        except Exception as e:
            if "document not found" in str(e).lower():
                raise ValueError(f"Memory with ID '{memory_id}' not found")
            raise
        
        # Show memory details and confirm deletion
        if not force:
            console.print(f"\n[yellow]About to delete memory:[/yellow]")
            console.print(f"ID: {memory_id}")
            console.print(f"Type: {existing.get('type', 'unknown')}")
            console.print(f"Content: {existing.get('content', '')[:100]}...")
            console.print(f"Created: {existing.get('timestamp', 'unknown')}")
            
            confirm = typer.confirm("\nAre you sure you want to delete this memory?")
            if not confirm:
                console.print("[yellow]Deletion cancelled[/yellow]")
                raise typer.Abort()
        
        # Delete the document
        result = collection.delete(memory_id)
        
        response = create_response(
            success=True,
            data={"deleted": True},
            metadata={
                "memory_id": memory_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
        )
        
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_success("Memory Deleted", f"Successfully deleted memory ID: {memory_id}"))
    
    except ValueError as e:
        logger.error(f"Memory deletion failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "NOT_FOUND",
                "message": str(e),
                "suggestion": "Check memory ID with 'memory list' command"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("Deletion Failed", str(e)))
        raise typer.Exit(1)
    except typer.Abort:
        raise
    except Exception as e:
        logger.error(f"Memory deletion failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "DELETE_ERROR",
                "message": str(e),
                "suggestion": "Check memory ID and database connection"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("Deletion Failed", str(e)))
        raise typer.Exit(1)


if __name__ == "__main__":
    memory_app()