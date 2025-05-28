# Start ArangoDB MCP Server

Serve the ArangoDB Memory Bank CLI as an MCP (Model Context Protocol) server for integration with AI tools.

## Usage

```bash
python -m arangodb.cli.main serve-mcp
```

## Examples

```bash
# In Claude Code:
/project:serve

# Start with default configuration
/project:serve

# Use custom configuration file
/project:serve --config custom_mcp.json

# Start on custom port
/project:serve --port 5001

# Enable debug mode
/project:serve --debug

# Specify host and port
/project:serve --host 0.0.0.0 --port 5000
```

## Configuration

Before starting the server, generate a configuration file:

```bash
# Generate default config
python -m arangodb.cli.main generate-mcp-config

# Generate with custom settings
python -m arangodb.cli.main generate-mcp-config \
  --name "arangodb-memory" \
  --port 5001 \
  --output custom_mcp.json
```

## Integration

The MCP server exposes all CLI commands as tools that can be called by AI agents:

- 66 tools available including all memory, search, CRUD, and graph operations
- JSON-based request/response format
- Async execution with proper error handling
- Output capture for all CLI operations

## Endpoints

Once running, the server provides:
- `http://localhost:5000/mcp` - Main MCP endpoint
- `http://localhost:5000/health` - Health check endpoint

---
*Auto-generated slash command*