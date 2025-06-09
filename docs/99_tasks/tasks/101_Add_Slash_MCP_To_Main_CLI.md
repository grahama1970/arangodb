# Task 101: Add Slash MCP To Main CLI

**Goal**: Integrate slash_mcp_mixin into ArangoDB's main CLI

## Current State
- Comprehensive CLI at src/arangodb/cli/main.py
- Multiple command groups (crud, search, memory, etc.)
- Complex nested structure needs MCP adaptation

## Implementation Steps

### Step 1: Create MCP-Enhanced Version

```python
# FILE: /home/graham/workspace/experiments/arangodb/src/arangodb/cli/main_mcp.py

import sys
from pathlib import Path

# Add claude_max_proxy to path
sys.path.insert(0, "/home/graham/workspace/experiments/claude_max_proxy/src")
from llm_call.cli.slash_mcp_mixin import add_slash_mcp_commands

# Import existing CLI app
from arangodb.cli.main import app

# Add MCP generation commands
add_slash_mcp_commands(app)

if __name__ == "__main__":
    app()
```

### Step 2: Test Existing Commands Work

```bash
cd /home/graham/workspace/experiments/arangodb
export ARANGO_HOST=localhost
export ARANGO_USERNAME=root  
export ARANGO_PASSWORD=openSesame

python src/arangodb/cli/main_mcp.py crud list documents
python src/arangodb/cli/main_mcp.py search semantic --query "test"
```

### Step 3: Generate MCP Configuration

```bash
python src/arangodb/cli/main_mcp.py generate-mcp-config --output arangodb_mcp.json
```

Note: This will generate a complex nested structure. May need simplification.

### Step 4: Create Simplified Interface (Optional)

For easier MCP usage, create flattened commands:

```python
# FILE: src/arangodb/cli/simple_mcp.py

import typer
from arangodb.core.db_manager import DatabaseManager

app = typer.Typer(name="arangodb-simple")

db = DatabaseManager().db

@app.command()
def create_entity(collection: str, data: str):
    """Create entity in collection."""
    import json
    doc = json.loads(data)
    result = db.collection(collection).insert(doc)
    return json.dumps({"success": True, "key": result["_key"]})

@app.command()
def search(query: str, collection: str = "documents"):
    """Search collection."""
    # Implementation
    pass

add_slash_mcp_commands(app)

if __name__ == "__main__":
    app()
```

## Validation Checklist

- [ ] Existing CLI commands still work
- [ ] MCP config generates successfully
- [ ] serve-mcp command available
- [ ] Can connect to ArangoDB
- [ ] Tools accessible via MCP protocol

## Next Steps

After basic MCP works, proceed to:
- Task 102: Create simplified interface
- Task 103: Fix async/sync issues
- Task 104: Add Natrium-specific operations