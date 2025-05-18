"""D3.js Visualization Engine for ArangoDB

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

# Type definitions for layout types
LayoutType = Literal["force", "tree", "radial", "sankey"]

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
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class D3VisualizationEngine:
    """Main visualization engine for generating D3.js visualizations from graph data"""
    
    def __init__(self, template_dir: Optional[Path] = None, static_dir: Optional[Path] = None):
        """Initialize the visualization engine
        
        Args:
            template_dir: Directory containing HTML templates
            static_dir: Directory for static assets
        """
        self.base_dir = Path(__file__).parent.parent
        self.template_dir = template_dir or self.base_dir / "templates"
        self.static_dir = static_dir or Path("/home/graham/workspace/experiments/arangodb/static")
        
        # Create directories if they don't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)
        
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
        logger.info("Generating force-directed layout")
        
        # To be implemented in Task 2
        # For now, return a placeholder
        template = self._get_base_template()
        
        script = f"""
        // Force-directed layout placeholder
        const data = {json.dumps(graph_data)};
        console.log('Force layout data loaded:', data);
        // Implementation will be added in Task 2
        """
        
        html = template.format(
            title=config.title or "Force-Directed Graph",
            script=script
        )
        
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
        
        # To be implemented in Task 3
        template = self._get_base_template()
        
        script = f"""
        // Tree layout placeholder
        const data = {json.dumps(graph_data)};
        console.log('Tree layout data loaded:', data);
        // Implementation will be added in Task 3
        """
        
        html = template.format(
            title=config.title or "Hierarchical Tree",
            script=script
        )
        
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
        
        # To be implemented in Task 4
        template = self._get_base_template()
        
        script = f"""
        // Radial layout placeholder
        const data = {json.dumps(graph_data)};
        console.log('Radial layout data loaded:', data);
        // Implementation will be added in Task 4
        """
        
        html = template.format(
            title=config.title or "Radial Tree",
            script=script
        )
        
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
        
        # To be implemented in Task 5
        template = self._get_base_template()
        
        script = f"""
        // Sankey layout placeholder
        const data = {json.dumps(graph_data)};
        console.log('Sankey layout data loaded:', data);
        // Implementation will be added in Task 5
        """
        
        html = template.format(
            title=config.title or "Sankey Diagram",
            script=script
        )
        
        return html


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
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("D3VisualizationEngine is validated and ready for implementation")
        exit(0)