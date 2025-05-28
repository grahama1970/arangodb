# ArangoDB Memory Bank Slash Commands

This directory contains slash command documentation for the ArangoDB Memory Bank CLI, making it easy to use from Claude Code and other AI-powered development environments.

## Available Commands

### Core Commands
- [`/project:arangodb`](arangodb.md) - Comprehensive CLI interface for all memory bank operations
- [`/project:quickstart`](quickstart.md) - Interactive guide for new users
- [`/project:health`](health.md) - System health check
- [`/project:llm-help`](llm-help.md) - AI-friendly command documentation

### Utility Commands
- [`/project:serve`](serve.md) - Start MCP server for AI tool integration
- [`/project:test`](test.md) - Run tests with comprehensive reporting
- [`/project:workflow`](workflow.md) - Common workflow patterns and automation

### Reference
- [`/project:terminal_commands`](terminal_commands.md) - Essential terminal commands reference

## Quick Start

1. **Check System Health**
   ```
   /project:health
   ```

2. **Interactive Tutorial**
   ```
   /project:quickstart
   ```

3. **View All Commands**
   ```
   /project:arangodb
   ```

## Command Categories

### Memory Operations
- Create, search, and manage conversation memories
- Episode management for conversation contexts
- Semantic search with vector embeddings

### Search Functions
- Semantic search using AI embeddings
- BM25 full-text search
- Keyword and tag-based filtering
- Graph traversal search

### Data Management
- CRUD operations for any collection
- Batch import/export
- Data validation and cleanup

### Graph Operations
- Relationship management
- Graph traversal
- Community detection
- Visualization generation

### Integration
- MCP server for AI tools
- Q&A generation for LLM training
- Agent communication protocols

## Usage Patterns

All commands follow consistent patterns:
```
/project:command [subcommand] [options]
```

Common options:
- `--output json|table|csv` - Output format
- `--limit N` - Limit results
- `--help` - Detailed help

## For AI Agents

Use `/project:llm-help` to get machine-readable command documentation:
```
/project:llm-help memory --output json
```

## Installation

```bash
# Install with pip
pip install arangodb-memory-bank

# Or with uv
uv add arangodb-memory-bank
```

## More Information

- [Project Repository](https://github.com/yourusername/arangodb-memory-bank)
- [Documentation](https://arangodb-memory-bank.readthedocs.io)
- [API Reference](https://arangodb-memory-bank.readthedocs.io/api)

---

*These slash commands are auto-generated and manually enhanced for the ArangoDB Memory Bank project.*