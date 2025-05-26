# Combined MCP Design for Inter-Module Communication

## Overview

This document describes how the ArangoDB Memory Bank project uses MCP (Model Context Protocol) to enable seamless inter-module communication with the agent as orchestrator. The fixed implementation now exposes all 61+ CLI commands as MCP tools.

## Architecture

### 1. MCP Server Generation

The `slash_mcp_mixin.py` automatically generates MCP configurations from Typer CLI commands:

```python
# Recursive traversal to capture all sub-commands
def get_all_tools(app_instance: typer.Typer, prefix: str = "") -> dict:
    """Recursively get all commands including sub-commands"""
    tools = {}
    
    # Process direct commands
    for command in app_instance.registered_commands:
        # Convert to MCP tool
    
    # Process sub-groups (critical for full exposure)
    for group_info in app_instance.registered_groups:
        sub_tools = get_all_tools(group_info.typer_instance, sub_prefix)
        tools.update(sub_tools)
    
    return tools
```

### 2. Inter-Module Communication Pattern

The optimal pattern for module orchestration:

```
Agent (Orchestrator)
    ├─> Marker MCP (PDF Extraction)
    │   └─> Sends extracted data
    │
    ├─> ArangoDB MCP (Storage & Processing)
    │   ├─> Stores documents
    │   ├─> Creates relationships
    │   └─> Generates Q&A pairs
    │
    └─> Visualization MCP (Graph Display)
        └─> Renders responsive D3 graphs
```

### 3. Example Workflow: PDF to Knowledge Graph

```bash
# 1. Agent extracts PDF using Marker
marker extract document.pdf --output json

# 2. Agent ingests into ArangoDB
arangodb qa ingest-from-marker marker_output.json

# 3. Agent generates Q&A pairs
arangodb qa generate --source documents/doc_123

# 4. Agent visualizes relationships
arangodb graph visualize --collection documents --layout force
```

### 4. MCP Tool Examples

The fixed implementation exposes all commands:

```json
{
  "tools": {
    "memory.add": "Add a memory to the system",
    "memory.search": "Search memories with various strategies",
    "graph.visualize": "Create responsive D3 visualizations",
    "qa.generate": "Generate Q&A pairs from documents",
    "qa.ingest-from-marker": "Ingest Marker PDF extraction",
    // ... 56+ more tools
  }
}
```

### 5. Agent Orchestration Capabilities

With the fixed MCP implementation, agents can:

1. **Chain Operations**: Extract PDF → Store → Generate Q&A → Visualize
2. **Parallel Processing**: Run multiple extractions simultaneously
3. **Cross-Module Queries**: Search memories while generating visualizations
4. **Conditional Workflows**: Check if document exists before processing

### 6. Implementation Details

#### Message Passing
Modules communicate via JSON messages stored in designated directories:
- `/messages/to_marker/` - Commands for Marker
- `/messages/from_marker/` - Results from Marker
- Agent polls and processes messages asynchronously

#### MCP Configuration
Generated automatically at:
- `~/.config/mcp/arangodb.json` - User configuration
- `./mcp.json` - Project configuration

#### Tool Discovery
Agents discover available tools through:
```bash
arangodb --mcp-generate-config
```

### 7. Best Practices

1. **Tool Naming**: Use dot notation for sub-commands (e.g., `memory.search`)
2. **Parameter Validation**: MCP enforces type checking from CLI annotations
3. **Error Handling**: Tools return structured errors for agent processing
4. **Async Operations**: Long-running tasks support progress callbacks

### 8. Testing Inter-Module Communication

```python
# Test script for verifying MCP integration
import json
import subprocess

def test_mcp_workflow():
    # 1. Generate MCP config
    subprocess.run(["arangodb", "--mcp-generate-config"])
    
    # 2. Verify tool count
    with open("mcp.json") as f:
        config = json.load(f)
        assert len(config["tools"]) > 60, "Not all tools exposed"
    
    # 3. Test tool execution via MCP
    result = subprocess.run([
        "mcp", "execute", "arangodb", 
        "memory.add", "--content", "Test memory"
    ], capture_output=True)
    
    assert result.returncode == 0
    print("✅ MCP integration working correctly")

if __name__ == "__main__":
    test_mcp_workflow()
```

## D3 Visualization MCP Integration

The visualization module is also exposed through MCP, enabling responsive graph generation:

### Responsive Design Features

All D3 visualizations now support:
- **Mobile** (< 768px): Simplified controls, touch gestures
- **Tablet** (768-1024px): Balanced layout, pinch-to-zoom
- **Desktop** (> 1024px): Full controls, mouse interactions

### Visualization Commands via MCP

```bash
# Generate responsive force-directed graph
arangodb graph visualize --collection memories --layout force

# Create hierarchical tree view
arangodb graph visualize --collection entities --layout tree

# Export graph data for custom visualization
arangodb graph export --format d3-json
```

### Touch Gesture Support

The responsive templates include:
- **Pinch to zoom**: Multi-touch scaling
- **Drag to pan**: Single finger movement
- **Double-tap**: Reset view to center
- **Touch-friendly controls**: Larger buttons for mobile

## Conclusion

The fixed MCP implementation enables true inter-module communication with:
- All 61+ CLI commands exposed as MCP tools
- Automatic configuration generation
- Support for complex agent-orchestrated workflows
- Integration with external tools like Marker
- Responsive D3 visualizations for all devices

This design allows agents to orchestrate complex workflows across multiple specialized tools while maintaining clean module boundaries.