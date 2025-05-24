"""
Simplified MCP Interface for ArangoDB

This module provides a flattened command structure for better MCP integration.
Instead of nested commands like 'crud create', 'search semantic', we provide
direct commands like 'create_entity', 'search_semantic'.
"""

import typer
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

from arangodb.cli.db_connection import get_db_connection
from arangodb.core.utils.embedding_utils import get_embedding
from arangodb.cli.slash_mcp_mixin import add_slash_mcp_commands

# Create simplified app
app = typer.Typer(
    name="arangodb-simple",
    help="Simplified ArangoDB CLI for MCP integration"
)

# CRUD Operations

@app.command()
def create_entity(
    collection: str = typer.Argument(..., help="Collection name"),
    data: str = typer.Argument(..., help="Entity data as JSON string"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Custom document key"),
    embed: bool = typer.Option(True, "--embed/--no-embed", help="Generate embeddings")
):
    """Create an entity in any collection with optional embeddings."""
    try:
        db = get_db_connection()
        doc_data = json.loads(data)
        
        # Add timestamp
        doc_data["created_at"] = datetime.now().isoformat()
        
        # Set custom key if provided
        if key:
            doc_data["_key"] = key
            
        # Generate embedding if requested
        if embed:
            text_fields = [v for v in doc_data.values() if isinstance(v, str) and len(v) > 20]
            if text_fields:
                text_content = " ".join(text_fields)
                doc_data["embedding"] = get_embedding(text_content)
        
        # Insert document
        collection_obj = db.collection(collection)
        result = collection_obj.insert(doc_data)
        
        return json.dumps({
            "success": True,
            "key": result["_key"],
            "collection": collection
        })
        
    except Exception as e:
        logger.error(f"Create entity failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@app.command()
def get_entity(
    collection: str = typer.Argument(..., help="Collection name"),
    key: str = typer.Argument(..., help="Document key")
):
    """Get an entity by key from any collection."""
    try:
        db = get_db_connection()
        collection_obj = db.collection(collection)
        document = collection_obj.get(key)
        
        if document:
            return json.dumps({
                "success": True,
                "data": document
            })
        else:
            return json.dumps({
                "success": False,
                "error": f"Document {key} not found in {collection}"
            })
            
    except Exception as e:
        logger.error(f"Get entity failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@app.command()
def update_entity(
    collection: str = typer.Argument(..., help="Collection name"),
    key: str = typer.Argument(..., help="Document key"),
    data: str = typer.Argument(..., help="Update data as JSON string"),
    replace: bool = typer.Option(False, "--replace", "-r", help="Replace entire document")
):
    """Update an entity in any collection."""
    try:
        db = get_db_connection()
        collection_obj = db.collection(collection)
        
        update_data = json.loads(data)
        update_data["updated_at"] = datetime.now().isoformat()
        
        if replace:
            result = collection_obj.replace({"_key": key}, update_data)
        else:
            result = collection_obj.update({"_key": key}, update_data)
            
        return json.dumps({
            "success": True,
            "key": key,
            "updated": True
        })
        
    except Exception as e:
        logger.error(f"Update entity failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@app.command()
def delete_entity(
    collection: str = typer.Argument(..., help="Collection name"),
    key: str = typer.Argument(..., help="Document key")
):
    """Delete an entity from any collection."""
    try:
        db = get_db_connection()
        collection_obj = db.collection(collection)
        result = collection_obj.delete(key)
        
        return json.dumps({
            "success": True,
            "key": key,
            "deleted": True
        })
        
    except Exception as e:
        logger.error(f"Delete entity failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# Search Operations

@app.command()
def search_semantic(
    query: str = typer.Argument(..., help="Search query"),
    collection: str = typer.Option("agent_memories", "--collection", "-c", help="Collection to search"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results")
):
    """Search using semantic similarity (vector search)."""
    try:
        db = get_db_connection()
        
        # Generate query embedding
        query_embedding = get_embedding(query)
        
        # Build AQL query for vector search
        aql = """
        FOR doc IN @@collection
            LET similarity = 1 - DISTANCE(doc.embedding, @embedding)
            FILTER similarity > 0.5
            SORT similarity DESC
            LIMIT @limit
            RETURN {
                _key: doc._key,
                content: doc.content,
                similarity: similarity,
                created_at: doc.created_at
            }
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                "@collection": collection,
                "embedding": query_embedding,
                "limit": limit
            }
        )
        
        results = list(cursor)
        return json.dumps({
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@app.command()
def search_keyword(
    query: str = typer.Argument(..., help="Search query"),
    collection: str = typer.Option("agent_memories", "--collection", "-c", help="Collection to search"),
    field: str = typer.Option("content", "--field", "-f", help="Field to search in"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results")
):
    """Search using keyword matching."""
    try:
        db = get_db_connection()
        
        # Build AQL query for text search
        aql = f"""
        FOR doc IN `{collection}`
            FILTER CONTAINS(LOWER(doc.{field}), LOWER(@query))
            LIMIT @limit
            RETURN doc
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                "query": query,
                "limit": limit
            }
        )
        
        results = list(cursor)
        return json.dumps({
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# Graph Operations

@app.command()
def create_relationship(
    from_collection: str = typer.Argument(..., help="Source collection"),
    from_key: str = typer.Argument(..., help="Source document key"),
    to_collection: str = typer.Argument(..., help="Target collection"),
    to_key: str = typer.Argument(..., help="Target document key"),
    edge_type: str = typer.Argument(..., help="Relationship type"),
    data: Optional[str] = typer.Option(None, "--data", "-d", help="Additional edge data as JSON")
):
    """Create a relationship between two entities."""
    try:
        db = get_db_connection()
        
        # Prepare edge data
        edge_data = {
            "_from": f"{from_collection}/{from_key}",
            "_to": f"{to_collection}/{to_key}",
            "type": edge_type,
            "created_at": datetime.now().isoformat()
        }
        
        # Add additional data if provided
        if data:
            additional = json.loads(data)
            edge_data.update(additional)
        
        # Insert into agent_relationships collection
        relationships = db.collection("agent_relationships")
        result = relationships.insert(edge_data)
        
        return json.dumps({
            "success": True,
            "edge_key": result["_key"],
            "from": edge_data["_from"],
            "to": edge_data["_to"],
            "type": edge_type
        })
        
    except Exception as e:
        logger.error(f"Create relationship failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@app.command()
def traverse_graph(
    start_collection: str = typer.Argument(..., help="Starting collection"),
    start_key: str = typer.Argument(..., help="Starting document key"),
    direction: str = typer.Option("outbound", "--direction", "-d", help="Traversal direction"),
    max_depth: int = typer.Option(3, "--depth", help="Maximum traversal depth")
):
    """Traverse the graph from a starting point."""
    try:
        db = get_db_connection()
        
        # Build traversal query
        start_vertex = f"{start_collection}/{start_key}"
        
        aql = """
        FOR v, e, p IN 1..@depth @direction @start
            GRAPH 'memory_graph'
            RETURN {
                vertex: v,
                edge: e,
                depth: LENGTH(p.edges)
            }
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                "start": start_vertex,
                "depth": max_depth,
                "direction": direction.upper()
            }
        )
        
        results = list(cursor)
        return json.dumps({
            "success": True,
            "start": start_vertex,
            "paths": results,
            "count": len(results)
        })
        
    except Exception as e:
        logger.error(f"Graph traversal failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# Memory Operations

@app.command()
def store_memory(
    content: str = typer.Argument(..., help="Memory content"),
    conversation_id: str = typer.Option("default", "--conversation", "-c", help="Conversation ID"),
    memory_type: str = typer.Option("observation", "--type", "-t", help="Memory type")
):
    """Store a new memory with embeddings."""
    try:
        db = get_db_connection()
        memories = db.collection("agent_memories")
        
        # Create memory document
        memory = {
            "content": content,
            "conversation_id": conversation_id,
            "type": memory_type,
            "created_at": datetime.now().isoformat(),
            "embedding": get_embedding(content)
        }
        
        result = memories.insert(memory)
        
        return json.dumps({
            "success": True,
            "key": result["_key"],
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        logger.error(f"Store memory failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

@app.command()
def query_aql(
    query: str = typer.Argument(..., help="AQL query to execute"),
    bind_vars: Optional[str] = typer.Option(None, "--vars", "-v", help="Bind variables as JSON")
):
    """Execute a raw AQL query (advanced users)."""
    try:
        db = get_db_connection()
        
        # Parse bind variables if provided
        vars_dict = {}
        if bind_vars:
            vars_dict = json.loads(bind_vars)
        
        # Execute query
        cursor = db.aql.execute(query, bind_vars=vars_dict)
        results = list(cursor)
        
        return json.dumps({
            "success": True,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        logger.error(f"AQL query failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# Add MCP commands
add_slash_mcp_commands(app, output_dir=".claude/arangodb_simple_commands")

if __name__ == "__main__":
    app()