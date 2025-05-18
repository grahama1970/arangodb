"""
Generic CRUD commands (simplified version)
"""

import json
from typing import Optional, List, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich import box
from loguru import logger

from arangodb.cli.db_connection import get_db_connection
from arangodb.core.constants import EMBEDDING_FIELD
from arangodb.core.utils.embedding_utils import get_embedding

app = typer.Typer(help="Generic CRUD operations for any collection")
console = Console()

@app.command("list")
def list_docs(
    collection: str = typer.Argument(..., help="Name of the collection"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of documents to return"),
    offset: int = typer.Option(0, "--offset", help="Number of documents to skip"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """List documents from any collection"""
    try:
        db = get_db_connection()
        
        # Build AQL query
        query = f"""
        FOR doc IN {collection}
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
                # Create table with limited columns for readability
                table = Table(title=f"Documents from {collection}", box=box.ROUNDED)
                
                # Add essential columns
                essential_keys = ["_key", "_id", "title", "name", "description", "type", "tags"]
                
                # Find which keys exist
                available_keys = []
                for key in essential_keys:
                    if any(key in doc for doc in documents):
                        available_keys.append(key)
                
                # Add any other keys (up to a limit)
                other_keys = set()
                for doc in documents:
                    other_keys.update(doc.keys())
                other_keys -= set(available_keys)
                other_keys -= {"_rev", "embedding", "embedding_metadata"}
                available_keys.extend(sorted(list(other_keys))[:3])
                
                # Add columns
                for key in available_keys:
                    table.add_column(key, style="cyan")
                
                # Add rows
                for doc in documents:
                    row = []
                    for key in available_keys:
                        value = doc.get(key, "")
                        if isinstance(value, (dict, list)):
                            value_str = json.dumps(value)
                            if len(value_str) > 50:
                                value_str = value_str[:47] + "..."
                        else:
                            value_str = str(value)
                            if len(value_str) > 50:
                                value_str = value_str[:47] + "..."
                        row.append(value_str)
                    table.add_row(*row)
                
                console.print(table)
                console.print(f"\nTotal: {len(documents)} documents", style="green")
                
    except Exception as e:
        console.print(f"❌ Error listing documents: {e}", style="red")
        raise typer.Exit(1)

@app.command()
def create(
    collection: str = typer.Argument(..., help="Name of the collection"),
    data: str = typer.Argument(..., help="JSON data for the document"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
):
    """Create a new document in any collection"""
    try:
        # Parse JSON data
        document = json.loads(data)
        
        # Get embedding if document has text fields
        text_fields = ["content", "text", "description", "summary", "title"]
        texts_to_embed = []
        for field in text_fields:
            if field in document:
                texts_to_embed.append(str(document[field]))
        
        if texts_to_embed:
            combined_text = " ".join(texts_to_embed)
            embedding = get_embedding(combined_text)
            if embedding:
                document[EMBEDDING_FIELD] = embedding
                document["embedding_metadata"] = {
                    "model": "default",
                    "dimensions": len(embedding),
                    "fields_embedded": [f for f in text_fields if f in document]
                }
        
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
            console.print(f"✅ Created document: {result['_key']}", style="green")
            
            # Show key fields
            table = Table(box=box.ROUNDED)
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")
            
            # Show key document fields
            for key in ["_key", "_id", "title", "name", "type"]:
                if key in document:
                    table.add_row(key, str(document[key]))
            
            if "embedding_metadata" in document:
                table.add_row("embedding", f"Generated ({document['embedding_metadata']['dimensions']}D)")
            
            console.print(table)
            
    except json.JSONDecodeError as e:
        console.print(f"❌ Invalid JSON: {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error creating document: {e}", style="red")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()