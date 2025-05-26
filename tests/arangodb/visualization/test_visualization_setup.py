"""Test script to verify D3.js visualization setup

This script tests the basic infrastructure, transformation utilities, and HTML generation.
Creates a test visualization file to confirm D3.js loads correctly.
"""

import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print

# Add project root to path
sys.path.insert(0, "/home/graham/workspace/experiments/arangodb")

from arangodb.visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig
from arangodb.visualization.core.data_transformer import DataTransformer

console = Console()

def test_infrastructure():
    """Test the basic infrastructure setup"""
    results = Table(title="D3.js Visualization Infrastructure Test")
    results.add_column("Component", style="cyan")
    results.add_column("Status", style="green")
    results.add_column("Details", style="yellow")
    
    test_passed = True
    
    # Test 1: Engine initialization
    try:
        engine = D3VisualizationEngine()
        results.add_row("Engine Initialization", "✓", "Successfully created D3VisualizationEngine")
    except Exception as e:
        results.add_row("Engine Initialization", "✗", f"Error: {e}")
        test_passed = False
    
    # Test 2: Template loading
    try:
        template = engine.load_template("base.html")
        if template and "<!DOCTYPE html>" in template:
            results.add_row("Template Loading", "✓", "Base template loaded successfully")
        else:
            results.add_row("Template Loading", "✗", "Template content invalid")
            test_passed = False
    except Exception as e:
        results.add_row("Template Loading", "✗", f"Error: {e}")
        test_passed = False
    
    # Test 3: Data transformer
    try:
        transformer = DataTransformer()
        
        # Test ArangoDB format data
        arango_data = {
            "vertices": [
                {"_id": "docs/1", "_key": "1", "name": "Main Concept", "type": "concept"},
                {"_id": "docs/2", "_key": "2", "name": "Related Idea", "type": "idea"},
                {"_id": "docs/3", "_key": "3", "name": "Implementation", "type": "implementation"}
            ],
            "edges": [
                {"_from": "docs/1", "_to": "docs/2", "type": "relates_to", "weight": 0.8},
                {"_from": "docs/2", "_to": "docs/3", "type": "implements", "weight": 0.9}
            ]
        }
        
        d3_data = transformer.transform_graph_data(arango_data)
        
        if d3_data["nodes"] and d3_data["links"]:
            results.add_row(
                "Data Transformation", 
                "✓", 
                f"{len(d3_data['nodes'])} nodes, {len(d3_data['links'])} links"
            )
        else:
            results.add_row("Data Transformation", "✗", "No data transformed")
            test_passed = False
            
    except Exception as e:
        results.add_row("Data Transformation", "✗", f"Error: {e}")
        test_passed = False
    
    # Test 4: D3.js loading
    try:
        # Create a minimal test HTML
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>D3.js Load Test</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
        </head>
        <body>
            <div id="test-svg"></div>
            <script>
                // Test if D3 loads by creating an SVG element
                const svg = d3.select("#test-svg")
                    .append("svg")
                    .attr("width", 100)
                    .attr("height", 100);
                
                svg.append("circle")
                    .attr("cx", 50)
                    .attr("cy", 50)
                    .attr("r", 30)
                    .style("fill", "steelblue");
                
                console.log("D3.js version:", d3.version);
            </script>
        </body>
        </html>
        """
        
        # Write test file
        test_file = Path("/home/graham/workspace/experiments/arangodb/static/d3_test.html")
        test_file.write_text(test_html)
        
        results.add_row("D3.js Test File", "✓", f"Created at {test_file}")
        
    except Exception as e:
        results.add_row("D3.js Test File", "✗", f"Error: {e}")
        test_passed = False
    
    # Test 5: Generate test visualization
    try:
        config = VisualizationConfig(
            width=800,
            height=600,
            title="Test Visualization"
        )
        
        visualization = engine.generate_visualization(d3_data, layout="force", config=config)
        
        if visualization:
            viz_file = Path("/home/graham/workspace/experiments/arangodb/static/test_visualization.html")
            viz_file.write_text(visualization)
            results.add_row("Test Visualization", "✓", f"Generated at {viz_file}")
        else:
            results.add_row("Test Visualization", "✗", "Empty visualization")
            test_passed = False
            
    except Exception as e:
        results.add_row("Test Visualization", "✗", f"Error: {e}")
        test_passed = False
    
    # Test 6: SVG rendering capability
    try:
        # Create a more complete test with actual D3 visualization
        d3_test_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>D3 SVG Rendering Test</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                #graph {{ border: 1px solid #ccc; }}
                .node {{ fill: steelblue; stroke: white; stroke-width: 2px; }}
                .link {{ stroke: #999; stroke-opacity: 0.6; }}
            </style>
        </head>
        <body>
            <h2>D3.js SVG Rendering Test</h2>
            <svg id="graph" width="400" height="300"></svg>
            <div id="status"></div>
            <script>
                const data = {json.dumps(d3_data, indent=2)};
                
                // Create a simple force simulation
                const width = 400;
                const height = 300;
                
                const svg = d3.select("#graph");
                
                // Add a test circle
                svg.append("circle")
                    .attr("cx", width/2)
                    .attr("cy", height/2)
                    .attr("r", 50)
                    .attr("class", "node");
                
                // Update status
                d3.select("#status").text("D3.js loaded successfully. Version: " + d3.version);
                
                console.log("Test data loaded:", data);
            </script>
        </body>
        </html>
        """
        
        svg_test_file = Path("/home/graham/workspace/experiments/arangodb/static/svg_test.html")
        svg_test_file.write_text(d3_test_html)
        
        results.add_row("SVG Rendering Test", "✓", f"Created at {svg_test_file}")
        
    except Exception as e:
        results.add_row("SVG Rendering Test", "✗", f"Error: {e}")
        test_passed = False
    
    # Display results
    console.print(results)
    
    # Summary
    if test_passed:
        console.print("\n[green]✅ All tests passed successfully![/green]")
        console.print("\nTest files created:")
        console.print("  1. Basic D3 test: /home/graham/workspace/experiments/arangodb/static/d3_test.html")
        console.print("  2. SVG rendering test: /home/graham/workspace/experiments/arangodb/static/svg_test.html")
        console.print("  3. Full visualization: /home/graham/workspace/experiments/arangodb/static/test_visualization.html")
        console.print("\nOpen these files in Chrome to verify D3.js rendering.")
    else:
        console.print("\n[red]❌ Some tests failed. Please check the errors above.[/red]")
    
    # Transformation metrics
    if 'd3_data' in locals():
        metrics_table = Table(title="Data Transformation Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        
        metadata = d3_data.get("metadata", {})
        metrics_table.add_row("Nodes Transformed", str(metadata.get("node_count", 0)))
        metrics_table.add_row("Edges Transformed", str(metadata.get("edge_count", 0))) 
        metrics_table.add_row("Node Types", str(list(metadata.get("node_types", []))))
        metrics_table.add_row("Edge Types", str(list(metadata.get("edge_types", []))))
        
        console.print("\n")
        console.print(metrics_table)
    
    return test_passed


if __name__ == "__main__":
    success = test_infrastructure()
    sys.exit(0 if success else 1)