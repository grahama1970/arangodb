# ArangoDB Memory System Overview

## 🚀 Quick Start

The ArangoDB memory system is a sophisticated knowledge management platform designed for AI agents. It combines graph database capabilities with temporal memory tracking, inspired by the Graphiti architecture.

### Installation & Setup
```bash
# Install dependencies
uv pip install -r pyproject.toml

# Run the CLI
uv run python -m arangodb.cli.main --help
```

## 🏗️ Architecture

### Three-Layer Design
1. **Core Layer**: Database operations, search algorithms, memory management
2. **CLI Layer**: Command-line interface for human/agent interaction
3. **MCP Layer**: Model Context Protocol server for external integrations

### Key Components
- **Memory Agent**: Manages conversation storage and retrieval
- **Search Modules**: Semantic, keyword, BM25, hybrid search capabilities
- **Graph Operations**: Relationship management and traversal
- **Temporal Tracking**: Bi-temporal memory with valid/system time

## 🧠 Memory System Features

### 1. Conversation Storage
```python
# Store a conversation
result = agent.store_conversation(
    user_message="What is Python?",
    agent_response="Python is a programming language...",
    conversation_id="session_123"
)
```

### 2. Temporal Search
```python
# Search memories in time window
memories = agent.temporal_search(
    query_text="Python programming",
    point_in_time=datetime.now(),
    top_n=5
)
```

### 3. Entity Extraction
- Automatically extracts entities from conversations
- Creates relationships between related concepts
- Builds knowledge graph over time

### 4. Search Capabilities
- **Semantic**: Vector similarity search
- **Keyword**: Text-based pattern matching
- **BM25**: Full-text search with relevance scoring
- **Hybrid**: Combined approach with reranking
- **Graph**: Relationship traversal

## 📝 CLI Commands

### Memory Operations
```bash
# Store conversation
uv run python -m arangodb.cli.main memory store \
    --user-message "Question" \
    --agent-response "Answer" \
    --conversation-id "session_001"

# Search memories
uv run python -m arangodb.cli.main memory search \
    --entity "Python" \
    --timestamp "2025-05-16T00:00:00Z"
```

### Search Operations
```bash
# Semantic search
uv run python -m arangodb.cli.main search semantic "query text"

# Keyword search with custom fields
uv run python -m arangodb.cli.main search keyword "python" \
    --fields title,content,summary
```

### Graph Operations
```bash
# Create relationship
uv run python -m arangodb.cli.main graph create-relationship \
    --from-id "doc1" \
    --to-id "doc2" \
    --relationship-type "relates_to"
```

## 🤖 Agent Integration

### Basic Usage Pattern
```python
class AIAgent:
    def __init__(self):
        client = connect_arango()
        db = ensure_database(client)
        self.memory = MemoryAgent(db=db)
    
    def process_message(self, user_input):
        # 1. Search for context
        context = self.memory.temporal_search(
            query_text=user_input,
            point_in_time=datetime.now()
        )
        
        # 2. Generate response
        response = self.generate_response(user_input, context)
        
        # 3. Store interaction
        self.memory.store_conversation(
            user_message=user_input,
            agent_response=response,
            conversation_id=self.session_id
        )
```

## 📊 Data Structure

### Collections
- `agent_messages`: Individual messages
- `agent_memories`: Aggregated conversations
- `agent_entities`: Extracted entities
- `agent_relationships`: Graph edges
- `agent_communities`: Entity clusters

### Document Structure
```json
{
    "_key": "unique_id",
    "content": "Message content",
    "embedding": [0.1, 0.2, ...],  // Always in "embedding" field
    "start_time": "2025-05-16T10:00:00Z",
    "end_time": "2025-05-16T10:05:00Z",
    "conversation_id": "session_123",
    "entities": ["Python", "programming"],
    "importance": 0.8
}
```

## 🔧 Configuration

### Field Flexibility
- **Embedding Field**: Always `"embedding"` (standardized)
- **Text Fields**: Configurable per search operation
- **Example**: Search custom fields
  ```python
  results = bm25_search(
      db=db,
      query_text="search query",
      fields_to_search=["custom_title", "body_text"]
  )
  ```

### Environment Variables
```bash
ARANGO_HOST=http://localhost:8529
ARANGO_USER=root
ARANGO_PASSWORD=openSesame
ARANGO_DB_NAME=memory_bank
```

## 🚨 Important Notes

1. **No Hardcoded Text Fields**: All text search operations accept configurable field names
2. **Embedding Standardization**: The embedding field is always named "embedding"
3. **Temporal Tracking**: All memories have valid_time and system_time
4. **Entity Extraction**: Requires OpenAI/Anthropic API key (graceful fallback)
5. **View Creation**: Custom collections need corresponding views for search

## 📈 Performance Considerations

- Use batch operations for multiple documents
- Index frequently searched fields
- Configure appropriate shard counts for large datasets
- Monitor embedding generation time
- Cache frequently accessed memories

## 🔮 Future Enhancements

1. Community detection algorithms
2. Memory consolidation features
3. Advanced contradiction resolution
4. Multi-modal memory support
5. Distributed processing capabilities

## 📚 Additional Resources

- [Task Plan Guide](docs/memory_bank/guides/TASK_PLAN_GUIDE.md)
- [Field Conventions](src/arangodb/core/FIELD_CONVENTIONS.md)
- [CLI Usage Guide](docs/memory_bank/cli/CLI_USAGE.md)
- [Graphiti Recommendations](docs/memory_bank/GRAPHITI_RECOMMENDATIONS.md)

## ✅ System Status

The ArangoDB memory system is production-ready with:
- ✅ Full memory storage and retrieval
- ✅ Temporal search capabilities
- ✅ Entity extraction (with API key)
- ✅ Relationship building
- ✅ Multiple search types
- ✅ Field flexibility
- ✅ Clean architecture
- ✅ Comprehensive logging

The system provides a solid foundation for AI agents to maintain conversation history, build knowledge graphs, and retrieve contextually relevant information across time.