# Graphiti Implementation Recommendations for ArangoDB

This document outlines key insights and implementation recommendations from the Graphiti (Neo4j) knowledge graph system that can be applied to enhance our ArangoDB implementation.

## Core Concepts from Graphiti

Graphiti is a temporal knowledge graph framework built on Neo4j that provides:

1. **Bi-Temporal Data Model**: Tracks both when events occurred and when they were recorded
2. **Incremental Updates**: Allows adding new information without recomputing the entire graph
3. **Hybrid Retrieval**: Combines semantic, keyword, and graph-based search
4. **Contradiction Handling**: Intelligently handles conflicts in information
5. **Community Detection**: Clusters related entities for better organization

## Implementation Recommendations

### 1. Enhanced Temporal Model

Implement a bi-temporal model that explicitly tracks:

- `created_at`: When the relationship was added to the database
- `valid_at`: When the relationship became true in the real world
- `invalid_at`: When the relationship stopped being true (null if still valid)

```python
def enhance_edge_with_temporal_metadata(edge_doc, reference_time=None):
    """Add temporal metadata to edge documents."""
    now = datetime.now(timezone.utc)
    
    # Add created_at time (when the edge was inserted)
    edge_doc["created_at"] = now.isoformat()
    
    # Add valid_at time (when the relationship became true)
    edge_doc["valid_at"] = reference_time.isoformat() if reference_time else now.isoformat()
    
    # Add NULL invalid_at time (representing "valid until further notice")
    edge_doc["invalid_at"] = None
    
    return edge_doc
```

### 2. Edge Contradiction Detection

Implement a system to detect and resolve contradicting information:

```python
async def detect_edge_contradictions(db, edge_doc, relationship_type, source_id, target_id):
    """Find potentially contradicting edges for a new relationship."""
    
    # Find existing edges between these nodes with same relationship type
    aql = """
    FOR e IN @@edge_collection
    FILTER e._from == @source_id AND e._to == @target_id
    FILTER e.type == @relationship_type
    FILTER e.invalid_at == null
    RETURN e
    """
    
    cursor = db.aql.execute(
        aql,
        bind_vars={
            "@edge_collection": "agent_relationships",
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": relationship_type
        }
    )
    
    contradicting_edges = list(cursor)
    return contradicting_edges
```

When a contradiction is found, invalidate the older edge:

```python
async def resolve_edge_contradictions(db, edge_doc, contradicting_edges, llm_client=None):
    """
    Resolve contradictions between a new edge and existing edges.
    Uses LLM to determine if the new information contradicts old information.
    """
    now = datetime.now(timezone.utc)
    invalidated_edges = []
    
    for existing_edge in contradicting_edges:
        # Option 1: Use simple rule-based approach
        if existing_edge["type"] == edge_doc["type"]:
            # If exact same type, consider it a potential contradiction
            
            # Option 2: Use LLM to determine if this is a contradiction
            if llm_client:
                is_contradiction = await check_contradiction_with_llm(
                    llm_client, edge_doc, existing_edge
                )
                
                if is_contradiction:
                    # Invalidate the existing edge
                    db.collection("agent_relationships").update(
                        existing_edge["_key"],
                        {"invalid_at": now.isoformat(), "invalidated_by": edge_doc["_key"]}
                    )
                    invalidated_edges.append(existing_edge)
            else:
                # Simple time-based invalidation
                db.collection("agent_relationships").update(
                    existing_edge["_key"],
                    {"invalid_at": now.isoformat(), "invalidated_by": edge_doc["_key"]}
                )
                invalidated_edges.append(existing_edge)
    
    return invalidated_edges
```

### 3. Advanced Entity Resolution

Implement a more sophisticated entity resolution system that combines exact matching and semantic similarity:

```python
async def resolve_entity(db, entity_doc, collection_name="agent_entities"):
    """
    Resolve an entity against existing entities in the database.
    Returns either a matching existing entity or the new entity.
    """
    # Check for exact name match first
    aql = """
    FOR doc IN @@collection
    FILTER doc.name == @name
    RETURN doc
    """
    
    cursor = db.aql.execute(
        aql,
        bind_vars={
            "@collection": collection_name,
            "name": entity_doc["name"]
        }
    )
    
    exact_matches = list(cursor)
    if exact_matches:
        return exact_matches[0]
    
    # If no exact match, try semantic search if entity has embeddings
    if "embedding" in entity_doc:
        aql = """
        FOR doc IN @@collection
        FILTER doc.embedding != null
        LET score = APPROX_NEAR_COSINE(doc.embedding, @embedding)
        FILTER score > 0.85  // High threshold for entity resolution
        SORT score DESC
        LIMIT 1
        RETURN {doc: doc, score: score}
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                "@collection": collection_name,
                "embedding": entity_doc["embedding"]
            }
        )
        
        similarity_matches = list(cursor)
        if similarity_matches:
            match = similarity_matches[0]
            logger.info(f"Found entity match with similarity {match['score']:.3f}: {match['doc']['name']}")
            return match["doc"]
    
    # If no matches, create new entity
    result = db.collection(collection_name).insert(entity_doc)
    entity_doc["_key"] = result["_key"]
    entity_doc["_id"] = result["_id"]
    return entity_doc
```

### 4. LLM-Based Relationship Extraction

Enhance relationship extraction from unstructured text using LLMs:

```python
async def extract_relationships_from_text(text, llm_client, embedding_client):
    """Extract relationships from unstructured text using LLM."""
    
    # Create a prompt for the LLM to extract entities and relationships
    prompt = f"""
    Extract entities and their relationships from the following text.
    Format your response as a JSON object with the following structure:
    
    {{
        "entities": [
            {{"name": "Entity1", "type": "Person", "attributes": {{"key1": "value1"}} }},
            {{"name": "Entity2", "type": "Organization", "attributes": {{"key1": "value1"}} }}
        ],
        "relationships": [
            {{
                "source": "Entity1",
                "target": "Entity2", 
                "type": "WORKS_FOR",
                "attributes": {{"start_date": "2023-01-01"}},
                "temporal": {{"valid_from": "2023-01-01", "valid_until": null}}
            }}
        ]
    }}
    
    Text: {text}
    """
    
    # Call the LLM to extract entities and relationships
    response = await llm_client.complete(prompt)
    
    try:
        # Parse the JSON response
        extracted_data = json.loads(response.choices[0].text)
        
        # Generate embeddings for entities
        for entity in extracted_data.get("entities", []):
            entity_text = f"{entity['name']} {entity.get('type', '')} {json.dumps(entity.get('attributes', {}))}"
            entity["embedding"] = await embedding_client.embed(entity_text)
        
        # Generate embeddings for relationships
        for relationship in extracted_data.get("relationships", []):
            relationship_text = f"{relationship['source']} {relationship['type']} {relationship['target']}"
            relationship["embedding"] = await embedding_client.embed(relationship_text)
        
        return extracted_data
    
    except Exception as e:
        logger.error(f"Failed to parse LLM response: {e}")
        return {"entities": [], "relationships": []}
```

### 5. Community Building

Implement community detection to group related entities:

```python
async def build_communities(db, group_id=None, min_members=3):
    """
    Build communities in the knowledge graph using ArangoDB graph algorithms.
    
    Args:
        db: ArangoDB connection
        group_id: Optional group ID to filter by
        min_members: Minimum number of members for a community
        
    Returns:
        List of community documents
    """
    # First, identify communities using a graph algorithm
    # Here using Louvain for community detection
    aql = """
    LET communities = (
        FOR v, e IN 0..1 OUTBOUND @start_vertex GRAPH @graph
        RETURN v._id
    )
    
    LET modularity = GRAPH_COMMUNITY_LOUVAIN(@graph, {
        direction: "any",
        max_iterations: 10,
        weights: "weight"
    })
    
    LET clusters = SORTED_UNIQUE(
        FOR vertex, community IN FLATTEN(modularity)
        FILTER LENGTH(modularity[community]) >= @min_members
        RETURN {
            community: community,
            members: modularity[community]
        }
    )
    
    // Now for each community, find representative entities and create a summary
    FOR cluster IN clusters
        // Get all members of this community
        LET members = (
            FOR member_id IN cluster.members
            LET doc = DOCUMENT(member_id)
            RETURN doc
        )
        
        // Generate a name for the community based on common attributes or types
        LET community_name = FIRST(
            FOR doc IN members
            COLLECT entity_type = doc.type WITH COUNT INTO count
            SORT count DESC
            RETURN CONCAT(entity_type, " Community")
        )
        
        RETURN {
            community_id: cluster.community,
            name: community_name,
            member_count: LENGTH(cluster.members),
            members: cluster.members
        }
    """
    
    # Execute query
    cursor = db.aql.execute(
        aql,
        bind_vars={
            "start_vertex": f"entity_collection/some_key",
            "graph": "knowledge_graph",
            "min_members": min_members
        }
    )
    
    # Process results and create community documents
    communities = []
    for community_data in cursor:
        # Create a community document
        community_doc = {
            "name": community_data["name"],
            "member_count": community_data["member_count"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "group_id": group_id
        }
        
        # Insert community into database
        result = db.collection("communities").insert(community_doc)
        community_doc["_key"] = result["_key"]
        community_doc["_id"] = result["_id"]
        
        # Create edges from community to members
        for member_id in community_data["members"]:
            edge = {
                "_from": community_doc["_id"],
                "_to": member_id,
                "type": "HAS_MEMBER",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            db.collection("community_edges").insert(edge)
        
        communities.append(community_doc)
    
    return communities
```

### 6. Cross-Encoder Reranking

Implement a cross-encoder reranking step for search results:

```python
async def cross_encoder_rerank(query_text, passages, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
    """
    Rerank passages using a cross-encoder model.
    
    Args:
        query_text: Query text
        passages: List of passages with text and metadata
        model_name: Cross-encoder model name
        
    Returns:
        Reranked passages
    """
    from sentence_transformers import CrossEncoder
    
    # Initialize cross-encoder
    model = CrossEncoder(model_name)
    
    # Prepare input pairs
    input_pairs = [(query_text, passage["text"]) for passage in passages]
    
    # Get scores
    scores = model.predict(input_pairs)
    
    # Combine scores with passages
    scored_passages = []
    for i, (score, passage) in enumerate(zip(scores, passages)):
        scored_passages.append({
            "doc": passage.get("doc", {}),
            "cross_encoder_score": float(score),
            "original_score": passage.get("score", 0),
            "hybrid_score": float(score)  # Replace with cross-encoder score
        })
    
    # Sort by cross-encoder score
    scored_passages.sort(key=lambda x: x["cross_encoder_score"], reverse=True)
    
    return scored_passages
```

### 7. Bi-Temporal Query Support

Implement queries that respect the temporal nature of the data:

```python
def temporal_search(
    db: StandardDatabase,
    query_text: str,
    point_in_time: Optional[datetime] = None,
    collections: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Search for relationships that were valid at a specific point in time.
    """
    # Set default point-in-time to now if not provided
    if point_in_time is None:
        point_in_time = datetime.now(timezone.utc)
    
    time_str = point_in_time.isoformat()
    
    # Use AQL to find temporally valid relationships
    aql = f"""
    FOR doc IN @@collection
    FILTER doc.embedding != null
    
    // Temporal filter: valid_at <= query_time AND (invalid_at IS NULL OR invalid_at > query_time)
    FILTER DATE_ISO8601(doc.valid_at) <= DATE_ISO8601(@time_str)
    FILTER doc.invalid_at == null OR DATE_ISO8601(doc.invalid_at) > DATE_ISO8601(@time_str)
    
    // Semantic search
    LET score = APPROX_NEAR_COSINE(doc.embedding, @query_vector)
    FILTER score > 0.7
    
    SORT score DESC
    LIMIT 20
    RETURN {{
        doc: doc,
        score: score,
        valid_at: doc.valid_at,
        invalid_at: doc.invalid_at
    }}
    """
    
    # Generate embedding for query
    query_vector = get_embedding(query_text)
    
    # Execute query
    cursor = db.aql.execute(
        aql,
        bind_vars={
            "@collection": collections[0] if collections else "agent_memories",
            "time_str": time_str,
            "query_vector": query_vector
        }
    )
    
    results = list(cursor)
    
    return {
        "results": results,
        "total": len(results),
        "query": query_text,
        "point_in_time": time_str,
        "search_engine": "temporal-semantic"
    }
```

## Integration Strategy

To implement these features in our existing ArangoDB implementation:

1. **Temporal Edge Model**:
   - Update the schema for relationships
   - Add validation in the database operations
   - Update search functions to respect temporal validity

2. **Edge Contradiction Handling**:
   - Add new functions for detecting contradictions
   - Implement contradiction resolution logic
   - Add handlers for invalidating contradicted edges

3. **Entity Resolution**:
   - Enhance entity creation with deduplication
   - Implement semantic matching for similar entities
   - Add merging logic for entity attributes

4. **Community Building**:
   - Create new collection for communities
   - Implement clustering algorithm for community detection
   - Add functions to manage community membership

## Next Steps

1. **Schema Updates**: Extend ArangoDB collections to support temporal metadata
2. **Function Implementation**: Add the enhanced functions described above
3. **Testing**: Develop tests for the new temporal features
4. **Documentation**: Update API documentation with the new capabilities

## Conclusion

By implementing these Graphiti-inspired features, our ArangoDB-based knowledge graph will gain:

1. **Better Temporal Awareness**: Track when relationships were valid, not just when they were created
2. **Improved Data Consistency**: Detect and resolve contradictions automatically
3. **Enhanced Entity Resolution**: More accurately identify and merge similar entities
4. **Community Structure**: Group related entities together for better organization
5. **Advanced Reranking**: Implement cross-encoder reranking for higher quality search results

These enhancements will significantly increase the robustness and utility of our knowledge graph implementation while maintaining the advantages of ArangoDB's flexible schema and multi-model architecture.
