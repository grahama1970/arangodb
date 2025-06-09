# ArangoDB Memory Agent: Quick Reference Guide

This quick reference guide provides a concise overview of the ArangoDB Memory Agent CLI commands.

## Command Structure

All commands follow this structure:
```bash
python -m arangodb.cli [command_group] [command] [arguments] [options]
```

## Memory Commands

| Command | Description | Example |
|---------|-------------|---------|
| `memory store` | Store conversation exchange | `memory store --conversation-id "conv_123" --user-message "Hello" --agent-response "Hi"` |
| `memory get-history` | Retrieve conversation history | `memory get-history "conv_123"` |
| `memory search` | Search for relevant memories | `memory search "project deadline" --point-in-time "2023-05-01T12:00:00"` |

## Episode Commands

| Command | Description | Example |
|---------|-------------|---------|
| `episode create` | Create a new episode | `episode create "Project Discussion" --description "Meeting about new project"` |
| `episode list` | List all episodes | `episode list --limit 20` |
| `episode get` | Get details of an episode | `episode get "ep_123" --include-messages` |

## Search Commands

| Command | Description | Example |
|---------|-------------|---------|
| `search bm25` | Keyword-based search | `search bm25 "database design" --threshold 0.1 --top-n 5` |
| `search semantic` | Meaning-based search | `search semantic "how to improve performance" --threshold 0.75` |
| `search hybrid` | Combined search with reranking | `search hybrid "api authentication" --rerank --top-n 5` |

## Graph Commands

| Command | Description | Example |
|---------|-------------|---------|
| `graph create-relationship` | Create relationship between entities | `graph create-relationship --from-key "doc1" --to-key "doc2" --type "references"` |
| `graph traverse` | Traverse the graph | `graph traverse --start-key "doc1" --direction "outbound" --depth 2` |

## Compaction Commands

| Command | Description | Example |
|---------|-------------|---------|
| `compaction create` | Create compacted summary | `compaction create --conversation-id "conv_123" --method "summarize"` |
| `compaction search` | Search compacted summaries | `compaction search "project goals" --threshold 0.75` |
| `compaction get` | Get a specific compacted summary | `compaction get "cmp_123" --include-workflow` |
| `compaction list` | List compacted summaries | `compaction list --sort-by "reduction_ratio" --descending` |

## Community Commands

| Command | Description | Example |
|---------|-------------|---------|
| `community detect` | Run community detection | `community detect --algorithm "louvain" --min-community-size 3` |
| `community show` | Show community details | `community show --community-id "comm_123"` |

## Contradiction Commands

| Command | Description | Example |
|---------|-------------|---------|
| `contradiction detect` | Detect contradictions | `contradiction detect --document-id "doc_123"` |
| `contradiction resolve` | Resolve contradiction | `contradiction resolve "edge_123" "edge_456" --strategy "newest_wins"` |

## CRUD Commands

| Command | Description | Example |
|---------|-------------|---------|
| `crud create` | Create a document | `crud create --collection "documents" --content-json '{"title": "Example"}'` |
| `crud read` | Read a document | `crud read --document-id "documents/123456"` |
| `crud update` | Update a document | `crud update --document-id "documents/123456" --content-json '{"title": "Updated"}'` |
| `crud delete` | Delete a document | `crud delete --document-id "documents/123456"` |

## Search Configuration Commands

| Command | Description | Example |
|---------|-------------|---------|
| `search-config view create` | Create a search view | `search-config view create --name "custom_view" --collection "documents"` |
| `search-config view update` | Update a search view | `search-config view update --name "custom_view" --fields "title,content"` |
| `search-config analyzer list` | List available analyzers | `search-config analyzer list` |

## Common Options

Most commands support these options:

| Option | Description |
|--------|-------------|
| `--json-output` | Return results as JSON |
| `--help` | Show help for the command |

## Common Workflows

1. **Store and retrieve conversations**:
   ```bash
   # Create episode
   python -m arangodb.cli episode create "Project Discussion"
   
   # Store conversation
   python -m arangodb.cli memory store --episode-id "ep_abc123" --user-message "Question" --agent-response "Answer"
   
   # Retrieve history
   python -m arangodb.cli memory get-history "conv_def456"
   ```

2. **Search for information**:
   ```bash
   # Semantic search
   python -m arangodb.cli search semantic "performance optimization techniques"
   
   # Hybrid search with reranking
   python -m arangodb.cli search hybrid "database indexing strategies" --rerank
   ```

3. **Create and search compacted summaries**:
   ```bash
   # Create compaction
   python -m arangodb.cli compaction create --conversation-id "conv_123" --method "extract_key_points"
   
   # Search compactions
   python -m arangodb.cli compaction search "project timeline"
   ```

4. **Build knowledge graph**:
   ```bash
   # Create relationships
   python -m arangodb.cli graph create-relationship --from-key "doc1" --to-key "doc2" --type "references"
   
   # Traverse graph
   python -m arangodb.cli graph traverse --start-key "doc1" --depth 2
   ```

5. **Detect and resolve contradictions**:
   ```bash
   # Detect contradictions
   python -m arangodb.cli contradiction detect --document-id "doc_123"
   
   # Resolve contradiction
   python -m arangodb.cli contradiction resolve "edge_123" "edge_456" --strategy "newest_wins"
   ```

6. **Community detection**:
   ```bash
   # Run community detection
   python -m arangodb.cli community detect --algorithm "louvain"
   
   # Show community details
   python -m arangodb.cli community show --community-id "comm_123"
   ```

Refer to the full documentation for more detailed information on each command and its options.
