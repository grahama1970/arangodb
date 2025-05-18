# ArangoDB Collection Field Schemas

This document defines the standard field names and schemas for all ArangoDB collections in the memory bank project.

## Message Collections

### agent_messages (MEMORY_MESSAGE_COLLECTION)
Primary collection for storing user and agent messages.

```json
{
  "_key": "string",                    // ArangoDB document key
  "_id": "string",                     // ArangoDB document ID
  "type": "string",                    // Message type: "user", "agent", "system"
  "content": "string",                 // Message content
  "conversation_id": "string",         // UUID for conversation
  "episode_id": "string (optional)",   // UUID for episode grouping
  "timestamp": "ISO 8601 string",      // UTC timestamp (e.g., "2025-01-17T10:30:00Z")
  "embedding": [float],                // Vector embedding (1024 dimensions for BGE)
  "metadata": {                        // Additional metadata
    "model": "string",
    "temperature": "float",
    // ... other metadata
  }
}
```

### system_messages (SYSTEM_MESSAGE_COLLECTION)
System-level messages and notifications.

```json
{
  "_key": "string",
  "_id": "string",
  "type": "string",                    // Always "system"
  "content": "string",
  "timestamp": "ISO 8601 string",
  "metadata": {}
}
```

## Entity Collections

### agent_entities (MEMORY_ENTITY_COLLECTION)
Extracted entities from conversations.

```json
{
  "_key": "string",
  "_id": "string",
  "name": "string",                    // Entity name
  "type": "string",                    // Entity type (Person, Organization, etc.)
  "description": "string",             // Description of the entity
  "attributes": {                      // Entity-specific attributes
    "key": "value"
  },
  "timestamp": "ISO 8601 string",
  "embedding": [float],
  "metadata": {}
}
```

## Relationship Collections (Edge Collections)

### agent_relationships (MEMORY_EDGE_COLLECTION)
Relationships between messages and entities.

```json
{
  "_key": "string",
  "_id": "string",
  "_from": "string",                   // Source document ID
  "_to": "string",                     // Target document ID
  "type": "string",                    // Relationship type: "next", "refers_to", etc.
  "relation": "string",                // Optional relationship description
  "valid_from": "ISO 8601 string",     // Temporal validity start
  "valid_to": "ISO 8601 string",       // Temporal validity end
  "timestamp": "ISO 8601 string",
  "metadata": {
    "conversation_id": "string",
    "confidence": "float"
  }
}
```

## Community and Contradiction Collections

### agent_communities
Community detection results.

```json
{
  "_key": "string",
  "_id": "string",
  "community_id": "string",
  "name": "string",
  "entities": ["entity_id"],
  "timestamp": "ISO 8601 string",
  "metadata": {}
}
```

### agent_contradiction_log
Detected contradictions in conversations.

```json
{
  "_key": "string",
  "_id": "string",
  "subjects": ["string"],
  "timestamp": "ISO 8601 string",
  "claims": [
    {
      "source_id": "string",
      "content": "string",
      "timestamp": "ISO 8601 string"
    }
  ],
  "metadata": {}
}
```

## Compaction Collections

### compacted_summaries
Compacted conversation summaries.

```json
{
  "_key": "string",
  "_id": "string",
  "content": "string",
  "source_message_ids": ["message_id"],
  "timestamp": "ISO 8601 string",
  "embedding": [float],
  "metadata": {
    "method": "string",
    "token_count": "integer"
  }
}
```

### compaction_links (Edge)
Links between original messages and compacted summaries.

```json
{
  "_key": "string",
  "_id": "string",
  "_from": "message_id",
  "_to": "summary_id",
  "type": "compaction",
  "timestamp": "ISO 8601 string",
  "metadata": {}
}
```

## Field Naming Conventions

### Core Fields
- **ID Fields**: `_key`, `_id` (ArangoDB standard)
- **Type Fields**: `type` (NOT `message_type` or `entity_type`)
- **Content Fields**: `content` (NOT `text` or `message`)
- **Timestamp Fields**: `timestamp` (NOT `created_at` or `date`)
- **Relationship Fields**: `_from`, `_to` (ArangoDB standard)

### Embedding Fields
- **Vector Field**: `embedding` (NOT `content_embedding` or `vector`)
- **Dimensions**: 1024 for BGE model

### Metadata Fields
- **Metadata Container**: `metadata` (object containing additional info)
- **Conversation Tracking**: `conversation_id`, `episode_id`
- **Temporal Validity**: `valid_from`, `valid_to`

## Usage Examples

### Creating a Message Document
```python
message_doc = {
    "type": MESSAGE_TYPE_USER,  # Use constants
    "content": "Hello, how are you?",
    "conversation_id": str(uuid.uuid4()),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "embedding": get_embedding(content),
    "metadata": {}
}
```

### Querying by Type
```python
# Correct field name
query = "FOR m IN agent_messages FILTER m.type == @type RETURN m"
bind_vars = {"type": MESSAGE_TYPE_USER}
```

## Migration Notes

When updating existing code:
1. Replace `message_type` with `type` in queries and display logic
2. Replace `content_embedding` with `embedding` where applicable
3. Ensure all timestamps use ISO 8601 format
4. Use field constants from `constants.py` where available