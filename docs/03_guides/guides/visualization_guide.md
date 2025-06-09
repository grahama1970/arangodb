# ArangoDB D3.js Visualization Guide

## Overview

The ArangoDB visualization system provides interactive graph visualizations using D3.js v7. It supports multiple layout types, LLM-driven recommendations, and performance optimization for large datasets.

## Features

- **Multiple Layout Types**: Force-directed, hierarchical tree, radial, and Sankey diagrams
- **LLM Integration**: Automatic layout recommendations using Gemini Flash 2.5
- **Performance Optimization**: Automatic optimization for graphs > 1000 nodes
- **Interactive Controls**: Physics simulation, zoom/pan, node dragging
- **CLI Integration**: Easy access through `memory visualize` command
- **FastAPI Server**: REST API and GraphQL subscriptions for real-time updates

## Installation

The visualization system is included with the ArangoDB memory bank installation:

```bash
uv install
```

## CLI Usage

### Basic Visualization

Generate a default force-directed visualization:

```bash
memory visualize
```

### Specify Layout Type

```bash
memory visualize --layout tree
memory visualize --layout radial
memory visualize --layout sankey
```

### Query-Based Visualization

Visualize specific query results:

```bash
memory visualize --query "concept: machine learning" --layout force
```

### File-Based Visualization

Visualize data from a JSON file:

```bash
memory visualize --from-file data.json --layout tree
```

### Advanced Options

```bash
memory visualize \
  --query "relationship: teaches" \
  --layout force \
  --title "Teaching Relationships" \
  --width 1200 \
  --height 800 \
  --output teaching_graph.html \
  --no-open-browser
```

### Start Visualization Server

Launch the FastAPI server for web access:

```bash
memory visualize --server --port 8000
```

Then access the API at `http://localhost:8000`

## Python API

### Basic Usage

```python
from arangodb.visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig
from arangodb.visualization.core.data_transformer import DataTransformer

# Initialize engine
engine = D3VisualizationEngine()

# Transform ArangoDB data
transformer = DataTransformer()
graph_data = transformer.transform_arangodb_to_d3({
    "vertices": vertices,
    "edges": edges
})

# Generate visualization
config = VisualizationConfig(
    layout="force",
    title="My Graph",
    width=1200,
    height=800
)

html = engine.generate_visualization(graph_data, config=config)

# Save to file
with open("graph.html", "w") as f:
    f.write(html)
```

### With LLM Recommendations

```python
# Let LLM choose the best layout
html = engine.generate_with_recommendation(
    graph_data, 
    query="Show me the hierarchical structure"
)
```

### Performance Optimization

```python
# Automatic optimization for large graphs
config = VisualizationConfig(
    layout="force",
    title="Large Network"
)

# Graphs > 1000 nodes are automatically optimized
html = engine.generate_visualization(large_graph_data, config=config)
```

## Layout Types

### Force-Directed Layout

Best for general network visualization:
- Interactive physics simulation
- Draggable nodes
- Configurable physics parameters

```python
config = VisualizationConfig(
    layout="force",
    physics_enabled=True,
    enable_drag=True,
    custom_settings={
        "link_distance": 100,
        "charge_force": -300,
        "collision_radius": 20
    }
)
```

### Hierarchical Tree Layout

Ideal for organizational structures:
- Collapsible nodes
- Breadcrumb navigation
- Horizontal/vertical orientation

```python
config = VisualizationConfig(
    layout="tree",
    tree_orientation="horizontal",
    animations=True
)
```

### Radial Layout

Circular tree visualization:
- Space-efficient for large hierarchies
- Interactive rotation
- Focus on subtrees

```python
config = VisualizationConfig(
    layout="radial",
    radius=500,
    angle_span=[0, 2 * 3.14159]
)
```

### Sankey Diagram

Flow visualization:
- Shows quantities through a network
- Draggable nodes
- Automatic flow calculation

```python
config = VisualizationConfig(
    layout="sankey",
    node_padding=20,
    node_alignment="justify"
)
```

## Performance Optimization

### Automatic Optimization

Large graphs are automatically optimized:
- Graphs > 1000 nodes trigger optimization
- Sampling reduces to manageable size
- Performance hints applied to rendering

### Manual Configuration

```python
from arangodb.visualization.core.performance_optimizer import (
    PerformanceOptimizer, 
    OptimizationConfig
)

# Custom optimization settings
opt_config = OptimizationConfig(
    max_nodes=500,
    max_edges=2000,
    sampling_strategy="degree",  # or "random", "community"
    edge_bundling=True,
    node_clustering=False
)

optimizer = PerformanceOptimizer(opt_config)
optimized_data = optimizer.optimize_graph(large_graph)
```

### Performance Hints

The optimizer generates rendering hints:
- WebGL usage recommendations
- Animation settings
- Label visibility
- Renderer selection (SVG/Canvas)

## Server API

### REST Endpoints

```python
# Generate visualization
POST /visualize
{
    "graph_data": {...},
    "layout": "force",
    "config": {...}
}

# Get layout recommendations
POST /recommend
{
    "graph_data": {...},
    "query": "Show community structure"
}

# Get available layouts
GET /layouts
```

### GraphQL Subscriptions

```python
# Subscribe to real-time updates
subscription {
    visualizationUpdate(sessionId: "abc123") {
        graphData
        config
        timestamp
    }
}
```

## Advanced Features

### Custom Node Styling

```python
config = VisualizationConfig(
    node_color_field="group",     # Color nodes by group
    node_size_field="importance", # Size nodes by importance
    link_width_field="weight"     # Width links by weight
)
```

### Template Customization

Create custom D3.js templates:

```javascript
// In templates/custom.html
const svg = d3.select("#graph-container")
    .append("svg")
    .attr("width", config.width)
    .attr("height", config.height);

// Add custom behaviors
svg.on("click", function(event) {
    // Custom click handler
});
```

### Data Preprocessing

```python
# Custom data transformation
def preprocess_graph(graph_data):
    # Add custom attributes
    for node in graph_data["nodes"]:
        node["custom_prop"] = calculate_custom_property(node)
    
    return graph_data

transformed_data = transformer.transform_arangodb_to_d3(
    arangodb_data,
    preprocessing_fn=preprocess_graph
)
```

## Best Practices

1. **Choose the Right Layout**:
   - Force: General networks, no clear hierarchy
   - Tree: Clear parent-child relationships
   - Radial: Large hierarchies with space constraints
   - Sankey: Flow or quantity visualization

2. **Optimize for Performance**:
   - Use sampling for graphs > 1000 nodes
   - Disable animations for large datasets
   - Consider WebGL for very large graphs

3. **User Experience**:
   - Provide clear tooltips
   - Use color meaningfully
   - Include legends for groupings
   - Enable zoom/pan for exploration

4. **Data Preparation**:
   - Ensure unique node IDs
   - Include meaningful labels
   - Add metadata for tooltips
   - Validate edge references

## Troubleshooting

### Common Issues

1. **Blank Visualization**:
   - Check console for D3.js errors
   - Verify data structure (nodes/links)
   - Ensure valid node IDs

2. **Performance Problems**:
   - Enable performance optimization
   - Reduce node count with sampling
   - Disable animations
   - Use WebGL renderer

3. **Layout Issues**:
   - Verify data hierarchy for tree layouts
   - Check for cycles in directed graphs
   - Ensure valid edge weights for Sankey

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use loguru
from loguru import logger
logger.add("visualization_debug.log", level="DEBUG")
```

## Examples

### Simple Network

```python
# Create a simple network
data = {
    "nodes": [
        {"id": "1", "name": "Node A"},
        {"id": "2", "name": "Node B"},
        {"id": "3", "name": "Node C"}
    ],
    "links": [
        {"source": "1", "target": "2"},
        {"source": "2", "target": "3"}
    ]
}

html = engine.generate_visualization(data)
```

### Hierarchical Organization

```python
# Organization chart
data = {
    "nodes": [
        {"id": "ceo", "name": "CEO", "level": 0},
        {"id": "cto", "name": "CTO", "level": 1},
        {"id": "dev1", "name": "Developer 1", "level": 2},
        {"id": "dev2", "name": "Developer 2", "level": 2}
    ],
    "links": [
        {"source": "ceo", "target": "cto"},
        {"source": "cto", "target": "dev1"},
        {"source": "cto", "target": "dev2"}
    ]
}

config = VisualizationConfig(layout="tree", tree_orientation="vertical")
html = engine.generate_visualization(data, config=config)
```

### Flow Diagram

```python
# Resource flow
data = {
    "nodes": [
        {"id": "source", "name": "Source"},
        {"id": "process", "name": "Process"},
        {"id": "output", "name": "Output"}
    ],
    "links": [
        {"source": "source", "target": "process", "value": 100},
        {"source": "process", "target": "output", "value": 80}
    ]
}

config = VisualizationConfig(layout="sankey")
html = engine.generate_visualization(data, config=config)
```

## Integration with Memory Bank

The visualization system integrates seamlessly with the ArangoDB memory bank:

```python
from arangodb.core.db_operations import DBOperations

# Query memory bank
db = DBOperations()
results = db.search_memories(query="concept: AI")

# Visualize results
transformer = DataTransformer()
graph_data = transformer.transform_arangodb_to_d3(results)

# Generate visualization with LLM recommendation
html = engine.generate_with_recommendation(
    graph_data,
    query="Show AI concept relationships"
)
```

## Future Enhancements

Planned features for future releases:

1. **3D Visualizations**: Three.js integration for 3D graphs
2. **Real-time Updates**: WebSocket support for live data
3. **Advanced Layouts**: Chord diagrams, matrix views
4. **Export Options**: SVG, PNG, PDF export
5. **Collaborative Features**: Multi-user interaction
6. **Mobile Support**: Touch-optimized controls

## Support

For issues or questions:
- GitHub Issues: [arangodb/issues](https://github.com/arangodb/issues)
- Documentation: [docs/](../README.md)
- Examples: [examples/visualization/](../../examples/visualization/)

## License

MIT License - see LICENSE file for details