"""
Generic CRUD commands that work with any collection

Provides create, read, update, delete, and list operations for any ArangoDB collection
with automatic re-embedding on document modifications.
"""

import json
from typing import Optional, List, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich import box
from loguru import logger

from arangodb.cli.db_connection import get_db_connection
from arangodb.core.utils.formatters import format_document, format_documents
from arangodb.core.constants import EMBEDDING_FIELD
EMBEDDING_METADATA_FIELD = "embedding_metadata"
from arangodb.core.utils.embedding_utils import get_embedding
from arangodb.core.utils.cli import OutputFormat

app = typer.Typer(help="Generic CRUD operations for any collection")
console = Console()

def ensure_embedding(document: Dict[str, Any], embed_fields: List[str] = None) -> Dict[str, Any]:
    """Ensure document has embeddings for specified fields"""
    if embed_fields is None:
        embed_fields = ["content", "text", "description", "summary"]
    
    # Find which fields exist in the document
    text_to_embed = []
    for field in embed_fields:
        if field in document:
            text_to_embed.append(str(document[field]))
    
    if text_to_embed:
        combined_text = " ".join(text_to_embed)
        embedding = get_embedding(combined_text)
        
        # Add embedding to document
        document[EMBEDDING_FIELD] = embedding
        document[EMBEDDING_METADATA_FIELD] = {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimensions": len(embedding),
            "fields_embedded": [f for f in embed_fields if f in document]
        }
    
    return document

@app.command()
def create(
    collection: str = typer.Argument(..., help="Name of the collection"),
    data: str = typer.Argument(..., help="JSON data for the document"),
    embed: bool = typer.Option(True, "--embed/--no-embed", help="Generate embeddings for the document"),
    embed_fields: Optional[str] = typer.Option(None, "--embed-fields", help="Comma-separated list of fields to embed"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """Create a new document in any collection"""
    try:
        # Parse JSON data
        document = json.loads(data)
        
        # Handle embedding
        if embed:
            fields = embed_fields.split(",") if embed_fields else None
            document = ensure_embedding(document, fields)
        
        # Create document
        db = get_db_connection()
        collection_obj = db[collection]
        
        result = collection_obj.insert(document)
        document["_id"] = result["_id"]
        document["_key"] = result["_key"]
        
        # Format output
        if output == "json":
            console.print_json(data=document)
        else:
            formatted = format_document(document)
            console.print(formatted)
            
    except json.JSONDecodeError as e:
        console.print(f"❌ Invalid JSON: {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error creating document: {e}", style="red")
        raise typer.Exit(1)

@app.command()
def read(
    collection: str = typer.Argument(..., help="Name of the collection"),
    key: str = typer.Argument(..., help="Document key or ID"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """Read a document from any collection"""
    try:
        db = get_db_connection()
        collection_obj = db[collection]
        
        # Support both key and full ID
        if "/" not in key:
            key = f"{collection}/{key}"
            
        document = collection_obj.get(key)
        
        if not document:
            console.print(f"❌ Document not found: {key}", style="red")
            raise typer.Exit(1)
        
        # Format output
        if output == "json":
            console.print_json(data=document)
        else:
            formatted = format_document(document)
            console.print(formatted)
            
    except Exception as e:
        console.print(f"❌ Error reading document: {e}", style="red")
        raise typer.Exit(1)

@app.command()
def update(
    collection: str = typer.Argument(..., help="Name of the collection"),
    key: str = typer.Argument(..., help="Document key or ID"),
    data: str = typer.Argument(..., help="JSON data to update"),
    embed: bool = typer.Option(True, "--embed/--no-embed", help="Re-generate embeddings for the document"),
    embed_fields: Optional[str] = typer.Option(None, "--embed-fields", help="Comma-separated list of fields to embed"),
    merge: bool = typer.Option(True, "--merge/--replace", help="Merge with existing data or replace"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """Update a document in any collection"""
    try:
        # Parse JSON data
        update_data = json.loads(data)
        
        db = get_db_connection()
        collection_obj = db[collection]
        
        # Support both key and full ID
        if "/" not in key:
            key = f"{collection}/{key}"
        
        # Get existing document if merging
        if merge:
            existing = collection_obj.get(key)
            if not existing:
                console.print(f"❌ Document not found: {key}", style="red")
                raise typer.Exit(1)
            
            # Merge data
            existing.update(update_data)
            document = existing
        else:
            document = update_data
        
        # Handle embedding
        if embed:
            fields = embed_fields.split(",") if embed_fields else None
            document = ensure_embedding(document, fields)
        
        # Update document
        result = collection_obj.update(document)
        
        # Get updated document
        updated = collection_obj.get(key)
        
        # Format output
        if output == "json":
            console.print_json(data=updated)
        else:
            formatted = format_document(updated)
            console.print(formatted)
            
    except json.JSONDecodeError as e:
        console.print(f"❌ Invalid JSON: {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error updating document: {e}", style="red")
        raise typer.Exit(1)

@app.command()
def delete(
    collection: str = typer.Argument(..., help="Name of the collection"),
    key: str = typer.Argument(..., help="Document key or ID"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """Delete a document from any collection"""
    try:
        db = get_db_connection()
        collection_obj = db[collection]
        
        # Support both key and full ID
        if "/" not in key:
            key = f"{collection}/{key}"
        
        # Get document before deletion for output
        document = collection_obj.get(key)
        if not document:
            console.print(f"❌ Document not found: {key}", style="red")
            raise typer.Exit(1)
        
        # Delete document
        collection_obj.delete(key)
        
        # Format output
        success_message = {"status": "deleted", "document": document}
        
        if output == "json":
            console.print_json(data=success_message)
        else:
            console.print(f"✅ Deleted document: {key}", style="green")
            formatted = format_document(document)
            console.print(formatted)
            
    except Exception as e:
        console.print(f"❌ Error deleting document: {e}", style="red")
        raise typer.Exit(1)

@app.command()
def list(
    collection: str = typer.Argument(..., help="Name of the collection"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of documents to return"),
    offset: int = typer.Option(0, "--offset", help="Number of documents to skip"),
    filter: Optional[str] = typer.Option(None, "--filter", "-f", help="AQL filter expression"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """List documents from any collection"""
    try:
        db = get_db_connection()
        
        # Build AQL query
        filter_clause = f"FILTER {filter}" if filter else ""
        query = f"""
        FOR doc IN {collection}
            {filter_clause}
            LIMIT @offset, @limit
            RETURN doc
        """
        
        bind_vars = {
            "offset": offset,
            "limit": limit
        }
        
        # Execute query
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        documents = list(cursor)
        
        # Format output
        if output == "json":
            console.print_json(data=documents)
        else:
            if not documents:
                console.print("No documents found", style="yellow")
            else:
                table = Table(title=f"Documents from {collection}")
                
                # Add columns based on first document
                if documents:
                    for key in documents[0].keys():
                        table.add_column(key, style="cyan")
                    
                    # Add rows
                    for doc in documents:
                        row = []
                        for key in documents[0].keys():
                            value = doc.get(key, "")
                            if isinstance(value, (dict, list)):
                                value = json.dumps(value, indent=2)
                            row.append(str(value))
                        table.add_row(*row)
                
                console.print(table)
                console.print(f"\nTotal: {len(documents)} documents", style="green")
                
    except Exception as e:
        console.print(f"❌ Error listing documents: {e}", style="red")
        raise typer.Exit(1)

@app.command()
def count(
    collection: str = typer.Argument(..., help="Name of the collection"),
    filter: Optional[str] = typer.Option(None, "--filter", "-f", help="AQL filter expression"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """Count documents in any collection"""
    try:
        db = get_db_connection()
        
        # Build AQL query
        filter_clause = f"FILTER {filter}" if filter else ""
        query = f"""
        FOR doc IN {collection}
            {filter_clause}
            COLLECT WITH COUNT INTO total
            RETURN total
        """
        
        # Execute query
        cursor = db.aql.execute(query)
        result = list(cursor)
        count = result[0] if result else 0
        
        # Format output
        if output == "json":
            console.print_json(data={"collection": collection, "count": count})
        else:
            console.print(f"Document count in '{collection}': {count}", style="green")
            
    except Exception as e:
        console.print(f"❌ Error counting documents: {e}", style="red")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()