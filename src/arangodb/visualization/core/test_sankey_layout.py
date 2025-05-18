"""Test script for Sankey diagram visualization

This script tests the Sankey diagram implementation and generates HTML outputs.

Sample input: Graph data with flow information
Expected output: HTML file with Sankey diagram visualization
"""

import json
import sys
from pathlib import Path
from loguru import logger

# Import the visualization engine
from d3_engine import D3VisualizationEngine, VisualizationConfig

def create_sankey_test_data():
    """Create sample flow data for Sankey testing"""
    return {
        "nodes": [
            # Sources
            {"id": "source1", "name": "Data Source 1", "type": "source"},
            {"id": "source2", "name": "Data Source 2", "type": "source"},
            {"id": "source3", "name": "Data Source 3", "type": "source"},
            # Processing
            {"id": "process1", "name": "Processing Unit 1", "type": "process"},
            {"id": "process2", "name": "Processing Unit 2", "type": "process"},
            {"id": "process3", "name": "Processing Unit 3", "type": "process"},
            # Output
            {"id": "output1", "name": "Output Stream 1", "type": "output"},
            {"id": "output2", "name": "Output Stream 2", "type": "output"},
            {"id": "output3", "name": "Output Stream 3", "type": "output"},
            # Final
            {"id": "final", "name": "Final Destination", "type": "destination"},
        ],
        "links": [
            # Sources to processing
            {"source": "source1", "target": "process1", "value": 30},
            {"source": "source1", "target": "process2", "value": 20},
            {"source": "source2", "target": "process1", "value": 15},
            {"source": "source2", "target": "process3", "value": 25},
            {"source": "source3", "target": "process2", "value": 35},
            {"source": "source3", "target": "process3", "value": 10},
            # Processing to output
            {"source": "process1", "target": "output1", "value": 25},
            {"source": "process1", "target": "output2", "value": 20},
            {"source": "process2", "target": "output1", "value": 15},
            {"source": "process2", "target": "output3", "value": 40},
            {"source": "process3", "target": "output2", "value": 20},
            {"source": "process3", "target": "output3", "value": 15},
            # Output to final
            {"source": "output1", "target": "final", "value": 40},
            {"source": "output2", "target": "final", "value": 40},
            {"source": "output3", "target": "final", "value": 55},
        ]
    }

def validate_sankey_layout(engine: D3VisualizationEngine):
    """Validate Sankey diagram generation with various configurations"""
    all_validation_failures = []
    total_tests = 0
    
    # Get test data
    sankey_data = create_sankey_test_data()
    
    # Test 1: Basic Sankey diagram
    total_tests += 1
    config = VisualizationConfig(
        layout="sankey",
        title="Sankey Diagram Test",
        width=1200,
        height=600,
        node_padding=20,
        show_labels=True
    )
    
    try:
        html = engine.generate_visualization(sankey_data, layout="sankey", config=config)
        if not html or len(html) < 1000:
            all_validation_failures.append(f"Basic sankey: Generated HTML too short ({len(html)} chars)")
        if "Sankey Diagram Test" not in html:
            all_validation_failures.append("Basic sankey: Missing title in output")
        if "d3-sankey" not in html:
            all_validation_failures.append("Basic sankey: Missing d3-sankey library")
    except Exception as e:
        all_validation_failures.append(f"Basic sankey: Failed with error {e}")
    
    # Test 2: Custom node padding
    total_tests += 1
    config.node_padding = 40
    config.title = "Wide Padding Sankey"
    
    try:
        html = engine.generate_visualization(sankey_data, layout="sankey", config=config)
        if '"nodePadding": 40' not in html:
            all_validation_failures.append("Custom padding: Missing padding config")
    except Exception as e:
        all_validation_failures.append(f"Custom padding: Failed with error {e}")
    
    # Test 3: Different alignment
    total_tests += 1
    config.node_alignment = "left"
    config.title = "Left Aligned Sankey"
    
    try:
        html = engine.generate_visualization(sankey_data, layout="sankey", config=config)
        if '"nodeAlignment": "left"' not in html:
            all_validation_failures.append("Alignment: Missing alignment config")
    except Exception as e:
        all_validation_failures.append(f"Alignment: Failed with error {e}")
    
    # Test 4: Create actual HTML file for visual verification
    total_tests += 1
    output_path = Path("/home/graham/workspace/experiments/arangodb/static/sankey_test.html")
    config.title = "Sankey Diagram Visual Test"
    config.node_alignment = "justify"
    config.node_padding = 20
    
    try:
        html = engine.generate_visualization(sankey_data, layout="sankey", config=config)
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
        print("Sankey diagram implementation is working correctly")
        return True

def main():
    """Main validation function"""
    logger.add("sankey_layout_test.log", rotation="10 MB")
    logger.info("Starting Sankey diagram validation")
    
    # Initialize engine
    engine = D3VisualizationEngine()
    logger.info(f"Template directory: {engine.template_dir}")
    
    # Check if sankey template exists
    sankey_template_path = engine.template_dir / "sankey.html"
    if sankey_template_path.exists():
        logger.info(f"Sankey template found at: {sankey_template_path}")
    else:
        logger.error(f"Sankey template not found at: {sankey_template_path}")
    
    # Run validation
    success = validate_sankey_layout(engine)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()