# Task 026: Bi-Temporal Data Model Implementation

## Overview
Implement a bi-temporal data model to track both event time (`valid_at`) and ingestion time (`created_at`) for all entities and relationships, enabling sophisticated temporal queries and historical analysis.

## Current State
- Single timestamp tracking (`created_at`)
- Basic time-based filtering
- No point-in-time queries
- No temporal invalidation

## Target State
- Dual timestamp tracking (event time and ingestion time)
- Point-in-time queries
- Temporal consistency
- Historical state reconstruction

## Implementation Steps

### 1. Update Data Models
```python
# core/models.py
class TemporalEntity(BaseModel):
    """Base class for temporal entities."""
    created_at: datetime  # When recorded in system
    valid_at: datetime    # When event occurred
    invalid_at: Optional[datetime] = None  # When invalidated
    
class MemoryEntity(TemporalEntity):
    """Memory with temporal tracking."""
    _key: Optional[str] = None
    user_message: str
    agent_response: str
    conversation_id: Optional[str] = None
    embedding: Optional[List[float]] = None
    # ... other fields
    
class EntityNode(TemporalEntity):
    """Entity with temporal tracking."""
    _key: Optional[str] = None
    name: str
    type: str
    attributes: Dict[str, Any] = {}
    # ... other fields

class Relationship(TemporalEntity):
    """Relationship with temporal tracking."""
    _key: Optional[str] = None
    source_key: str
    target_key: str
    relationship_type: str
    properties: Dict[str, Any] = {}
    # ... other fields
```

### 2. Update Database Operations
```python
# core/db_operations.py
def create_temporal_entity(db, collection_name: str, entity: dict, valid_at: Optional[datetime] = None):
    """Create entity with temporal tracking."""
    now = datetime.utcnow()
    entity["created_at"] = now
    entity["valid_at"] = valid_at or now
    entity["invalid_at"] = None
    
    collection = db.collection(collection_name)
    return collection.insert(entity)

def invalidate_entity(db, collection_name: str, key: str, invalid_at: Optional[datetime] = None):
    """Mark entity as invalid at specific time."""
    collection = db.collection(collection_name)
    return collection.update({
        "_key": key
    }, {
        "invalid_at": invalid_at or datetime.utcnow()
    })
```

### 3. Implement Point-in-Time Queries
```python
# core/search/temporal_search.py
def point_in_time_query(
    db,
    collection_name: str,
    timestamp: datetime,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """Query entities valid at specific point in time."""
    
    query = f"""
    FOR doc IN {collection_name}
        FILTER doc.valid_at <= @timestamp
        FILTER doc.invalid_at == null OR doc.invalid_at > @timestamp
    """
    
    if filters:
        for key, value in filters.items():
            query += f" FILTER doc.{key} == @{key}"
    
    query += " RETURN doc"
    
    bind_vars = {"timestamp": timestamp}
    if filters:
        bind_vars.update(filters)
    
    cursor = db.aql.execute(query, bind_vars=bind_vars)
    return list(cursor)

def temporal_range_query(
    db,
    collection_name: str,
    start_time: datetime,
    end_time: datetime,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """Query entities within temporal range."""
    
    query = f"""
    FOR doc IN {collection_name}
        FILTER doc.valid_at <= @end_time
        FILTER doc.invalid_at == null OR doc.invalid_at >= @start_time
    """
    
    # ... rest of implementation
```

### 4. Update Search Functions
```python
# core/search/semantic_search.py
def semantic_search_temporal(
    db,
    query_text: str,
    collection_name: str,
    timestamp: Optional[datetime] = None,
    filters: Optional[Dict] = None,
    limit: int = 10
) -> SearchResults:
    """Semantic search with temporal awareness."""
    
    # Get embedding
    query_embedding = get_embedding(query_text)
    
    # Build temporal query
    aql_query = f"""
    FOR doc IN {collection_name}
        LET score = APPROX_NEAR_COSINE(doc.embedding, @query_embedding)
    """
    
    # Add temporal filter
    if timestamp:
        aql_query += """
        FILTER doc.valid_at <= @timestamp
        FILTER doc.invalid_at == null OR doc.invalid_at > @timestamp
        """
    
    aql_query += """
        SORT score DESC
        LIMIT @limit
        RETURN MERGE(doc, {similarity_score: score})
    """
    
    # ... rest of implementation
```

### 5. Update Memory Agent
```python
# core/memory/memory_agent.py
class MemoryAgent:
    def add_memory(
        self,
        user_message: str,
        agent_response: str,
        conversation_id: Optional[str] = None,
        valid_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Add memory with temporal tracking."""
        
        memory = MemoryEntity(
            user_message=user_message,
            agent_response=agent_response,
            conversation_id=conversation_id,
            valid_at=valid_at or datetime.utcnow(),
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Extract entities and relationships with temporal info
        entities = await self._extract_entities(memory)
        relationships = await self._extract_relationships(memory, entities)
        
        # Store with temporal tracking
        memory_id = await self._store_memory(memory)
        await self._store_temporal_entities(entities, memory.valid_at)
        await self._store_temporal_relationships(relationships, memory.valid_at)
        
        return memory_id
    
    def search_at_time(
        self,
        query: str,
        timestamp: datetime,
        search_type: SearchType = SearchType.HYBRID
    ) -> List[SearchResult]:
        """Search memories valid at specific time."""
        
        results = []
        
        if search_type in [SearchType.SEMANTIC, SearchType.HYBRID]:
            semantic_results = semantic_search_temporal(
                self.db,
                query,
                self.collection_name,
                timestamp=timestamp
            )
            results.extend(semantic_results)
        
        # ... other search types
        
        return self._deduplicate_results(results)
```

### 6. Add Temporal CLI Commands
```python
# cli/temporal_commands.py
@app.command("search-at-time")
def search_at_time(
    query: str = typer.Argument(..., help="Search query"),
    timestamp: str = typer.Argument(..., help="ISO timestamp"),
    search_type: str = typer.Option("hybrid", help="Search type")
):
    """Search entities valid at specific time."""
    
    db = get_db_connection()
    memory_agent = MemoryAgent(db)
    
    # Parse timestamp
    ts = datetime.fromisoformat(timestamp)
    
    # Perform temporal search
    results = memory_agent.search_at_time(query, ts, search_type)
    
    # Display results
    display_search_results(results)

@app.command("history")
def entity_history(
    entity_key: str = typer.Argument(..., help="Entity key"),
    start_time: Optional[str] = typer.Option(None, help="Start time"),
    end_time: Optional[str] = typer.Option(None, help="End time")
):
    """Show entity history within time range."""
    
    db = get_db_connection()
    
    # Get entity history
    history = get_entity_history(
        db,
        entity_key,
        start_time=datetime.fromisoformat(start_time) if start_time else None,
        end_time=datetime.fromisoformat(end_time) if end_time else None
    )
    
    # Display timeline
    display_entity_timeline(history)
```

### 7. Migration Scripts
```python
# scripts/migrate_to_bitemporal.py
def migrate_to_bitemporal(db):
    """Migrate existing data to bi-temporal model."""
    
    collections = [
        "memories",
        "entities", 
        "relationships",
        "episodes"
    ]
    
    for collection_name in collections:
        collection = db.collection(collection_name)
        
        # Update all documents
        for doc in collection.all():
            # Set valid_at to created_at if not present
            if "valid_at" not in doc:
                doc["valid_at"] = doc.get("created_at", datetime.utcnow())
            
            # Ensure invalid_at is null
            if "invalid_at" not in doc:
                doc["invalid_at"] = None
            
            # Update document
            collection.update(doc)
    
    print("Migration complete")
```

## Validation Steps

1. **Unit Tests**
```python
def test_temporal_entity_creation():
    """Test creating entity with temporal fields."""
    entity = MemoryEntity(
        user_message="test",
        agent_response="response",
        valid_at=datetime(2024, 1, 1),
        created_at=datetime(2024, 1, 2)
    )
    assert entity.valid_at < entity.created_at
    assert entity.invalid_at is None

def test_point_in_time_query():
    """Test querying at specific time."""
    # Create entities at different times
    # Query at specific points
    # Verify correct results
```

2. **Integration Tests**
```python
def test_temporal_search_flow():
    """Test complete temporal search flow."""
    # Add memories at different times
    # Invalidate some memories
    # Search at various points in time
    # Verify temporal consistency
```

3. **CLI Validation**
```bash
# Test temporal search
arangodb search-at-time "test query" "2024-01-01T00:00:00"

# Test entity history
arangodb history entity_123 --start-time "2024-01-01" --end-time "2024-12-31"

# Test temporal filtering
arangodb search "test" --valid-at "2024-06-01T00:00:00"
```

## Success Criteria

- [ ] All entities have valid_at and created_at timestamps
- [ ] Invalid_at field properly tracks invalidation
- [ ] Point-in-time queries return correct results
- [ ] Temporal range queries work correctly
- [ ] Search respects temporal boundaries
- [ ] CLI commands support temporal operations
- [ ] Migration script successfully updates existing data
- [ ] Performance remains acceptable with temporal queries
- [ ] Documentation updated with temporal examples

## Performance Considerations

1. **Indexing**
   - Create composite index on (valid_at, invalid_at)
   - Add index on created_at
   - Consider temporal-specific indexes

2. **Query Optimization**
   - Use index hints for temporal queries
   - Limit time range scans
   - Cache frequently accessed time periods

3. **Storage Impact**
   - Additional timestamp fields increase storage
   - Consider archiving old invalidated data
   - Monitor collection growth

## Next Steps

After implementing bi-temporal model:
1. Add edge invalidation and contradiction detection
2. Implement temporal aggregations
3. Add time-based analytics
4. Create temporal visualization tools