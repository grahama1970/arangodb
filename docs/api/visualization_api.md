# Visualization API Reference

## Table of Contents

1. [D3VisualizationEngine](#d3visualizationengine)
2. [DataTransformer](#datatransformer)
3. [LLMRecommender](#llmrecommender)
4. [PerformanceOptimizer](#performanceoptimizer)
5. [VisualizationServer](#visualizationserver)
6. [CLI Commands](#cli-commands)
7. [Data Models](#data-models)

## D3VisualizationEngine

Main visualization engine for generating D3.js visualizations from graph data.

### Class: `D3VisualizationEngine`

```python
class D3VisualizationEngine:
    def __init__(
        self, 
        template_dir: Optional[Path] = None, 
        static_dir: Optional[Path] = None, 
        use_llm: bool = True,
        optimize_performance: bool = True
    )
```

#### Parameters:
- `template_dir`: Directory containing HTML templates (default: `templates/`)
- `static_dir`: Directory for static assets (default: `static/`)
- `use_llm`: Whether to use LLM for recommendations (default: `True`)
- `optimize_performance`: Whether to optimize large graphs (default: `True`)

### Methods

#### `generate_visualization()`

Generate a D3.js visualization from graph data.

```python
def generate_visualization(
    self, 
    graph_data: Dict[str, Any], 
    layout: LayoutType = "force",
    config: Optional[VisualizationConfig] = None
) -> str
```

**Parameters:**
- `graph_data`: Dictionary containing nodes and links
- `layout`: Type of layout ("force", "tree", "radial", "sankey")
- `config`: Optional configuration object

**Returns:** HTML string containing the complete visualization

**Example:**
```python
engine = D3VisualizationEngine()
html = engine.generate_visualization(
    {"nodes": [...], "links": [...]},
    layout="force"
)
```

#### `generate_with_recommendation()`

Generate visualization using LLM recommendation.

```python
def generate_with_recommendation(
    self, 
    graph_data: Dict[str, Any], 
    query: Optional[str] = None,
    base_config: Optional[VisualizationConfig] = None
) -> str
```

**Parameters:**
- `graph_data`: Graph data to visualize
- `query`: Optional user query for context
- `base_config`: Base configuration to override with LLM suggestions

**Returns:** HTML string with recommended visualization

## DataTransformer

Transforms ArangoDB graph data to D3.js format.

### Class: `DataTransformer`

```python
class DataTransformer:
    def __init__(self)
```

### Methods

#### `transform_arangodb_to_d3()`

Transform ArangoDB query results to D3.js format.

```python
def transform_arangodb_to_d3(
    self, 
    arangodb_data: Dict[str, Any],
    node_label_field: str = "name",
    edge_label_field: str = "relationship",
    include_metadata: bool = True,
    preprocessing_fn: Optional[Callable] = None
) -> Dict[str, Any]
```

**Parameters:**
- `arangodb_data`: Data from ArangoDB with vertices and edges
- `node_label_field`: Field to use for node labels
- `edge_label_field`: Field to use for edge labels
- `include_metadata`: Whether to include additional metadata
- `preprocessing_fn`: Optional preprocessing function

**Returns:** D3.js formatted data with nodes and links

## LLMRecommender

LLM-based visualization recommender for graph data.

### Class: `LLLMRecommender`

```python
class LLMRecommender:
    def __init__(
        self, 
        model_name: str = "vertex_ai/gemini-2.5-flash",
        temperature: float = 0.1
    )
```

### Methods

#### `get_recommendation()`

Get visualization recommendation based on graph structure.

```python
def get_recommendation(
    self, 
    graph_data: Dict[str, Any], 
    query: Optional[str] = None
) -> VisualizationRecommendation
```

**Parameters:**
- `graph_data`: Graph data to analyze
- `query`: Optional user query for context

**Returns:** `VisualizationRecommendation` object

## PerformanceOptimizer

Optimize graph visualizations for performance.

### Class: `PerformanceOptimizer`

```python
class PerformanceOptimizer:
    def __init__(self, config: Optional[OptimizationConfig] = None)
```

### Methods

#### `optimize_graph()`

Optimize a graph for visualization performance.

```python
def optimize_graph(self, graph_data: Dict[str, Any]) -> Dict[str, Any]
```

**Parameters:**
- `graph_data`: Graph data to optimize

**Returns:** Optimized graph data with performance hints

#### `get_lod_level()`

Get level of detail based on zoom level.

```python
def get_lod_level(
    self, 
    zoom_level: float, 
    node_count: int
) -> Literal["high", "medium", "low"]
```

## VisualizationServer

FastAPI server for serving visualizations.

### Endpoints

#### `POST /visualize`

Generate a visualization.

**Request Body:**
```json
{
    "graph_data": {
        "nodes": [...],
        "links": [...]
    },
    "layout": "force",
    "config": {
        "width": 1200,
        "height": 800
    }
}
```

**Response:**
```json
{
    "html": "<html>...</html>",
    "config": {...},
    "stats": {
        "nodes": 100,
        "edges": 200,
        "generation_time": 0.5
    }
}
```

#### `POST /recommend`

Get layout recommendation.

**Request Body:**
```json
{
    "graph_data": {...},
    "query": "Show hierarchical structure"
}
```

**Response:**
```json
{
    "layout_type": "tree",
    "reason": "Graph has clear hierarchical structure",
    "title": "Hierarchical Organization",
    "config_overrides": {...}
}
```

#### `GET /layouts`

Get available layout types.

**Response:**
```json
{
    "layouts": [
        {
            "id": "force",
            "name": "Force-Directed",
            "description": "Physics-based layout for general networks"
        },
        ...
    ]
}
```

## CLI Commands

### `memory visualize`

Generate graph visualizations from memory bank data.

```bash
memory visualize [OPTIONS]
```

**Options:**
- `--query TEXT`: Search query for data
- `--layout TEXT`: Layout type (force/tree/radial/sankey)
- `--output PATH`: Output file path
- `--from-file PATH`: Load data from JSON file
- `--server`: Start visualization server
- `--port INT`: Server port (default: 8000)
- `--title TEXT`: Visualization title
- `--width INT`: Canvas width
- `--height INT`: Canvas height
- `--no-open-browser`: Don't open browser automatically

**Examples:**
```bash
# Basic visualization
memory visualize

# Specific layout with query
memory visualize --query "concept: AI" --layout tree

# Start server
memory visualize --server --port 8000

# Save to file
memory visualize --output graph.html --no-open-browser
```

## Data Models

### VisualizationConfig

Configuration for visualization generation.

```python
@dataclass
class VisualizationConfig:
    width: int = 960
    height: int = 600
    layout: LayoutType = "force"
    theme: str = "default"
    title: Optional[str] = None
    node_color_field: Optional[str] = None
    node_size_field: Optional[str] = None
    link_width_field: Optional[str] = None
    physics_enabled: bool = True
    show_labels: bool = True
    enable_zoom: bool = True
    enable_drag: bool = True
    llm_optimized: bool = False
    tree_orientation: TreeOrientation = "horizontal"
    node_radius: int = 8
    node_color: str = "#steelblue"
    link_color: str = "#999"
    animations: bool = True
    radius: int = 500
    angle_span: List[float] = [0, 2 * 3.14159]
    node_padding: int = 20
    node_alignment: str = "justify"
    custom_settings: Dict[str, Any] = field(default_factory=dict)
```

### OptimizationConfig

Configuration for performance optimization.

```python
@dataclass
class OptimizationConfig:
    max_nodes: int = 500
    max_edges: int = 2000
    sampling_strategy: Literal["degree", "random", "community"] = "degree"
    sample_size: int = 10
    edge_bundling: bool = True
    node_clustering: bool = True
    use_viewport_culling: bool = True
    progressive_loading: bool = False
```

### VisualizationRecommendation

LLM recommendation result.

```python
@dataclass
class VisualizationRecommendation:
    layout_type: LayoutType
    reason: str
    title: str
    config_overrides: Dict[str, Any]
    confidence: float
```

### GraphData Format

Standard graph data format:

```python
{
    "nodes": [
        {
            "id": "unique_id",
            "name": "Display Name",
            "group": 1,  # Optional grouping
            "size": 10,  # Optional size
            # ... additional properties
        }
    ],
    "links": [
        {
            "source": "node_id_1",
            "target": "node_id_2",
            "value": 1,  # Optional weight
            # ... additional properties
        }
    ],
    "metadata": {  # Optional
        "created_at": "2024-01-01",
        "description": "Graph description"
    }
}
```

### ArangoDB Data Format

Input format from ArangoDB:

```python
{
    "vertices": [
        {
            "_id": "collection/key",
            "_key": "key",
            "name": "Node Name",
            # ... vertex properties
        }
    ],
    "edges": [
        {
            "_id": "edges/key",
            "_from": "collection/source_key",
            "_to": "collection/target_key",
            "relationship": "connects_to",
            # ... edge properties
        }
    ]
}
```

## Error Handling

### Common Exceptions

```python
class VisualizationError(Exception):
    """Base exception for visualization errors"""

class InvalidGraphDataError(VisualizationError):
    """Raised when graph data is invalid"""

class TemplateNotFoundError(VisualizationError):
    """Raised when template file is missing"""

class OptimizationError(VisualizationError):
    """Raised when optimization fails"""
```

### Error Responses

API error responses follow this format:

```json
{
    "error": {
        "type": "InvalidGraphDataError",
        "message": "Graph data must contain 'nodes' and 'links' keys",
        "details": {...}
    }
}
```

## Performance Considerations

### Large Graph Handling

1. **Automatic Optimization**: Graphs > 1000 nodes are automatically optimized
2. **Sampling Strategies**: 
   - `degree`: Preserves high-degree nodes (hubs)
   - `random`: Random sampling
   - `community`: Community-aware sampling
3. **Performance Hints**: Generated for rendering optimization

### Best Practices

```python
# For large graphs
config = VisualizationConfig(
    show_labels=False,  # Hide labels for performance
    animations=False,   # Disable animations
    custom_settings={
        "use_webgl": True,          # Use WebGL if available
        "progressive_loading": True  # Load data progressively
    }
)

# Custom optimization
optimizer = PerformanceOptimizer(
    OptimizationConfig(
        max_nodes=200,  # Aggressive sampling
        sampling_strategy="community"
    )
)
```

## Examples

### Complete Example

```python
from arangodb.visualization.core.d3_engine import D3VisualizationEngine
from arangodb.visualization.core.data_transformer import DataTransformer
from arangodb.core.db_operations import DBOperations

# Query data
db = DBOperations()
results = db.search_memories(query="concept: machine learning")

# Transform data
transformer = DataTransformer()
graph_data = transformer.transform_arangodb_to_d3(results)

# Generate visualization with LLM
engine = D3VisualizationEngine()
html = engine.generate_with_recommendation(
    graph_data,
    query="Show ML concept relationships"
)

# Save to file
with open("ml_concepts.html", "w") as f:
    f.write(html)

print(f"Visualization saved to ml_concepts.html")
```

### Server Example

```python
from fastapi import FastAPI
from arangodb.visualization.server.visualization_server import app

# Run with: uvicorn app:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Custom Layout Example

```python
# Custom tree layout
config = VisualizationConfig(
    layout="tree",
    tree_orientation="vertical",
    node_radius=10,
    node_color="#ff6b6b",
    link_color="#4ecdc4",
    animations=True,
    custom_settings={
        "node_spacing": 50,
        "level_spacing": 100
    }
)

html = engine.generate_visualization(data, config=config)
```