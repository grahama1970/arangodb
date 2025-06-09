# ArangoDB Memory Bank CLI Guide

## Quick Start

```bash
# Install
pip install -e .

# Basic usage
python -m arangodb.cli [COMMAND] [OPTIONS]
```

## Most Used Commands

### 1. Generic CRUD (Works with ANY Collection)

```bash
# List documents from any collection
python -m arangodb.cli generic list <collection> --output json --limit 10

# Create document with auto-embedding
python -m arangodb.cli generic create <collection> '{"key": "value"}'

# Examples
python -m arangodb.cli generic list glossary --output json
python -m arangodb.cli generic create notes '{"title": "Meeting", "content": "AI discussion"}'
```

### 2. Search Commands

```bash
# BM25 text search
python -m arangodb.cli search bm25 <query>

# Semantic search (concept-based)
python -m arangodb.cli search semantic <query>

# Examples
python -m arangodb.cli search bm25 "database indexing"
python -m arangodb.cli search semantic "machine learning concepts"
```

### 3. Memory & Episodes

```bash
# Store conversation
python -m arangodb.cli memory store --user-input "question" --agent-response "answer"

# List episodes
python -m arangodb.cli episode list

# Create episode
python -m arangodb.cli episode create --user-message "Hello" --agent-message "Hi!" --summary "Greeting"
```

### 4. Communities & Relationships

```bash
# List communities
python -m arangodb.cli community list

# Detect communities
python -m arangodb.cli community detect

# Traverse relationships
python -m arangodb.cli graph traverse --lesson-id <id>
```

## Command Reference

### Episode Commands
- `episode list` - List all episodes
- `episode create` - Create new episode
- `episode search` - Search episodes

### Community Commands
- `community list` - List all communities
- `community detect` - Run community detection
- `community get` - Get community details

### Search Commands (Position Args)
- `search bm25 <query>` - Text-based search
- `search semantic <query>` - Concept-based search
- `search keyword <query>` - Keyword search

### Memory Commands
- `memory store` - Store conversation
- `memory search` - Search memory
- `memory list` - List memories

### Graph Commands
- `graph traverse` - Traverse relationships
- `graph add-relationship` - Add relationship
- `graph list-relationships` - List relationships

### Contradiction Commands
- `contradiction list` - List contradictions
- `contradiction check` - Check for contradictions
- `contradiction resolve` - Resolve contradiction

## Options

### Common Options
- `--output json|table` - Output format (default: table)
- `--limit N` - Limit results
- `--offset N` - Skip results
- `--help` - Get help

### Search Options
- No `--query` flag needed, just pass query directly
- Use quotes for multi-word queries

## Examples

### Complete Workflow

```bash
# 1. Create documents
python -m arangodb.cli generic create docs '{"title": "AI Basics", "content": "Introduction to AI"}'

# 2. Search for content
python -m arangodb.cli search semantic "artificial intelligence"

# 3. Store conversation
python -m arangodb.cli memory store --user-input "What is AI?" --agent-response "AI is..."

# 4. List episodes
python -m arangodb.cli episode list --output json
```

### Working with JSON Output

```bash
# Get JSON for processing
python -m arangodb.cli generic list glossary --output json | jq '.'

# Filter results
python -m arangodb.cli search semantic "ML algorithms" | jq '.results[:5]'
```

## Tips & Best Practices

1. **Use Generic Commands** - They work with any collection
2. **JSON for Scripts** - Use `--output json` for automation
3. **Auto-Embedding** - Enabled by default for text fields
4. **Check Help** - Use `--help` on any command

## Common Issues

### "No such command" Error
- Check spelling (use hyphens not underscores)
- Some commands are subcommands: `episode list` not just `list`

### Parameter Errors
- Search commands: Don't use `--query`, just pass query directly
- Generic commands: Collection name is required first argument
- JSON data: Use single quotes around JSON

## Version Notes

- **v2.0.0**: Migrated to consistent patterns (backward compatible)
- **v1.0.0**: Initial release

---
*Last updated: 2025-05-17*