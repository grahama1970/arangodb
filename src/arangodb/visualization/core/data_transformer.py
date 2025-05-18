"""Data transformation utilities for ArangoDB to D3.js format conversion

This module provides utilities to transform ArangoDB query results into D3.js compatible formats.
Handles node and edge transformations, metadata extraction, and graph sampling for large datasets.

Links to third-party package documentation:
- D3.js Data Formats: https://d3js.org/d3-force
- ArangoDB Documentation: https://www.arangodb.com/docs/

Sample input (ArangoDB format):
{
    "vertices": [
        {"_id": "docs/1", "_key": "1", "name": "Document 1", "type": "document"},
        {"_id": "docs/2", "_key": "2", "name": "Document 2", "type": "document"}
    ],
    "edges": [
        {"_from": "docs/1", "_to": "docs/2", "type": "references", "weight": 1.0}
    ]
}

Expected output (D3.js format):
{
    "nodes": [
        {"id": "1", "name": "Document 1", "group": "document"},
        {"id": "2", "name": "Document 2", "group": "document"}
    ],
    "links": [
        {"source": "1", "target": "2", "type": "references", "value": 1.0}
    ]
}
"""

import json
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
import random
from loguru import logger


class DataTransformer:
    """Transform ArangoDB data structures to D3.js compatible formats"""
    
    def __init__(self):
        """Initialize the data transformer"""
        self.node_mapping = {}
        self.edge_mapping = {}
        self.metadata = {
            "node_count": 0,
            "edge_count": 0,
            "node_types": set(),
            "edge_types": set(),
            "node_attributes": set(),
            "edge_attributes": set()
        }
    
    def transform_graph_data(
        self, 
        arango_data: Dict[str, Any],
        node_id_field: str = "_key",
        edge_source_field: str = "_from",
        edge_target_field: str = "_to",
        node_group_field: Optional[str] = "type",
        edge_value_field: Optional[str] = "weight"
    ) -> Dict[str, Any]:
        """Transform ArangoDB graph data to D3.js format
        
        Args:
            arango_data: Dictionary with 'vertices' and 'edges' from ArangoDB
            node_id_field: Field to use as node ID
            edge_source_field: Field for edge source
            edge_target_field: Field for edge target
            node_group_field: Field to use for node grouping
            edge_value_field: Field to use for edge values
            
        Returns:
            Dictionary with 'nodes' and 'links' for D3.js
        """
        logger.info("Transforming ArangoDB data to D3.js format")
        
        # Extract vertices and edges
        vertices = arango_data.get("vertices", [])
        edges = arango_data.get("edges", [])
        
        # Handle invalid data types
        if not isinstance(vertices, list):
            logger.warning(f"Invalid vertices data type: {type(vertices)}. Using empty list.")
            vertices = []
        if not isinstance(edges, list):
            logger.warning(f"Invalid edges data type: {type(edges)}. Using empty list.")
            edges = []
        
        # Transform nodes
        nodes = self._transform_nodes(
            vertices, 
            node_id_field, 
            node_group_field
        )
        
        # Transform edges
        links = self._transform_edges(
            edges,
            edge_source_field, 
            edge_target_field,
            edge_value_field
        )
        
        # Update metadata
        self._extract_metadata(vertices, edges)
        
        # Convert sets to lists for JSON serialization
        metadata = dict(self.metadata)
        for key, value in metadata.items():
            if isinstance(value, set):
                metadata[key] = list(value)
        
        result = {
            "nodes": nodes,
            "links": links,
            "metadata": metadata
        }
        
        logger.info(f"Transformed {len(nodes)} nodes and {len(links)} links")
        return result
    
    def _transform_nodes(
        self, 
        vertices: List[Dict[str, Any]],
        id_field: str,
        group_field: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Transform ArangoDB vertices to D3.js nodes
        
        Args:
            vertices: List of vertex documents
            id_field: Field to use as node ID
            group_field: Field to use for grouping
            
        Returns:
            List of D3.js node objects
        """
        nodes = []
        
        for vertex in vertices:
            # Skip invalid vertex entries
            if not isinstance(vertex, dict):
                logger.warning(f"Skipping invalid vertex: {vertex}")
                continue
                
            # Extract ID (handle both _key and full _id)
            vertex_id = vertex.get(id_field, "")
            if "/" in vertex_id:
                vertex_id = vertex_id.split("/")[-1]
            
            # Build node object
            node = {
                "id": vertex_id,
                "name": vertex.get("name", vertex_id),
            }
            
            # Add group if specified
            if group_field and group_field in vertex:
                node["group"] = vertex[group_field]
                self.metadata["node_types"].add(vertex[group_field])
            
            # Copy additional attributes
            for key, value in vertex.items():
                if key not in ["_id", "_key", "_rev"] and key not in node:
                    node[key] = value
                    self.metadata["node_attributes"].add(key)
            
            nodes.append(node)
            self.node_mapping[vertex.get("_id", vertex_id)] = vertex_id
        
        self.metadata["node_count"] = len(nodes)
        return nodes
    
    def _transform_edges(
        self,
        edges: List[Dict[str, Any]],
        source_field: str,
        target_field: str,
        value_field: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Transform ArangoDB edges to D3.js links
        
        Args:
            edges: List of edge documents
            source_field: Field for source node
            target_field: Field for target node  
            value_field: Field for edge value
            
        Returns:
            List of D3.js link objects
        """
        links = []
        
        for edge in edges:
            # Skip invalid edge entries
            if not isinstance(edge, dict):
                logger.warning(f"Skipping invalid edge: {edge}")
                continue
                
            # Extract source and target IDs
            source_id = edge.get(source_field, "")
            target_id = edge.get(target_field, "")
            
            # Handle full document IDs
            if "/" in source_id:
                source_id = source_id.split("/")[-1]
            if "/" in target_id:
                target_id = target_id.split("/")[-1]
            
            # Build link object
            link = {
                "source": source_id,
                "target": target_id
            }
            
            # Add value if specified
            if value_field and value_field in edge:
                link["value"] = edge[value_field]
            else:
                link["value"] = 1
            
            # Add edge type if available
            if "type" in edge:
                link["type"] = edge["type"]
                self.metadata["edge_types"].add(edge["type"])
            
            # Copy additional attributes
            for key, value in edge.items():
                if key not in ["_id", "_key", "_from", "_to", "_rev"] and key not in link:
                    link[key] = value
                    self.metadata["edge_attributes"].add(key)
            
            links.append(link)
            
        self.metadata["edge_count"] = len(links)
        return links
    
    def _extract_metadata(self, vertices: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> None:
        """Extract metadata from the graph data
        
        Args:
            vertices: List of vertices
            edges: List of edges
        """
        # Calculate node degrees
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for edge in edges:
            source = edge.get("_from", "").split("/")[-1]
            target = edge.get("_to", "").split("/")[-1]
            out_degree[source] += 1
            in_degree[target] += 1
        
        # Find important nodes
        max_in_degree = max(in_degree.values()) if in_degree else 0
        max_out_degree = max(out_degree.values()) if out_degree else 0
        
        self.metadata["max_in_degree"] = max_in_degree
        self.metadata["max_out_degree"] = max_out_degree
        self.metadata["highly_connected_nodes"] = [
            node for node, degree in in_degree.items() 
            if degree > max_in_degree * 0.8
        ]
    
    def sample_large_graph(
        self, 
        graph_data: Dict[str, Any],
        max_nodes: int = 1000,
        sampling_method: str = "random"
    ) -> Dict[str, Any]:
        """Sample a large graph to reduce size for visualization
        
        Args:
            graph_data: Full graph data
            max_nodes: Maximum number of nodes to include
            sampling_method: Method to use ('random', 'importance', 'cluster')
            
        Returns:
            Sampled graph data
        """
        nodes = graph_data["nodes"]
        links = graph_data["links"]
        
        if len(nodes) <= max_nodes:
            return graph_data
        
        logger.info(f"Sampling graph from {len(nodes)} to {max_nodes} nodes")
        
        if sampling_method == "random":
            sampled_nodes = self._random_sample(nodes, max_nodes)
        elif sampling_method == "importance":
            sampled_nodes = self._importance_sample(nodes, links, max_nodes)
        elif sampling_method == "cluster":
            sampled_nodes = self._cluster_sample(nodes, links, max_nodes)
        else:
            raise ValueError(f"Unknown sampling method: {sampling_method}")
        
        # Get node IDs
        sampled_ids = {node["id"] for node in sampled_nodes}
        
        # Filter links
        sampled_links = [
            link for link in links
            if link["source"] in sampled_ids and link["target"] in sampled_ids
        ]
        
        return {
            "nodes": sampled_nodes,
            "links": sampled_links,
            "metadata": {
                **graph_data.get("metadata", {}),
                "sampled": True,
                "original_node_count": len(nodes),
                "original_edge_count": len(links),
                "sampling_method": sampling_method
            }
        }
    
    def _random_sample(self, nodes: List[Dict[str, Any]], max_nodes: int) -> List[Dict[str, Any]]:
        """Random sampling of nodes"""
        return random.sample(nodes, max_nodes)
    
    def _importance_sample(
        self, 
        nodes: List[Dict[str, Any]], 
        links: List[Dict[str, Any]], 
        max_nodes: int
    ) -> List[Dict[str, Any]]:
        """Sample based on node importance (degree)"""
        # Calculate node degrees
        degree = defaultdict(int)
        for link in links:
            degree[link["source"]] += 1
            degree[link["target"]] += 1
        
        # Sort nodes by degree
        nodes_with_degree = [(node, degree[node["id"]]) for node in nodes]
        nodes_with_degree.sort(key=lambda x: x[1], reverse=True)
        
        # Take top nodes by degree
        return [node for node, _ in nodes_with_degree[:max_nodes]]
    
    def _cluster_sample(
        self, 
        nodes: List[Dict[str, Any]], 
        links: List[Dict[str, Any]], 
        max_nodes: int
    ) -> List[Dict[str, Any]]:
        """Sample by selecting representative nodes from clusters"""
        # Group nodes by type/group if available
        clusters = defaultdict(list)
        
        for node in nodes:
            group = node.get("group", "default")
            clusters[group].append(node)
        
        # Sample proportionally from each cluster
        sampled_nodes = []
        nodes_per_cluster = max_nodes // len(clusters) if clusters else max_nodes
        
        for group, cluster_nodes in clusters.items():
            sample_size = min(len(cluster_nodes), nodes_per_cluster)
            sampled_nodes.extend(random.sample(cluster_nodes, sample_size))
        
        # Fill remaining slots if needed
        remaining = max_nodes - len(sampled_nodes)
        if remaining > 0:
            unsampled = [n for n in nodes if n not in sampled_nodes]
            if unsampled:
                sampled_nodes.extend(random.sample(unsampled, min(remaining, len(unsampled))))
        
        return sampled_nodes[:max_nodes]
    
    def convert_to_hierarchical(
        self, 
        graph_data: Dict[str, Any],
        root_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert graph data to hierarchical format for tree layouts
        
        Args:
            graph_data: Graph data with nodes and links
            root_id: ID of root node (if None, finds node with no incoming edges)
            
        Returns:
            Hierarchical data structure
        """
        nodes = {node["id"]: node for node in graph_data["nodes"]}
        
        # Build adjacency list
        children = defaultdict(list)
        parents = defaultdict(list)
        
        for link in graph_data["links"]:
            children[link["source"]].append(link["target"])
            parents[link["target"]].append(link["source"])
        
        # Find root if not specified
        if root_id is None:
            # Find nodes with no parents
            potential_roots = [
                node_id for node_id in nodes
                if not parents[node_id]
            ]
            root_id = potential_roots[0] if potential_roots else list(nodes.keys())[0]
        
        # Build tree recursively
        def build_tree(node_id: str, visited: Set[str]) -> Dict[str, Any]:
            if node_id in visited:
                return None
            
            visited.add(node_id)
            node = nodes.get(node_id, {"id": node_id, "name": node_id})
            
            tree_node = {
                "id": node["id"],
                "name": node.get("name", node["id"]),
                "data": node
            }
            
            # Add children
            child_nodes = []
            for child_id in children[node_id]:
                child_tree = build_tree(child_id, visited)
                if child_tree:
                    child_nodes.append(child_tree)
            
            if child_nodes:
                tree_node["children"] = child_nodes
            
            return tree_node
        
        visited = set()
        root = build_tree(root_id, visited)
        
        # Handle disconnected nodes
        orphans = []
        for node_id in nodes:
            if node_id not in visited:
                orphan_tree = build_tree(node_id, visited)
                if orphan_tree:
                    orphans.append(orphan_tree)
        
        if orphans:
            # Create artificial root if there are orphans
            root = {
                "id": "_root",
                "name": "Root",
                "children": [root] + orphans if root else orphans
            }
        
        return root


if __name__ == "__main__":
    # Validation tests
    transformer = DataTransformer()
    
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Basic transformation
    total_tests += 1
    test_arango_data = {
        "vertices": [
            {"_id": "docs/1", "_key": "1", "name": "Document 1", "type": "document"},
            {"_id": "docs/2", "_key": "2", "name": "Document 2", "type": "document"},
            {"_id": "docs/3", "_key": "3", "name": "Document 3", "type": "concept"}
        ],
        "edges": [
            {"_from": "docs/1", "_to": "docs/2", "type": "references", "weight": 1.0},
            {"_from": "docs/2", "_to": "docs/3", "type": "describes", "weight": 0.8}
        ]
    }
    
    result = transformer.transform_graph_data(test_arango_data)
    
    # Check nodes
    if len(result["nodes"]) != 3:
        all_validation_failures.append(f"Basic transformation: Expected 3 nodes, got {len(result['nodes'])}")
    
    # Check links
    if len(result["links"]) != 2:
        all_validation_failures.append(f"Basic transformation: Expected 2 links, got {len(result['links'])}")
    
    # Check metadata
    if result["metadata"]["node_count"] != 3:
        all_validation_failures.append(f"Basic transformation: Wrong node count in metadata")
    
    # Test 2: Large graph sampling
    total_tests += 1
    large_data = {
        "nodes": [{"id": str(i), "name": f"Node {i}"} for i in range(2000)],
        "links": [{"source": str(i), "target": str(i+1), "value": 1} for i in range(1999)]
    }
    
    sampled = transformer.sample_large_graph(large_data, max_nodes=500)
    
    if len(sampled["nodes"]) > 500:
        all_validation_failures.append(f"Graph sampling: Too many nodes ({len(sampled['nodes'])})")
    
    if not sampled["metadata"].get("sampled"):
        all_validation_failures.append("Graph sampling: Missing 'sampled' flag in metadata")
    
    # Test 3: Hierarchical conversion
    total_tests += 1
    graph_data = {
        "nodes": [
            {"id": "1", "name": "Root"},
            {"id": "2", "name": "Child 1"},
            {"id": "3", "name": "Child 2"},
            {"id": "4", "name": "Grandchild"}
        ],
        "links": [
            {"source": "1", "target": "2"},
            {"source": "1", "target": "3"},
            {"source": "2", "target": "4"}
        ]
    }
    
    hierarchical = transformer.convert_to_hierarchical(graph_data, root_id="1")
    
    if hierarchical["id"] != "1":
        all_validation_failures.append(f"Hierarchical conversion: Wrong root ID")
    
    if "children" not in hierarchical:
        all_validation_failures.append("Hierarchical conversion: Missing children")
    
    # Test 4: Error handling for invalid data
    total_tests += 1
    invalid_data = {
        "vertices": "not a list",  # Invalid format
        "edges": []
    }
    
    try:
        # Should handle gracefully
        result = transformer.transform_graph_data(invalid_data)
        if result["nodes"]:  # Should be empty
            all_validation_failures.append("Invalid data handling: Should return empty nodes")
    except Exception as e:
        all_validation_failures.append(f"Invalid data handling: Unexpected error {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("DataTransformer is validated and ready for use")
        print("\nTransformation metrics:")
        print(f"  - Nodes transformed: {result['metadata']['node_count']}")
        print(f"  - Edges transformed: {result['metadata']['edge_count']}")
        print(f"  - Node types found: {result['metadata']['node_types']}")
        exit(0)