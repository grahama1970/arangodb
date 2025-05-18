# Temporal Model Usage Guide

## Overview

The bi-temporal model in ArangoDB Memory Bank tracks two dimensions of time:
- **Transaction Time**: When data was recorded in the system
- **Valid Time**: When the fact was true in reality

## Core Concepts

### Temporal Fields
- `created_at`: When the record was created (transaction time)
- `valid_at`: When the fact became true (valid time)
- `invalid_at`: When the fact became invalid (null if still valid)

## CLI Commands

### Store with Temporal Data
```bash
# Store a conversation with specific temporal metadata
arangodb-cli memory store \
    --user-message "What's the weather?" \
    --agent-response "It's sunny today" \
    --point-in-time "2024-01-01T12:00:00" \
    --valid-at "2024-01-01T12:00:00"
```

### Search at a Specific Time
```bash
# Find messages valid at a specific point in time
arangodb-cli memory search-at-time "weather" \
    --timestamp "2024-01-01T12:00:00"
```

### View Conversation History
```bash
# Get conversation state at a specific time
arangodb-cli memory conversation-at-time <conversation_id> \
    --timestamp "2024-01-01T12:00:00"
```

### Migrate Existing Data
```bash
# Add temporal fields to existing messages
arangodb-cli memory migrate-to-temporal
```

## API Usage

### Python Examples

```python
from datetime import datetime, timezone, timedelta
from arangodb.core.memory.memory_agent import MemoryAgent

# Initialize agent
memory_agent = MemoryAgent(db)

# Store with temporal data
memory_agent.store_conversation(
    user_message="Query",
    agent_response="Response",
    point_in_time=datetime.now(timezone.utc) - timedelta(hours=1),
    valid_at=datetime.now(timezone.utc) - timedelta(hours=1)
)

# Search at a specific time
results = memory_agent.search_at_time(
    query="weather",
    timestamp=datetime.now(timezone.utc) - timedelta(hours=1)
)

# Get conversation at a time
messages = memory_agent.get_conversation_at_time(
    conversation_id="12345",
    timestamp=datetime.now(timezone.utc) - timedelta(hours=1)
)
```

## Temporal Queries

### AQL Examples

```aql
// Point-in-time query
FOR doc IN agent_messages
    FILTER doc.valid_at <= @timestamp
    FILTER doc.invalid_at == null OR doc.invalid_at > @timestamp
    RETURN doc

// Temporal range query
FOR doc IN agent_messages
    FILTER doc.valid_at >= @start_time
    FILTER doc.valid_at <= @end_time
    FILTER doc.invalid_at == null OR doc.invalid_at > @end_time
    RETURN doc
```

## Best Practices

1. **Always Set Valid Time**: When storing data, consider when the fact became true
2. **Use Invalidation**: Mark outdated information as invalid rather than deleting
3. **Query Efficiently**: Use point-in-time queries to get consistent historical views
4. **Index Temporal Fields**: Ensure temporal fields are included in search views

## Migration Tips

For existing data:
1. Run the migration command to add temporal fields
2. Review and adjust timestamps as needed
3. Consider invalidating outdated information
4. Update queries to use temporal filtering

## Common Use Cases

1. **Historical Analysis**: View system state at past times
2. **Audit Trails**: Track when information was recorded
3. **Contradiction Detection**: Identify conflicting statements over time
4. **Version Control**: Maintain multiple versions of facts