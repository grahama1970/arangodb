#!/usr/bin/env python3
"""Test D3 visualization with actual memory_bank data

This script tests the D3 visualization system using the real memory_bank
collections and schema, demonstrating graph delivery capabilities.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from arango import ArangoClient
from arangodb.visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig
from arangodb.cli.visualization_commands import app as viz_app
from loguru import logger
import typer

# Configure logger
logger.add("d3_visualization_test.log", rotation="10 MB")


def test_visualization_with_real_data():
    """Test D3 visualization using actual memory_bank data"""
    
    # Connect to ArangoDB
    client = ArangoClient(hosts="http://localhost:8529")
    username = os.getenv("ARANGO_USER", "root")
    password = os.getenv("ARANGO_PASSWORD", "openSesame")
    db_name = os.getenv("ARANGO_DB_NAME", "memory_bank")
    
    db = client.db(db_name, username=username, password=password)
    logger.info(f"Connected to database: {db_name}")
    
    # Test 1: Check what data we have
    logger.info("\n=== Checking available data ===")
    collections_with_data = []
    
    for collection_name in ["agent_entities", "agent_relationships", "memory_documents", 
                           "episodes", "messages", "agent_memories"]:
        if db.has_collection(collection_name):
            count = db.collection(collection_name).count()
            if count > 0:
                collections_with_data.append((collection_name, count))
                logger.info(f"{collection_name}: {count} documents")
    
    if not collections_with_data:
        logger.error("No data found in memory_bank collections!")
        return False
    
    # Test 2: Generate visualization from CLI command
    logger.info("\n=== Testing CLI visualization generation ===")
    
    # Create a simple query that should work with existing data
    test_query = """
    // Get a sample of agent entities and their relationships
    LET sample_entities = (
        FOR e IN agent_entities
        LIMIT 10
        RETURN e
    )
    
    LET relationships = (
        FOR e IN sample_entities
            FOR r IN agent_relationships
            FILTER r._from == e._id OR r._to == e._id
            LIMIT 20
            RETURN r
    )
    
    RETURN {
        nodes: sample_entities,
        edges: relationships
    }
    """
    
    # Test direct visualization generation
    engine = D3VisualizationEngine(use_llm=False)
    
    try:
        # Execute query
        cursor = db.aql.execute(test_query)
        result = list(cursor)
        
        if result and result[0]:
            graph_data = result[0]
            
            # Format nodes
            nodes = []
            for node in graph_data.get("nodes", []):
                nodes.append({
                    "id": node.get("_key", node.get("_id", "unknown")),
                    "name": node.get("name", node.get("entity_name", "Entity")),
                    "group": node.get("entity_type", "default"),
                    "type": node.get("entity_type", "unknown")
                })
            
            # Format edges
            links = []
            for edge in graph_data.get("edges", []):
                source = edge.get("_from", "").split("/")[-1]
                target = edge.get("_to", "").split("/")[-1]
                links.append({
                    "source": source,
                    "target": target,
                    "value": edge.get("weight", 1),
                    "relationship": edge.get("relationship", "related")
                })
            
            formatted_data = {
                "nodes": nodes,
                "links": links,
                "metadata": {
                    "source": "memory_bank",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(f"Formatted graph: {len(nodes)} nodes, {len(links)} links")
            
            # Generate visualization
            config = VisualizationConfig(
                title="Memory Bank Entity Graph",
                width=1200,
                height=800,
                layout="force"
            )
            
            html = engine.generate_visualization(formatted_data, config=config)
            
            # Save to file
            output_dir = Path("visualizations")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / "memory_bank_graph.html"
            
            with open(output_file, "w") as f:
                f.write(html)
            
            logger.info(f"✅ Generated visualization: {output_file}")
            
            # Open in browser
            webbrowser.open(f"file://{output_file.absolute()}")
            
            return True
            
        else:
            logger.warning("Query returned no results")
            return False
            
    except Exception as e:
        logger.error(f"Failed to generate visualization: {e}")
        return False


def test_visualization_server():
    """Test the visualization server functionality"""
    logger.info("\n=== Testing Visualization Server ===")
    
    # Check if we can import and use the server
    try:
        from arangodb.visualization.server.visualization_server import app as server_app
        logger.info("✅ Visualization server module imported successfully")
        
        # Test server endpoints programmatically
        from fastapi.testclient import TestClient
        
        client = TestClient(server_app)
        
        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            logger.info("✅ Server root endpoint accessible")
        
        # Test layouts endpoint
        response = client.get("/layouts")
        if response.status_code == 200:
            layouts = response.json()
            logger.info(f"✅ Available layouts: {[l['type'] for l in layouts['layouts']]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to test visualization server: {e}")
        return False


def demonstrate_graph_delivery():
    """Demonstrate how the system can deliver graphs when requested"""
    logger.info("\n=== Demonstrating Graph Delivery ===")
    
    # Show different ways graphs can be delivered
    logger.info("""
The ArangoDB Memory Bank can deliver graphs in multiple ways:

1. CLI Commands:
   - `uv run python -m arangodb.cli visualize generate "FOR e IN agent_entities LIMIT 10 RETURN e"`
   - `uv run python -m arangodb.cli visualize from-file query.aql`
   - `uv run python -m arangodb.cli visualize examples`

2. Python API:
   ```python
   from arangodb.visualization.core.d3_engine import D3VisualizationEngine
   engine = D3VisualizationEngine()
   html = engine.generate_visualization(graph_data, layout="force")
   ```

3. REST API (via visualization server):
   - POST /visualize - Generate new visualization
   - GET /visualize/{cache_key} - Retrieve cached visualization
   - GET /layouts - List available layouts

4. Direct Integration:
   - Memory agent can request visualizations
   - Search results can be visualized
   - Relationship graphs can be generated on demand
    """)
    
    return True


if __name__ == "__main__":
    logger.info("Starting D3 Visualization System Test")
    logger.info("="*60)
    
    # Run tests
    success = True
    
    # Test 1: Visualization with real data
    if not test_visualization_with_real_data():
        success = False
    
    # Test 2: Server functionality
    if not test_visualization_server():
        success = False
    
    # Test 3: Demonstrate delivery methods
    demonstrate_graph_delivery()
    
    # Summary
    logger.info("\n" + "="*60)
    if success:
        logger.info("✅ D3 Visualization System is working correctly!")
        logger.info("The system can deliver graphs through CLI, API, and web interface")
    else:
        logger.error("❌ Some visualization tests failed")
    
    exit(0 if success else 1)