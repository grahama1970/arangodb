# ArangoDB D3.js Visualization System

A powerful graph visualization system for ArangoDB memory bank data using D3.js v7.

## Features

- **Multiple Layout Types**
  - Force-directed: Interactive physics-based layout for general networks
  - Hierarchical Tree: Collapsible tree with breadcrumb navigation
  - Radial: Space-efficient circular tree visualization
  - Sankey: Flow visualization for directed graphs

- **Intelligent Layout Selection**
  - LLM-powered recommendations using Gemini Flash 2.5
  - Automatic layout optimization based on graph structure
  - Natural language queries for visualization preferences

- **Performance Optimization**
  - Automatic optimization for large graphs (> 1000 nodes)
  - Multiple sampling strategies (degree, random, community)
  - Performance hints for rendering
  - Level-of-detail (LOD) support

- **Interactive Features**
  - Zoom and pan controls
  - Node dragging
  - Collapsible nodes (tree layouts)
  - Tooltips with metadata
  - Configurable physics simulation

- **Integration**
  - CLI commands via `memory visualize`
  - FastAPI server with REST and GraphQL
  - Direct Python API
  - ArangoDB query integration

## Installation

The visualization system is included with the ArangoDB memory bank:

```bash
uv install
```

## Quick Start

### CLI Usage

Generate a basic visualization:
```bash
memory visualize
```

Specify a layout:
```bash
memory visualize --layout tree
```

Query-based visualization:
```bash
memory visualize --query "concept: machine learning" --layout force
```

Start the visualization server:
```bash
memory visualize --server --port 8000
```

### Python API

```python
from arangodb.visualization.core.d3_engine import D3VisualizationEngine
from arangodb.visualization.core.data_transformer import DataTransformer

# Initialize
engine = D3VisualizationEngine()
transformer = DataTransformer()

# Transform ArangoDB data
graph_data = transformer.transform_graph_data({
    "vertices": vertices,
    "edges": edges
})

# Generate visualization
html = engine.generate_visualization(graph_data, layout="force")

# Save to file
with open("graph.html", "w") as f:
    f.write(html)
```

### With LLM Recommendations

```python
# Let LLM choose the best layout
html = engine.generate_with_recommendation(
    graph_data, 
    query="Show the hierarchical relationships"
)
```

## Architecture

```
visualization/
├── core/
│   ├── d3_engine.py          # Main visualization engine
│   ├── data_transformer.py   # ArangoDB to D3.js conversion
│   ├── llm_recommender.py    # LLM layout recommendations
│   └── performance_optimizer.py  # Large graph optimization
├── templates/
│   ├── force.html            # Force-directed layout
│   ├── tree.html             # Hierarchical tree layout
│   ├── radial.html           # Radial tree layout
│   └── sankey.html           # Sankey diagram
├── server/
│   └── visualization_server.py  # FastAPI server
└── cli/
    └── visualization_commands.py  # CLI integration
```

## Layout Types

### Force-Directed Layout
- Best for: General networks, social graphs, concept maps
- Features: Physics simulation, node dragging, dynamic positioning
- Controls: Link distance, charge force, collision detection

### Hierarchical Tree Layout
- Best for: Organizational charts, taxonomies, file systems
- Features: Collapsible nodes, breadcrumb navigation, orientation options
- Controls: Expand/collapse all, horizontal/vertical layout

### Radial Layout
- Best for: Large hierarchies, space-constrained displays
- Features: Circular arrangement, interactive rotation, zoom to subtree
- Controls: Angle span, radius adjustment, focus controls

### Sankey Diagram
- Best for: Flow visualization, resource allocation, process mapping
- Features: Flow quantities, draggable nodes, automatic layout
- Controls: Node alignment, padding, flow highlighting

## Performance

The system automatically optimizes large graphs:

- Graphs > 1000 nodes trigger optimization
- Sampling reduces to ~500 nodes by default
- Edge bundling for visual clarity
- Performance hints for rendering engine
- WebGL recommendation for very large graphs

### Manual Optimization

```python
from arangodb.visualization.core.performance_optimizer import (
    PerformanceOptimizer, 
    OptimizationConfig
)

config = OptimizationConfig(
    max_nodes=200,
    sampling_strategy="community",
    edge_bundling=True
)

optimizer = PerformanceOptimizer(config)
optimized_data = optimizer.optimize_graph(large_graph)
```

## Configuration

### VisualizationConfig Options

```python
config = VisualizationConfig(
    width=1200,
    height=800,
    layout="force",
    title="My Graph",
    node_color_field="group",
    node_size_field="importance",
    link_width_field="weight",
    physics_enabled=True,
    show_labels=True,
    enable_zoom=True,
    enable_drag=True,
    custom_settings={
        "link_distance": 100,
        "charge_force": -300
    }
)
```

## API Endpoints

### REST API

```http
POST /visualize
Content-Type: application/json

{
    "graph_data": {...},
    "layout": "force",
    "config": {...}
}
```

```http
POST /recommend
Content-Type: application/json

{
    "graph_data": {...},
    "query": "Show community structure"
}
```

### GraphQL Subscriptions

```graphql
subscription {
    visualizationUpdate(sessionId: "abc123") {
        graphData
        config
        timestamp
    }
}
```

## Development

### Running Tests

```bash
# Run all visualization tests
pytest tests/visualization/

# Run specific test
pytest tests/visualization/test_visualization_suite.py

# Run with coverage
pytest tests/visualization/ --cov=arangodb.visualization
```

### Adding New Layouts

1. Create template in `templates/`
2. Add layout method to `D3VisualizationEngine`
3. Update `LayoutType` literal
4. Add tests for new layout

### Custom Templates

Templates use Jinja2-style variables:

```html
<script>
    const data = {{ graph_data | tojson | safe }};
    const config = {{ config | tojson | safe }};
    
    // Your D3.js code here
</script>
```

## Examples

### Simple Network

```python
data = {
    "nodes": [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
        {"id": "3", "name": "Charlie"}
    ],
    "links": [
        {"source": "1", "target": "2"},
        {"source": "2", "target": "3"}
    ]
}

html = engine.generate_visualization(data)
```

### With ArangoDB Integration

```python
from arangodb.core.db_operations import DBOperations

db = DBOperations()
results = db.search_memories(query="concept: AI")

transformer = DataTransformer()
graph_data = transformer.transform_graph_data(results)

html = engine.generate_with_recommendation(
    graph_data,
    query="Show AI concept relationships"
)
```

## Troubleshooting

### Common Issues

1. **Blank Visualization**
   - Check browser console for errors
   - Verify data has correct structure
   - Ensure node IDs are unique

2. **Performance Issues**
   - Enable optimization for large graphs
   - Reduce node count through sampling
   - Disable animations
   - Consider WebGL renderer

3. **Layout Problems**
   - Verify data hierarchy for tree layouts
   - Check for cycles in directed graphs
   - Ensure edge weights are valid

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or with loguru
from loguru import logger
logger.add("debug.log", level="DEBUG")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Documentation: [docs/guides/visualization_guide.md](../../docs/guides/visualization_guide.md)
- API Reference: [docs/api/visualization_api.md](../../docs/api/visualization_api.md)
- Issues: GitHub Issues