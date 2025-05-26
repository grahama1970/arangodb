#!/usr/bin/env python3
"""Test D3 visualization with real ArangoDB data

This script tests the D3 visualization system with actual data from the memory_bank database,
demonstrating how the system can deliver graphs when requested.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from arango import ArangoClient
from arangodb.visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig
from loguru import logger

# Configure logger
logger.add("visualization_test.log", rotation="10 MB")


def connect_to_arangodb() -> Any:
    """Connect to ArangoDB using credentials from .env"""
    client = ArangoClient(hosts="http://localhost:8529")
    
    # Get credentials from environment
    username = os.getenv("ARANGO_USER", "root")
    password = os.getenv("ARANGO_PASSWORD", "openSesame")
    db_name = os.getenv("ARANGO_DB_NAME", "memory_bank")
    
    # Connect directly to the memory_bank database
    db = client.db(db_name, username=username, password=password)
    
    return db


def fetch_graph_data_from_arangodb(db: Any, query: str) -> Dict[str, Any]:
    """Execute AQL query and format results for D3.js
    
    Args:
        db: ArangoDB database connection
        query: AQL query that returns nodes and edges
        
    Returns:
        Dictionary with nodes and links for D3.js
    """
    try:
        cursor = db.aql.execute(query)
        result = list(cursor)
        
        if not result:
            logger.warning("Query returned no results")
            return {"nodes": [], "links": []}
        
        # Handle different query result formats
        if result and isinstance(result[0], dict):
            # If query returns a single object with nodes/edges
            if "nodes" in result[0] and "edges" in result[0]:
                nodes = result[0]["nodes"]
                edges = result[0]["edges"]
            else:
                # If query returns nodes directly
                nodes = result
                edges = []
        else:
            nodes = result
            edges = []
        
        # Format nodes for D3.js
        d3_nodes = []
        node_map = {}
        
        for i, node in enumerate(nodes):
            node_id = node.get("_id", node.get("id", f"node_{i}"))
            node_key = node.get("_key", node_id)
            
            d3_node = {
                "id": node_key,
                "name": node.get("name", node.get("content", node_key)[:50]),
                "group": node.get("entity_type", node.get("type", "default")),
                "type": node.get("entity_type", node.get("type", "unknown")),
                "created_at": node.get("created_at", ""),
                "fact_count": node.get("fact_count", 0),
                "original_id": node_id
            }
            
            # Add custom properties
            for key in ["content", "summary", "description", "facts"]:
                if key in node and node[key]:
                    d3_node[key] = str(node[key])[:200]  # Truncate long text
            
            d3_nodes.append(d3_node)
            node_map[node_id] = node_key
        
        # Format edges for D3.js
        d3_links = []
        for edge in edges:
            source_id = edge.get("_from", edge.get("source", ""))
            target_id = edge.get("_to", edge.get("target", ""))
            
            # Map to node keys
            source_key = node_map.get(source_id, source_id.split("/")[-1] if "/" in source_id else source_id)
            target_key = node_map.get(target_id, target_id.split("/")[-1] if "/" in target_id else target_id)
            
            # Only add link if both nodes exist
            if source_key in [n["id"] for n in d3_nodes] and target_key in [n["id"] for n in d3_nodes]:
                d3_link = {
                    "source": source_key,
                    "target": target_key,
                    "value": edge.get("weight", edge.get("strength", 1)),
                    "relationship": edge.get("relationship", edge.get("relation", "related")),
                    "type": edge.get("edge_type", "default")
                }
                d3_links.append(d3_link)
        
        return {
            "nodes": d3_nodes,
            "links": d3_links,
            "metadata": {
                "query": query,
                "node_count": len(d3_nodes),
                "link_count": len(d3_links),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch graph data: {e}")
        return {"nodes": [], "links": []}


def test_queries() -> List[Dict[str, Any]]:
    """Define test queries for different visualization scenarios"""
    return [
        {
            "name": "Document Memory Network",
            "description": "Shows memory documents and their relationships",
            "query": """
                // Get a sample of memory documents
                LET docs = (
                    FOR d IN memory_documents
                    SORT RAND()
                    LIMIT 20
                    RETURN d
                )
                
                LET relationships = (
                    FOR doc IN docs
                        FOR r IN memory_relationships
                        FILTER r._from == doc._id OR r._to == doc._id
                        LIMIT 50
                        RETURN DISTINCT r
                )
                
                // Get connected documents
                LET connected_ids = UNION(
                    relationships[*]._from,
                    relationships[*]._to
                )
                
                LET all_docs = (
                    FOR d IN memory_documents
                    FILTER d._id IN connected_ids
                    RETURN d
                )
                
                RETURN {
                    nodes: UNION_DISTINCT(docs, all_docs),
                    edges: relationships
                }
            """,
            "layout": "force"
        },
        {
            "name": "Episode Timeline",
            "description": "Temporal view of episodes",
            "query": """
                // Get recent episodes
                LET episodes = (
                    FOR e IN episodes
                    FILTER e.created_at != null
                    SORT e.created_at DESC
                    LIMIT 10
                    RETURN e
                )
                
                // Create temporal links between consecutive episodes
                LET temporal_edges = (
                    FOR i IN 0..LENGTH(episodes)-2
                        LET current = episodes[i]
                        LET next = episodes[i+1]
                        RETURN {
                            _from: next._id,
                            _to: current._id,
                            relationship: "precedes",
                            value: 1
                        }
                )
                
                RETURN {
                    nodes: episodes,
                    edges: temporal_edges
                }
            """,
            "layout": "tree"
        },
        {
            "name": "Agent Memory Graph",
            "description": "Agent entities and their relationships",
            "query": """
                // Get agent entities
                LET entities = (
                    FOR e IN agent_entities
                    LIMIT 30
                    RETURN e
                )
                
                LET relationships = (
                    FOR e IN entities
                        FOR r IN agent_relationships
                        FILTER r._from == e._id OR r._to == e._id
                        LIMIT 50
                        RETURN DISTINCT r
                )
                
                // Get connected entities
                LET connected_ids = UNION(
                    relationships[*]._from,
                    relationships[*]._to
                )
                
                LET all_entities = (
                    FOR e IN agent_entities
                    FILTER e._id IN connected_ids
                    RETURN e
                )
                
                RETURN {
                    nodes: UNION_DISTINCT(entities, all_entities),
                    edges: relationships
                }
            """,
            "layout": "force"
        },
        {
            "name": "Message Flow",
            "description": "Show message connections",
            "query": """
                // Get recent messages and their links
                LET msgs = (
                    FOR m IN messages
                    SORT m.created_at DESC
                    LIMIT 20
                    RETURN m
                )
                
                LET links = (
                    FOR m IN msgs
                        FOR l IN message_links
                        FILTER l._from == m._id OR l._to == m._id
                        LIMIT 30
                        RETURN DISTINCT l
                )
                
                // Get connected messages
                LET connected_ids = UNION(
                    links[*]._from,
                    links[*]._to
                )
                
                LET all_msgs = (
                    FOR m IN messages
                    FILTER m._id IN connected_ids
                    RETURN m
                )
                
                RETURN {
                    nodes: UNION_DISTINCT(msgs, all_msgs),
                    edges: links
                }
            """,
            "layout": "sankey"
        }
    ]


def generate_test_visualizations():
    """Generate test visualizations with real ArangoDB data"""
    logger.info("Starting D3 visualization tests with real data")
    
    # Connect to database
    try:
        db = connect_to_arangodb()
        logger.info(f"Connected to ArangoDB database: {db.name}")
    except Exception as e:
        logger.error(f"Failed to connect to ArangoDB: {e}")
        return
    
    # Initialize visualization engine
    engine = D3VisualizationEngine(use_llm=False)  # Disable LLM for testing
    
    # Create output directory
    output_dir = Path("visualizations")
    output_dir.mkdir(exist_ok=True)
    
    # Test each query
    test_results = []
    
    for test_case in test_queries():
        logger.info(f"\nTesting: {test_case['name']}")
        logger.info(f"Description: {test_case['description']}")
        
        try:
            # Fetch data from ArangoDB
            graph_data = fetch_graph_data_from_arangodb(db, test_case["query"])
            
            if not graph_data["nodes"]:
                logger.warning(f"No data returned for {test_case['name']}")
                test_results.append({
                    "test": test_case["name"],
                    "status": "no_data",
                    "nodes": 0,
                    "links": 0
                })
                continue
            
            logger.info(f"Fetched {len(graph_data['nodes'])} nodes and {len(graph_data['links'])} links")
            
            # Create visualization config
            config = VisualizationConfig(
                layout=test_case["layout"],
                title=test_case["name"],
                width=1200,
                height=800,
                show_labels=True,
                enable_zoom=True,
                enable_drag=True,
                physics_enabled=True
            )
            
            # Generate visualization
            html = engine.generate_visualization(
                graph_data,
                layout=test_case["layout"],
                config=config
            )
            
            # Save to file
            output_file = output_dir / f"{test_case['name'].lower().replace(' ', '_')}.html"
            with open(output_file, "w") as f:
                f.write(html)
            
            logger.info(f"✅ Generated visualization: {output_file}")
            
            test_results.append({
                "test": test_case["name"],
                "status": "success",
                "nodes": len(graph_data["nodes"]),
                "links": len(graph_data["links"]),
                "file": str(output_file)
            })
            
            # Open first visualization in browser
            if len(test_results) == 1:
                webbrowser.open(f"file://{output_file.absolute()}")
            
        except Exception as e:
            logger.error(f"Failed to generate visualization for {test_case['name']}: {e}")
            test_results.append({
                "test": test_case["name"],
                "status": "error",
                "error": str(e)
            })
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("VISUALIZATION TEST SUMMARY")
    logger.info("="*60)
    
    for result in test_results:
        if result["status"] == "success":
            logger.info(f"✅ {result['test']}: {result['nodes']} nodes, {result['links']} links")
        elif result["status"] == "no_data":
            logger.warning(f"⚠️  {result['test']}: No data returned from query")
        else:
            logger.error(f"❌ {result['test']}: {result.get('error', 'Unknown error')}")
    
    # Save test results
    results_file = output_dir / "test_results.json"
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2)
    
    logger.info(f"\nTest results saved to: {results_file}")
    logger.info(f"Visualizations saved to: {output_dir}/")
    
    # Test CLI integration
    logger.info("\nTesting CLI visualization commands...")
    
    # Test the visualization CLI commands
    cli_test_commands = [
        "uv run python -m arangodb visualize layouts",
        "uv run python -m arangodb visualize examples",
        # Don't test server command as it blocks
    ]
    
    for cmd in cli_test_commands:
        logger.info(f"\nTesting: {cmd}")
        exit_code = os.system(cmd)
        if exit_code == 0:
            logger.info(f"✅ Command successful: {cmd}")
        else:
            logger.error(f"❌ Command failed: {cmd}")


if __name__ == "__main__":
    generate_test_visualizations()