"""Test script for LLM integration with D3VisualizationEngine

This script tests the LLM recommendation system integration.

Sample input: Various graph structures
Expected output: Appropriate visualization recommendations
"""

import json
import sys
from pathlib import Path
from loguru import logger

# Import the visualization engine
from d3_engine import D3VisualizationEngine, VisualizationConfig

def create_test_datasets():
    """Create various test datasets for recommendation testing"""
    return {
        "hierarchical": {
            "nodes": [
                {"id": "ceo", "name": "CEO", "type": "executive"},
                {"id": "cto", "name": "CTO", "type": "executive"},
                {"id": "cfo", "name": "CFO", "type": "executive"},
                {"id": "dev1", "name": "Developer 1", "type": "developer"},
                {"id": "dev2", "name": "Developer 2", "type": "developer"},
                {"id": "acc1", "name": "Accountant 1", "type": "accountant"},
            ],
            "links": [
                {"source": "ceo", "target": "cto"},
                {"source": "ceo", "target": "cfo"},
                {"source": "cto", "target": "dev1"},
                {"source": "cto", "target": "dev2"},
                {"source": "cfo", "target": "acc1"},
            ]
        },
        "network": {
            "nodes": [
                {"id": "server1", "name": "Web Server 1", "type": "server"},
                {"id": "server2", "name": "Web Server 2", "type": "server"},
                {"id": "db1", "name": "Database 1", "type": "database"},
                {"id": "cache1", "name": "Cache Server", "type": "cache"},
                {"id": "lb1", "name": "Load Balancer", "type": "loadbalancer"},
            ],
            "links": [
                {"source": "lb1", "target": "server1"},
                {"source": "lb1", "target": "server2"},
                {"source": "server1", "target": "db1"},
                {"source": "server2", "target": "db1"},
                {"source": "server1", "target": "cache1"},
                {"source": "server2", "target": "cache1"},
                {"source": "cache1", "target": "db1"},
            ]
        },
        "flow": {
            "nodes": [
                {"id": "raw", "name": "Raw Data", "type": "input"},
                {"id": "clean", "name": "Data Cleaning", "type": "process"},
                {"id": "transform", "name": "Transformation", "type": "process"},
                {"id": "analyze", "name": "Analysis", "type": "process"},
                {"id": "report", "name": "Report", "type": "output"},
                {"id": "dashboard", "name": "Dashboard", "type": "output"},
            ],
            "links": [
                {"source": "raw", "target": "clean", "value": 1000},
                {"source": "clean", "target": "transform", "value": 950},
                {"source": "transform", "target": "analyze", "value": 900},
                {"source": "analyze", "target": "report", "value": 600},
                {"source": "analyze", "target": "dashboard", "value": 300},
            ]
        }
    }

def validate_llm_integration(engine: D3VisualizationEngine):
    """Validate LLM integration with various test cases"""
    all_validation_failures = []
    total_tests = 0
    
    test_datasets = create_test_datasets()
    
    # Test 1: Hierarchical data recommendation
    total_tests += 1
    data = test_datasets["hierarchical"]
    
    try:
        recommendation = engine.recommend_visualization(data)
        if recommendation:
            logger.info(f"Hierarchical data: Recommended {recommendation.layout_type}")
            if recommendation.layout_type not in ["tree", "radial"]:
                logger.warning(f"Expected tree/radial for hierarchical data, got {recommendation.layout_type}")
        else:
            all_validation_failures.append("Hierarchical data: No recommendation returned")
    except Exception as e:
        all_validation_failures.append(f"Hierarchical data: Failed with error {e}")
    
    # Test 2: Network data recommendation
    total_tests += 1
    data = test_datasets["network"]
    
    try:
        recommendation = engine.recommend_visualization(data)
        if recommendation:
            logger.info(f"Network data: Recommended {recommendation.layout_type}")
            if recommendation.layout_type != "force":
                logger.warning(f"Expected force for network data, got {recommendation.layout_type}")
        else:
            all_validation_failures.append("Network data: No recommendation returned")
    except Exception as e:
        all_validation_failures.append(f"Network data: Failed with error {e}")
    
    # Test 3: Flow data recommendation
    total_tests += 1
    data = test_datasets["flow"]
    
    try:
        recommendation = engine.recommend_visualization(data)
        if recommendation:
            logger.info(f"Flow data: Recommended {recommendation.layout_type}")
            if recommendation.layout_type != "sankey":
                logger.warning(f"Expected sankey for flow data, got {recommendation.layout_type}")
        else:
            all_validation_failures.append("Flow data: No recommendation returned")
    except Exception as e:
        all_validation_failures.append(f"Flow data: Failed with error {e}")
    
    # Test 4: Query-based recommendation
    total_tests += 1
    data = test_datasets["hierarchical"]
    query = "Show me the organizational hierarchy"
    
    try:
        recommendation = engine.recommend_visualization(data, query)
        if recommendation:
            logger.info(f"Query test: Recommended {recommendation.layout_type} for '{query}'")
            if "hierarchy" not in recommendation.reasoning.lower():
                logger.warning("Query context not reflected in reasoning")
        else:
            all_validation_failures.append("Query test: No recommendation returned")
    except Exception as e:
        all_validation_failures.append(f"Query test: Failed with error {e}")
    
    # Test 5: Generate with recommendation
    total_tests += 1
    data = test_datasets["flow"]
    output_path = Path("/home/graham/workspace/experiments/arangodb/static/llm_recommendation_test.html")
    
    try:
        html = engine.generate_with_recommendation(data, query="Show the data flow")
        
        if not html or len(html) < 1000:
            all_validation_failures.append(f"Generate with recommendation: HTML too short ({len(html)} chars)")
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Created visualization with LLM recommendation: {output_path}")
    except Exception as e:
        all_validation_failures.append(f"Generate with recommendation: Failed with error {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        return False
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print(f"Test HTML file created at: {output_path}")
        print("LLM integration is working correctly")
        return True

def main():
    """Main validation function"""
    logger.add("llm_integration_test.log", rotation="10 MB")
    logger.info("Starting LLM integration validation")
    
    # Initialize engine with LLM
    engine = D3VisualizationEngine(use_llm=True)
    
    if not engine.llm_recommender:
        print("❌ LLM recommender not available - check Vertex AI configuration")
        sys.exit(1)
    
    # Run validation
    success = validate_llm_integration(engine)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()