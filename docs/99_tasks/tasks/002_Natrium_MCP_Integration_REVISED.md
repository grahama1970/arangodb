# Task List: ArangoDB MCP Integration for Natrium (REVISED)

## Overview
This task list is based on the original 19 Natrium tasks. ArangoDB is responsible for supporting Tasks 5-6 (partial) and Tasks 9-19 of the pipeline.

## ArangoDB's Role in the 19-Task Pipeline

### Task 5: Contradiction Detection (partial - graph-based)
### Task 6: Error Cascade 
### Task 9: BM25 Search
### Task 10: Semantic Search
### Task 11: Graph Traversal
### Task 12-15: Memory Management (Store, Retrieve, Compact, Episodes)
### Task 16: Entity Storage & Resolution
### Task 17: Relationship Storage
### Task 18: Community Analysis
### Task 19: Graph Contradiction Management

## Implementation Tasks

### Task 2.1: Create MCP Server Supporting All Required Endpoints

**Goal**: Implement MCP server with all endpoints for Tasks 5-6, 9-19

Create arangodb_mcp_server.py:

```python
#!/usr/bin/env python3
"""
ArangoDB MCP Server - Supports Tasks 5-6, 9-19 of Natrium pipeline
Based on original_natrium_task_list_gemini.md requirements
"""
from fastmcp import FastMCP
from arango import ArangoClient
from typing import Dict, List, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
from datetime import datetime

# Initialize MCP server
mcp = FastMCP(
    name="arangodb-mcp-server",
    version="0.1.0",
    description="Knowledge graph for Natrium Tasks 5-6, 9-19"
)

# Initialize ArangoDB
client = ArangoClient(hosts='http://localhost:8529')
db = client.db('natrium', username='root', password='openSesame')

# Initialize embedding model for semantic search (Task 10)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Task 9: BM25 Search Implementation
@mcp.tool()
async def bm25_search(query: str, collections: List[str], top_k: int = 10) -> dict:
    """
    Task 9: BM25 keyword search across collections.
    Based on arangodb_bm25_search_001 test requirements.
    """
    try:
        # BM25 search using ArangoDB analyzer
        results = []
        
        for collection_name in collections:
            # Use ArangoDB full-text search with BM25 scoring
            aql = """
            FOR doc IN @@collection
                SEARCH ANALYZER(doc.text IN TOKENS(@query, 'text_en'), 'text_en')
                SORT BM25(doc) DESC
                LIMIT @top_k
                RETURN {
                    id: doc._id,
                    text: doc.text,
                    score: BM25(doc),
                    metadata: doc.metadata
                }
            """
            
            cursor = db.aql.execute(
                aql,
                bind_vars={
                    '@collection': collection_name,
                    'query': query,
                    'top_k': top_k
                }
            )
            
            for doc in cursor:
                results.append({
                    "collection": collection_name,
                    **doc
                })
        
        # Sort by score across all collections
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            "success": True,
            "results": results[:top_k],
            "total_found": len(results),
            "query": query
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Task 10: Semantic Search Implementation
@mcp.tool()
async def semantic_search(query: str, collections: List[str], top_k: int = 10) -> dict:
    """
    Task 10: Semantic search using embeddings.
    Based on arangodb_semantic_search_001 test requirements.
    """
    try:
        # Generate query embedding
        query_embedding = embedding_model.encode(query).tolist()
        
        results = []
        
        for collection_name in collections:
            # Cosine similarity search
            aql = """
            FOR doc IN @@collection
                LET similarity = DOT(doc.embedding, @query_embedding) / 
                    (LENGTH(doc.embedding) * LENGTH(@query_embedding))
                FILTER similarity > 0.5
                SORT similarity DESC
                LIMIT @top_k
                RETURN {
                    id: doc._id,
                    text: doc.text,
                    similarity: similarity,
                    metadata: doc.metadata
                }
            """
            
            cursor = db.aql.execute(
                aql,
                bind_vars={
                    '@collection': collection_name,
                    'query_embedding': query_embedding,
                    'top_k': top_k
                }
            )
            
            results.extend(cursor)
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            "success": True,
            "results": results[:top_k],
            "query": query,
            "embedding_model": "all-MiniLM-L6-v2"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Task 11: Graph Traversal Implementation
@mcp.tool()
async def graph_traversal(
    start_vertex: str,
    direction: str = "OUTBOUND",
    max_depth: int = 3,
    edge_collections: List[str] = None
) -> dict:
    """
    Task 11: Traverse graph relationships.
    Based on arangodb_graph_traversal_001 test requirements.
    """
    try:
        edge_clause = ""
        if edge_collections:
            edge_clause = ", ".join(edge_collections)
        else:
            edge_clause = "depends_on, references, contradicts"
            
        aql = f"""
        FOR vertex, edge, path IN 1..@max_depth {direction} @start_vertex
            {edge_clause}
            OPTIONS {{uniqueVertices: 'global'}}
            RETURN {{
                vertex: vertex,
                edge: edge,
                path: path,
                depth: LENGTH(path.edges)
            }}
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                'start_vertex': start_vertex,
                'max_depth': max_depth
            }
        )
        
        results = list(cursor)
        
        return {
            "success": True,
            "traversal_results": results,
            "total_vertices": len(results),
            "start_vertex": start_vertex,
            "direction": direction,
            "max_depth": max_depth
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Task 12: Store Conversation
@mcp.tool()
async def store_conversation(
    conversation_id: str,
    turn_id: str,
    role: str,
    content: str,
    metadata: Dict = None
) -> dict:
    """
    Task 12: Store conversation history.
    Based on arangodb_memory_store_conversation_001 test requirements.
    """
    try:
        conversations = db.collection('conversations')
        
        doc = {
            "_key": f"{conversation_id}_{turn_id}",
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        result = conversations.insert(doc)
        
        return {
            "success": True,
            "stored": result,
            "conversation_id": conversation_id,
            "turn_id": turn_id
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Task 13: Retrieve Conversation
@mcp.tool()
async def retrieve_conversation(
    conversation_id: str,
    last_n_turns: Optional[int] = None
) -> dict:
    """
    Task 13: Retrieve conversation history.
    Based on arangodb_memory_retrieve_conversation_001 test requirements.
    """
    try:
        aql = """
        FOR turn IN conversations
            FILTER turn.conversation_id == @conversation_id
            SORT turn.timestamp DESC
            LIMIT @limit
            RETURN turn
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                'conversation_id': conversation_id,
                'limit': last_n_turns or 100
            }
        )
        
        turns = list(cursor)
        turns.reverse()  # Chronological order
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "turns": turns,
            "total_turns": len(turns)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Task 16: Entity Storage & Resolution
@mcp.tool()
async def resolve_entity(entity_doc: dict, collection: str = "entities") -> dict:
    """
    Task 16: Store and resolve entities with deduplication.
    Based on arangodb_entity_storage_resolution_001 test requirements.
    """
    try:
        coll = db.collection(collection)
        
        # Generate entity hash for deduplication
        entity_text = entity_doc.get('text', '')
        entity_hash = hashlib.md5(entity_text.encode()).hexdigest()
        
        # Check if entity exists
        existing = None
        try:
            existing = coll.get(entity_hash)
        except:
            pass
            
        if existing:
            # Update existing entity
            for key, value in entity_doc.items():
                if key not in ['_key', '_id', '_rev']:
                    existing[key] = value
            result = coll.update(existing)
            operation = "resolved"
        else:
            # Create new entity
            entity_doc['_key'] = entity_hash
            entity_doc['created_at'] = datetime.utcnow().isoformat()
            
            # Generate embedding for semantic search
            if 'text' in entity_doc:
                entity_doc['embedding'] = embedding_model.encode(entity_doc['text']).tolist()
                
            result = coll.insert(entity_doc)
            operation = "created"
            
        return {
            "success": True,
            "operation": operation,
            "entity": {
                "_id": result['_id'],
                "_key": result['_key']
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Task 17: Relationship Storage
@mcp.tool()
async def create_edge(
    from_id: str,
    to_id: str,
    edge_type: str,
    properties: Dict = None
) -> dict:
    """
    Task 17: Create relationships between entities.
    Based on arangodb_relationship_storage_001 test requirements.
    """
    try:
        edge_collection_name = f"{edge_type}_edges"
        
        # Ensure edge collection exists
        if edge_collection_name not in db.collections():
            db.create_collection(edge_collection_name, edge=True)
            
        edge_coll = db.collection(edge_collection_name)
        
        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "type": edge_type,
            "created_at": datetime.utcnow().isoformat(),
            **(properties or {})
        }
        
        result = edge_coll.insert(edge_doc)
        
        return {
            "success": True,
            "edge": {
                "_id": result['_id'],
                "_key": result['_key'],
                "type": edge_type
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Task 5 (partial): Find Contradictions in Graph
@mcp.tool()
async def find_contradictions(entity_id: str, depth: int = 2) -> dict:
    """
    Task 5 (partial): Find contradictions using graph traversal.
    Supports contradiction_detection_001 test requirements.
    """
    try:
        aql = """
        FOR v, e, p IN 1..@depth ANY @start_vertex 
            contradicts, references, depends_on
            OPTIONS {uniqueVertices: 'global'}
            FILTER e.type == 'contradicts' OR 
                   (LENGTH(p.edges) > 1 AND 
                    p.edges[0].type != p.edges[-1].type)
            RETURN {
                entity: v,
                path: p,
                relationship: e,
                contradiction_type: e.type == 'contradicts' ? 'explicit' : 'implicit'
            }
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                'start_vertex': entity_id,
                'depth': depth
            }
        )
        
        contradictions = list(cursor)
        
        return {
            "success": True,
            "contradictions": contradictions,
            "total_found": len(contradictions),
            "search_depth": depth
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Task 6: Error Cascade Tracing
@mcp.tool()
async def trace_error_cascade(requirement_id: str, max_depth: int = 10) -> dict:
    """
    Task 6: Trace error cascades through dependencies.
    Based on error_cascade_001 test requirements.
    """
    try:
        aql = """
        FOR v, e, p IN 1..@max_depth OUTBOUND @req_id 
            depends_on, impacts, derives_from
            OPTIONS {uniqueVertices: 'path'}
            RETURN {
                affected_entity: v,
                impact_path: p,
                cascade_depth: LENGTH(p.edges),
                relationship_types: p.edges[*].type
            }
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                'req_id': requirement_id,
                'max_depth': max_depth
            }
        )
        
        cascade_results = list(cursor)
        
        # Group by cascade depth
        cascade_by_depth = {}
        for result in cascade_results:
            depth = result['cascade_depth']
            if depth not in cascade_by_depth:
                cascade_by_depth[depth] = []
            cascade_by_depth[depth].append(result)
            
        return {
            "success": True,
            "source_requirement": requirement_id,
            "total_affected": len(cascade_results),
            "cascade_by_depth": cascade_by_depth,
            "max_cascade_depth": max(cascade_by_depth.keys()) if cascade_by_depth else 0
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Additional endpoints for Tasks 14, 15, 18, 19 would follow similar patterns...

if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp.run())
```

### Task 2.2: Implement Remaining Endpoints (Tasks 14, 15, 18, 19)

**Goal**: Complete implementation of all ArangoDB-related tasks

Add to arangodb_mcp_server.py:

```python
# Task 14: Compact Conversation
@mcp.tool()
async def compact_conversation(conversation_id: str, strategy: str = "summary") -> dict:
    """Task 14: Compact conversation history"""
    # Implementation based on original task requirements
    pass

# Task 15: Episode Management
@mcp.tool()
async def manage_episodes(action: str, episode_data: Dict = None) -> dict:
    """Task 15: Manage conversation episodes"""
    # Implementation based on original task requirements
    pass

# Task 18: Community Analysis
@mcp.tool()
async def detect_communities(collection: str, algorithm: str = "louvain") -> dict:
    """Task 18: Detect communities in graph"""
    # Implementation based on original task requirements
    pass

# Task 19: Contradiction Management
@mcp.tool()
async def manage_contradictions(action: str, contradiction_data: Dict = None) -> dict:
    """Task 19: Log and manage contradictions"""
    # Implementation based on original task requirements
    pass
```

### Task 2.3: Create Required Collections and Indexes

**Goal**: Set up ArangoDB for all 19 tasks

```python
async def setup_natrium_collections():
    """Create all collections required by Tasks 9-19"""
    
    # Document collections
    doc_collections = [
        'entities',          # Task 16
        'requirements',      # Tasks 5, 6
        'conversations',     # Tasks 12-13
        'episodes',          # Task 15
        'contradictions'     # Task 19
    ]
    
    # Edge collections
    edge_collections = [
        'depends_on',        # Task 6
        'references',        # Task 11
        'contradicts',       # Tasks 5, 19
        'impacts',           # Task 6
        'derives_from'       # Task 6
    ]
    
    # Create collections
    for name in doc_collections:
        if name not in db.collections():
            db.create_collection(name)
            
    for name in edge_collections:
        if name not in db.collections():
            db.create_collection(name, edge=True)
            
    # Create indexes for performance
    # Full-text index for BM25 search (Task 9)
    entities = db.collection('entities')
    entities.add_fulltext_index(fields=['text'])
    
    # Hash index for entity resolution (Task 16)
    entities.add_hash_index(fields=['_key'], unique=True)
    
    # Persistent index for conversations (Tasks 12-13)
    conversations = db.collection('conversations')
    conversations.add_persistent_index(fields=['conversation_id', 'timestamp'])
```

### Task 2.4: Integration Tests for All Tasks

**Goal**: Verify each task works as specified in original requirements

Create tests/test_natrium_tasks.py with tests for each task (9-19).

## Validation Checklist

Based on original task requirements:

- [ ] Task 9: BM25 search returns ranked results
- [ ] Task 10: Semantic search uses embeddings correctly
- [ ] Task 11: Graph traversal follows specified depth
- [ ] Task 12-13: Conversation storage and retrieval work
- [ ] Task 14-15: Memory compaction and episodes function
- [ ] Task 16: Entity deduplication works correctly
- [ ] Task 17: Relationships store with properties
- [ ] Task 18: Community detection identifies clusters
- [ ] Task 19: Contradiction management logs issues
- [ ] Task 5: Graph-based contradiction detection
- [ ] Task 6: Error cascade tracing works

## Dependencies to Add

```toml
[project.dependencies]
python-arango = ">=7.0.0"
sentence-transformers = ">=2.0.0"
numpy = ">=1.20.0"
fastmcp = ">=0.1.0"
```

## Notes

This implementation supports Tasks 5-6 (partial) and Tasks 9-19 from the original Natrium pipeline. The graph-based features complement the logical contradiction detection that will be handled by Claude Max Proxy's Z3 solver implementation.
