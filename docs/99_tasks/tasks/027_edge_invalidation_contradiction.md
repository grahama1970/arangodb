# Task 027: Edge Invalidation and Temporal Contradiction Detection

## Overview
Implement edge invalidation and temporal contradiction detection to maintain historical accuracy in the knowledge graph. This allows the system to handle changing relationships over time and detect when new information contradicts existing edges.

## Dependencies
- Task 026: Bi-Temporal Data Model Implementation (must be completed first)

## Current State
- No edge invalidation
- No contradiction detection
- Static relationships
- No temporal conflict resolution

## Target State
- Automatic edge invalidation when contradictions detected
- LLM-driven contradiction analysis
- Temporal edge dating
- Historical relationship tracking

## Implementation Steps

### 1. Update Edge Model
```python
# core/models.py
class TemporalEdge(BaseModel):
    """Edge with temporal tracking and invalidation."""
    _key: Optional[str] = None
    _from: str  # Source node
    _to: str    # Target node
    relationship_type: str
    properties: Dict[str, Any] = {}
    
    # Temporal fields
    created_at: datetime
    valid_at: datetime
    invalid_at: Optional[datetime] = None
    
    # Invalidation metadata
    invalidated_by: Optional[str] = None  # Edge that invalidated this
    invalidation_reason: Optional[str] = None
    
    # Dating information
    start_date: Optional[datetime] = None  # When relationship began
    end_date: Optional[datetime] = None    # When relationship ended
    temporal_confidence: float = 1.0       # Confidence in dates

class EdgeContradiction(BaseModel):
    """Detected contradiction between edges."""
    edge1_key: str
    edge2_key: str
    contradiction_type: str
    confidence: float
    resolution: str
    detected_at: datetime
```

### 2. Implement Edge Dating
```python
# core/graph/temporal_operations.py
from typing import Tuple, Optional
import asyncio

async def extract_edge_dates(
    llm_client: LLMClient,
    edge: TemporalEdge,
    current_episode: Episode,
    previous_episodes: List[Episode]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Extract temporal boundaries for edge using LLM."""
    
    prompt = f"""
    Analyze the following information to determine when this relationship started and ended:
    
    Edge: {edge.relationship_type} between {edge._from} and {edge._to}
    Current Episode: {current_episode.content}
    Valid At: {edge.valid_at}
    
    Previous Context:
    {[ep.content for ep in previous_episodes]}
    
    Determine:
    1. When did this relationship start? (or null if unknown)
    2. When did this relationship end? (or null if still active)
    3. How confident are you in these dates? (0.0-1.0)
    
    Consider only explicit temporal information. Do not guess.
    """
    
    response = await llm_client.generate_json(
        prompt,
        schema={
            "start_date": {"type": "string", "format": "date-time", "nullable": True},
            "end_date": {"type": "string", "format": "date-time", "nullable": True},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reasoning": {"type": "string"}
        }
    )
    
    return (
        datetime.fromisoformat(response["start_date"]) if response["start_date"] else None,
        datetime.fromisoformat(response["end_date"]) if response["end_date"] else None,
        response["confidence"]
    )
```

### 3. Implement Contradiction Detection
```python
# core/graph/contradiction_detection.py
async def detect_edge_contradictions(
    db,
    new_edge: TemporalEdge,
    existing_edges: List[TemporalEdge],
    llm_client: LLMClient
) -> List[EdgeContradiction]:
    """Detect contradictions between new edge and existing edges."""
    
    contradictions = []
    
    for existing_edge in existing_edges:
        # Skip if already invalidated
        if existing_edge.invalid_at:
            continue
            
        # Check for potential contradiction
        if is_potential_contradiction(new_edge, existing_edge):
            contradiction = await analyze_contradiction(
                llm_client,
                new_edge,
                existing_edge
            )
            
            if contradiction:
                contradictions.append(contradiction)
    
    return contradictions

def is_potential_contradiction(edge1: TemporalEdge, edge2: TemporalEdge) -> bool:
    """Quick check for potential contradiction."""
    # Same nodes, different relationship types
    if (edge1._from == edge2._from and edge1._to == edge2._to and 
        edge1.relationship_type != edge2.relationship_type):
        return True
    
    # Mutually exclusive relationships
    exclusive_pairs = [
        ("loves", "hates"),
        ("friend", "enemy"),
        ("alive", "dead"),
        ("married", "divorced")
    ]
    
    for pair in exclusive_pairs:
        if (edge1.relationship_type in pair and 
            edge2.relationship_type in pair and
            edge1.relationship_type != edge2.relationship_type):
            return True
    
    return False

async def analyze_contradiction(
    llm_client: LLMClient,
    edge1: TemporalEdge,
    edge2: TemporalEdge
) -> Optional[EdgeContradiction]:
    """Use LLM to analyze if edges contradict."""
    
    prompt = f"""
    Analyze these two relationships for contradiction:
    
    Edge 1: {edge1._from} {edge1.relationship_type} {edge1._to}
    Valid at: {edge1.valid_at}
    Properties: {edge1.properties}
    
    Edge 2: {edge2._from} {edge2.relationship_type} {edge2._to}
    Valid at: {edge2.valid_at}
    Properties: {edge2.properties}
    
    Questions:
    1. Do these edges contradict each other?
    2. If yes, what type of contradiction? (temporal, logical, factual)
    3. How should it be resolved? (invalidate_older, invalidate_newer, both_valid, requires_context)
    4. Confidence in this analysis? (0.0-1.0)
    """
    
    response = await llm_client.generate_json(
        prompt,
        schema={
            "is_contradiction": {"type": "boolean"},
            "contradiction_type": {"type": "string", "enum": ["temporal", "logical", "factual", "none"]},
            "resolution": {"type": "string", "enum": ["invalidate_older", "invalidate_newer", "both_valid", "requires_context"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reasoning": {"type": "string"}
        }
    )
    
    if response["is_contradiction"]:
        return EdgeContradiction(
            edge1_key=edge1._key,
            edge2_key=edge2._key,
            contradiction_type=response["contradiction_type"],
            confidence=response["confidence"],
            resolution=response["resolution"],
            detected_at=datetime.utcnow()
        )
    
    return None
```

### 4. Implement Resolution Logic
```python
# core/graph/contradiction_resolution.py
async def resolve_contradiction(
    db,
    contradiction: EdgeContradiction,
    llm_client: Optional[LLMClient] = None
) -> Dict[str, Any]:
    """Resolve detected contradiction."""
    
    edge1 = db.collection("edges").get(contradiction.edge1_key)
    edge2 = db.collection("edges").get(contradiction.edge2_key)
    
    resolution_result = {
        "contradiction": contradiction,
        "actions": []
    }
    
    if contradiction.resolution == "invalidate_older":
        older_edge = edge1 if edge1["valid_at"] < edge2["valid_at"] else edge2
        newer_edge = edge2 if edge1["valid_at"] < edge2["valid_at"] else edge1
        
        # Invalidate older edge
        invalidate_edge(
            db,
            older_edge["_key"],
            invalid_at=newer_edge["valid_at"],
            reason=f"Contradicted by newer edge {newer_edge['_key']}",
            invalidated_by=newer_edge["_key"]
        )
        
        resolution_result["actions"].append({
            "action": "invalidated",
            "edge": older_edge["_key"],
            "reason": "older_contradicting_edge"
        })
        
    elif contradiction.resolution == "invalidate_newer":
        # Similar logic but invalidate newer edge
        pass
        
    elif contradiction.resolution == "requires_context":
        # Use LLM for complex resolution
        if llm_client:
            context_resolution = await resolve_with_context(
                llm_client,
                edge1,
                edge2,
                contradiction
            )
            resolution_result["actions"].extend(context_resolution["actions"])
    
    # Log resolution
    db.collection("contradiction_resolutions").insert(resolution_result)
    
    return resolution_result

def invalidate_edge(
    db,
    edge_key: str,
    invalid_at: datetime,
    reason: str,
    invalidated_by: Optional[str] = None
):
    """Mark edge as invalid."""
    
    db.collection("edges").update({
        "_key": edge_key
    }, {
        "invalid_at": invalid_at,
        "invalidation_reason": reason,
        "invalidated_by": invalidated_by
    })
```

### 5. Update Edge Creation Flow
```python
# core/graph/relationship_extraction.py
async def create_temporal_edge(
    db,
    source_key: str,
    target_key: str,
    relationship_type: str,
    properties: Dict[str, Any],
    episode: Episode,
    llm_client: LLMClient
) -> TemporalEdge:
    """Create edge with temporal tracking and contradiction detection."""
    
    # Create base edge
    edge = TemporalEdge(
        _from=f"entities/{source_key}",
        _to=f"entities/{target_key}",
        relationship_type=relationship_type,
        properties=properties,
        created_at=datetime.utcnow(),
        valid_at=episode.valid_at
    )
    
    # Extract temporal boundaries
    previous_episodes = await get_previous_episodes(db, episode)
    start_date, end_date, confidence = await extract_edge_dates(
        llm_client,
        edge,
        episode,
        previous_episodes
    )
    
    edge.start_date = start_date
    edge.end_date = end_date
    edge.temporal_confidence = confidence
    
    # Check for contradictions
    existing_edges = await get_related_edges(db, source_key, target_key)
    contradictions = await detect_edge_contradictions(
        db,
        edge,
        existing_edges,
        llm_client
    )
    
    # Handle contradictions
    for contradiction in contradictions:
        await resolve_contradiction(db, contradiction, llm_client)
    
    # Store edge
    edge_doc = edge.dict()
    result = db.collection("edges").insert(edge_doc)
    edge._key = result["_key"]
    
    return edge
```

### 6. Update Search to Respect Invalidation
```python
# core/search/graph_search.py
def search_valid_edges(
    db,
    timestamp: Optional[datetime] = None,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """Search edges that are valid at given time."""
    
    query = """
    FOR edge IN edges
        FILTER edge.invalid_at == null OR edge.invalid_at > @timestamp
        FILTER edge.valid_at <= @timestamp
    """
    
    if filters:
        for key, value in filters.items():
            query += f" FILTER edge.{key} == @{key}"
    
    query += " RETURN edge"
    
    bind_vars = {
        "timestamp": timestamp or datetime.utcnow()
    }
    if filters:
        bind_vars.update(filters)
    
    cursor = db.aql.execute(query, bind_vars=bind_vars)
    return list(cursor)
```

### 7. Add CLI Commands
```python
# cli/contradiction_commands.py
@app.command("detect")
def detect_contradictions(
    entity_key: Optional[str] = typer.Option(None, help="Check specific entity"),
    edge_type: Optional[str] = typer.Option(None, help="Check specific edge type"),
    resolve: bool = typer.Option(False, help="Auto-resolve contradictions")
):
    """Detect contradictions in the graph."""
    
    db = get_db_connection()
    llm_client = get_llm_client()
    
    # Find potential contradictions
    contradictions = find_contradictions(
        db,
        entity_key=entity_key,
        edge_type=edge_type
    )
    
    console.print(f"Found {len(contradictions)} potential contradictions")
    
    for contradiction in contradictions:
        display_contradiction(contradiction)
        
        if resolve:
            resolution = resolve_contradiction(
                db,
                contradiction,
                llm_client
            )
            display_resolution(resolution)

@app.command("invalidate")
def invalidate_edge(
    edge_key: str = typer.Argument(..., help="Edge key to invalidate"),
    reason: str = typer.Option(..., help="Invalidation reason"),
    timestamp: Optional[str] = typer.Option(None, help="Invalidation timestamp")
):
    """Manually invalidate an edge."""
    
    db = get_db_connection()
    
    invalid_at = (
        datetime.fromisoformat(timestamp) if timestamp 
        else datetime.utcnow()
    )
    
    db.collection("edges").update({
        "_key": edge_key
    }, {
        "invalid_at": invalid_at,
        "invalidation_reason": reason,
        "invalidated_by": "manual"
    })
    
    console.print(f"Edge {edge_key} invalidated at {invalid_at}")
```

## Validation Steps

1. **Unit Tests**
```python
def test_contradiction_detection():
    """Test detecting contradictions between edges."""
    edge1 = TemporalEdge(
        _from="person/alice",
        _to="person/bob",
        relationship_type="married",
        valid_at=datetime(2020, 1, 1)
    )
    
    edge2 = TemporalEdge(
        _from="person/alice",
        _to="person/bob",
        relationship_type="divorced",
        valid_at=datetime(2021, 1, 1)
    )
    
    contradiction = detect_edge_contradictions(db, edge2, [edge1])
    assert len(contradiction) == 1
    assert contradiction[0].contradiction_type == "temporal"

def test_edge_invalidation():
    """Test edge invalidation flow."""
    # Create edge
    # Detect contradiction
    # Verify invalidation
    # Check search excludes invalid edge
```

2. **Integration Tests**
```python
def test_temporal_contradiction_flow():
    """Test complete contradiction detection and resolution."""
    # Create conflicting relationships over time
    # Verify automatic invalidation
    # Test temporal queries
    # Verify historical accuracy
```

## Success Criteria

- [ ] Edges have temporal dating information
- [ ] Contradictions are automatically detected
- [ ] LLM analysis provides accurate contradiction detection
- [ ] Resolution strategies work correctly
- [ ] Invalid edges are excluded from searches
- [ ] Historical queries show correct state
- [ ] CLI commands work for contradiction management
- [ ] Performance acceptable with contradiction checks

## Next Steps

1. Implement more sophisticated contradiction types
2. Add bulk contradiction detection
3. Create contradiction analytics
4. Build temporal visualization
5. Add contradiction learning/patterns