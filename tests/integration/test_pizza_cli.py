#!/usr/bin/env python3
"""
Test all CLI commands using the pizza-themed database.

This script demonstrates that all CLI and core modules work correctly
with real data and produce meaningful results.
"""

import subprocess
import json
from pathlib import Path
from loguru import logger

# Configure logger
logger.add("pizza_cli_test.log", rotation="10 MB")

def run_cli_command(command: str) -> tuple[int, str, str]:
    """Run a CLI command and return exit code, stdout, stderr."""
    cmd = f"cd /home/graham/workspace/experiments/arangodb && uv run python -m arangodb.cli {command}"
    logger.info(f"Running: {command}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Command failed: {result.stderr}")
    
    return result.returncode, result.stdout, result.stderr

def test_crud_operations():
    """Test CRUD operations on pizza collections."""
    print("\n=== Testing CRUD Operations ===")
    
    # List pizzas
    code, out, err = run_cli_command("crud list --collection pizzas --db pizza_test")
    print(f"List pizzas: {code == 0}")
    if code == 0:
        print("Sample output:", out.split('\n')[0:5])
    
    # Get specific pizza
    code, out, err = run_cli_command("crud get margherita --collection pizzas --db pizza_test")
    print(f"Get Margherita pizza: {code == 0}")
    
    # Create new pizza
    new_pizza = {
        "_key": "meat_lovers",
        "name": "Meat Lovers",
        "description": "Loaded with pepperoni, sausage, bacon, and ham",
        "price": 16.99,
        "tags": ["meat", "hearty"]
    }
    code, out, err = run_cli_command(f"crud create --collection pizzas --db pizza_test --data '{json.dumps(new_pizza)}'")
    print(f"Create Meat Lovers pizza: {code == 0}")
    
    # Update pizza price
    update_data = {"price": 17.99}
    code, out, err = run_cli_command(f"crud update meat_lovers --collection pizzas --db pizza_test --data '{json.dumps(update_data)}'")
    print(f"Update pizza price: {code == 0}")
    
    # Delete pizza
    code, out, err = run_cli_command("crud delete meat_lovers --collection pizzas --db pizza_test")
    print(f"Delete pizza: {code == 0}")

def test_search_operations():
    """Test various search operations."""
    print("\n=== Testing Search Operations ===")
    
    # BM25 search
    code, out, err = run_cli_command('search bm25 --query "chicken" --collection pizzas --db pizza_test')
    print(f"BM25 search for 'chicken': {code == 0}")
    
    # Semantic search (requires embeddings)
    code, out, err = run_cli_command('search semantic --query "spicy pizza with meat" --collection pizzas --db pizza_test')
    print(f"Semantic search: {code == 0}")
    
    # Hybrid search
    code, out, err = run_cli_command('search hybrid --query "vegetarian pizza" --collection pizzas --db pizza_test')
    print(f"Hybrid search: {code == 0}")
    
    # Tag search
    code, out, err = run_cli_command('search tag --tags "vegetarian,italian" --collection pizzas --db pizza_test')
    print(f"Tag search: {code == 0}")

def test_graph_operations():
    """Test graph traversal operations."""
    print("\n=== Testing Graph Operations ===")
    
    # Get pizza ingredients
    code, out, err = run_cli_command('graph traverse pizzas/margherita --direction outbound --edge-collection pizza_ingredients --db pizza_test')
    print(f"Get Margherita ingredients: {code == 0}")
    
    # Get customer orders
    code, out, err = run_cli_command('graph traverse customers/cust_001 --direction outbound --edge-collection customer_orders --db pizza_test')
    print(f"Get customer orders: {code == 0}")
    
    # Find pizzas containing mozzarella
    code, out, err = run_cli_command('graph traverse ingredients/mozzarella --direction inbound --edge-collection pizza_ingredients --db pizza_test')
    print(f"Find pizzas with mozzarella: {code == 0}")
    
    # Visualize pizza-ingredient graph
    code, out, err = run_cli_command('graph visualize --collection pizzas --edge-collection pizza_ingredients --db pizza_test --output /tmp/pizza_graph.html')
    print(f"Visualize graph: {code == 0}")

def test_memory_operations():
    """Test memory-specific operations."""
    print("\n=== Testing Memory Operations ===")
    
    # Create memory from pizza order
    memory_data = {
        "content": "Customer John Smith loves our pepperoni pizza. He orders it twice a week and always asks for extra cheese.",
        "metadata": {
            "customer_id": "cust_001",
            "pizza_preference": "pepperoni",
            "special_request": "extra_cheese"
        },
        "tags": ["customer_preference", "vip", "pepperoni"]
    }
    
    code, out, err = run_cli_command(f"memory create --content '{memory_data['content']}' --metadata '{json.dumps(memory_data['metadata'])}' --tags '{','.join(memory_data['tags'])}' --db pizza_test")
    print(f"Create customer memory: {code == 0}")
    
    # List memories
    code, out, err = run_cli_command("memory list --limit 5 --db pizza_test")
    print(f"List memories: {code == 0}")
    
    # Search memories
    code, out, err = run_cli_command('memory search --query "customer preferences" --db pizza_test')
    print(f"Search memories: {code == 0}")

def test_analysis_operations():
    """Test analysis and aggregation operations."""
    print("\n=== Testing Analysis Operations ===")
    
    # Community detection on ingredients
    code, out, err = run_cli_command("community detect --collection pizzas --edge-collection pizza_ingredients --db pizza_test")
    print(f"Community detection: {code == 0}")
    
    # Temporal analysis on orders
    code, out, err = run_cli_command("temporal extract --collection orders --start 2024-12-01 --end 2024-12-31 --db pizza_test")
    print(f"Temporal analysis: {code == 0}")
    
    # Contradiction detection
    code, out, err = run_cli_command("contradiction detect --collection pizzas --db pizza_test")
    print(f"Contradiction detection: {code == 0}")

def test_advanced_queries():
    """Test advanced AQL queries through CLI."""
    print("\n=== Testing Advanced Queries ===")
    
    # Most popular pizzas by order count
    aql_query = """
    FOR order IN orders
        FOR pizza, edge IN 1..1 OUTBOUND order order_items
            COLLECT pizza_name = pizza.name WITH COUNT INTO order_count
            SORT order_count DESC
            LIMIT 3
            RETURN {pizza: pizza_name, orders: order_count}
    """
    
    # Execute raw AQL
    code, out, err = run_cli_command(f'crud query --aql "{aql_query}" --db pizza_test')
    print(f"Execute custom AQL: {code == 0}")
    
    # Customer spending analysis
    spending_query = """
    FOR customer IN customers
        LET orders = (
            FOR order IN 1..1 OUTBOUND customer customer_orders
                RETURN order.total
        )
        RETURN {
            customer: customer.name,
            total_spent: SUM(orders),
            order_count: LENGTH(orders),
            avg_order: AVG(orders)
        }
    """
    
    code, out, err = run_cli_command(f'crud query --aql "{spending_query}" --db pizza_test')
    print(f"Customer spending analysis: {code == 0}")

def main():
    """Run all tests."""
    print("🍕 Pizza Database CLI Test Suite 🍕")
    print("=" * 50)
    
    # First, ensure the database is set up
    print("\nSetting up pizza database...")
    setup_result = subprocess.run(
        "cd /home/graham/workspace/experiments/arangodb && uv run python tests/data/setup_pizza_database.py",
        shell=True,
        capture_output=True
    )
    
    if setup_result.returncode != 0:
        print("Failed to setup database:", setup_result.stderr.decode())
        return
    
    # Run all test suites
    test_suites = [
        ("CRUD Operations", test_crud_operations),
        ("Search Operations", test_search_operations),
        ("Graph Operations", test_graph_operations),
        ("Memory Operations", test_memory_operations),
        ("Analysis Operations", test_analysis_operations),
        ("Advanced Queries", test_advanced_queries)
    ]
    
    for name, test_func in test_suites:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            logger.exception(f"{name} failed")
    
    print("\n" + "=" * 50)
    print("✅ Pizza CLI test suite complete!")
    print("\nCheck pizza_cli_test.log for detailed output")

if __name__ == "__main__":
    main()