# LLM-Friendly Command Documentation

Generate structured command documentation optimized for AI agents and automation tools.

## Usage

```bash
python -m arangodb.cli.main llm-help [command]
```

## Examples

```bash
# In Claude Code:
/project:llm-help

# Get general CLI structure
/project:llm-help

# Get specific command documentation
/project:llm-help memory

# Get search command details in JSON
/project:llm-help search --output json

# Document CRUD operations
/project:llm-help crud --output json
```

## General Structure Output

When called without arguments, returns the overall CLI structure:

```json
{
  "cli_name": "arangodb",
  "pattern": "arangodb <resource> <action> [OPTIONS]",
  "resources": ["crud", "search", "memory", "episode", "community", "graph"],
  "common_options": {
    "--output": "json or table",
    "--limit": "number of results",
    "--help": "detailed help"
  },
  "examples": [
    "arangodb crud list users --output json",
    "arangodb search semantic --query 'topic' --collection docs",
    "arangodb memory create --user 'Q' --agent 'A'"
  ]
}
```

## Command-Specific Output

When called with a command name, returns detailed information:

```json
{
  "command": "memory",
  "pattern": "arangodb memory <action> [OPTIONS]",
  "actions": ["create", "list", "search", "get", "history"],
  "parameters": {
    "create": ["--user", "--agent", "--conversation-id", "--output"],
    "list": ["--output", "--limit", "--conversation-id"],
    "search": ["--query", "--output", "--limit"]
  }
}
```

## Available Commands

- `crud` - CRUD operations for any collection
- `search` - Multi-algorithm search operations
- `memory` - Conversation memory management
- `episode` - Episode lifecycle management
- `community` - Community detection and analysis
- `graph` - Graph traversal and relationships
- `compaction` - Memory compaction operations
- `contradiction` - Contradiction detection
- `temporal` - Time-based queries
- `visualize` - D3.js visualizations
- `qa` - Q&A pair generation
- `agent` - Inter-module communication

## Integration Tips

For AI agents:
1. First call without arguments to understand structure
2. Then call with specific commands for details
3. Use JSON output for easy parsing
4. Parameters are returned in order of importance

Example workflow:
```bash
# 1. Get overall structure
structure=$(python -m arangodb.cli.main llm-help --output json)

# 2. Get specific command details
memory_info=$(python -m arangodb.cli.main llm-help memory --output json)

# 3. Use the information to construct commands
python -m arangodb.cli.main memory create --user "Question" --agent "Answer"
```

---
*Auto-generated slash command*