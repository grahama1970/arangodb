"""Test script for force-directed layout visualization

This script tests the force-directed graph implementation with sample data.
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

def generate_test_data(node_count: int = 50, edge_count: int = 80):
    """Generate test graph data"""
    import random
    
    # Create nodes
    nodes = []
    groups = ["database", "application", "service", "user", "resource"]
    
    for i in range(node_count):
        node = {
            "id": f"node_{i}",
            "name": f"Node {i}",
            "group": random.choice(groups),
            "importance": random.uniform(0.1, 1.0),
            "connections": 0  # Will be calculated
        }
        nodes.append(node)
    
    # Create edges
    links = []
    node_ids = [n["id"] for n in nodes]
    
    for i in range(edge_count):
        source = random.choice(node_ids)
        target = random.choice(node_ids)
        
        # Avoid self-loops
        while target == source:
            target = random.choice(node_ids)
        
        link = {
            "source": source,
            "target": target,
            "type": random.choice(["depends_on", "calls", "references", "owns"]),
            "weight": random.uniform(0.1, 1.0)
        }
        links.append(link)
    
    # Calculate connection counts
    for link in links:
        for node in nodes:
            if node["id"] == link["source"] or node["id"] == link["target"]:
                node["connections"] += 1
    
    return {
        "nodes": nodes,
        "links": links,
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(links),
            "node_types": list(set(n["group"] for n in nodes)),
            "edge_types": list(set(l["type"] for l in links))
        }
    }

def test_force_layout():
    """Test force-directed layout visualization"""
    results = Table(title="Force-Directed Layout Test")
    results.add_column("Test", style="cyan")
    results.add_column("Status", style="green")
    results.add_column("Details", style="yellow")
    
    test_passed = True
    
    # Test 1: Initialize engine
    try:
        engine = D3VisualizationEngine()
        results.add_row("Engine Initialization", "✓", "Successfully created D3VisualizationEngine")
    except Exception as e:
        results.add_row("Engine Initialization", "✗", f"Error: {e}")
        test_passed = False
        return
    
    # Test 2: Generate test data
    try:
        # Small test data
        small_data = generate_test_data(20, 30)
        results.add_row(
            "Small Test Data", 
            "✓", 
            f"{small_data['metadata']['node_count']} nodes, {small_data['metadata']['edge_count']} edges"
        )
        
        # Medium test data
        medium_data = generate_test_data(50, 100)
        results.add_row(
            "Medium Test Data", 
            "✓", 
            f"{medium_data['metadata']['node_count']} nodes, {medium_data['metadata']['edge_count']} edges"
        )
        
        # Large test data
        large_data = generate_test_data(100, 200)
        results.add_row(
            "Large Test Data", 
            "✓", 
            f"{large_data['metadata']['node_count']} nodes, {large_data['metadata']['edge_count']} edges"
        )
        
    except Exception as e:
        results.add_row("Test Data Generation", "✗", f"Error: {e}")
        test_passed = False
        return
    
    # Test 3: Basic force layout generation
    try:
        config = VisualizationConfig(
            width=1200,
            height=800,
            title="Basic Force Layout Test",
            node_color_field="group",
            node_size_field="connections",
            link_width_field="weight"
        )
        
        html = engine.generate_visualization(small_data, layout="force", config=config)
        
        if html and len(html) > 1000:
            # Save the visualization
            output_file = Path("/home/graham/workspace/experiments/arangodb/static/force_basic_test.html")
            output_file.write_text(html)
            results.add_row("Basic Force Layout", "✓", f"Generated {len(html)} bytes, saved to {output_file.name}")
        else:
            results.add_row("Basic Force Layout", "✗", "Generated HTML too short")
            test_passed = False
            
    except Exception as e:
        results.add_row("Basic Force Layout", "✗", f"Error: {e}")
        test_passed = False
    
    # Test 4: Physics configuration test
    try:
        config = VisualizationConfig(
            width=1200,
            height=800,
            title="Physics Configuration Test",
            physics_enabled=True,
            custom_settings={
                "link_distance": 100,
                "charge_force": -300,
                "collision_radius": 20
            }
        )
        
        html = engine.generate_visualization(medium_data, layout="force", config=config)
        output_file = Path("/home/graham/workspace/experiments/arangodb/static/force_physics_test.html")
        output_file.write_text(html)
        results.add_row("Physics Configuration", "✓", f"Saved to {output_file.name}")
        
    except Exception as e:
        results.add_row("Physics Configuration", "✗", f"Error: {e}")
        test_passed = False
    
    # Test 5: Large graph performance test
    try:
        config = VisualizationConfig(
            width=1400,
            height=900,
            title="Large Graph Performance Test",
            node_color_field="group",
            show_labels=False  # Hide labels for performance
        )
        
        html = engine.generate_visualization(large_data, layout="force", config=config)
        output_file = Path("/home/graham/workspace/experiments/arangodb/static/force_large_test.html")
        output_file.write_text(html)
        results.add_row("Large Graph", "✓", f"100 nodes rendered, saved to {output_file.name}")
        
    except Exception as e:
        results.add_row("Large Graph", "✗", f"Error: {e}")
        test_passed = False
    
    # Test 6: ArangoDB format conversion
    try:
        # Simulate ArangoDB format
        arango_data = {
            "vertices": [
                {"_id": "docs/1", "_key": "1", "name": "Database", "type": "system"},
                {"_id": "docs/2", "_key": "2", "name": "API Server", "type": "service"},
                {"_id": "docs/3", "_key": "3", "name": "Web Client", "type": "application"},
                {"_id": "docs/4", "_key": "4", "name": "Cache", "type": "system"},
                {"_id": "docs/5", "_key": "5", "name": "User Service", "type": "service"}
            ],
            "edges": [
                {"_from": "docs/2", "_to": "docs/1", "type": "queries", "weight": 0.9},
                {"_from": "docs/3", "_to": "docs/2", "type": "calls", "weight": 0.8},
                {"_from": "docs/2", "_to": "docs/4", "type": "caches", "weight": 0.6},
                {"_from": "docs/5", "_to": "docs/1", "type": "queries", "weight": 0.7},
                {"_from": "docs/3", "_to": "docs/5", "type": "calls", "weight": 0.5}
            ]
        }
        
        transformer = DataTransformer()
        d3_data = transformer.transform_graph_data(arango_data)
        
        config = VisualizationConfig(
            width=1000,
            height=600,
            title="ArangoDB Integration Test",
            node_color_field="type"
        )
        
        html = engine.generate_visualization(d3_data, layout="force", config=config)
        output_file = Path("/home/graham/workspace/experiments/arangodb/static/force_arango_test.html")
        output_file.write_text(html)
        results.add_row("ArangoDB Integration", "✓", f"Converted and rendered, saved to {output_file.name}")
        
    except Exception as e:
        results.add_row("ArangoDB Integration", "✗", f"Error: {e}")
        test_passed = False
    
    # Display results
    console.print(results)
    
    # Performance metrics
    if test_passed:
        metrics = Table(title="Force Layout Performance Metrics")
        metrics.add_column("Graph Size", style="cyan")
        metrics.add_column("Nodes", style="green")
        metrics.add_column("Edges", style="green")
        metrics.add_column("File Size", style="yellow")
        
        for test_name, data, filename in [
            ("Small", small_data, "force_basic_test.html"),
            ("Medium", medium_data, "force_physics_test.html"), 
            ("Large", large_data, "force_large_test.html")
        ]:
            file_path = Path(f"/home/graham/workspace/experiments/arangodb/static/{filename}")
            if file_path.exists():
                file_size = file_path.stat().st_size / 1024  # KB
                metrics.add_row(
                    test_name,
                    str(data["metadata"]["node_count"]),
                    str(data["metadata"]["edge_count"]),
                    f"{file_size:.1f} KB"
                )
        
        console.print("\n")
        console.print(metrics)
        
        console.print("\n[green]✅ All force layout tests passed![/green]")
        console.print("\nTest visualizations created:")
        console.print("  1. Basic test: /home/graham/workspace/experiments/arangodb/static/force_basic_test.html")
        console.print("  2. Physics test: /home/graham/workspace/experiments/arangodb/static/force_physics_test.html")
        console.print("  3. Large graph: /home/graham/workspace/experiments/arangodb/static/force_large_test.html")
        console.print("  4. ArangoDB test: /home/graham/workspace/experiments/arangodb/static/force_arango_test.html")
        console.print("\nOpen these files in Chrome to view the interactive visualizations.")
    else:
        console.print("\n[red]❌ Some tests failed. Please check the errors above.[/red]")
    
    return test_passed


if __name__ == "__main__":
    success = test_force_layout()
    sys.exit(0 if success else 1)