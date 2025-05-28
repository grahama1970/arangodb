# ArangoDB Memory Bank CLI Commands

Comprehensive CLI interface for managing memories, episodes, and knowledge graphs in ArangoDB.

## Setup and Configuration

### Initial Setup
/project:quickstart
Description: Interactive guide to get started with ArangoDB Memory Bank
```bash
python -m arangodb.cli.main quickstart
```

### Health Check
/project:health  
Description: Verify database connection and system status
Arguments:
  - --output: Output format (json/text)
```bash
# Check system health
python -m arangodb.cli.main health

# Get JSON health report
python -m arangodb.cli.main health --output json
```

### LLM Integration Help
/project:llm-help [command]
Description: Get AI-friendly command documentation
Arguments:
  - command: Specific command to document (optional)
  - --output: Output format (json/text)
```bash
# Get general CLI structure
python -m arangodb.cli.main llm-help

# Get specific command help
python -m arangodb.cli.main llm-help memory --output json
```

## Memory Operations

### Create Memory
/project:memory-create --user "text" --agent "text"
Description: Store a new memory in the system
Arguments:
  - --user: User message content
  - --agent: Agent response content  
  - --conversation-id: Conversation identifier
  - --metadata: Additional metadata as JSON
  - --output: Output format (json/table)
```bash
# Basic memory creation
python -m arangodb.cli.main memory create --user "What is ArangoDB?" --agent "ArangoDB is a multi-model database"

# With conversation ID
python -m arangodb.cli.main memory create --user "Tell me more" --agent "It supports documents, graphs, and key-value" --conversation-id conv123

# With metadata
python -m arangodb.cli.main memory create --user "Question" --agent "Answer" --metadata '{"topic": "databases", "importance": "high"}'
```

### List Memories
/project:memory-list [options]
Description: List stored memories with filtering
Arguments:
  - --conversation-id: Filter by conversation
  - --limit: Number of results
  - --offset: Skip first N results
  - --output: Output format (json/table/csv)
```bash
# List recent memories
python -m arangodb.cli.main memory list

# Filter by conversation
python -m arangodb.cli.main memory list --conversation-id conv123 --limit 10

# Export as JSON
python -m arangodb.cli.main memory list --output json > memories.json
```

### Search Memories
/project:memory-search --query "text"
Description: Search memories using semantic similarity
Arguments:
  - --query: Search query text
  - --limit: Number of results  
  - --threshold: Similarity threshold (0-1)
  - --output: Output format
```bash
# Basic search
python -m arangodb.cli.main memory search --query "database features"

# With threshold
python -m arangodb.cli.main memory search --query "ArangoDB capabilities" --threshold 0.8

# Top 5 results as JSON
python -m arangodb.cli.main memory search --query "multi-model" --limit 5 --output json
```

### Get Memory History
/project:memory-history [options]
Description: View conversation history
Arguments:
  - --conversation-id: Specific conversation
  - --limit: Number of messages
  - --format: Output format (chat/json/table)
```bash
# Recent history
python -m arangodb.cli.main memory history

# Specific conversation
python -m arangodb.cli.main memory history --conversation-id conv123

# Export chat format
python -m arangodb.cli.main memory history --format chat --limit 50
```

## Search Operations

### Semantic Search
/project:search-semantic --query "text"
Description: Find documents using AI embeddings
Arguments:
  - --query: Search query
  - --collection: Target collection
  - --threshold: Similarity threshold
  - --limit: Number of results
  - --tags: Filter by tags
```bash
# Search across all collections
python -m arangodb.cli.main search semantic --query "machine learning concepts"

# Search specific collection
python -m arangodb.cli.main search semantic --query "neural networks" --collection documents

# With tag filtering
python -m arangodb.cli.main search semantic --query "databases" --tags "technical,tutorial"
```

### BM25 Text Search
/project:search-bm25 --query "text"
Description: Full-text search using BM25 algorithm
Arguments:
  - --query: Search terms
  - --collection: Target collection
  - --limit: Number of results
```bash
# Basic BM25 search
python -m arangodb.cli.main search bm25 --query "graph database"

# Search in specific collection
python -m arangodb.cli.main search bm25 --query "multi model" --collection articles --limit 20
```

### Keyword Search
/project:search-keyword --query "text"
Description: Exact keyword matching
Arguments:
  - --query: Keywords to match
  - --collection: Target collection
  - --fields: Fields to search in
```bash
# Simple keyword search
python -m arangodb.cli.main search keyword --query "ArangoDB"

# Search specific fields
python -m arangodb.cli.main search keyword --query "tutorial" --fields "title,tags"
```

### Tag Search
/project:search-tag --tags "tag1,tag2"
Description: Find documents by tags
Arguments:
  - --tags: Comma-separated tags
  - --match-all: Require all tags (default: any)
  - --collection: Target collection
```bash
# Search by single tag
python -m arangodb.cli.main search tag --tags "database"

# Multiple tags (any match)
python -m arangodb.cli.main search tag --tags "graph,nosql,distributed"

# Require all tags
python -m arangodb.cli.main search tag --tags "tutorial,beginner" --match-all
```

### Graph Traversal Search
/project:search-graph --start "key" 
Description: Search via graph relationships
Arguments:
  - --start: Starting node key
  - --direction: Traversal direction (outbound/inbound/any)
  - --max-depth: Maximum traversal depth
  - --collection: Edge collection
```bash
# Find related documents
python -m arangodb.cli.main search graph --start "doc123" --direction outbound

# Bidirectional search
python -m arangodb.cli.main search graph --start "user456" --direction any --max-depth 3

# Using specific edge collection
python -m arangodb.cli.main search graph --start "topic789" --collection references
```

## Episode Management

### Create Episode
/project:episode-create --user-id "id" --description "text"
Description: Start a new conversation episode
Arguments:
  - --user-id: User identifier
  - --description: Episode description
  - --metadata: Additional metadata as JSON
```bash
# Basic episode
python -m arangodb.cli.main episode create --user-id user123 --description "Database discussion"

# With metadata
python -m arangodb.cli.main episode create --user-id user456 --description "Learning session" --metadata '{"topic": "graphs"}'
```

### List Episodes
/project:episode-list [options]
Description: View all episodes
Arguments:
  - --user-id: Filter by user
  - --active: Show only active episodes
  - --limit: Number of results
```bash
# All episodes
python -m arangodb.cli.main episode list

# User's episodes
python -m arangodb.cli.main episode list --user-id user123

# Active episodes only
python -m arangodb.cli.main episode list --active --limit 10
```

### End Episode
/project:episode-end "episode_id"
Description: Mark episode as completed
Arguments:
  - episode_id: Episode identifier
```bash
python -m arangodb.cli.main episode end episode789
```

## Graph Operations

### Add Relationship
/project:graph-add --from "key1" --to "key2" --type "relation"
Description: Create graph edge between nodes
Arguments:
  - --from: Source node key
  - --to: Target node key
  - --type: Relationship type
  - --weight: Edge weight (0-1)
  - --metadata: Additional properties
```bash
# Basic relationship
python -m arangodb.cli.main graph add --from doc1 --to doc2 --type "references"

# With weight
python -m arangodb.cli.main graph add --from user1 --to topic1 --type "interested_in" --weight 0.8

# With metadata
python -m arangodb.cli.main graph add --from concept1 --to concept2 --type "related" --metadata '{"strength": "strong"}'
```

### Traverse Graph
/project:graph-traverse --start "key"
Description: Explore graph relationships
Arguments:
  - --start: Starting node
  - --direction: Direction (outbound/inbound/any)
  - --max-depth: Maximum depth
  - --min-depth: Minimum depth
```bash
# Outbound traversal
python -m arangodb.cli.main graph traverse --start doc123 --direction outbound

# Find all connections
python -m arangodb.cli.main graph traverse --start user456 --direction any --max-depth 3

# Specific depth range
python -m arangodb.cli.main graph traverse --start topic789 --min-depth 2 --max-depth 4
```

## Community Detection

### Detect Communities
/project:community-detect [options]
Description: Find clusters in the graph
Arguments:
  - --algorithm: Detection algorithm (louvain/label_propagation)
  - --resolution: Resolution parameter for louvain
  - --min-size: Minimum community size
```bash
# Basic detection
python -m arangodb.cli.main community detect

# With parameters
python -m arangodb.cli.main community detect --algorithm louvain --resolution 1.5

# Filter small communities
python -m arangodb.cli.main community detect --min-size 5
```

### List Communities
/project:community-list [options]
Description: View detected communities
Arguments:
  - --sort-by: Sort field (size/id)
  - --min-size: Minimum size filter
```bash
# All communities
python -m arangodb.cli.main community list

# Large communities only
python -m arangodb.cli.main community list --min-size 10 --sort-by size
```

## CRUD Operations

### Create Document
/project:crud-create "collection" 'data'
Description: Insert document into any collection
Arguments:
  - collection: Target collection name
  - data: JSON document data
  - --key: Custom document key
  - --embed: Generate embeddings
```bash
# Basic creation
python -m arangodb.cli.main crud create articles '{"title": "Graph Databases", "content": "..."}'

# With custom key
python -m arangodb.cli.main crud create users '{"name": "Alice", "email": "alice@example.com"}' --key user123

# With embedding generation
python -m arangodb.cli.main crud create documents '{"text": "Important content"}' --embed
```

### Read Document
/project:crud-read "collection" "key"
Description: Retrieve document by key
Arguments:
  - collection: Collection name
  - key: Document key
```bash
python -m arangodb.cli.main crud read articles article456
```

### Update Document  
/project:crud-update "collection" "key" 'data'
Description: Update existing document
Arguments:
  - collection: Collection name
  - key: Document key
  - data: Update data (JSON)
  - --replace: Replace entire document
```bash
# Partial update
python -m arangodb.cli.main crud update users user123 '{"email": "newemail@example.com"}'

# Full replacement
python -m arangodb.cli.main crud update articles article456 '{"title": "New Title", "content": "New content"}' --replace
```

### Delete Document
/project:crud-delete "collection" "key"
Description: Remove document
Arguments:
  - collection: Collection name
  - key: Document key
  - --force: Skip confirmation
```bash
# With confirmation
python -m arangodb.cli.main crud delete users user123

# Force delete
python -m arangodb.cli.main crud delete articles article456 --force
```

### List Documents
/project:crud-list "collection"
Description: List collection documents
Arguments:
  - collection: Collection name
  - --limit: Number of results
  - --offset: Skip first N
  - --filter: AQL filter expression
```bash
# Basic listing
python -m arangodb.cli.main crud list users

# With pagination
python -m arangodb.cli.main crud list articles --limit 20 --offset 40

# With filtering
python -m arangodb.cli.main crud list documents --filter "doc.type == 'tutorial'"
```

## Visualization

### Generate Visualization
/project:visualize-generate [options]
Description: Create D3.js graph visualizations
Arguments:
  - --collection: Source collection
  - --layout: Layout type (force/tree/radial/sankey)
  - --query: Custom AQL query
  - --limit: Node limit
  - --output: Output file path
```bash
# Basic force layout
python -m arangodb.cli.main visualize generate --layout force

# From specific collection
python -m arangodb.cli.main visualize generate --collection entities --layout radial

# Custom query visualization
python -m arangodb.cli.main visualize generate --query "FOR v, e IN 1..2 OUTBOUND 'users/user1' GRAPH 'memory_graph' RETURN {node: v, edge: e}"

# Save to file
python -m arangodb.cli.main visualize generate --layout tree --output graph.html
```

### Serve Visualization
/project:visualize-serve [options]
Description: Start visualization web server
Arguments:
  - --port: Server port
  - --host: Host address
```bash
# Start server
python -m arangodb.cli.main visualize serve

# Custom port
python -m arangodb.cli.main visualize serve --port 8080
```

## Q&A Generation

### Generate Q&A Pairs
/project:qa-generate --input "file"
Description: Create Q&A pairs for LLM training
Arguments:
  - --input: Input document/collection
  - --output: Output file path
  - --format: Output format (json/jsonl)
  - --model: LLM model to use
```bash
# From document
python -m arangodb.cli.main qa generate --input document.txt --output qa_pairs.json

# From collection
python -m arangodb.cli.main qa generate --input memories --format jsonl

# With specific model
python -m arangodb.cli.main qa generate --input articles --model gpt-4 --output training_data.json
```

## Common Workflows

### 1. Memory Storage and Retrieval
```bash
# Store conversation
/project:memory-create --user "What is graph theory?" --agent "Graph theory studies relationships between objects"
/project:memory-create --user "Give an example" --agent "Social networks are a common example" --conversation-id conv1

# Search related memories
/project:memory-search --query "graph relationships"

# View conversation history
/project:memory-history --conversation-id conv1
```

### 2. Document Management with Search
```bash
# Add documents
/project:crud-create documents '{"title": "ArangoDB Guide", "content": "...", "tags": ["database", "nosql"]}'
/project:crud-create documents '{"title": "Graph Algorithms", "content": "...", "tags": ["algorithms", "graph"]}'

# Search semantically
/project:search-semantic --query "database algorithms"

# Search by tags
/project:search-tag --tags "graph" --match-all
```

### 3. Knowledge Graph Building
```bash
# Create entities
/project:crud-create entities '{"name": "Machine Learning", "type": "topic"}'
/project:crud-create entities '{"name": "Neural Networks", "type": "concept"}'

# Add relationships
/project:graph-add --from "entities/machine-learning" --to "entities/neural-networks" --type "includes"

# Explore connections
/project:graph-traverse --start "entities/machine-learning" --direction outbound

# Detect communities
/project:community-detect --min-size 3
```

### 4. Episode-Based Conversations
```bash
# Start episode
/project:episode-create --user-id user123 --description "Learning about databases"

# Add memories to episode
/project:memory-create --user "What are multi-model databases?" --agent "They support multiple data models" --conversation-id episode123

# End episode
/project:episode-end episode123

# Review episodes
/project:episode-list --user-id user123
```

## Integration Examples

### With LLM Agents
```bash
# Get command structure for agents
/project:llm-help memory --output json > memory_commands.json

# Health check before operations
/project:health --output json

# Structured memory storage
/project:memory-create --user "$USER_INPUT" --agent "$LLM_RESPONSE" --metadata '{"model": "gpt-4", "timestamp": "2024-01-26"}'
```

### Batch Operations
```bash
# Export memories
/project:memory-list --output json > all_memories.json

# Export search results
/project:search-semantic --query "important concepts" --limit 100 --output json > concepts.json

# List all episodes for analysis
/project:episode-list --output csv > episodes.csv
```

### Visualization Pipeline
```bash
# Generate visualization from search results
/project:search-graph --start "topics/ai" --direction any > graph_data.json
/project:visualize-generate --layout force --query "@graph_data.json"

# Serve the visualization
/project:visualize-serve --port 8080
```

## MCP Server Commands

### Generate MCP Configuration
/project:generate-mcp-config
Description: Create MCP server configuration
Arguments:
  - --output: Output file path
  - --name: Server name
  - --host: Server host
  - --port: Server port
```bash
# Generate config
python -m arangodb.cli.main generate-mcp-config --output mcp_config.json

# Custom configuration
python -m arangodb.cli.main generate-mcp-config --name "arangodb-memory" --port 5001
```

### Start MCP Server
/project:serve-mcp
Description: Run the MCP server
Arguments:
  - --config: Config file path
  - --host: Server host
  - --port: Server port
  - --debug: Enable debug mode
```bash
# Start with default config
python -m arangodb.cli.main serve-mcp

# Custom config
python -m arangodb.cli.main serve-mcp --config custom_mcp.json --debug
```

---

## Quick Reference

Common command patterns:
- Output formats: `--output json|table|csv`
- Pagination: `--limit N --offset M`
- Filtering: `--filter "expression"` or specific flags
- All commands support `--help` for detailed documentation

For AI agents:
- Use `/project:llm-help [command]` for structured command info
- All outputs can be JSON formatted for parsing
- Health check before operations: `/project:health --output json`

Installation:
```bash
# Install ArangoDB Memory Bank
pip install arangodb-memory-bank

# Or with uv
uv add arangodb-memory-bank
```