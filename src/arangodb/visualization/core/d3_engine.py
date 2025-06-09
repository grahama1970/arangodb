"""D3.js Visualization Engine for ArangoDB
Module: d3_engine.py

This module provides a unified interface for generating D3.js visualizations from ArangoDB graph data.
Supports multiple layout types including force-directed, hierarchical tree, radial, and Sankey diagrams.

Links to third-party package documentation:
- D3.js v7: https://d3js.org/
- FastAPI: https://fastapi.tiangolo.com/
- Vertex AI: https://cloud.google.com/vertex-ai/docs

Sample input:
{
    "nodes": [{"id": "1", "name": "Node 1"}, {"id": "2", "name": "Node 2"}],
    "links": [{"source": "1", "target": "2", "value": 1}]
}

Expected output:
Standalone HTML file with embedded D3.js visualization
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal
from loguru import logger
from dataclasses import dataclass, field

# Import LLM recommender
try:
    from .llm_recommender import LLMRecommender, VisualizationRecommendation
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM recommender not available")

# Import performance optimizer
try:
    from .performance_optimizer import PerformanceOptimizer
    OPTIMIZER_AVAILABLE = True
except ImportError:
    OPTIMIZER_AVAILABLE = False
    logger.warning("Performance optimizer not available")

# Type definitions for layout types
LayoutType = Literal["force", "tree", "radial", "sankey"]
TreeOrientation = Literal["horizontal", "vertical"]

@dataclass
class VisualizationConfig:
    """Configuration for visualization generation"""
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
    # Tree-specific settings
    tree_orientation: TreeOrientation = "horizontal"
    node_radius: int = 8
    node_color: str = "#steelblue"
    link_color: str = "#999"
    animations: bool = True
    # Radial-specific settings
    radius: int = 500
    angle_span: List[float] = field(default_factory=lambda: [0, 2 * 3.14159])
    # Sankey-specific settings
    node_padding: int = 20
    node_alignment: str = "justify"  # left, right, center, justify
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class D3VisualizationEngine:
    """Main visualization engine for generating D3.js visualizations from graph data"""
    
    def __init__(self, template_dir: Optional[Path] = None, static_dir: Optional[Path] = None, use_llm: bool = True, optimize_performance: bool = True):
        """Initialize the visualization engine
        
        Args:
            template_dir: Directory containing HTML templates
            static_dir: Directory for static assets
            use_llm: Whether to use LLM for recommendations
            optimize_performance: Whether to optimize large graphs for performance
        """
        self.base_dir = Path(__file__).parent.parent
        self.template_dir = template_dir or self.base_dir / "templates"
        self.static_dir = static_dir or Path("/home/graham/workspace/experiments/arangodb/static")
        self.use_llm = use_llm and LLM_AVAILABLE
        self.optimize_performance = optimize_performance and OPTIMIZER_AVAILABLE
        
        # Create directories if they don't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM recommender if available
        self.llm_recommender = None
        if self.use_llm:
            try:
                self.llm_recommender = LLMRecommender()
                logger.info("LLM recommender initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM recommender: {e}")
                self.use_llm = False
        
        # Initialize performance optimizer if available
        self.performance_optimizer = None
        if self.optimize_performance:
            try:
                self.performance_optimizer = PerformanceOptimizer()
                logger.info("Performance optimizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize performance optimizer: {e}")
                self.optimize_performance = False
        
        logger.info(f"D3VisualizationEngine initialized with template_dir: {self.template_dir}")
    
    def generate_visualization(
        self, 
        graph_data: Dict[str, Any], 
        layout: LayoutType = "force",
        config: Optional[VisualizationConfig] = None
    ) -> str:
        """Generate a D3.js visualization from graph data
        
        Args:
            graph_data: Dictionary containing nodes and links
            layout: Type of layout to use
            config: Optional configuration object
            
        Returns:
            HTML string containing the complete visualization
        """
        if config is None:
            config = VisualizationConfig(layout=layout)
        else:
            config.layout = layout
            
        logger.info(f"Generating visualization with layout: {layout}")
        
        # Validate input data
        if not self._validate_graph_data(graph_data):
            raise ValueError("Invalid graph data structure")
        
        # Apply performance optimization if enabled and needed
        if self.performance_optimizer:
            node_count = len(graph_data.get('nodes', []))
            edge_count = len(graph_data.get('links', []))
            
            # Optimize large graphs
            if node_count > 1000 or edge_count > 3000:
                logger.info(f"Optimizing large graph: {node_count} nodes, {edge_count} edges")
                optimized_data = self.performance_optimizer.optimize_graph(graph_data)
                
                # Extract performance hints if present
                performance_hints = optimized_data.pop('performance_hints', {})
                
                # Apply optimized data
                graph_data = optimized_data
                
                # Update config with performance hints
                if performance_hints:
                    if not config.custom_settings:
                        config.custom_settings = {}
                    config.custom_settings.update(performance_hints)
                    logger.info(f"Applied performance hints: {performance_hints}")
                
                logger.info(f"Optimization complete: {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('links', []))} edges")
        
        # Select generation method based on layout type
        if layout == "force":
            html = self.generate_force_layout(graph_data, config)
        elif layout == "tree":
            html = self.generate_tree_layout(graph_data, config)
        elif layout == "radial":
            html = self.generate_radial_layout(graph_data, config)
        elif layout == "sankey":
            html = self.generate_sankey_layout(graph_data, config)
        else:
            raise ValueError(f"Unsupported layout type: {layout}")
            
        logger.info(f"Visualization generated successfully for {len(graph_data.get('nodes', []))} nodes")
        return html
    
    def _validate_graph_data(self, graph_data: Dict[str, Any]) -> bool:
        """Validate the structure of graph data
        
        Args:
            graph_data: Input graph data
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(graph_data, dict):
            return False
            
        if "nodes" not in graph_data or "links" not in graph_data:
            logger.error("Graph data must contain 'nodes' and 'links' keys")
            return False
            
        if not isinstance(graph_data["nodes"], list) or not isinstance(graph_data["links"], list):
            logger.error("Nodes and links must be lists")
            return False
            
        return True
    
    def load_template(self, template_name: str) -> str:
        """Load an HTML template from the template directory
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Template content as string
        """
        template_path = self.template_dir / template_name
        
        if not template_path.exists():
            logger.warning(f"Template not found: {template_path}, using base template")
            # If template doesn't exist, return a basic template
            return self._get_base_template()
            
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _process_graph_data(self, graph_data: Dict[str, Any], config: VisualizationConfig) -> Dict[str, Any]:
        """Process graph data based on configuration
        
        Args:
            graph_data: Raw graph data
            config: Visualization configuration
            
        Returns:
            Processed graph data
        """
        processed = {
            "nodes": [],
            "links": []
        }
        
        # Process nodes
        for node in graph_data.get("nodes", []):
            processed_node = dict(node)
            
            # Apply size scaling if specified
            if config.node_size_field and config.node_size_field in node:
                value = node[config.node_size_field]
                # Scale value to reasonable size (5-30 pixels)
                if isinstance(value, (int, float)):
                    processed_node["size"] = 5 + (value * 5)  # Basic scaling
            else:
                processed_node["size"] = 8  # Default size
            
            # Set group for coloring if specified
            if config.node_color_field and config.node_color_field in node:
                processed_node["group"] = node[config.node_color_field]
            
            processed["nodes"].append(processed_node)
        
        # Process links
        for link in graph_data.get("links", []):
            processed_link = dict(link)
            
            # Apply width scaling if specified
            if config.link_width_field and config.link_width_field in link:
                value = link[config.link_width_field]
                if isinstance(value, (int, float)):
                    processed_link["value"] = value
            elif "value" not in link:
                processed_link["value"] = 1  # Default value
            
            processed["links"].append(processed_link)
        
        # Include metadata if present
        if "metadata" in graph_data:
            processed["metadata"] = graph_data["metadata"]
        
        return processed
    
    def _get_base_template(self) -> str:
        """Get the base HTML template structure"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        #graph-container {{
            width: 100%;
            height: 100vh;
            background-color: white;
            border: 1px solid #ddd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        svg {{
            width: 100%;
            height: 100%;
        }}
    </style>
</head>
<body>
    <div id="graph-container"></div>
    <script>
        {script}
    </script>
</body>
</html>"""

    def generate_force_layout(self, graph_data: Dict[str, Any], config: VisualizationConfig) -> str:
        """Generate a force-directed layout visualization
        
        Args:
            graph_data: Graph data with nodes and links
            config: Visualization configuration
            
        Returns:
            HTML string with force-directed visualization
        """
        logger.info("Generating responsive force-directed layout")
        
        # Load the responsive force template first, then fallback to regular force template
        responsive_template_path = self.template_dir / "responsive_force.html"
        template_path = self.template_dir / "force.html"
        
        if responsive_template_path.exists():
            logger.info("Using responsive force template")
            with open(responsive_template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        elif template_path.exists():
            logger.info("Using standard force template")
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            logger.warning("No force template found, using base template")
            template = self._get_base_template()
        
        # Apply node and link transformations based on config
        processed_data = self._process_graph_data(graph_data, config)
        
        # Replace template variables
        html = template.replace("{{ title or \"Force-Directed Graph\" }}", config.title or "Force-Directed Graph")
        html = html.replace("{{ graph_data | tojson | safe }}", json.dumps(processed_data))
        html = html.replace("{{ config | tojson | safe }}", json.dumps({
            "width": config.width,
            "height": config.height,
            "physics_enabled": config.physics_enabled,
            "show_labels": config.show_labels,
            "enable_zoom": config.enable_zoom,
            "enable_drag": config.enable_drag,
            "node_color_field": config.node_color_field,
            "node_size_field": config.node_size_field,
            "link_width_field": config.link_width_field,
            **config.custom_settings
        }))
        
        return html
    
    def generate_tree_layout(self, graph_data: Dict[str, Any], config: VisualizationConfig) -> str:
        """Generate a hierarchical tree layout visualization
        
        Args:
            graph_data: Graph data with hierarchical structure
            config: Visualization configuration
            
        Returns:
            HTML string with tree visualization
        """
        logger.info("Generating hierarchical tree layout")
        
        # Load the tree template
        template_path = self.template_dir / "tree.html"
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            logger.warning("Tree template not found, using base template")
            template = self._get_base_template()
        
        # Apply node and link transformations based on config
        processed_data = self._process_graph_data(graph_data, config)
        
        # Replace template variables
        html = template.replace("{{ title or \"Hierarchical Tree\" }}", config.title or "Hierarchical Tree")
        html = html.replace("{{ graph_data | tojson | safe }}", json.dumps(processed_data))
        html = html.replace("{{ config | tojson | safe }}", json.dumps({
            "width": config.width,
            "height": config.height,
            "orientation": config.tree_orientation,
            "nodeRadius": config.node_radius,
            "nodeColor": config.node_color,
            "linkColor": config.link_color,
            "showLabels": config.show_labels,
            "animations": config.animations
        }))
        
        logger.info("Tree layout generation complete")
        return html
    
    def generate_radial_layout(self, graph_data: Dict[str, Any], config: VisualizationConfig) -> str:
        """Generate a radial tree layout visualization
        
        Args:
            graph_data: Graph data with hierarchical structure
            config: Visualization configuration
            
        Returns:
            HTML string with radial visualization
        """
        logger.info("Generating radial layout")
        
        # Load the radial template
        template_path = self.template_dir / "radial.html"
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            logger.warning("Radial template not found, using base template")
            template = self._get_base_template()
        
        # Apply node and link transformations based on config
        processed_data = self._process_graph_data(graph_data, config)
        
        # Replace template variables
        html = template.replace("{{ title or \"Radial Tree\" }}", config.title or "Radial Tree")
        html = html.replace("{{ graph_data | tojson | safe }}", json.dumps(processed_data))
        html = html.replace("{{ config | tojson | safe }}", json.dumps({
            "width": config.width,
            "height": config.height,
            "radius": config.radius,
            "angleSpan": config.angle_span,
            "nodeRadius": config.node_radius,
            "nodeColor": config.node_color,
            "linkColor": config.link_color,
            "showLabels": config.show_labels,
            "animations": config.animations
        }))
        
        logger.info("Radial layout generation complete")
        return html
    
    def generate_sankey_layout(self, graph_data: Dict[str, Any], config: VisualizationConfig) -> str:
        """Generate a Sankey diagram visualization
        
        Args:
            graph_data: Graph data with flow information
            config: Visualization configuration
            
        Returns:
            HTML string with Sankey diagram
        """
        logger.info("Generating Sankey diagram")
        
        # Load the sankey template
        template_path = self.template_dir / "sankey.html"
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            logger.warning("Sankey template not found, using base template")
            template = self._get_base_template()
        
        # Apply node and link transformations based on config
        processed_data = self._process_graph_data(graph_data, config)
        
        # Ensure links have value property for Sankey
        for link in processed_data.get("links", []):
            if "value" not in link and "weight" in link:
                link["value"] = link["weight"]
            elif "value" not in link:
                link["value"] = 1
        
        # Replace template variables
        html = template.replace("{{ title or \"Sankey Diagram\" }}", config.title or "Sankey Diagram")
        html = html.replace("{{ graph_data | tojson | safe }}", json.dumps(processed_data))
        html = html.replace("{{ config | tojson | safe }}", json.dumps({
            "width": config.width,
            "height": config.height,
            "nodePadding": config.node_padding,
            "nodeAlignment": config.node_alignment,
            "showLabels": config.show_labels,
            "animations": config.animations
        }))
        
        logger.info("Sankey diagram generation complete")
        return html
    
    def recommend_visualization(
        self, 
        graph_data: Dict[str, Any], 
        query: Optional[str] = None
    ) -> Optional[VisualizationRecommendation]:
        """Get LLM recommendation for visualization type
        
        Args:
            graph_data: Graph data to analyze
            query: Optional user query for context
            
        Returns:
            VisualizationRecommendation or None if LLM not available
        """
        if not self.llm_recommender:
            logger.warning("LLM recommender not available")
            return None
        
        try:
            recommendation = self.llm_recommender.get_recommendation(graph_data, query)
            logger.info(f"LLM recommended: {recommendation.layout_type} - {recommendation.title}")
            return recommendation
        except Exception as e:
            logger.error(f"Failed to get LLM recommendation: {e}")
            return None
    
    def generate_with_recommendation(
        self, 
        graph_data: Dict[str, Any], 
        query: Optional[str] = None,
        base_config: Optional[VisualizationConfig] = None
    ) -> str:
        """Generate visualization using LLM recommendation
        
        Args:
            graph_data: Graph data to visualize
            query: Optional user query for context
            base_config: Base configuration to override with LLM suggestions
            
        Returns:
            HTML string with recommended visualization
        """
        # Get recommendation
        recommendation = self.recommend_visualization(graph_data, query)
        
        if recommendation:
            # Create or update config with recommendation
            if base_config:
                config = base_config
                config.layout = recommendation.layout_type
                config.title = recommendation.title
                # Apply any config overrides from LLM
                for key, value in recommendation.config_overrides.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            else:
                config = VisualizationConfig(
                    layout=recommendation.layout_type,
                    title=recommendation.title,
                    **recommendation.config_overrides
                )
            
            logger.info(f"Using LLM recommendation: {recommendation.layout_type}")
        else:
            # Fallback to force layout if no recommendation
            config = base_config or VisualizationConfig(layout="force")
            logger.info("Using default force layout (no LLM recommendation)")
        
        # Generate visualization
        return self.generate_visualization(graph_data, layout=config.layout, config=config)


if __name__ == "__main__":
    # Validation function for the module
    logger.add("visualization_test.log", rotation="10 MB")
    
    # Test data
    test_data = {
        "nodes": [
            {"id": "1", "name": "Node 1", "group": 1},
            {"id": "2", "name": "Node 2", "group": 1}, 
            {"id": "3", "name": "Node 3", "group": 2}
        ],
        "links": [
            {"source": "1", "target": "2", "value": 1},
            {"source": "2", "target": "3", "value": 2}
        ]
    }
    
    # Initialize engine
    engine = D3VisualizationEngine()
    
    # Test configuration
    config = VisualizationConfig(
        width=1200,
        height=800,
        title="Test Visualization"
    )
    
    # Test each layout type
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Force layout generation
    total_tests += 1
    try:
        html = engine.generate_visualization(test_data, layout="force", config=config)
        if not html or len(html) < 100:
            all_validation_failures.append(f"Force layout: Generated HTML too short ({len(html)} chars)")
        # Check for config title or default title
        if config.title and config.title not in html:
            all_validation_failures.append("Force layout: Missing configured title")
        elif not config.title and "Force-Directed Graph" not in html:
            all_validation_failures.append("Force layout: Missing expected default title")
    except Exception as e:
        all_validation_failures.append(f"Force layout: Failed with error {e}")
    
    # Test 2: Tree layout generation  
    total_tests += 1
    try:
        html = engine.generate_visualization(test_data, layout="tree", config=config)
        if not html or len(html) < 100:
            all_validation_failures.append(f"Tree layout: Generated HTML too short ({len(html)} chars)")
        # Check for config title or default title
        if config.title and config.title not in html:
            all_validation_failures.append("Tree layout: Missing configured title")
        elif not config.title and "Hierarchical Tree" not in html:
            all_validation_failures.append("Tree layout: Missing expected default title")
    except Exception as e:
        all_validation_failures.append(f"Tree layout: Failed with error {e}")
    
    # Test 3: Invalid data validation
    total_tests += 1
    try:
        invalid_data = {"invalid": "data"}
        html = engine.generate_visualization(invalid_data, layout="force", config=config)
        all_validation_failures.append("Invalid data: Should have raised ValueError")
    except ValueError:
        # This is expected
        pass
    except Exception as e:
        all_validation_failures.append(f"Invalid data: Unexpected error {e}")
    
    # Test 4: Template loading
    total_tests += 1
    try:
        template = engine.load_template("base.html")
        if len(template) < 50:
            all_validation_failures.append(f"Template loading: Template too short ({len(template)} chars)")
    except Exception as e:
        all_validation_failures.append(f"Template loading: Failed with error {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f" VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        exit(1)
    else:
        print(f" VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("D3VisualizationEngine is validated and ready for implementation")
        exit(0)