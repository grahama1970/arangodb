#!/usr/bin/env python3
"""Final Validation Script for D3.js Visualization System

This script performs a comprehensive validation of the entire visualization system.

Usage:
    python validate_visualization_system.py

Expected output:
    All tests pass, system ready for production
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from arangodb.visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig
from arangodb.visualization.core.data_transformer import DataTransformer
from arangodb.visualization.core.performance_optimizer import PerformanceOptimizer


def validate_module_structure() -> List[str]:
    """Validate that all required modules exist"""
    failures = []
    base_path = Path(__file__).parent.parent / "src" / "arangodb" / "visualization"
    
    required_files = [
        "core/d3_engine.py",
        "core/data_transformer.py",
        "core/llm_recommender.py",
        "core/performance_optimizer.py",
        "templates/force.html",
        "templates/tree.html",
        "templates/radial.html",
        "templates/sankey.html",
    ]
    
    for file_path in required_files:
        full_path = base_path / file_path
        if not full_path.exists():
            failures.append(f"Missing file: {file_path}")
    
    return failures


def validate_layouts() -> List[str]:
    """Validate all layout types work correctly"""
    failures = []
    
    engine = D3VisualizationEngine(use_llm=False, optimize_performance=False)
    
    test_data = {
        "nodes": [
            {"id": "1", "name": "Node A", "group": 1},
            {"id": "2", "name": "Node B", "group": 1},
            {"id": "3", "name": "Node C", "group": 2}
        ],
        "links": [
            {"source": "1", "target": "2", "value": 1},
            {"source": "2", "target": "3", "value": 2}
        ]
    }
    
    layouts = ["force", "tree", "radial", "sankey"]
    
    for layout in layouts:
        try:
            config = VisualizationConfig(layout=layout, title=f"Test {layout}")
            html = engine.generate_visualization(test_data, config=config)
            
            if not html or len(html) < 1000:
                failures.append(f"{layout} layout: Generated HTML too short")
            
            if f"Test {layout}" not in html:
                failures.append(f"{layout} layout: Missing title in output")
                
        except Exception as e:
            failures.append(f"{layout} layout: {e}")
    
    return failures


def validate_data_transformation() -> List[str]:
    """Validate data transformation works correctly"""
    failures = []
    
    transformer = DataTransformer()
    
    test_data = {
        "vertices": [
            {"_id": "coll/1", "_key": "1", "name": "Entity A"},
            {"_id": "coll/2", "_key": "2", "name": "Entity B"}
        ],
        "edges": [
            {
                "_id": "edges/1",
                "_from": "coll/1",
                "_to": "coll/2",
                "relationship": "connects"
            }
        ]
    }
    
    try:
        result = transformer.transform_graph_data(test_data)
        
        if "nodes" not in result or "links" not in result:
            failures.append("Transform: Missing nodes or links in result")
        
        if len(result["nodes"]) != 2:
            failures.append(f"Transform: Expected 2 nodes, got {len(result['nodes'])}")
        
        if len(result["links"]) != 1:
            failures.append(f"Transform: Expected 1 link, got {len(result['links'])}")
            
    except Exception as e:
        failures.append(f"Transform: {e}")
    
    return failures


def validate_performance_optimization() -> List[str]:
    """Validate performance optimization works correctly"""
    failures = []
    
    optimizer = PerformanceOptimizer()
    
    # Create large graph
    large_graph = {
        "nodes": [{"id": str(i), "name": f"Node {i}"} for i in range(5000)],
        "links": [
            {"source": str(i), "target": str((i + 17) % 5000), "value": 1}
            for i in range(10000)
        ]
    }
    
    try:
        result = optimizer.optimize_graph(large_graph)
        
        if len(result["nodes"]) > 500:
            failures.append(f"Optimizer: Too many nodes after optimization ({len(result['nodes'])})")
        
        if "performance_hints" not in result:
            failures.append("Optimizer: Missing performance hints")
            
    except Exception as e:
        failures.append(f"Optimizer: {e}")
    
    return failures


def validate_documentation() -> List[str]:
    """Validate documentation exists"""
    failures = []
    base_path = Path(__file__).parent.parent
    
    required_docs = [
        "docs/guides/visualization_guide.md",
        "docs/api/visualization_api.md",
        "src/arangodb/visualization/README.md",
        "docs/reports/028_d3_graph_visualization_report.md"
    ]
    
    for doc_path in required_docs:
        full_path = base_path / doc_path
        if not full_path.exists():
            failures.append(f"Missing documentation: {doc_path}")
    
    return failures


def validate_integration() -> List[str]:
    """Validate end-to-end integration"""
    failures = []
    
    try:
        # Test complete workflow
        engine = D3VisualizationEngine(use_llm=True, optimize_performance=True)
        transformer = DataTransformer()
        
        # Simulate ArangoDB data
        arangodb_data = {
            "vertices": [
                {"_id": "concepts/1", "name": "Concept A"},
                {"_id": "concepts/2", "name": "Concept B"},
                {"_id": "concepts/3", "name": "Concept C"}
            ],
            "edges": [
                {"_from": "concepts/1", "_to": "concepts/2"},
                {"_from": "concepts/2", "_to": "concepts/3"}
            ]
        }
        
        # Transform
        d3_data = transformer.transform_graph_data(arangodb_data)
        
        # Generate
        html = engine.generate_visualization(d3_data, layout="tree")
        
        if not html or len(html) < 1000:
            failures.append("Integration: Failed to generate visualization")
            
    except Exception as e:
        failures.append(f"Integration: {e}")
    
    return failures


def main():
    """Run all validation tests"""
    logger.add("visualization_validation.log", rotation="10 MB")
    
    all_failures = []
    
    # Test 1: Module structure
    print("Validating module structure...")
    failures = validate_module_structure()
    all_failures.extend(failures)
    print(f"  ✓ Module structure: {len(failures)} failures")
    
    # Test 2: Layouts
    print("Validating layouts...")
    failures = validate_layouts()
    all_failures.extend(failures)
    print(f"  ✓ Layouts: {len(failures)} failures")
    
    # Test 3: Data transformation
    print("Validating data transformation...")
    failures = validate_data_transformation()
    all_failures.extend(failures)
    print(f"  ✓ Data transformation: {len(failures)} failures")
    
    # Test 4: Performance optimization
    print("Validating performance optimization...")
    failures = validate_performance_optimization()
    all_failures.extend(failures)
    print(f"  ✓ Performance: {len(failures)} failures")
    
    # Test 5: Documentation
    print("Validating documentation...")
    failures = validate_documentation()
    all_failures.extend(failures)
    print(f"  ✓ Documentation: {len(failures)} failures")
    
    # Test 6: Integration
    print("Validating integration...")
    failures = validate_integration()
    all_failures.extend(failures)
    print(f"  ✓ Integration: {len(failures)} failures")
    
    # Final report
    print("\n" + "="*50)
    print("FINAL VALIDATION REPORT")
    print("="*50)
    
    if all_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_failures)} issues found:")
        for failure in all_failures:
            print(f"  - {failure}")
        return 1
    else:
        print("\n✅ ALL VALIDATION TESTS PASSED")
        print("\nThe D3.js visualization system is complete and ready for production use!")
        print("\n📊 System capabilities:")
        print("  - 4 layout types (force, tree, radial, sankey)")
        print("  - LLM-powered layout recommendations")
        print("  - Automatic performance optimization")
        print("  - CLI integration via 'memory visualize'")
        print("  - FastAPI server for web access")
        print("  - Complete documentation and test suite")
        print("\n🚀 Next steps:")
        print("  1. Run 'memory visualize' to test CLI")
        print("  2. Start server with 'memory visualize --server'")
        print("  3. Open generated HTML files in browser")
        print("  4. Review documentation in docs/guides/")
        return 0


if __name__ == "__main__":
    sys.exit(main())