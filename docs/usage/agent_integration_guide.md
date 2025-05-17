# Agent Integration Guide for ArangoDB Memory System

This guide provides information on how to integrate the ArangoDB Memory Agent system into an AI agent architecture. It focuses on creating a streamlined setup process with sensible defaults and provides programming patterns for effective integration.

## 1. Agent Integration Strategies

### 1.1 Basic Integration

For basic integration with minimal configuration:

```python
from arangodb.core.memory.agent_client import MemoryAgentClient

# One-line initialization with sensible defaults
memory = MemoryAgentClient.from_environment()

# Basic memory operations
conversation_id = memory.store_exchange(
    user_message="What is the project deadline?",
    agent_response="The project deadline is October 15th."
)

# Retrieve relevant memories for context
relevant_memories = memory.search("project deadline", top_n=3)

# Include memories in context for next response
context = memory.format_context(relevant_memories)
```

### 1.2 Advanced Integration with Auto-Configuration

For a more sophisticated integration that adapts to available resources:

```python
from arangodb.core.memory.agent_client import MemoryAgentClient
from arangodb.core.utils.auto_config import AutoConfig

# Auto-detect optimal configuration based on environment
config = AutoConfig.detect()

# Initialize with auto-configured settings
memory = MemoryAgentClient(
    config=config,
    session_id="agent-session-123",
    enable_cache=True  # Automatically uses Redis if available or fallbacks to in-memory
)

# Memory operations with auto-configured settings
memory.store_exchange(
    user_message="What approach should we use for the database?",
    agent_response="I recommend a graph database like ArangoDB for this use case.",
    metadata={"topic": "database-design", "confidence": 0.92}
)
```

## 2. Simplified Setup For Agents

### 2.1 Agent-Optimized Configuration

```python
from arangodb.core.memory.agent_config import AgentMemoryConfig

# Agent-optimized configuration with sensible defaults
config = AgentMemoryConfig.create_agent_defaults(
    embedding_model="small",  # Defaults to a lightweight embedding model optimized for agents
    enable_graph=True,        # Enable knowledge graph capabilities
    enable_compaction=True,   # Enable conversation compaction for efficiency
    enable_contradiction=True # Enable contradiction detection
)
```

### 2.2 Environment Auto-Detection

```python
from arangodb.core.utils.environment import detect_environment

# Auto-detect environment and available resources
env_info = detect_environment()

if env_info.has_gpu:
    # Use GPU-optimized embedding model
    config.set_embedding_model("sentence-transformers/all-mpnet-base-v2")
else:
    # Use CPU-optimized model
    config.set_embedding_model("sentence-transformers/all-MiniLM-L6-v2")

# Adjust batch sizes based on available memory
config.set_batch_sizes(
    embedding_batch_size=env_info.recommended_batch_size,
    search_batch_size=env_info.recommended_batch_size
)
```

### 2.3 Automatic Fallbacks

```python
from arangodb.core.memory.agent_client import MemoryAgentClient
from arangodb.core.utils.fallbacks import FallbackManager

# Initialize with fallback capabilities
fallbacks = FallbackManager()
memory = MemoryAgentClient(fallback_manager=fallbacks)

# Fallbacks will automatically handle:
# - Missing embedding models by downloading or using alternatives
# - Database connection issues by using temporary storage
# - Missing dependencies by using simpler alternatives
```

## 3. Session Management for Agents

### 3.1 Persistent Agent Sessions

```python
from arangodb.core.memory.session_manager import SessionManager

# Create a session manager for persistent connections
session_mgr = SessionManager(
    agent_id="assistant-123",
    ttl_hours=24  # Session data persists for 24 hours
)

# Get or create a session
memory_session = session_mgr.get_or_create_session(user_id="user-456")

# Use the session for operations
memory_session.store_exchange(
    user_message="Will you remember this conversation tomorrow?",
    agent_response="Yes, I'll remember this conversation."
)

# Session handles reconnection automatically if the connection is lost
```

### 3.2 Episode Management for Agent Conversations

```python
from arangodb.core.memory.agent_client import MemoryAgentClient

memory = MemoryAgentClient.from_environment()

# Create a new episode for a specific topic
episode_id = memory.create_episode(
    name="Product Requirements Discussion",
    description="Conversation about the new product features and requirements"
)

# Store conversation in the episode
memory.store_exchange(
    user_message="What features are we including in the MVP?",
    agent_response="The MVP will include user authentication, basic data visualization, and export functionality.",
    episode_id=episode_id
)

# Get the full episode conversation for context
episode_context = memory.get_episode_context(episode_id, message_limit=50)
```

## 4. Memory Retrieval Patterns for Agents

### 4.1 Relevant Memory Retrieval for Context

```python
from arangodb.core.memory.agent_client import MemoryAgentClient

memory = MemoryAgentClient.from_environment()

def get_relevant_context(query, conversation_id=None):
    """Get relevant context for the agent based on the current query."""
    # Combine different search methods for best results
    semantic_results = memory.search_semantic(query, top_n=3)
    
    # Get conversation history if conversation_id is provided
    history = []
    if conversation_id:
        history = memory.get_recent_history(conversation_id, limit=5)
    
    # Get any compacted summaries that might be relevant
    compactions = memory.search_compactions(query, top_n=2)
    
    # Combine all context sources with appropriate weighting and formatting
    context = memory.format_agent_context(
        semantic_results=semantic_results,
        conversation_history=history,
        compactions=compactions
    )
    
    return context

# Use the context in agent prompt
user_query = "What did we decide about the database architecture?"
context = get_relevant_context(user_query, conversation_id="conv_123")

# Include context in LLM prompt
agent_prompt = f"""
Based on the following context:
{context}

Answer the user's question: {user_query}
"""
```

### 4.2 Temporal Memory Management

```python
from arangodb.core.memory.agent_client import MemoryAgentClient
from datetime import datetime, timedelta

memory = MemoryAgentClient.from_environment()

# Get memories from a specific time period
one_week_ago = datetime.now() - timedelta(days=7)
recent_memories = memory.search_temporal(
    query="project status",
    point_in_time=one_week_ago,
    top_n=5
)

# Compare past knowledge with current knowledge
current_knowledge = memory.search("project status", top_n=5)

# Detect changes or conflicts
conflicts = memory.detect_changes(
    old_memories=recent_memories,
    new_memories=current_knowledge
)

if conflicts:
    # Inform the agent about changes in knowledge
    print("Knowledge has changed since last week:")
    for conflict in conflicts:
        print(f"- {conflict['description']}")
```

## 5. Optimizing Memory Usage for Agents

### 5.1 Automatic Memory Compaction

```python
from arangodb.core.memory.agent_client import MemoryAgentClient

memory = MemoryAgentClient.from_environment()

# Configure automatic compaction
memory.configure_auto_compaction(
    threshold_message_count=20,  # Compact when conversation exceeds 20 messages
    compaction_method="extract_key_points",
    retention_days=30  # Keep original messages for 30 days
)

# Store exchanges normally - compaction happens automatically
memory.store_exchange(
    user_message="What's the status of the project?",
    agent_response="We're currently in the design phase, expected to move to development next week.",
    conversation_id="conv_123"
)

# Get the latest compacted summary of a conversation
latest_summary = memory.get_latest_compaction("conv_123")
```

### 5.2 Memory Importance Scoring

```python
from arangodb.core.memory.agent_client import MemoryAgentClient

memory = MemoryAgentClient.from_environment()

# Configure memory importance scoring
memory.configure_importance_scoring(
    enable_decay=True,  # Enable importance decay over time
    recency_weight=0.4,  # Weight for recency factor
    relevance_weight=0.3,  # Weight for semantic relevance
    interaction_weight=0.3,  # Weight for user interaction frequency
)

# Get memories prioritized by importance
important_memories = memory.get_important_memories(
    reference_query="current project status",
    top_n=5
)
```

## 6. Dependency Management for Agents

### 6.1 Automatic Dependency Detection

```python
from arangodb.core.utils.dependency_manager import DependencyManager

# Initialize dependency manager
dep_manager = DependencyManager()

# Check for and adapt to available dependencies
embedding_config = dep_manager.get_best_embedding_config()
search_config = dep_manager.get_best_search_config()
storage_config = dep_manager.get_best_storage_config()

# Configure with the optimal settings based on dependencies
from arangodb.core.memory.agent_client import MemoryAgentClient

memory = MemoryAgentClient(
    embedding_config=embedding_config,
    search_config=search_config,
    storage_config=storage_config
)
```

### 6.2 Lightweight Mode for Constrained Environments

```python
from arangodb.core.memory.agent_client import MemoryAgentClient

# Initialize in lightweight mode for constrained environments
memory = MemoryAgentClient.create_lightweight(
    use_local_embeddings=True,  # Use lightweight local embedding models
    disable_graph=True,        # Disable graph features to reduce complexity
    storage_type="sqlite"      # Use SQLite instead of ArangoDB for simpler deployment
)
```

## 7. Agent Memory API

The core API for agent integration includes:

### 7.1 Memory Storage and Retrieval

```python
# Initialize
memory = MemoryAgentClient.from_environment()

# Store memory
conversation_id = memory.store_exchange(
    user_message="User message",
    agent_response="Agent response",
    metadata={"importance": "high"}
)

# Retrieve conversation history
history = memory.get_conversation_history(conversation_id)

# Search memories
results = memory.search("search query", top_n=5)
```

### 7.2 Knowledge Graph Operations

```python
# Create relationships
memory.create_relationship(
    from_key="doc1",
    to_key="doc2", 
    relationship_type="relates_to",
    attributes={"confidence": 0.9}
)

# Traverse graph
traversal = memory.traverse_graph(
    start_key="doc1",
    direction="outbound",
    depth=2
)
```

### 7.3 Compaction Operations

```python
# Create compaction
compaction_id = memory.create_compaction(
    conversation_id="conv_123",
    method="summarize"
)

# Search compactions
results = memory.search_compactions("search query", top_n=3)
```

### 7.4 Contradiction Management

```python
# Detect contradictions
contradictions = memory.detect_contradictions("doc_123")

# Resolve contradiction
resolution = memory.resolve_contradiction(
    newer_edge="edge_123",
    older_edge="edge_456",
    strategy="newest_wins"
)
```

## 8. Best Practices for Agent Integration

1. **Use Session Management** - Maintain persistent sessions for each agent instance to avoid reconnection overhead.

2. **Implement Caching** - Enable caching for frequently accessed memories to improve response time.

3. **Use Async Operations** - For high-throughput applications, use the async API methods to avoid blocking.

4. **Implement Memory Rotation** - Set up automatic memory rotation to archive older, less relevant memories.

5. **Follow Least Privilege Principle** - Configure the system to use the minimal set of permissions needed.

6. **Implement Graceful Degradation** - Design your agent to function with reduced capabilities if some dependencies are missing.

7. **Use Compaction Strategically** - Apply different compaction methods based on conversation types and importance.

8. **Monitor Memory Usage** - Implement memory usage tracking to prevent excessive resource consumption.

9. **Implement Rate Limiting** - Add rate limiting for memory operations to prevent overloading the database.

10. **Ensure Proper Error Handling** - Implement robust error handling for all memory operations.
