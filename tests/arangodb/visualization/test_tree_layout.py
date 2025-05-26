"""Test script for tree layout visualization

This script tests the tree layout implementation and generates HTML outputs.

Sample input: Graph data with hierarchical relationships
Expected output: HTML file with collapsible tree visualization
"""

import json
import sys
from pathlib import Path
from loguru import logger

# Import the visualization engine
from arangodb.visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig

def create_tree_test_data():
    """Create sample hierarchical data for testing"""
    return {
        "nodes": [
            # Root
            {"id": "root", "name": "Root Node", "type": "root", "value": 100},
            # Level 1
            {"id": "child1", "name": "Child 1", "type": "branch", "value": 60},
            {"id": "child2", "name": "Child 2", "type": "branch", "value": 40},
            # Level 2
            {"id": "grandchild1-1", "name": "Grandchild 1-1", "type": "leaf", "value": 30},
            {"id": "grandchild1-2", "name": "Grandchild 1-2", "type": "leaf", "value": 30},
            {"id": "grandchild2-1", "name": "Grandchild 2-1", "type": "leaf", "value": 20},
            {"id": "grandchild2-2", "name": "Grandchild 2-2", "type": "leaf", "value": 20},
            # Level 3
            {"id": "greatgrand1-1-1", "name": "Great Grandchild 1-1-1", "type": "leaf", "value": 15},
            {"id": "greatgrand1-1-2", "name": "Great Grandchild 1-1-2", "type": "leaf", "value": 15},
        ],
        "links": [
            # Root to children
            {"source": "root", "target": "child1", "weight": 1},
            {"source": "root", "target": "child2", "weight": 1},
            # Child 1 to grandchildren
            {"source": "child1", "target": "grandchild1-1", "weight": 1},
            {"source": "child1", "target": "grandchild1-2", "weight": 1},
            # Child 2 to grandchildren
            {"source": "child2", "target": "grandchild2-1", "weight": 1},
            {"source": "child2", "target": "grandchild2-2", "weight": 1},
            # Grandchild 1-1 to great grandchildren
            {"source": "grandchild1-1", "target": "greatgrand1-1-1", "weight": 1},
            {"source": "grandchild1-1", "target": "greatgrand1-1-2", "weight": 1},
        ]
    }

def validate_tree_layout(engine: D3VisualizationEngine):
    """Validate tree layout generation with various configurations"""
    all_validation_failures = []
    total_tests = 0
    
    # Get test data
    tree_data = create_tree_test_data()
    
    # Test 1: Basic horizontal tree
    total_tests += 1
    config = VisualizationConfig(
        layout="tree",
        title="Horizontal Tree Test",
        width=1200,
        height=800,
        tree_orientation="horizontal",
        show_labels=True,
        animations=True
    )
    
    try:
        html = engine.generate_visualization(tree_data, layout="tree", config=config)
        if not html or len(html) < 1000:
            all_validation_failures.append(f"Horizontal tree: Generated HTML too short ({len(html)} chars)")
        if "Horizontal Tree Test" not in html:
            all_validation_failures.append("Horizontal tree: Missing title in output")
        if "tree.html" not in str(engine.template_dir):
            logger.warning("Tree template not found in expected location")
    except Exception as e:
        all_validation_failures.append(f"Horizontal tree: Failed with error {e}")
    
    # Test 2: Vertical tree configuration
    total_tests += 1
    config.tree_orientation = "vertical"
    config.title = "Vertical Tree Test"
    
    try:
        html = engine.generate_visualization(tree_data, layout="tree", config=config)
        if not html or len(html) < 1000:
            all_validation_failures.append(f"Vertical tree: Generated HTML too short ({len(html)} chars)")
        if "Vertical Tree Test" not in html:
            all_validation_failures.append("Vertical tree: Missing title in output")
        if '"orientation": "vertical"' not in html:
            all_validation_failures.append("Vertical tree: Missing orientation config")
    except Exception as e:
        all_validation_failures.append(f"Vertical tree: Failed with error {e}")
    
    # Test 3: Tree with custom colors
    total_tests += 1
    config.node_color = "#ff6b6b"
    config.link_color = "#4ecdc4"
    config.title = "Custom Color Tree"
    
    try:
        html = engine.generate_visualization(tree_data, layout="tree", config=config)
        if "#ff6b6b" not in html:
            all_validation_failures.append("Custom color tree: Missing node color")
        if "#4ecdc4" not in html:
            all_validation_failures.append("Custom color tree: Missing link color")
    except Exception as e:
        all_validation_failures.append(f"Custom color tree: Failed with error {e}")
    
    # Test 4: Create actual HTML file for visual verification
    total_tests += 1
    output_path = Path("/home/graham/workspace/experiments/arangodb/static/tree_test.html")
    config.title = "Tree Layout Visual Test"
    config.tree_orientation = "horizontal"
    
    try:
        html = engine.generate_visualization(tree_data, layout="tree", config=config)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        if not output_path.exists():
            all_validation_failures.append("HTML file creation: File not created")
        else:
            file_size = output_path.stat().st_size
            if file_size < 1000:
                all_validation_failures.append(f"HTML file creation: File too small ({file_size} bytes)")
            else:
                logger.info(f"Created test HTML file: {output_path} ({file_size} bytes)")
    except Exception as e:
        all_validation_failures.append(f"HTML file creation: Failed with error {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        return False
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print(f"Test HTML file created at: {output_path}")
        print("Tree layout implementation is working correctly")
        return True

def main():
    """Main validation function"""
    logger.add("tree_layout_test.log", rotation="10 MB")
    logger.info("Starting tree layout validation")
    
    # Initialize engine
    engine = D3VisualizationEngine()
    logger.info(f"Template directory: {engine.template_dir}")
    
    # Check if tree template exists
    tree_template_path = engine.template_dir / "tree.html"
    if tree_template_path.exists():
        logger.info(f"Tree template found at: {tree_template_path}")
    else:
        logger.error(f"Tree template not found at: {tree_template_path}")
    
    # Run validation
    success = validate_tree_layout(engine)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()