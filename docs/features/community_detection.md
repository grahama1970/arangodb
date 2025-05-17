# Community Detection Feature

## Overview

Community Detection is the first of 10 features implemented to achieve parity with Graphiti. It automatically identifies and groups related entities in the knowledge graph using the Louvain algorithm for modularity optimization.

## Features

- **Automatic Detection**: Communities are detected automatically when new entities are created during conversation storage
- **Louvain Algorithm**: Uses a simplified implementation of the Louvain algorithm for fast and effective community detection
- **Configurable Parameters**: Min size and resolution can be adjusted based on your needs
- **CLI Integration**: Full CLI support for manual detection and management
- **Database Persistence**: Communities are stored in the `agent_communities` collection

## Usage

### CLI Commands

```bash
# Detect communities with default parameters
uv run arangodb-cli community detect

# Detect with custom parameters
uv run arangodb-cli community detect --min-size 3 --resolution 1.5

# List all communities
uv run arangodb-cli community list

# Show details of a specific community
uv run arangodb-cli community show community_12345

# Force rebuild all communities
uv run arangodb-cli community detect --rebuild
```

### Memory Agent Integration

When using the Memory Agent, community detection happens automatically:

```python
from arangodb.core.memory.memory_agent import MemoryAgent

# Initialize with community detection enabled (default)
agent = MemoryAgent(
    db=db,
    auto_detect_communities=True,
    community_min_size=2,
    community_resolution=1.0
)

# Store conversation - entities and communities are detected automatically
result = agent.store_conversation(
    user_message="Tell me about Python frameworks",
    agent_response="Django and Flask are popular Python web frameworks..."
)
```

### Direct API Usage

```python
from arangodb.core.graph.community_detection import CommunityDetector

# Initialize detector
detector = CommunityDetector(db)

# Detect communities
communities = detector.detect_communities(min_size=2, resolution=1.0)

# Get all communities
all_communities = detector.get_all_communities()

# Get community for specific entity
community = detector.get_community_for_entity("entity_123")
```

## Configuration

### Memory Agent Parameters

- `auto_detect_communities` (bool): Enable/disable automatic detection (default: True)
- `community_min_size` (int): Minimum community size (default: 2)
- `community_resolution` (float): Resolution parameter - higher values create more communities (default: 1.0)

### CLI Options

- `--min-size`: Minimum number of members required for a community
- `--resolution`: Resolution parameter for the Louvain algorithm
- `--rebuild`: Force rebuild all communities from scratch
- `--json`: Output results in JSON format

## Database Schema

### Community Collection (`agent_communities`)

```json
{
  "_key": "community_12345",
  "original_id": "entity_group_id",
  "member_count": 5,
  "member_ids": ["entity_1", "entity_2", ...],
  "sample_members": ["Python", "Django", "Flask", ...],
  "created_at": "2025-01-17T10:00:00Z",
  "metadata": {
    "algorithm": "louvain",
    "modularity_score": 0.82
  }
}
```

### Entity Updates

Entities in `agent_entities` are updated with:
- `community_id`: The assigned community key
- `community_scores`: Confidence scores for potential community memberships

## Algorithm Details

The implementation uses a simplified Louvain algorithm:

1. **Initialization**: Each entity starts in its own community
2. **Optimization**: Entities are moved between communities to maximize modularity
3. **Merging**: Small communities below the minimum size are merged with their most connected neighbors
4. **Storage**: Final communities are persisted to the database

### Modularity Score

Modularity measures the quality of community structure:
- Range: -1 to 1 (higher is better)
- Good scores: > 0.3
- Excellent scores: > 0.6

## Performance

- Detection time: O(n log n) for n entities
- Scales well to thousands of entities
- Incremental updates supported
- Caching for repeated queries

## Examples

### Example Output

```bash
$ uv run arangodb-cli community detect

Community Detection Results
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Community ID       ┃ Size ┃ Key Entities        ┃ Modularity ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ community_66c305a5 │  3   │ Python, Django,     │   0.682    │
│                    │      │ Flask               │            │
│ community_231a25bf │  4   │ Java, Spring,       │   0.654    │
│                    │      │ Hibernate, Maven    │            │
│ community_dc85ec2d │  2   │ PostgreSQL, MongoDB │   0.501    │
└────────────────────┴──────┴─────────────────────┴────────────┘

Total communities: 3
Total entities: 9
```

### Integration Example

```python
# Full example with error handling
import logging
from arangodb.core.arango_setup import connect_arango, ensure_database
from arangodb.core.memory.memory_agent import MemoryAgent

logging.basicConfig(level=logging.INFO)

try:
    # Connect to database
    client = connect_arango()
    db = ensure_database(client)
    
    # Initialize agent with custom settings
    agent = MemoryAgent(
        db=db,
        auto_detect_communities=True,
        community_min_size=3,
        community_resolution=1.2
    )
    
    # Store conversation
    result = agent.store_conversation(
        user_message="Compare Python and Java for web development",
        agent_response="Python offers Django and Flask, while Java has Spring Boot..."
    )
    
    print(f"Conversation stored: {result['conversation_id']}")
    
except Exception as e:
    logging.error(f"Error: {e}")
```

## Troubleshooting

### Common Issues

1. **No communities detected**
   - Check if entities have relationships
   - Try lowering `min_size` parameter
   - Verify entities exist in `agent_entities` collection

2. **Too many small communities**
   - Increase `min_size` parameter
   - Adjust `resolution` parameter (lower values merge more)

3. **Poor modularity scores**
   - May indicate weak relationship structure
   - Consider adjusting confidence thresholds
   - Review entity extraction quality

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.getLogger("arangodb.core.graph.community_detection").setLevel(logging.DEBUG)
```

## Future Enhancements

- Hierarchical community detection
- Dynamic community updates
- Community evolution tracking
- Custom similarity metrics
- Visualization tools

## Related Features

- **Entity Resolution**: Ensures unique entities for better communities
- **Relationship Extraction**: Provides the edges for community detection
- **Contradiction Resolution**: Uses communities to contextualize conflicts
- **Search Enhancement**: Communities improve search relevance

## API Reference

See the full API documentation at `src/arangodb/core/graph/community_detection.py`