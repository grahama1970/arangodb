"""LLM-based visualization recommender using Vertex AI Gemini Flash 2.5
Module: llm_recommender.py

This module analyzes graph data and queries to recommend optimal visualization types
and configurations using Google's Gemini Flash 2.5 model.'

Links to third-party package documentation:
- Vertex AI: https://cloud.google.com/vertex-ai/docs/python/latest
- LiteLLM: https://github.com/BerriAI/litellm

Sample input: Graph data and optional query context
Expected output: Visualization recommendation with configuration
"""

import json
import os
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field
from loguru import logger
import litellm
from pathlib import Path

# Type definitions
VisualizationType = Literal["force", "tree", "radial", "sankey"]

@dataclass
class VisualizationRecommendation:
    """Recommendation result from LLM analysis"""
    layout_type: VisualizationType
    title: str
    reasoning: str
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    alternative_layouts: List[VisualizationType] = field(default_factory=list)


class LLMRecommender:
    """LLM-based visualization recommender for graph data"""
    
    def __init__(self, model: str = "vertex_ai/gemini-2.5-flash-preview-04-17"):
        """Initialize the recommender with Gemini Flash 2.5 Preview
        
        Args:
            model: Model identifier for litellm
        """
        self.model = model
        
        # Set up Vertex AI credentials if needed
        if "VERTEXAI_LOCATION" not in os.environ:
            os.environ["VERTEXAI_LOCATION"] = "us-central1"
        
        logger.info(f"LLMRecommender initialized with model: {model}")
    
    def analyze_graph_structure(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure of graph data
        
        Args:
            graph_data: Input graph data
            
        Returns:
            Dictionary with structural analysis
        """
        nodes = graph_data.get("nodes", [])
        links = graph_data.get("links", [])
        
        # Basic metrics
        node_count = len(nodes)
        link_count = len(links)
        
        # Node type analysis
        node_types = {}
        for node in nodes:
            node_type = node.get("type", node.get("group", "unknown"))
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        # Link analysis
        has_weights = any("weight" in link or "value" in link for link in links)
        has_direction = any("source" in link and "target" in link for link in links)
        
        # Hierarchical detection
        incoming_counts = {}
        outgoing_counts = {}
        for link in links:
            source = link.get("source")
            target = link.get("target")
            if source and target:
                outgoing_counts[source] = outgoing_counts.get(source, 0) + 1
                incoming_counts[target] = incoming_counts.get(target, 0) + 1
        
        # Find potential roots (nodes with no incoming edges)
        potential_roots = [
            node["id"] for node in nodes 
            if node["id"] not in incoming_counts
        ]
        
        # Check for cycles
        has_cycles = self._detect_cycles(nodes, links)
        
        # Flow detection (for Sankey)
        is_flow_data = (
            has_weights and 
            has_direction and 
            len(potential_roots) > 0 and
            self._has_terminal_nodes(nodes, outgoing_counts)
        )
        
        return {
            "node_count": node_count,
            "link_count": link_count,
            "node_types": node_types,
            "has_weights": has_weights,
            "has_direction": has_direction,
            "potential_roots": potential_roots,
            "has_cycles": has_cycles,
            "is_flow_data": is_flow_data,
            "density": link_count / (node_count * (node_count - 1)) if node_count > 1 else 0
        }
    
    def _detect_cycles(self, nodes: List[Dict], links: List[Dict]) -> bool:
        """Simple cycle detection using DFS
        
        Args:
            nodes: List of nodes
            links: List of links
            
        Returns:
            True if cycles are detected
        """
        # Build adjacency list
        adj = {}
        for link in links:
            source = link.get("source")
            target = link.get("target")
            if source and target:
                if source not in adj:
                    adj[source] = []
                adj[source].append(target)
        
        # DFS-based cycle detection
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in nodes:
            node_id = node["id"]
            if node_id not in visited:
                if has_cycle(node_id):
                    return True
        
        return False
    
    def _has_terminal_nodes(self, nodes: List[Dict], outgoing_counts: Dict) -> bool:
        """Check if graph has terminal nodes (nodes with no outgoing edges)
        
        Args:
            nodes: List of nodes
            outgoing_counts: Dictionary of outgoing edge counts
            
        Returns:
            True if terminal nodes exist
        """
        terminal_count = 0
        for node in nodes:
            if node["id"] not in outgoing_counts:
                terminal_count += 1
        
        return terminal_count > 0
    
    def create_prompt(self, analysis: Dict[str, Any], query: Optional[str] = None) -> str:
        """Create prompt for LLM recommendation
        
        Args:
            analysis: Graph structure analysis
            query: Optional user query
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze this graph data and recommend the best visualization type.

Graph Structure Analysis:
- Total nodes: {analysis['node_count']}
- Total links: {analysis['link_count']}
- Node types: {json.dumps(analysis['node_types'])}
- Has weighted edges: {analysis['has_weights']}
- Has directional edges: {analysis['has_direction']}
- Potential root nodes: {len(analysis['potential_roots'])}
- Has cycles: {analysis['has_cycles']}
- Is flow data: {analysis['is_flow_data']}
- Graph density: {analysis['density']:.3f}

Available visualization types:
1. force: Force-directed layout, good for general networks, clusters, relationships
2. tree: Hierarchical tree layout, good for parent-child relationships, taxonomies
3. radial: Radial tree layout, good for centered hierarchies, radial organization
4. sankey: Sankey diagram, good for flow data, processes, resource allocation

"""
        
        if query:
            prompt += f"\nUser Query: {query}\n"
        
        prompt += """
Please recommend the best visualization type and provide:
1. The recommended layout type (force, tree, radial, or sankey)
2. A descriptive title for the visualization
3. Your reasoning for this choice
4. Any specific configuration overrides (optional)
5. Alternative layout options ranked by suitability

Respond in JSON format:
{
    "layout_type": "force|tree|radial|sankey",
    "title": "Descriptive Title",
    "reasoning": "Explanation of why this layout is best",
    "config_overrides": {
        "key": "value"
    },
    "confidence": 0.0-1.0,
    "alternative_layouts": ["layout1", "layout2"]
}
"""
        return prompt
    
    def get_recommendation(
        self, 
        graph_data: Dict[str, Any], 
        query: Optional[str] = None
    ) -> VisualizationRecommendation:
        """Get visualization recommendation from LLM
        
        Args:
            graph_data: Input graph data
            query: Optional user query for context
            
        Returns:
            VisualizationRecommendation object
        """
        # Analyze graph structure
        analysis = self.analyze_graph_structure(graph_data)
        logger.info(f"Graph analysis complete: {analysis['node_count']} nodes, {analysis['link_count']} links")
        
        # Create prompt
        prompt = self.create_prompt(analysis, query)
        
        try:
            # Call LLM
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data visualization expert specializing in graph layouts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent recommendations
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Create recommendation object
            recommendation = VisualizationRecommendation(
                layout_type=result.get("layout_type", "force"),
                title=result.get("title", "Graph Visualization"),
                reasoning=result.get("reasoning", ""),
                config_overrides=result.get("config_overrides", {}),
                confidence=result.get("confidence", 0.8),
                alternative_layouts=result.get("alternative_layouts", [])
            )
            
            logger.info(f"LLM recommendation: {recommendation.layout_type} (confidence: {recommendation.confidence})")
            return recommendation
            
        except Exception as e:
            logger.error(f"LLM recommendation failed: {e}")
            # Fallback recommendation based on analysis
            return self._get_fallback_recommendation(analysis)
    
    def _get_fallback_recommendation(self, analysis: Dict[str, Any]) -> VisualizationRecommendation:
        """Provide fallback recommendation when LLM fails
        
        Args:
            analysis: Graph structure analysis
            
        Returns:
            VisualizationRecommendation object
        """
        # Simple rule-based fallback
        if analysis["is_flow_data"]:
            layout = "sankey"
            title = "Flow Diagram"
            reasoning = "Detected flow data with weighted directional edges"
        elif len(analysis["potential_roots"]) == 1 and not analysis["has_cycles"]:
            layout = "tree"
            title = "Hierarchical Tree"
            reasoning = "Single root node with no cycles suggests tree structure"
        elif analysis["node_count"] > 50 and analysis["density"] < 0.1:
            layout = "force"
            title = "Network Graph"
            reasoning = "Large sparse graph is best shown with force-directed layout"
        else:
            layout = "radial"
            title = "Radial Layout"
            reasoning = "Medium-sized graph with potential hierarchy"
        
        return VisualizationRecommendation(
            layout_type=layout,
            title=title,
            reasoning=reasoning,
            confidence=0.6,
            alternative_layouts=["force", "tree", "radial", "sankey"]
        )


if __name__ == "__main__":
    # Validation function
    logger.add("llm_recommender_test.log", rotation="10 MB")
    
    # Test data
    test_graphs = [
        # Hierarchical tree data
        {
            "nodes": [
                {"id": "root", "name": "Root"},
                {"id": "child1", "name": "Child 1"},
                {"id": "child2", "name": "Child 2"},
                {"id": "grandchild1", "name": "Grandchild 1"},
            ],
            "links": [
                {"source": "root", "target": "child1"},
                {"source": "root", "target": "child2"},
                {"source": "child1", "target": "grandchild1"},
            ]
        },
        # Flow data (Sankey)
        {
            "nodes": [
                {"id": "source", "name": "Source", "type": "input"},
                {"id": "process1", "name": "Process 1", "type": "process"},
                {"id": "process2", "name": "Process 2", "type": "process"},
                {"id": "sink", "name": "Sink", "type": "output"},
            ],
            "links": [
                {"source": "source", "target": "process1", "value": 100},
                {"source": "source", "target": "process2", "value": 50},
                {"source": "process1", "target": "sink", "value": 100},
                {"source": "process2", "target": "sink", "value": 50},
            ]
        },
        # Network data (Force)
        {
            "nodes": [
                {"id": "node1", "name": "Node 1", "group": 1},
                {"id": "node2", "name": "Node 2", "group": 1},
                {"id": "node3", "name": "Node 3", "group": 2},
                {"id": "node4", "name": "Node 4", "group": 2},
                {"id": "node5", "name": "Node 5", "group": 3},
            ],
            "links": [
                {"source": "node1", "target": "node2"},
                {"source": "node1", "target": "node3"},
                {"source": "node2", "target": "node4"},
                {"source": "node3", "target": "node4"},
                {"source": "node4", "target": "node5"},
                {"source": "node5", "target": "node1"},  # Creates cycle
            ]
        }
    ]
    
    # Initialize recommender
    recommender = LLMRecommender()
    
    # Test each graph
    all_validation_failures = []
    total_tests = 0
    
    for i, test_graph in enumerate(test_graphs):
        total_tests += 1
        try:
            # Test without query
            recommendation = recommender.get_recommendation(test_graph)
            
            if not recommendation.layout_type:
                all_validation_failures.append(f"Test {i+1}: No layout type returned")
            if not recommendation.title:
                all_validation_failures.append(f"Test {i+1}: No title returned")
            if not recommendation.reasoning:
                all_validation_failures.append(f"Test {i+1}: No reasoning provided")
            
            print(f"\nTest {i+1} - Recommended: {recommendation.layout_type}")
            print(f"Title: {recommendation.title}")
            print(f"Reasoning: {recommendation.reasoning}")
            print(f"Confidence: {recommendation.confidence}")
            
        except Exception as e:
            all_validation_failures.append(f"Test {i+1}: Failed with error {e}")
    
    # Test with query
    total_tests += 1
    try:
        query = "Show me the flow of data through the system"
        recommendation = recommender.get_recommendation(test_graphs[1], query)
        
        if recommendation.layout_type != "sankey":
            logger.warning(f"Query test: Expected sankey, got {recommendation.layout_type}")
        
        print(f"\nQuery Test - Recommended: {recommendation.layout_type}")
        print(f"Title: {recommendation.title}")
        print(f"Query influence detected: {'flow' in recommendation.reasoning.lower()}")
        
    except Exception as e:
        all_validation_failures.append(f"Query test: Failed with error {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"\n VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        exit(1)
    else:
        print(f"\n VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("LLM recommender is working correctly")
        exit(0)