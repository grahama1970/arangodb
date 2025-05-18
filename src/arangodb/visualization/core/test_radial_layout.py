"""Test script for radial layout visualization

This script tests the radial layout implementation and generates HTML outputs.

Sample input: Graph data with hierarchical relationships
Expected output: HTML file with radial tree visualization
"""

import json
import sys
from pathlib import Path
from loguru import logger

# Import the visualization engine
from d3_engine import D3VisualizationEngine, VisualizationConfig

def create_radial_test_data():
    """Create sample hierarchical data for radial testing"""
    return {
        "nodes": [
            # Center
            {"id": "center", "name": "System Core", "type": "root", "value": 100},
            # Inner ring
            {"id": "module1", "name": "Module 1", "type": "module", "value": 50},
            {"id": "module2", "name": "Module 2", "type": "module", "value": 50},
            {"id": "module3", "name": "Module 3", "type": "module", "value": 50},
            # Middle ring
            {"id": "comp1-1", "name": "Component 1.1", "type": "component", "value": 25},
            {"id": "comp1-2", "name": "Component 1.2", "type": "component", "value": 25},
            {"id": "comp2-1", "name": "Component 2.1", "type": "component", "value": 25},
            {"id": "comp3-1", "name": "Component 3.1", "type": "component", "value": 30},
            {"id": "comp3-2", "name": "Component 3.2", "type": "component", "value": 20},
            # Outer ring
            {"id": "func1-1-1", "name": "Function 1.1.1", "type": "function", "value": 10},
            {"id": "func1-1-2", "name": "Function 1.1.2", "type": "function", "value": 15},
            {"id": "func1-2-1", "name": "Function 1.2.1", "type": "function", "value": 25},
            {"id": "func2-1-1", "name": "Function 2.1.1", "type": "function", "value": 12},
            {"id": "func2-1-2", "name": "Function 2.1.2", "type": "function", "value": 13},
        ],
        "links": [
            # Center to modules
            {"source": "center", "target": "module1", "weight": 1},
            {"source": "center", "target": "module2", "weight": 1},
            {"source": "center", "target": "module3", "weight": 1},
            # Module 1 to components
            {"source": "module1", "target": "comp1-1", "weight": 1},
            {"source": "module1", "target": "comp1-2", "weight": 1},
            # Module 2 to components
            {"source": "module2", "target": "comp2-1", "weight": 1},
            # Module 3 to components
            {"source": "module3", "target": "comp3-1", "weight": 1},
            {"source": "module3", "target": "comp3-2", "weight": 1},
            # Components to functions
            {"source": "comp1-1", "target": "func1-1-1", "weight": 1},
            {"source": "comp1-1", "target": "func1-1-2", "weight": 1},
            {"source": "comp1-2", "target": "func1-2-1", "weight": 1},
            {"source": "comp2-1", "target": "func2-1-1", "weight": 1},
            {"source": "comp2-1", "target": "func2-1-2", "weight": 1},
        ]
    }

def validate_radial_layout(engine: D3VisualizationEngine):
    """Validate radial layout generation with various configurations"""
    all_validation_failures = []
    total_tests = 0
    
    # Get test data
    radial_data = create_radial_test_data()
    
    # Test 1: Basic radial layout
    total_tests += 1
    config = VisualizationConfig(
        layout="radial",
        title="Radial Layout Test",
        width=1000,
        height=1000,
        radius=400,
        show_labels=True,
        animations=True
    )
    
    try:
        html = engine.generate_visualization(radial_data, layout="radial", config=config)
        if not html or len(html) < 1000:
            all_validation_failures.append(f"Basic radial: Generated HTML too short ({len(html)} chars)")
        if "Radial Layout Test" not in html:
            all_validation_failures.append("Basic radial: Missing title in output")
        if "radial.html" not in str(engine.template_dir):
            logger.warning("Radial template not found in expected location")
    except Exception as e:
        all_validation_failures.append(f"Basic radial: Failed with error {e}")
    
    # Test 2: Half circle configuration
    total_tests += 1
    config.angle_span = [0, 3.14159]  # Half circle
    config.title = "Half Circle Radial"
    
    try:
        html = engine.generate_visualization(radial_data, layout="radial", config=config)
        if not html or len(html) < 1000:
            all_validation_failures.append(f"Half circle: Generated HTML too short ({len(html)} chars)")
        if "Half Circle Radial" not in html:
            all_validation_failures.append("Half circle: Missing title in output")
        if '"angleSpan": [0, 3.14159]' not in html:
            all_validation_failures.append("Half circle: Missing angle span config")
    except Exception as e:
        all_validation_failures.append(f"Half circle: Failed with error {e}")
    
    # Test 3: Custom radius
    total_tests += 1
    config.radius = 600
    config.title = "Large Radius Radial"
    
    try:
        html = engine.generate_visualization(radial_data, layout="radial", config=config)
        if '"radius": 600' not in html:
            all_validation_failures.append("Custom radius: Missing radius config")
    except Exception as e:
        all_validation_failures.append(f"Custom radius: Failed with error {e}")
    
    # Test 4: Create actual HTML file for visual verification
    total_tests += 1
    output_path = Path("/home/graham/workspace/experiments/arangodb/static/radial_test.html")
    config.title = "Radial Layout Visual Test"
    config.angle_span = [0, 2 * 3.14159]  # Full circle
    config.radius = 500
    
    try:
        html = engine.generate_visualization(radial_data, layout="radial", config=config)
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
        print("Radial layout implementation is working correctly")
        return True

def main():
    """Main validation function"""
    logger.add("radial_layout_test.log", rotation="10 MB")
    logger.info("Starting radial layout validation")
    
    # Initialize engine
    engine = D3VisualizationEngine()
    logger.info(f"Template directory: {engine.template_dir}")
    
    # Check if radial template exists
    radial_template_path = engine.template_dir / "radial.html"
    if radial_template_path.exists():
        logger.info(f"Radial template found at: {radial_template_path}")
    else:
        logger.error(f"Radial template not found at: {radial_template_path}")
    
    # Run validation
    success = validate_radial_layout(engine)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()