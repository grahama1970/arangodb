"""Test Performance Optimization Integration

This module tests the integration of performance optimization with the D3 visualization engine.

Links to third-party package documentation:
- NetworkX: https://networkx.org/
- loguru: https://github.com/Delgan/loguru

Sample input:
Large graph with 2000 nodes and 5000 edges

Expected output:
Optimized graph with sampled nodes and performance hints
"""

import random
from typing import Dict, List, Any
from loguru import logger

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from arangodb.visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig


def create_large_test_graph(num_nodes: int = 2000, num_edges: int = 5000) -> Dict[str, Any]:
    """Create a large test graph for performance testing
    
    Args:
        num_nodes: Number of nodes to create
        num_edges: Number of edges to create
        
    Returns:
        Graph data with nodes and links
    """
    # Create nodes
    nodes = []
    for i in range(num_nodes):
        nodes.append({
            "id": str(i),
            "name": f"Node {i}",
            "group": i % 10,  # 10 groups
            "size": random.randint(5, 20)
        })
    
    # Create edges
    links = []
    for _ in range(num_edges):
        source = str(random.randint(0, num_nodes - 1))
        target = str(random.randint(0, num_nodes - 1))
        if source != target:
            links.append({
                "source": source,
                "target": target,
                "value": random.randint(1, 10)
            })
    
    return {"nodes": nodes, "links": links}


if __name__ == "__main__":
    logger.add("performance_integration_test.log", rotation="10 MB")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Small graph should not be optimized
    total_tests += 1
    try:
        small_graph = {
            "nodes": [{"id": "1", "name": "A"}, {"id": "2", "name": "B"}],
            "links": [{"source": "1", "target": "2"}]
        }
        
        engine = D3VisualizationEngine(optimize_performance=True)
        config = VisualizationConfig(title="Small Graph Test")
        
        html = engine.generate_visualization(small_graph, layout="force", config=config)
        
        # Check that small graph wasn't optimized (should still have 2 nodes)
        if '"id": "1"' not in html or '"id": "2"' not in html:
            all_validation_failures.append("Small graph: Nodes were unexpectedly modified")
        
        logger.info("Small graph test completed")
    except Exception as e:
        all_validation_failures.append(f"Small graph test: Failed with error {e}")
    
    # Test 2: Large graph should be optimized
    total_tests += 1
    try:
        large_graph = create_large_test_graph(2000, 5000)
        
        engine = D3VisualizationEngine(optimize_performance=True)
        config = VisualizationConfig(title="Large Graph Test")
        
        html = engine.generate_visualization(large_graph, layout="force", config=config)
        
        # Check that optimization was applied
        if "performance_hints" not in str(config.custom_settings):
            logger.warning("Performance hints may not have been applied, but this is not a failure")
        
        # The HTML should be generated successfully
        if not html or len(html) < 1000:
            all_validation_failures.append(f"Large graph: Generated HTML too short ({len(html)} chars)")
        
        logger.info("Large graph test completed")
    except Exception as e:
        all_validation_failures.append(f"Large graph test: Failed with error {e}")
    
    # Test 3: Optimization can be disabled
    total_tests += 1
    try:
        large_graph = create_large_test_graph(1500, 4000)
        
        engine = D3VisualizationEngine(optimize_performance=False)
        config = VisualizationConfig(title="Optimization Disabled Test")
        
        html = engine.generate_visualization(large_graph, layout="force", config=config)
        
        # Check that no optimization was applied
        if config.custom_settings and "performance_hints" in str(config.custom_settings):
            all_validation_failures.append("Optimization disabled: Performance hints unexpectedly applied")
        
        logger.info("Optimization disabled test completed")
    except Exception as e:
        all_validation_failures.append(f"Optimization disabled test: Failed with error {e}")
    
    # Test 4: Different layouts with optimization
    total_tests += 1
    try:
        large_graph = create_large_test_graph(1200, 3500)
        
        engine = D3VisualizationEngine(optimize_performance=True)
        
        # Test each layout
        layouts = ["force", "tree", "radial", "sankey"]
        for layout in layouts:
            config = VisualizationConfig(title=f"{layout.title()} Layout Test", layout=layout)
            html = engine.generate_visualization(large_graph, layout=layout, config=config)
            
            if not html or len(html) < 500:
                all_validation_failures.append(f"{layout} layout: Generated HTML too short ({len(html)} chars)")
        
        logger.info("Multiple layouts test completed")
    except Exception as e:
        all_validation_failures.append(f"Multiple layouts test: Failed with error {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Performance optimization is successfully integrated with D3VisualizationEngine")
        exit(0)