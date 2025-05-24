# Task List: ArangoDB MCP Integration for Natrium

## Overview
This task list defines the necessary changes to make the ArangoDB project easily available as an MCP tool for the Natrium orchestrator. This project requires SIGNIFICANT updates to its CLI and MCP integrations.

## Core Principle: Transform ArangoDB into a Knowledge Graph MCP Tool

The Natrium project needs to store extracted document content in a queryable knowledge graph. ArangoDB must provide clear MCP endpoints for entity storage, relationship creation, and graph queries.

## Task 1: Create Proper MCP Server Implementation

**Goal**: Replace or fix the existing MCP configuration with a working server

### Current Issues
- Existing .mcp.json may not properly expose ArangoDB functions
- CLI integration needs to be MCP-compatible
- Missing async support in some functions

### Working Code Example

Create `arangodb_mcp_server.py`:

```python
#!/usr/bin/env python3
"""
ArangoDB MCP Server - Knowledge graph storage for engineering documents
"""
from fastmcp import FastMCP
from arango import ArangoClient
import json
from typing import Dict, List, Any, Optional

# Initialize MCP server
mcp = FastMCP(
    name="arangodb-mcp-server",
    version="0.1.0",
    description="Knowledge graph storage and query tools for Natrium"
)

# ArangoDB connection
client = ArangoClient(hosts='http://localhost:8529')
db = client.db('natrium', username='root', password='openSesame')

@mcp.tool()
async def resolve_entity(entity_doc: dict, collection: str) -> dict:
    """
    Store or update an entity in the knowledge graph.
    
    Args:
        entity_doc: Entity document with properties
        collection: Target collection name
        
    Returns:
        Created/updated entity with _id and _key
    """
    try:
        coll = db.collection(collection)
        
        # Check if entity exists (by unique identifier)
        unique_field = entity_doc.get('unique_id') or entity_doc.get('name')
        if unique_field:
            existing = coll.find({'unique_id': unique_field})
            if existing:
                # Update existing
                result = coll.update(existing['_key'], entity_doc)
                return {"success": True, "operation": "update", "entity": result}
        
        # Create new
        result = coll.insert(entity_doc)
        return {"success": True, "operation": "create", "entity": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def create_edge(from_id: str, to_id: str, edge_type: str, properties: dict = None) -> dict:
    """
    Create a relationship between two entities.
    
    Args:
        from_id: Source entity _id
        to_id: Target entity _id
        edge_type: Type of relationship
        properties: Additional edge properties
        
    Returns:
        Created edge document
    """
    try:
        edge_collection = db.collection(f"{edge_type}_edges")
        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "type": edge_type,
            **(properties or {})
        }
        result = edge_collection.insert(edge_doc)
        return {"success": True, "edge": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def query(aql_query: str, bind_vars: dict = None) -> dict:
    """
    Execute an AQL query on the knowledge graph.
    
    Args:
        aql_query: AQL query string
        bind_vars: Query bind variables
        
    Returns:
        Query results
    """
    try:
        cursor = db.aql.execute(aql_query, bind_vars=bind_vars or {})
        results = list(cursor)
        return {"success": True, "results": results, "count": len(results)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp.run())
```

## Task 2: Fix CLI to Support MCP Operations

**Goal**: Update CLI to work seamlessly with MCP calls

### Current Issues
- CLI may not support all required operations
- Missing async support
- Inconsistent response formats

### Working Code Example

Update `cli/app.py`:

```python
import asyncio
from typing import Optional
import typer
import json

app = typer.Typer()

@app.command()
def serve():
    """Start the ArangoDB MCP server"""
    from ..arangodb_mcp_server import mcp
    asyncio.run(mcp.run())

@app.command()
def test_connection():
    """Test ArangoDB connection"""
    try:
        from arango import ArangoClient
        client = ArangoClient(hosts='http://localhost:8529')
        db = client.db('natrium', username='root', password='openSesame')
        collections = db.collections()
        typer.echo(f"Connected! Found {len(collections)} collections")
    except Exception as e:
        typer.echo(f"Connection failed: {e}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
```

## Task 3: Create Natrium-Specific Collections

**Goal**: Set up collections optimized for engineering documents

### Working Code Example

Create `setup_natrium_collections.py`:

```python
async def setup_natrium_collections():
    """Create collections for Natrium knowledge graph"""
    
    collections_to_create = [
        # Document collections
        ("papers", "document"),
        ("sections", "document"),
        ("requirements", "document"),
        ("materials", "document"),
        ("systems", "document"),
        
        # Edge collections
        ("has_section", "edge"),
        ("references", "edge"),
        ("depends_on", "edge"),
        ("contradicts", "edge"),
        ("validates", "edge")
    ]
    
    for name, collection_type in collections_to_create:
        if name not in db.collections():
            if collection_type == "edge":
                db.create_collection(name, edge=True)
            else:
                db.create_collection(name)
                
    # Create indexes for performance
    requirements = db.collection('requirements')
    requirements.add_hash_index(fields=['unique_id'], unique=True)
    requirements.add_fulltext_index(fields=['text'])
```

## Task 4: Add Graph Traversal Tools

**Goal**: Provide tools for analyzing relationships

### Working Code Example

Add to MCP server:

```python
@mcp.tool()
async def find_contradictions(entity_id: str, depth: int = 2) -> dict:
    """
    Find potential contradictions related to an entity.
    
    Args:
        entity_id: Starting entity _id
        depth: How many hops to traverse
        
    Returns:
        List of potential contradictions with paths
    """
    query = """
    FOR v, e, p IN 1..@depth ANY @start_vertex 
        contradicts, references, depends_on
        OPTIONS {uniqueVertices: 'global'}
        FILTER e.type == 'contradicts' OR 
               (p.edges[0].type != p.edges[-1].type)
        RETURN {
            entity: v,
            path: p,
            relationship: e
        }
    """
    
    result = await query(query, {"start_vertex": entity_id, "depth": depth})
    return result

@mcp.tool()
async def get_requirement_dependencies(requirement_id: str) -> dict:
    """
    Get all dependencies for a requirement.
    
    Args:
        requirement_id: Requirement entity _id
        
    Returns:
        Dependency tree
    """
    query = """
    FOR v, e, p IN 1..10 OUTBOUND @req_id depends_on
        OPTIONS {uniqueVertices: 'path'}
        RETURN {
            dependent: v,
            path_length: LENGTH(p.edges),
            dependency_type: e.dependency_type
        }
    """
    
    result = await query(query, {"req_id": requirement_id})
    return result
```

## Task 5: Add Bulk Import for Natrium

**Goal**: Efficiently import large document structures

### Working Code Example

```python
@mcp.tool()
async def bulk_import_document(document_data: dict) -> dict:
    """
    Import a complete document with all its structures.
    
    Args:
        document_data: Complete document data from marker
        
    Returns:
        Import statistics
    """
    stats = {
        "entities_created": 0,
        "edges_created": 0,
        "errors": []
    }
    
    try:
        # Start transaction
        transaction = db.begin_transaction(
            read_collections=[],
            write_collections=['papers', 'sections', 'requirements', 'has_section', 'references']
        )
        
        # Create paper entity
        paper = transaction.collection('papers').insert({
            "title": document_data.get("title"),
            "source": document_data.get("source"),
            "type": "engineering_spec"
        })
        stats["entities_created"] += 1
        
        # Create sections and relationships
        for section in document_data.get("sections", []):
            section_entity = transaction.collection('sections').insert(section)
            stats["entities_created"] += 1
            
            # Link to paper
            transaction.collection('has_section').insert({
                "_from": paper["_id"],
                "_to": section_entity["_id"],
                "order": section.get("order", 0)
            })
            stats["edges_created"] += 1
        
        # Commit transaction
        transaction.commit()
        
    except Exception as e:
        transaction.abort()
        stats["errors"].append(str(e))
        
    return stats
```

## Task 6: Add Query Builder for Common Patterns

**Goal**: Simplify complex queries for Natrium

### Working Code Example

```python
class NatriumQueryBuilder:
    """Build common AQL queries for Natrium patterns"""
    
    @staticmethod
    def find_requirements_by_keyword(keywords: List[str]) -> str:
        """Build query to find requirements containing keywords"""
        keyword_filters = " OR ".join([
            f"CONTAINS(LOWER(r.text), LOWER('{kw}'))" 
            for kw in keywords
        ])
        
        return f"""
        FOR r IN requirements
            FILTER {keyword_filters}
            RETURN {{
                id: r._id,
                text: r.text,
                section: r.section,
                priority: r.priority
            }}
        """
    
    @staticmethod
    def get_material_specifications(material_name: str) -> str:
        """Build query for material specifications"""
        return """
        FOR m IN materials
            FILTER m.name == @material_name
            LET specs = (
                FOR s IN specifications
                    FILTER s.material_id == m._id
                    RETURN s
            )
            RETURN {
                material: m,
                specifications: specs
            }
        """
```

## Task 7: Add Health Check and Monitoring

**Goal**: Ensure ArangoDB MCP is always available

### Working Code Example

```python
@mcp.tool()
async def health_check() -> dict:
    """
    Check ArangoDB connection and collection status.
    
    Returns:
        Health status and statistics
    """
    try:
        # Test connection
        db.version()
        
        # Get collection stats
        collections = {}
        for coll_name in ['papers', 'sections', 'requirements']:
            if coll_name in db.collections():
                coll = db.collection(coll_name)
                collections[coll_name] = {
                    "count": coll.count(),
                    "indexes": len(coll.indexes())
                }
        
        return {
            "status": "healthy",
            "database": db.name,
            "collections": collections
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## Validation Checklist

- [ ] MCP server connects to ArangoDB successfully
- [ ] All CRUD operations work via MCP
- [ ] Graph traversal queries return correct results
- [ ] Bulk import handles large documents
- [ ] Error responses are properly formatted
- [ ] Transaction support for atomic operations
- [ ] Performance indexes are created
- [ ] Health check endpoint works

## Common Issues & Solutions

### Issue 1: Connection refused
```python
# Solution: Check ArangoDB is running and credentials are correct
client = ArangoClient(
    hosts='http://localhost:8529',
    http_client=DefaultHTTPClient(verify=False)  # For self-signed certs
)
```

### Issue 2: Collection not found
```python
# Solution: Auto-create collections
if collection_name not in db.collections():
    db.create_collection(collection_name)
```

### Issue 3: Large query timeouts
```python
# Solution: Use streaming and pagination
cursor = db.aql.execute(
    query,
    bind_vars=bind_vars,
    batch_size=1000,
    stream=True
)
```
