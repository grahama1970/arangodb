#!/usr/bin/env python3
"""Test D3 visualization with pizza test database

This tests the D3 visualization system using the self-contained pizza_test database.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from arango import ArangoClient
from arangodb.visualization.core.d3_engine import D3VisualizationEngine, VisualizationConfig
from loguru import logger

logger.add("pizza_d3_test.log", rotation="10 MB")


def test_pizza_visualizations():
    """Test D3 visualizations with pizza test database"""
    
    # Connect to pizza_test database
    client = ArangoClient(hosts="http://localhost:8529")
    username = os.getenv("ARANGO_USER", "root")
    password = os.getenv("ARANGO_PASSWORD", "openSesame")
    
    db = client.db("pizza_test", username=username, password=password)
    logger.info("Connected to pizza_test database")
    
    # Initialize visualization engine
    engine = D3VisualizationEngine(use_llm=False)
    
    # Create output directory
    output_dir = Path("visualizations/pizza_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test 1: Pizza Ingredients Network
    logger.info("\n=== Test 1: Pizza Ingredients Network ===")
    query1 = """
    // Get all pizzas and their ingredients
    LET pizzas = (FOR p IN pizzas RETURN p)
    LET ingredients = (FOR i IN ingredients RETURN i)
    LET edges = (FOR e IN pizza_ingredients RETURN e)
    
    RETURN {
        nodes: APPEND(
            (FOR p IN pizzas RETURN {
                id: p._key,
                name: p.name,
                group: "pizza",
                type: "pizza",
                price: p.price,
                category: p.category
            }),
            (FOR i IN ingredients RETURN {
                id: i._key,
                name: i.name,
                group: "ingredient",
                type: i.category,
                cost: i.cost
            })
        ),
        links: (FOR e IN edges RETURN {
            source: SPLIT(e._from, "/")[1],
            target: SPLIT(e._to, "/")[1],
            value: 1,
            amount: e.amount
        })
    }
    """
    
    result = list(db.aql.execute(query1))[0]
    logger.info(f"Pizza network: {len(result['nodes'])} nodes, {len(result['links'])} links")
    
    config = VisualizationConfig(
        title="Pizza Ingredients Network",
        layout="force",
        width=1400,
        height=900,
        node_color_field="group"
    )
    
    html = engine.generate_visualization(result, config=config)
    output_file = output_dir / "pizza_ingredients_network.html"
    with open(output_file, "w") as f:
        f.write(html)
    logger.info(f"✅ Generated: {output_file}")
    
    # Test 2: Customer Order Flow
    logger.info("\n=== Test 2: Customer Order Flow ===")
    query2 = """
    // Get customers, orders, and pizzas flow
    LET flow_data = (
        FOR c IN customers
            FOR o IN 1..1 OUTBOUND c customer_orders
                FOR p IN 1..1 OUTBOUND o order_items
                RETURN {
                    customer: c.name,
                    customer_key: c._key,
                    order: o._key,
                    pizza: p.name,
                    pizza_key: p._key,
                    total: o.total,
                    status: o.status
                }
    )
    
    RETURN {
        nodes: UNION_DISTINCT(
            (FOR f IN flow_data RETURN {id: f.customer_key, name: f.customer, group: "customer"}),
            (FOR f IN flow_data RETURN {id: f.order, name: CONCAT("Order ", f.order), group: "order", total: f.total}),
            (FOR f IN flow_data RETURN {id: f.pizza_key, name: f.pizza, group: "pizza"})
        ),
        links: UNION(
            (FOR f IN flow_data RETURN {source: f.customer_key, target: f.order, value: 1}),
            (FOR f IN flow_data RETURN {source: f.order, target: f.pizza_key, value: 1})
        )
    }
    """
    
    result = list(db.aql.execute(query2))[0]
    logger.info(f"Order flow: {len(result['nodes'])} nodes, {len(result['links'])} links")
    
    config = VisualizationConfig(
        title="Customer Order Flow",
        layout="sankey",
        width=1200,
        height=800
    )
    
    html = engine.generate_visualization(result, config=config)
    output_file = output_dir / "customer_order_flow.html"
    with open(output_file, "w") as f:
        f.write(html)
    logger.info(f"✅ Generated: {output_file}")
    
    # Test 3: Pizza Category Tree
    logger.info("\n=== Test 3: Pizza Category Tree ===")
    query3 = """
    // Create hierarchical structure by category
    LET categories = UNIQUE(FOR p IN pizzas RETURN p.category)
    
    RETURN {
        nodes: APPEND(
            [{id: "root", name: "All Pizzas", group: "root"}],
            (FOR c IN categories RETURN {id: c, name: UPPER(c), group: "category"}),
            (FOR p IN pizzas RETURN {id: p._key, name: p.name, group: "pizza", price: p.price})
        ),
        links: UNION(
            (FOR c IN categories RETURN {source: "root", target: c, value: 1}),
            (FOR p IN pizzas RETURN {source: p.category, target: p._key, value: 1})
        )
    }
    """
    
    result = list(db.aql.execute(query3))[0]
    logger.info(f"Category tree: {len(result['nodes'])} nodes, {len(result['links'])} links")
    
    config = VisualizationConfig(
        title="Pizza Category Hierarchy",
        layout="tree",
        width=1200,
        height=800,
        tree_orientation="vertical"
    )
    
    html = engine.generate_visualization(result, config=config)
    output_file = output_dir / "pizza_category_tree.html"
    with open(output_file, "w") as f:
        f.write(html)
    logger.info(f"✅ Generated: {output_file}")
    
    # Test 4: Review Network
    logger.info("\n=== Test 4: Review Network ===")
    query4 = """
    // Get reviews and what they're reviewing
    LET review_data = (
        FOR r IN reviews
            FOR p IN 1..1 OUTBOUND r review_for
            RETURN {
                review_id: r._key,
                rating: r.rating,
                comment: r.comment,
                pizza_id: p._key,
                pizza_name: p.name
            }
    )
    
    RETURN {
        nodes: UNION_DISTINCT(
            (FOR d IN review_data RETURN {
                id: d.review_id, 
                name: CONCAT("★", d.rating, " - ", SUBSTRING(d.comment, 0, 20), "..."),
                group: CONCAT("rating_", d.rating),
                rating: d.rating
            }),
            (FOR d IN review_data RETURN {
                id: d.pizza_id,
                name: d.pizza_name,
                group: "pizza"
            })
        ),
        links: (FOR d IN review_data RETURN {
            source: d.review_id,
            target: d.pizza_id,
            value: d.rating
        })
    }
    """
    
    result = list(db.aql.execute(query4))[0]
    logger.info(f"Review network: {len(result['nodes'])} nodes, {len(result['links'])} links")
    
    config = VisualizationConfig(
        title="Pizza Reviews Network",
        layout="force",
        width=1000,
        height=700,
        node_color_field="group"
    )
    
    html = engine.generate_visualization(result, config=config)
    output_file = output_dir / "pizza_reviews_network.html"
    with open(output_file, "w") as f:
        f.write(html)
    logger.info(f"✅ Generated: {output_file}")
    
    # Open first visualization
    webbrowser.open(f"file://{(output_dir / 'pizza_ingredients_network.html').absolute()}")
    
    logger.info(f"\n✅ All visualizations generated in: {output_dir}")
    logger.info("\nThe D3 visualization system is working correctly!")
    logger.info("It can deliver graphs through:")
    logger.info("  1. Direct API calls (as shown above)")
    logger.info("  2. CLI commands: uv run python -m arangodb.cli visualize generate <query>")
    logger.info("  3. Visualization server: uv run python -m arangodb.cli visualize server")
    
    return True


if __name__ == "__main__":
    try:
        test_pizza_visualizations()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        exit(1)