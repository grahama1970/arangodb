"""Comprehensive Test Suite for D3.js Visualization System

This module provides complete test coverage for the visualization system.

Links to third-party package documentation:
- pytest: https://docs.pytest.org/
- D3.js: https://d3js.org/
- FastAPI: https://fastapi.tiangolo.com/

Sample input:
Various graph structures for different layout types

Expected output:
All tests pass with valid HTML generation
"""

import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from arangodb.visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig
from arangodb.visualization.core.data_transformer import DataTransformer
from arangodb.visualization.core.llm_recommender import LLMRecommender
from arangodb.visualization.core.performance_optimizer import PerformanceOptimizer


class TestD3VisualizationEngine:
    """Test cases for the D3VisualizationEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create a test engine instance"""
        return D3VisualizationEngine(use_llm=False, optimize_performance=False)
    
    @pytest.fixture
    def sample_graph(self):
        """Sample graph data for testing"""
        return {
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
    
    def test_engine_initialization(self):
        """Test engine initialization"""
        engine = D3VisualizationEngine()
        assert engine.template_dir.exists()
        assert engine.static_dir.exists()
    
    def test_force_layout_generation(self, engine, sample_graph):
        """Test force-directed layout generation"""
        config = VisualizationConfig(layout="force", title="Test Force Layout")
        html = engine.generate_visualization(sample_graph, config=config)
        
        assert html is not None
        assert len(html) > 1000
        assert "Test Force Layout" in html
        assert "force" in html.lower()
    
    def test_tree_layout_generation(self, engine, sample_graph):
        """Test hierarchical tree layout generation"""
        config = VisualizationConfig(layout="tree", title="Test Tree Layout")
        html = engine.generate_visualization(sample_graph, config=config)
        
        assert html is not None
        assert len(html) > 1000
        assert "Test Tree Layout" in html
    
    def test_radial_layout_generation(self, engine, sample_graph):
        """Test radial layout generation"""
        config = VisualizationConfig(layout="radial", title="Test Radial Layout")
        html = engine.generate_visualization(sample_graph, config=config)
        
        assert html is not None
        assert len(html) > 1000
        assert "Test Radial Layout" in html
    
    def test_sankey_diagram_generation(self, engine, sample_graph):
        """Test Sankey diagram generation"""
        config = VisualizationConfig(layout="sankey", title="Test Sankey Diagram")
        html = engine.generate_visualization(sample_graph, config=config)
        
        assert html is not None
        assert len(html) > 1000
        assert "Test Sankey Diagram" in html
    
    def test_invalid_layout_type(self, engine, sample_graph):
        """Test error handling for invalid layout type"""
        with pytest.raises(ValueError, match="Unsupported layout type"):
            engine.generate_visualization(sample_graph, layout="invalid")
    
    def test_invalid_graph_data(self, engine):
        """Test error handling for invalid graph data"""
        invalid_data = {"invalid": "data"}
        
        with pytest.raises(ValueError, match="Invalid graph data"):
            engine.generate_visualization(invalid_data)
    
    def test_custom_configuration(self, engine, sample_graph):
        """Test custom configuration options"""
        config = VisualizationConfig(
            width=1200,
            height=800,
            node_color_field="group",
            node_size_field="value",
            physics_enabled=False,
            show_labels=False
        )
        
        html = engine.generate_visualization(sample_graph, config=config)
        assert "1200" in html
        assert "800" in html


class TestDataTransformer:
    """Test cases for the DataTransformer"""
    
    @pytest.fixture
    def transformer(self):
        """Create a test transformer instance"""
        return DataTransformer()
    
    @pytest.fixture
    def arangodb_data(self):
        """Sample ArangoDB data"""
        return {
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
    
    def test_basic_transformation(self, transformer, arangodb_data):
        """Test basic data transformation"""
        result = transformer.transform_graph_data(arangodb_data)
        
        assert "nodes" in result
        assert "links" in result
        assert len(result["nodes"]) == 2
        assert len(result["links"]) == 1
        
        # Check node structure
        node = result["nodes"][0]
        assert "id" in node
        assert "name" in node
        assert node["name"] == "Entity A"
        
        # Check link structure
        link = result["links"][0]
        assert "source" in link
        assert "target" in link
        assert link["source"] == "1"
        assert link["target"] == "2"
    
    def test_custom_fields(self, transformer, arangodb_data):
        """Test transformation with custom fields"""
        result = transformer.transform_graph_data(
            arangodb_data,
            node_label_field="name",
            edge_label_field="relationship"
        )
        
        assert result["nodes"][0]["label"] == "Entity A"
        assert result["links"][0]["label"] == "connects"
    
    def test_preprocessing_function(self, transformer, arangodb_data):
        """Test transformation with preprocessing"""
        def preprocess(data):
            for vertex in data["vertices"]:
                vertex["custom"] = "processed"
            return data
        
        result = transformer.transform_graph_data(
            arangodb_data,
            preprocessing_fn=preprocess
        )
        
        assert result["nodes"][0]["custom"] == "processed"
    
    def test_empty_data_handling(self, transformer):
        """Test handling of empty data"""
        empty_data = {"vertices": [], "edges": []}
        result = transformer.transform_graph_data(empty_data)
        
        assert result["nodes"] == []
        assert result["links"] == []
    
    def test_missing_fields_handling(self, transformer):
        """Test handling of missing fields"""
        partial_data = {
            "vertices": [{"_id": "coll/1", "_key": "1"}],
            "edges": []
        }
        
        result = transformer.transform_graph_data(partial_data)
        assert result["nodes"][0]["label"] == "1"  # Falls back to _key


class TestPerformanceOptimizer:
    """Test cases for the PerformanceOptimizer"""
    
    @pytest.fixture
    def optimizer(self):
        """Create a test optimizer instance"""
        from arangodb.visualization.core.performance_optimizer import OptimizationConfig
        config = OptimizationConfig(max_nodes=10, max_edges=20)
        return PerformanceOptimizer(config)
    
    @pytest.fixture
    def large_graph(self):
        """Create a large graph for testing"""
        nodes = [{"id": str(i), "name": f"Node {i}"} for i in range(100)]
        links = [
            {"source": str(i), "target": str((i + 1) % 100), "value": 1}
            for i in range(150)
        ]
        return {"nodes": nodes, "links": links}
    
    def test_small_graph_optimization(self, optimizer):
        """Test that small graphs are not modified"""
        small_graph = {
            "nodes": [{"id": "1"}, {"id": "2"}],
            "links": [{"source": "1", "target": "2"}]
        }
        
        result = optimizer.optimize_graph(small_graph)
        assert len(result["nodes"]) == 2
        assert len(result["links"]) == 1
    
    def test_large_graph_sampling(self, optimizer, large_graph):
        """Test graph sampling for large graphs"""
        result = optimizer.optimize_graph(large_graph)
        
        assert len(result["nodes"]) <= 10  # Max nodes
        assert len(result["links"]) <= 20  # Max edges
        assert "performance_hints" in result
    
    def test_performance_hints_generation(self, optimizer, large_graph):
        """Test performance hints generation"""
        result = optimizer.optimize_graph(large_graph)
        hints = result.get("performance_hints", {})
        
        assert "use_webgl" in hints
        assert "recommended_renderer" in hints
        assert "edge_opacity" in hints
        assert "force_iterations" in hints
    
    def test_lod_calculation(self, optimizer):
        """Test level of detail calculation"""
        assert optimizer.get_lod_level(2.0, 100) == "high"
        assert optimizer.get_lod_level(1.0, 100) == "medium"
        assert optimizer.get_lod_level(0.5, 100) == "low"
    
    def test_custom_sampling_strategy(self):
        """Test different sampling strategies"""
        from arangodb.visualization.core.performance_optimizer import OptimizationConfig
        
        config = OptimizationConfig(
            max_nodes=5,
            sampling_strategy="random"
        )
        optimizer = PerformanceOptimizer(config)
        
        large_graph = {
            "nodes": [{"id": str(i)} for i in range(20)],
            "links": []
        }
        
        result = optimizer.optimize_graph(large_graph)
        assert len(result["nodes"]) <= 5


class TestLLMRecommender:
    """Test cases for the LLMRecommender"""
    
    @pytest.fixture
    def sample_hierarchical_graph(self):
        """Sample hierarchical graph structure"""
        return {
            "nodes": [
                {"id": "root", "level": 0},
                {"id": "child1", "level": 1},
                {"id": "child2", "level": 1},
                {"id": "grandchild1", "level": 2}
            ],
            "links": [
                {"source": "root", "target": "child1"},
                {"source": "root", "target": "child2"},
                {"source": "child1", "target": "grandchild1"}
            ]
        }
    
    @pytest.mark.skipif(not LLMRecommender, reason="LLM not available")
    def test_recommendation_generation(self, sample_hierarchical_graph):
        """Test LLM recommendation generation"""
        recommender = LLMRecommender()
        recommendation = recommender.get_recommendation(
            sample_hierarchical_graph,
            query="Show the hierarchy"
        )
        
        assert recommendation is not None
        assert recommendation.layout_type in ["tree", "radial"]
        assert recommendation.reason is not None
        assert recommendation.confidence > 0


class TestVisualizationIntegration:
    """Integration tests for the complete visualization system"""
    
    @pytest.fixture
    def complete_system(self):
        """Create a complete system setup"""
        engine = D3VisualizationEngine(use_llm=True, optimize_performance=True)
        transformer = DataTransformer()
        return engine, transformer
    
    def test_end_to_end_workflow(self, complete_system):
        """Test complete workflow from ArangoDB to visualization"""
        engine, transformer = complete_system
        
        # Simulate ArangoDB data
        arangodb_data = {
            "vertices": [
                {"_id": "concepts/ai", "name": "Artificial Intelligence"},
                {"_id": "concepts/ml", "name": "Machine Learning"},
                {"_id": "concepts/dl", "name": "Deep Learning"}
            ],
            "edges": [
                {"_from": "concepts/ai", "_to": "concepts/ml", "relationship": "includes"},
                {"_from": "concepts/ml", "_to": "concepts/dl", "relationship": "includes"}
            ]
        }
        
        # Transform data
        d3_data = transformer.transform_graph_data(arangodb_data)
        
        # Generate visualization
        html = engine.generate_visualization(d3_data, layout="tree")
        
        assert html is not None
        assert "Artificial Intelligence" in html
        assert "Machine Learning" in html
        assert "Deep Learning" in html
    
    def test_file_output(self, complete_system):
        """Test saving visualization to file"""
        engine, _ = complete_system
        
        data = {
            "nodes": [{"id": "1", "name": "Test"}],
            "links": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html = engine.generate_visualization(data)
            f.write(html)
            
            # Verify file exists and has content
            assert Path(f.name).exists()
            assert Path(f.name).stat().st_size > 1000
    
    def test_large_graph_optimization(self, complete_system):
        """Test optimization of large graphs"""
        engine, _ = complete_system
        
        # Create large graph
        nodes = [{"id": str(i), "name": f"Node {i}"} for i in range(2000)]
        links = [
            {"source": str(i), "target": str((i + 17) % 2000)}
            for i in range(5000)
        ]
        large_graph = {"nodes": nodes, "links": links}
        
        # Should trigger optimization
        html = engine.generate_visualization(large_graph)
        
        assert html is not None
        # Optimized graph should have fewer nodes
        assert "nodes: 10" in html or len(nodes) == 10


if __name__ == "__main__":
    # Run validation tests
    logger.add("test_visualization_suite.log", rotation="10 MB")
    
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Engine initialization
    total_tests += 1
    try:
        engine = D3VisualizationEngine()
        if not engine.template_dir.exists():
            all_validation_failures.append("Engine: Template directory doesn't exist")
    except Exception as e:
        all_validation_failures.append(f"Engine initialization: {e}")
    
    # Test 2: Data transformation
    total_tests += 1
    try:
        transformer = DataTransformer()
        test_data = {
            "vertices": [{"_id": "test/1", "name": "Test"}],
            "edges": []
        }
        result = transformer.transform_graph_data(test_data)
        if not result["nodes"]:
            all_validation_failures.append("Transformer: Failed to transform nodes")
    except Exception as e:
        all_validation_failures.append(f"Data transformation: {e}")
    
    # Test 3: Visualization generation
    total_tests += 1
    try:
        engine = D3VisualizationEngine()
        data = {
            "nodes": [{"id": "1", "name": "Test"}],
            "links": []
        }
        html = engine.generate_visualization(data)
        if not html or len(html) < 100:
            all_validation_failures.append("Visualization: Generated HTML too short")
    except Exception as e:
        all_validation_failures.append(f"Visualization generation: {e}")
    
    # Test 4: Performance optimization
    total_tests += 1
    try:
        optimizer = PerformanceOptimizer()
        large_data = {
            "nodes": [{"id": str(i)} for i in range(100)],
            "links": []
        }
        result = optimizer.optimize_graph(large_data)
        if "nodes" not in result:
            all_validation_failures.append("Optimizer: Missing nodes in result")
    except Exception as e:
        all_validation_failures.append(f"Performance optimization: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Visualization test suite is ready for pytest execution")
        exit(0)