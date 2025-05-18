"""Performance optimizer for D3.js visualizations

This module provides performance optimization strategies for handling large graphs
including data sampling, level-of-detail rendering, and WebGL acceleration.

Links to third-party package documentation:
- NumPy: https://numpy.org/doc/stable/
- NetworkX: https://networkx.org/documentation/stable/

Sample input: Large graph data with 1000+ nodes
Expected output: Optimized graph data suitable for visualization
"""

import random
import math
from typing import Dict, Any, List, Set, Tuple, Optional
from dataclasses import dataclass
from loguru import logger
import numpy as np

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not available for advanced graph algorithms")


@dataclass
class OptimizationConfig:
    """Configuration for performance optimization"""
    max_nodes: int = 1000
    max_edges: int = 5000
    sampling_strategy: str = "degree"  # degree, random, community
    edge_bundling: bool = True
    node_clustering: bool = True
    webgl_threshold: int = 500
    lod_levels: List[int] = None
    
    def __post_init__(self):
        if self.lod_levels is None:
            self.lod_levels = [100, 500, 1000, 5000]


class PerformanceOptimizer:
    """Optimize graph visualizations for performance"""
    
    def __init__(self, config: OptimizationConfig = None):
        """Initialize the performance optimizer
        
        Args:
            config: Optimization configuration
        """
        self.config = config or OptimizationConfig()
        logger.info("PerformanceOptimizer initialized")
    
    def optimize_graph(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize graph data for visualization
        
        Args:
            graph_data: Input graph data
            
        Returns:
            Optimized graph data
        """
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("links", [])
        
        logger.info(f"Optimizing graph: {len(nodes)} nodes, {len(edges)} edges")
        
        # Check if optimization is needed
        if len(nodes) <= self.config.max_nodes and len(edges) <= self.config.max_edges:
            logger.info("Graph within size limits, minimal optimization needed")
            return self._apply_minimal_optimization(graph_data)
        
        # Apply sampling strategy
        if len(nodes) > self.config.max_nodes:
            sampled_data = self._sample_graph(graph_data)
        else:
            sampled_data = graph_data
        
        # Apply edge bundling if enabled
        if self.config.edge_bundling and len(edges) > 1000:
            sampled_data = self._bundle_edges(sampled_data)
        
        # Apply node clustering if enabled
        if self.config.node_clustering and len(nodes) > 500:
            sampled_data = self._cluster_nodes(sampled_data)
        
        # Add performance hints
        sampled_data["performance_hints"] = self._generate_performance_hints(sampled_data)
        
        return sampled_data
    
    def _apply_minimal_optimization(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply minimal optimization for small graphs
        
        Args:
            graph_data: Input graph data
            
        Returns:
            Minimally optimized graph data
        """
        optimized = graph_data.copy()
        
        # Add indexing for faster lookups
        node_index = {node["id"]: i for i, node in enumerate(optimized["nodes"])}
        
        # Convert edge references to indices
        for edge in optimized.get("links", []):
            if isinstance(edge.get("source"), str):
                edge["source_id"] = edge["source"]
                edge["source"] = node_index.get(edge["source"], 0)
            if isinstance(edge.get("target"), str):
                edge["target_id"] = edge["target"]
                edge["target"] = node_index.get(edge["target"], 0)
        
        optimized["node_index"] = node_index
        return optimized
    
    def _sample_graph(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sample nodes and edges from large graph
        
        Args:
            graph_data: Input graph data
            
        Returns:
            Sampled graph data
        """
        strategy = self.config.sampling_strategy
        
        if strategy == "degree":
            return self._degree_based_sampling(graph_data)
        elif strategy == "random":
            return self._random_sampling(graph_data)
        elif strategy == "community" and HAS_NETWORKX:
            return self._community_based_sampling(graph_data)
        else:
            logger.warning(f"Unknown or unavailable sampling strategy: {strategy}")
            return self._random_sampling(graph_data)
    
    def _degree_based_sampling(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sample nodes based on degree (number of connections)
        
        Args:
            graph_data: Input graph data
            
        Returns:
            Sampled graph data
        """
        nodes = graph_data["nodes"]
        edges = graph_data["links"]
        
        # Calculate node degrees
        degrees = {node["id"]: 0 for node in nodes}
        for edge in edges:
            degrees[edge["source"]] = degrees.get(edge["source"], 0) + 1
            degrees[edge["target"]] = degrees.get(edge["target"], 0) + 1
        
        # Sort nodes by degree
        sorted_nodes = sorted(nodes, key=lambda n: degrees.get(n["id"], 0), reverse=True)
        
        # Sample top nodes
        sampled_nodes = sorted_nodes[:self.config.max_nodes]
        sampled_ids = {node["id"] for node in sampled_nodes}
        
        # Sample edges connecting sampled nodes
        sampled_edges = [
            edge for edge in edges 
            if edge["source"] in sampled_ids and edge["target"] in sampled_ids
        ][:self.config.max_edges]
        
        return {
            "nodes": sampled_nodes,
            "links": sampled_edges,
            "metadata": {
                "sampling_method": "degree",
                "original_nodes": len(nodes),
                "original_edges": len(edges),
                "sampled_nodes": len(sampled_nodes),
                "sampled_edges": len(sampled_edges)
            }
        }
    
    def _random_sampling(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Randomly sample nodes and edges
        
        Args:
            graph_data: Input graph data
            
        Returns:
            Sampled graph data
        """
        nodes = graph_data["nodes"]
        edges = graph_data["links"]
        
        # Randomly sample nodes
        sampled_nodes = random.sample(nodes, min(self.config.max_nodes, len(nodes)))
        sampled_ids = {node["id"] for node in sampled_nodes}
        
        # Sample edges connecting sampled nodes
        sampled_edges = [
            edge for edge in edges 
            if edge["source"] in sampled_ids and edge["target"] in sampled_ids
        ][:self.config.max_edges]
        
        return {
            "nodes": sampled_nodes,
            "links": sampled_edges,
            "metadata": {
                "sampling_method": "random",
                "original_nodes": len(nodes),
                "original_edges": len(edges),
                "sampled_nodes": len(sampled_nodes),
                "sampled_edges": len(sampled_edges)
            }
        }
    
    def _community_based_sampling(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sample based on community detection
        
        Args:
            graph_data: Input graph data
            
        Returns:
            Sampled graph data
        """
        if not HAS_NETWORKX:
            return self._random_sampling(graph_data)
        
        # Create NetworkX graph
        G = nx.Graph()
        for node in graph_data["nodes"]:
            G.add_node(node["id"], **node)
        
        for edge in graph_data["links"]:
            G.add_edge(edge["source"], edge["target"], **edge)
        
        # Detect communities
        communities = list(nx.community.greedy_modularity_communities(G))
        
        # Sample from each community proportionally
        sampled_nodes = []
        nodes_per_community = self.config.max_nodes // len(communities)
        
        for community in communities:
            community_nodes = list(community)
            sample_size = min(nodes_per_community, len(community_nodes))
            sampled_nodes.extend(random.sample(community_nodes, sample_size))
        
        # Get node data for sampled IDs
        node_dict = {node["id"]: node for node in graph_data["nodes"]}
        sampled_node_data = [node_dict[node_id] for node_id in sampled_nodes if node_id in node_dict]
        sampled_ids = set(sampled_nodes)
        
        # Sample edges
        sampled_edges = [
            edge for edge in graph_data["links"]
            if edge["source"] in sampled_ids and edge["target"] in sampled_ids
        ][:self.config.max_edges]
        
        return {
            "nodes": sampled_node_data,
            "links": sampled_edges,
            "metadata": {
                "sampling_method": "community",
                "original_nodes": len(graph_data["nodes"]),
                "original_edges": len(graph_data["links"]),
                "sampled_nodes": len(sampled_node_data),
                "sampled_edges": len(sampled_edges),
                "communities_found": len(communities)
            }
        }
    
    def _bundle_edges(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Bundle edges to reduce visual clutter
        
        Args:
            graph_data: Input graph data
            
        Returns:
            Graph data with bundled edges
        """
        # This is a simplified edge bundling - in practice you'd use
        # more sophisticated algorithms
        edges = graph_data["links"]
        
        # Group edges by source-target pairs
        edge_groups = {}
        for edge in edges:
            key = (edge["source"], edge["target"])
            if key not in edge_groups:
                edge_groups[key] = []
            edge_groups[key].append(edge)
        
        # Bundle similar edges
        bundled_edges = []
        for (source, target), group in edge_groups.items():
            if len(group) > 1:
                # Combine multiple edges into one with higher weight
                bundled_edge = {
                    "source": source,
                    "target": target,
                    "value": sum(e.get("value", 1) for e in group),
                    "bundled_count": len(group)
                }
                bundled_edges.append(bundled_edge)
            else:
                bundled_edges.extend(group)
        
        graph_data["links"] = bundled_edges
        graph_data["metadata"] = graph_data.get("metadata", {})
        graph_data["metadata"]["edge_bundling"] = True
        graph_data["metadata"]["original_edges"] = len(edges)
        graph_data["metadata"]["bundled_edges"] = len(bundled_edges)
        
        return graph_data
    
    def _cluster_nodes(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cluster nearby nodes to reduce complexity
        
        Args:
            graph_data: Input graph data
            
        Returns:
            Graph data with clustered nodes
        """
        # This is a simplified clustering - in practice you'd use
        # spatial clustering algorithms
        nodes = graph_data["nodes"]
        
        # Group nodes by type or attribute
        node_groups = {}
        for node in nodes:
            group_key = node.get("type", node.get("group", "default"))
            if group_key not in node_groups:
                node_groups[group_key] = []
            node_groups[group_key].append(node)
        
        # Create cluster representatives
        clustered_nodes = []
        cluster_map = {}
        
        for group_key, group_nodes in node_groups.items():
            if len(group_nodes) > 10:
                # Create cluster node
                cluster_node = {
                    "id": f"cluster_{group_key}",
                    "name": f"{group_key} Cluster",
                    "type": "cluster",
                    "size": len(group_nodes),
                    "children": [n["id"] for n in group_nodes]
                }
                clustered_nodes.append(cluster_node)
                
                # Map original nodes to cluster
                for node in group_nodes:
                    cluster_map[node["id"]] = cluster_node["id"]
            else:
                # Keep individual nodes
                clustered_nodes.extend(group_nodes)
        
        # Update edges to point to clusters
        clustered_edges = []
        for edge in graph_data["links"]:
            source = cluster_map.get(edge["source"], edge["source"])
            target = cluster_map.get(edge["target"], edge["target"])
            
            # Skip self-loops on clusters
            if source != target:
                clustered_edges.append({
                    "source": source,
                    "target": target,
                    "value": edge.get("value", 1)
                })
        
        return {
            "nodes": clustered_nodes,
            "links": clustered_edges,
            "metadata": {
                "clustering": True,
                "original_nodes": len(nodes),
                "clustered_nodes": len(clustered_nodes),
                "clusters_created": len(cluster_map)
            }
        }
    
    def _generate_performance_hints(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance hints for rendering
        
        Args:
            graph_data: Optimized graph data
            
        Returns:
            Performance hints dictionary
        """
        num_nodes = len(graph_data.get("nodes", []))
        num_edges = len(graph_data.get("links", []))
        
        hints = {
            "use_webgl": num_nodes > self.config.webgl_threshold,
            "disable_animations": num_nodes > 1000,
            "reduce_labels": num_nodes > 500,
            "edge_opacity": min(1.0, 100.0 / num_edges) if num_edges > 100 else 1.0,
            "force_iterations": max(100, 1000 - num_nodes),
            "recommended_renderer": "canvas" if num_nodes > 500 else "svg"
        }
        
        # Level of detail recommendations
        if num_nodes > 5000:
            hints["lod_enabled"] = True
            hints["initial_zoom"] = 0.5
            hints["min_zoom"] = 0.1
            hints["max_zoom"] = 10
        else:
            hints["lod_enabled"] = False
            hints["initial_zoom"] = 1.0
            hints["min_zoom"] = 0.5
            hints["max_zoom"] = 5
        
        return hints
    
    def get_lod_level(self, zoom_level: float, node_count: int) -> int:
        """Determine level of detail based on zoom and node count
        
        Args:
            zoom_level: Current zoom level
            node_count: Number of nodes
            
        Returns:
            LOD level (0-3)
        """
        if node_count < 100:
            return 3  # Full detail
        
        if zoom_level > 2:
            return 3  # Full detail when zoomed in
        elif zoom_level > 1:
            return 2  # Medium detail
        elif zoom_level > 0.5:
            return 1  # Low detail
        else:
            return 0  # Minimal detail
    
    def should_render_labels(self, zoom_level: float, node_count: int) -> bool:
        """Determine if labels should be rendered
        
        Args:
            zoom_level: Current zoom level
            node_count: Number of nodes
            
        Returns:
            True if labels should be rendered
        """
        if node_count < 50:
            return True
        
        if node_count < 200:
            return zoom_level > 0.8
        
        return zoom_level > 1.5


if __name__ == "__main__":
    # Validation function
    logger.add("performance_optimizer_test.log", rotation="10 MB")
    
    # Create test data
    def create_large_graph(num_nodes: int, num_edges: int) -> Dict[str, Any]:
        """Create a large random graph for testing"""
        nodes = [{"id": f"node_{i}", "name": f"Node {i}", "group": i % 10} for i in range(num_nodes)]
        
        edges = []
        for _ in range(num_edges):
            source = random.choice(nodes)["id"]
            target = random.choice(nodes)["id"]
            if source != target:
                edges.append({"source": source, "target": target, "value": random.randint(1, 10)})
        
        return {"nodes": nodes, "links": edges}
    
    # Initialize optimizer
    config = OptimizationConfig(max_nodes=500, max_edges=2000)
    optimizer = PerformanceOptimizer(config)
    
    # Test with different graph sizes
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Small graph (no optimization needed)
    total_tests += 1
    small_graph = create_large_graph(50, 100)
    try:
        optimized = optimizer.optimize_graph(small_graph)
        if len(optimized["nodes"]) != 50:
            all_validation_failures.append(f"Small graph: Expected 50 nodes, got {len(optimized['nodes'])}")
        logger.info(f"Small graph optimization: {len(optimized['nodes'])} nodes, {len(optimized['links'])} edges")
    except Exception as e:
        all_validation_failures.append(f"Small graph: Failed with error {e}")
    
    # Test 2: Large graph (needs sampling)
    total_tests += 1
    large_graph = create_large_graph(2000, 5000)
    try:
        optimized = optimizer.optimize_graph(large_graph)
        if len(optimized["nodes"]) > config.max_nodes:
            all_validation_failures.append(f"Large graph: Too many nodes ({len(optimized['nodes'])})")
        if len(optimized["links"]) > config.max_edges:
            all_validation_failures.append(f"Large graph: Too many edges ({len(optimized['links'])})")
        logger.info(f"Large graph optimization: {len(optimized['nodes'])} nodes, {len(optimized['links'])} edges")
    except Exception as e:
        all_validation_failures.append(f"Large graph: Failed with error {e}")
    
    # Test 3: Performance hints
    total_tests += 1
    try:
        hints = optimizer._generate_performance_hints(optimized)
        if "use_webgl" not in hints:
            all_validation_failures.append("Performance hints: Missing use_webgl")
        if "recommended_renderer" not in hints:
            all_validation_failures.append("Performance hints: Missing recommended_renderer")
        logger.info(f"Performance hints: {hints}")
    except Exception as e:
        all_validation_failures.append(f"Performance hints: Failed with error {e}")
    
    # Test 4: LOD calculation
    total_tests += 1
    try:
        lod_high = optimizer.get_lod_level(3.0, 1000)
        lod_low = optimizer.get_lod_level(0.3, 1000)
        if lod_high <= lod_low:
            all_validation_failures.append(f"LOD calculation: High zoom ({lod_high}) <= Low zoom ({lod_low})")
        logger.info(f"LOD levels: High zoom={lod_high}, Low zoom={lod_low}")
    except Exception as e:
        all_validation_failures.append(f"LOD calculation: Failed with error {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Performance optimizer is working correctly")
        exit(0)