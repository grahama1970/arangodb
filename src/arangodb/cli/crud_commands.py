"""
Fixed CRUD Commands with Consistent Interface
Module: crud_commands.py
Description: Functions for crud commands operations

This module provides standardized CRUD commands following the stellar CLI template.
Works with ANY collection, not just lesson-specific operations.
"""

import typer
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
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
from arangodb.core.utils.embedding_utils import get_embedding

# Initialize CRUD app
crud_app = typer.Typer(help="CRUD operations with consistent interface")

# Standard response structure
def create_response(success: bool, data: Any = None, metadata: Dict = None, errors: List = None):
    """Create standardized response structure"""
    return {
        "success": success,
        "data": data,
        "metadata": metadata or {},
        "errors": errors or []
    }

@crud_app.command("create")
def create_document(
    collection: str = typer.Argument(..., help="Collection name"),
    data: str = typer.Argument(..., help="Document data as JSON string"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Custom document key"),
    embed: bool = typer.Option(True, "--embed/--no-embed", help="Generate embeddings for text fields"),
    embed_fields: Optional[str] = typer.Option(None, "--embed-fields", help="Comma-separated fields to embed"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)"),
):
    """
    Create a new document in any collection.
    
    USAGE:
        arangodb crud create <collection> <json_data> [OPTIONS]
    
    WHEN TO USE:
        When adding new documents to any collection with optional embedding
    
    OUTPUT:
        - TABLE: Summary with created document ID
        - JSON: Complete document with metadata
    
    EXAMPLES:
        arangodb crud create users '{"name": "John", "email": "john@example.com"}'
        arangodb crud create articles '{"title": "Guide", "content": "..."}' --embed
        arangodb crud create products '{"name": "Widget", "price": 9.99}' --key "widget-001"
    """
    logger.info(f"Creating document in collection: {collection}")
    
    try:
        db = get_db_connection()
        collection_obj = db.collection(collection)
        
        # Parse JSON data
        try:
            doc_data = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        # Add metadata
        doc_data["created_at"] = datetime.now().isoformat()
        
        # Set custom key if provided
        if key:
            doc_data["_key"] = key
        
        # Generate embeddings if requested
        if embed:
            fields_to_embed = []
            if embed_fields:
                fields_to_embed = [f.strip() for f in embed_fields.split(",")]
            else:
                # Auto-detect text fields
                fields_to_embed = [k for k, v in doc_data.items() 
                                 if isinstance(v, str) and len(v) > 20]
            
            if fields_to_embed:
                # Combine text from specified fields
                text_content = " ".join(str(doc_data.get(f, "")) for f in fields_to_embed)
                if text_content.strip():
                    embedding = get_embedding(text_content)
                    doc_data["embedding"] = embedding
                    doc_data["embedding_fields"] = fields_to_embed
                    logger.debug(f"Generated embedding for fields: {fields_to_embed}")
        
        # Insert document
        start_time = datetime.now()
        result = collection_obj.insert(doc_data)
        insert_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Get the created document
        created_doc = collection_obj.get(result["_key"])
        
        response = create_response(
            success=True,
            data=created_doc,
            metadata={
                "operation": "create",
                "collection": collection,
                "key": result["_key"],
                "embedded": embed and "embedding" in created_doc,
                "timing": {"insert_ms": round(insert_time, 2)}
            }
        )
        
        if output_format == "json":
            console.print_json(data=response)
        else:
            console.print(format_success(
                f"Document created successfully\n"
                f"Collection: {collection}\n"
                f"Key: {result['_key']}\n"
                f"Embedded: {'Yes' if embed and 'embedding' in created_doc else 'No'}"
            ))
        
    except Exception as e:
        logger.error(f"Create failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "CREATE_ERROR",
                "message": str(e),
                "suggestion": "Check JSON syntax and collection exists"
            }]
        )
        if output_format == "json":
            console.print_json(data=response)
        else:
            console.print(format_error("Create Failed", str(e)))
        raise typer.Exit(1)

@crud_app.command("read")
def read_document(
    collection: str = typer.Argument(..., help="Collection name"),
    key: str = typer.Argument(..., help="Document key"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)"),
):
    """
    Read a document from any collection.
    
    USAGE:
        arangodb crud read <collection> <key> [OPTIONS]
    
    WHEN TO USE:
        When retrieving a specific document by its key
    
    OUTPUT:
        - TABLE: Formatted document fields
        - JSON: Complete document data
    
    EXAMPLES:
        arangodb crud read users user-123
        arangodb crud read articles article-456 --output json
    """
    logger.info(f"Reading document: {collection}/{key}")
    
    try:
        db = get_db_connection()
        collection_obj = db.collection(collection)
        
        # Get document
        document = collection_obj.get(key)
        
        if not document:
            raise ValueError(f"Document '{key}' not found in collection '{collection}'")
        
        response = create_response(
            success=True,
            data=document,
            metadata={
                "operation": "read",
                "collection": collection,
                "key": key
            }
        )
        
        if output_format == "json":
            console.print_json(data=response)
        else:
            from rich.table import Table
            table = Table(title=f"Document: {collection}/{key}", show_header=False)
            table.add_column("Field", style="cyan")
            table.add_column("Value")
            
            for field, value in document.items():
                if field == "embedding":
                    value = f"[{len(value)} dimensions]"
                elif isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                table.add_row(field.replace('_', ' ').title(), str(value))
            
            console.print(table)
        
    except Exception as e:
        logger.error(f"Read failed: {e}")
        error_message = str(e)
        response = create_response(
            success=False,
            errors=[{
                "code": "READ_ERROR",
                "message": error_message,
                "suggestion": f"Verify document '{key}' exists in '{collection}'"
            }]
        )
        # Add error field for backward compatibility with tests
        response["error"] = error_message
        
        if output_format == "json":
            console.print_json(data=response)
        else:
            console.print(format_error("Read Failed", error_message))
        # Exit with 0 for read operations to allow error handling in scripts

@crud_app.command("update")
def update_document(
    collection: str = typer.Argument(..., help="Collection name"),
    key: str = typer.Argument(..., help="Document key"),
    data: str = typer.Argument(..., help="Update data as JSON string"),
    replace: bool = typer.Option(False, "--replace", "-r", help="Replace entire document"),
    embed: bool = typer.Option(True, "--embed/--no-embed", help="Update embeddings"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)"),
):
    """
    Update a document in any collection.
    
    USAGE:
        arangodb crud update <collection> <key> <json_data> [OPTIONS]
    
    WHEN TO USE:
        When modifying existing documents
    
    OUTPUT:
        - TABLE: Summary of update operation
        - JSON: Updated document with metadata
    
    EXAMPLES:
        arangodb crud update users user-123 '{"email": "newemail@example.com"}'
        arangodb crud update articles article-456 '{"status": "published"}' --no-embed
        arangodb crud update products widget-001 '{"price": 12.99}' --replace
    """
    logger.info(f"Updating document: {collection}/{key}")
    
    try:
        db = get_db_connection()
        collection_obj = db.collection(collection)
        
        # Parse update data
        try:
            update_data = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        # Add metadata
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Get existing document for embedding update
        existing_doc = collection_obj.get(key)
        if not existing_doc:
            raise ValueError(f"Document '{key}' not found")
        
        # Update embeddings if requested
        if embed:
            # Determine which fields to embed
            text_fields = []
            if replace:
                # For replace, use fields from new data
                text_fields = [k for k, v in update_data.items() 
                             if isinstance(v, str) and len(v) > 20]
            else:
                # For merge, combine existing and new text fields
                merged_data = {**existing_doc, **update_data}
                text_fields = [k for k, v in merged_data.items() 
                             if isinstance(v, str) and len(v) > 20]
            
            if text_fields:
                # Generate new embedding
                if replace:
                    text_content = " ".join(str(update_data.get(f, "")) for f in text_fields)
                else:
                    merged_data = {**existing_doc, **update_data}
                    text_content = " ".join(str(merged_data.get(f, "")) for f in text_fields)
                
                if text_content.strip():
                    embedding = get_embedding(text_content)
                    update_data["embedding"] = embedding
                    update_data["embedding_fields"] = text_fields
                    logger.debug(f"Updated embedding for fields: {text_fields}")
        
        # Perform update
        start_time = datetime.now()
        if replace:
            # For replace, include the _key in the document
            update_data["_key"] = key
            result = collection_obj.replace(update_data)
        else:
            # For update, merge the changes into existing doc
            merged_doc = {**existing_doc, **update_data}
            merged_doc["_key"] = key
            result = collection_obj.replace(merged_doc)
        update_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Get updated document
        updated_doc = collection_obj.get(key)
        
        response = create_response(
            success=True,
            data=updated_doc,
            metadata={
                "operation": "update",
                "collection": collection,
                "key": key,
                "replace": replace,
                "embedded": embed and "embedding" in update_data,
                "timing": {"update_ms": round(update_time, 2)}
            }
        )
        
        if output_format == "json":
            console.print_json(data=response)
        else:
            console.print(format_success(
                f"Document updated successfully\n"
                f"Collection: {collection}\n"
                f"Key: {key}\n"
                f"Mode: {'Replace' if replace else 'Merge'}\n"
                f"Embedded: {'Updated' if embed and 'embedding' in update_data else 'No'}"
            ))
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        error_message = str(e)
        response = create_response(
            success=False,
            errors=[{
                "code": "UPDATE_ERROR",
                "message": error_message,
                "suggestion": "Check document exists and JSON is valid"
            }]
        )
        # Add error field for backward compatibility with tests
        response["error"] = error_message
        
        if output_format == "json":
            console.print_json(data=response)
        else:
            console.print(format_error("Update Failed", error_message))
        # Exit with 0 for update operations to allow error handling in scripts

@crud_app.command("delete")
def delete_document(
    collection: str = typer.Argument(..., help="Collection name"),
    key: str = typer.Argument(..., help="Document key"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)"),
):
    """
    Delete a document from any collection.
    
    USAGE:
        arangodb crud delete <collection> <key> [OPTIONS]
    
    WHEN TO USE:
        When removing documents from a collection
    
    OUTPUT:
        - TABLE: Deletion confirmation
        - JSON: Operation metadata
    
    EXAMPLES:
        arangodb crud delete users user-123 --force
        arangodb crud delete articles article-456 --output json
    """
    logger.info(f"Deleting document: {collection}/{key}")
    
    try:
        db = get_db_connection()
        collection_obj = db.collection(collection)
        
        # Check if document exists
        document = collection_obj.get(key)
        if not document:
            raise ValueError(f"Document '{key}' not found in collection '{collection}'")
        
        # Confirm deletion
        if not force:
            console.print(f"[yellow]About to delete document: {collection}/{key}[/yellow]")
            if not typer.confirm("Are you sure?"):
                console.print("[red]Deletion cancelled[/red]")
                raise typer.Exit(0)
        
        # Delete document
        start_time = datetime.now()
        result = collection_obj.delete(key)
        delete_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = create_response(
            success=True,
            data={"deleted_key": key},
            metadata={
                "operation": "delete",
                "collection": collection,
                "key": key,
                "timing": {"delete_ms": round(delete_time, 2)}
            }
        )
        
        if output_format == "json":
            console.print_json(data=response)
        else:
            console.print(format_success(
                f"Document deleted successfully\n"
                f"Collection: {collection}\n"
                f"Key: {key}"
            ))
        
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "DELETE_ERROR",
                "message": str(e),
                "suggestion": f"Verify document '{key}' exists in '{collection}'"
            }]
        )
        if output_format == "json":
            console.print_json(data=response)
        else:
            console.print(format_error("Delete Failed", str(e)))
        raise typer.Exit(1)

@crud_app.command("list")
def list_documents(
    collection: str = typer.Argument(..., help="Collection name"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    offset: int = typer.Option(0, "--offset", help="Skip this many results"),
    filter_field: Optional[str] = typer.Option(None, "--filter-field", help="Field to filter by"),
    filter_value: Optional[str] = typer.Option(None, "--filter-value", help="Value to filter for"),
    sort_by: Optional[str] = typer.Option(None, "--sort", "-s", help="Field to sort by"),
    descending: bool = typer.Option(False, "--desc", help="Sort in descending order"),
    output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)"),
):
    """
    List documents from any collection.
    
    USAGE:
        arangodb crud list <collection> [OPTIONS]
    
    WHEN TO USE:
        When browsing documents in a collection
    
    OUTPUT:
        - TABLE: Document summaries in table format
        - JSON: Complete document list with metadata
    
    EXAMPLES:
        arangodb crud list users --limit 20
        arangodb crud list articles --filter-field status --filter-value published
        arangodb crud list products --sort price --desc --output json
    """
    logger.info(f"Listing documents from collection: {collection}")
    logger.debug(f"Parameters: limit={limit}, offset={offset}, filter_field={filter_field}, filter_value={filter_value}, sort_by={sort_by}")
    
    try:
        db = get_db_connection()
        
        # Build query - use backticks for collection name to handle special characters
        query = f"FOR doc IN `{collection}`"
        bind_vars = {}
        
        # Add filter if specified
        if filter_field and filter_value:
            query += f" FILTER doc.{filter_field} == @value"
            bind_vars["value"] = filter_value
        
        # Add sorting
        if sort_by:
            query += f" SORT doc.{sort_by} {'DESC' if descending else 'ASC'}"
        
        # Add limit and offset
        query += " LIMIT @offset, @limit"
        bind_vars.update({"offset": offset, "limit": limit})
        
        query += " RETURN doc"
        
        logger.debug(f"Query: {query}")
        logger.debug(f"Bind vars: {bind_vars}")
        
        # Execute query
        start_time = datetime.now()
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Get total count
        count_query = f"FOR doc IN `{collection}`"
        if filter_field and filter_value:
            count_query += f" FILTER doc.{filter_field} == @value"
        count_query += " RETURN doc"
        
        if filter_field and filter_value:
            count_cursor = db.aql.execute(count_query, bind_vars={"value": filter_value})
        else:
            count_cursor = db.aql.execute(count_query)
        total = len(list(count_cursor))
        
        response = create_response(
            success=True,
            data=results,
            metadata={
                "collection": collection,
                "count": len(results),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filter": {"field": filter_field, "value": filter_value} if filter_field else None,
                "sort": {"field": sort_by, "order": "desc" if descending else "asc"} if sort_by else None,
                "timing": {"query_ms": round(query_time, 2)}
            }
        )
        
        if output_format == "json":
            console.print_json(data=response)
        else:
            if results:
                from rich.table import Table
                table = Table(title=f"Documents in {collection}")
                
                # Add columns based on first document
                if results[0]:
                    for key in results[0].keys():
                        if not key.startswith('_') or key == "_key":
                            table.add_column(key.replace('_', ' ').title())
                
                # Add rows
                for doc in results:
                    row = []
                    for key in results[0].keys():
                        if not key.startswith('_') or key == "_key":
                            value = doc.get(key, '')
                            if key == "embedding":
                                value = f"[{len(value)} dims]"
                            elif isinstance(value, (dict, list)):
                                value = json.dumps(value)[:30] + "..."
                            else:
                                value = str(value)[:50]
                            row.append(value)
                    table.add_row(*row)
                
                table.caption = f"Showing {len(results)} of {total} documents"
                console.print(table)
            else:
                console.print("[yellow]No documents found[/yellow]")
        
    except Exception as e:
        logger.error(f"List failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "LIST_ERROR",
                "message": str(e),
                "suggestion": f"Verify collection '{collection}' exists"
            }]
        )
        if output_format == "json":
            console.print_json(data=response)
        else:
            console.print(format_error("List Failed", str(e)))
        raise typer.Exit(1)

if __name__ == "__main__":
    crud_app()