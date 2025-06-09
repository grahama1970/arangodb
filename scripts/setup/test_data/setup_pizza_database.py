"""
Module: setup_pizza_database.py
Description: Implementation of setup pizza database functionality

External Dependencies:
- arango: https://docs.python-arango.com/
- loguru: https://loguru.readthedocs.io/

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))



#!/usr/bin/env python3
"""
Setup script to create pizza-themed test database in ArangoDB.

This script creates:
- Document collections: pizzas, ingredients, customers, orders
- Edge collections: pizza_ingredients, customer_orders, order_items
- Loads test data from JSON files
- Creates necessary indexes for search operations
"""

import json
import os
from pathlib import Path
from arango import ArangoClient
from loguru import logger

# Configure logger
logger.add("pizza_db_setup.log", rotation="10 MB")

def setup_pizza_database():
    """Create and populate the pizza test database."""
    # Connect to ArangoDB
    client = ArangoClient(hosts='http://localhost:8529')
    sys_db = client.db('_system', username='root', password='root')
    
    # Create database if it doesn't exist
    db_name = 'pizza_test'
    if not sys_db.has_database(db_name):
        sys_db.create_database(db_name)
        logger.info(f"Created database: {db_name}")
    
    # Connect to the pizza database
    db = client.db(db_name, username='root', password='root')
    
    # Define collections
    document_collections = ['pizzas', 'ingredients', 'customers', 'orders']
    edge_collections = ['pizza_ingredients', 'customer_orders', 'order_items']
    
    # Create document collections
    for coll_name in document_collections:
        if not db.has_collection(coll_name):
            db.create_collection(coll_name)
            logger.info(f"Created document collection: {coll_name}")
    
    # Create edge collections
    for coll_name in edge_collections:
        if not db.has_collection(coll_name):
            db.create_collection(coll_name, edge=True)
            logger.info(f"Created edge collection: {coll_name}")
    
    # Get data directory
    data_dir = Path(__file__).parent
    
    # Load data into collections
    collections_to_load = [
        ('pizzas', 'pizzas.json'),
        ('ingredients', 'ingredients.json'),
        ('customers', 'customers.json'),
        ('orders', 'orders.json'),
        ('pizza_ingredients', 'pizza_ingredients.json'),
        ('customer_orders', 'customer_orders.json'),
        ('order_items', 'order_items.json')
    ]
    
    for coll_name, filename in collections_to_load:
        file_path = data_dir / filename
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            collection = db.collection(coll_name)
            # Clear existing data
            collection.truncate()
            
            # Insert new data
            result = collection.insert_many(data)
            logger.info(f"Loaded {len(data)} documents into {coll_name}")
        else:
            logger.warning(f"Data file not found: {file_path}")
    
    # Create indexes for search operations
    pizzas = db.collection('pizzas')
    
    # Create fulltext index for pizza names and descriptions
    if not any(idx['type'] == 'fulltext' for idx in pizzas.indexes()):
        pizzas.add_fulltext_index(fields=['name', 'description'])
        logger.info("Created fulltext index on pizzas collection")
    
    # Create persistent index on tags
    pizzas.add_persistent_index(fields=['tags[*]'])
    logger.info("Created persistent index on pizza tags")
    
    # Create index on customer email
    customers = db.collection('customers')
    customers.add_persistent_index(fields=['email'], unique=True)
    logger.info("Created unique index on customer email")
    
    # Create index on order status and date
    orders = db.collection('orders')
    orders.add_persistent_index(fields=['status', 'order_date'])
    logger.info("Created compound index on order status and date")
    
    logger.info("Pizza database setup complete!")
    
    # Print summary statistics
    print("\n=== Pizza Database Summary ===")
    for coll_name in document_collections + edge_collections:
        count = db.collection(coll_name).count()
        print(f"{coll_name}: {count} documents")
    
    return db

def verify_graph_relationships(db):
    """Verify that graph relationships are working correctly."""
    print("\n=== Verifying Graph Relationships ===")
    
    # Test 1: Find all ingredients for Margherita pizza
    query = """
    FOR pizza IN pizzas
        FILTER pizza._key == 'margherita'
        FOR v, e IN 1..1 OUTBOUND pizza pizza_ingredients
            RETURN {
                pizza: pizza.name,
                ingredient: v.name,
                quantity: e.quantity,
                unit: e.unit
            }
    """
    cursor = db.aql.execute(query)
    results = list(cursor)
    print(f"\nMargherita ingredients: {len(results)} found")
    for r in results:
        print(f"  - {r['ingredient']}: {r['quantity']} {r['unit']}")
    
    # Test 2: Find all orders for a customer
    query = """
    FOR customer IN customers
        FILTER customer._key == 'cust_001'
        FOR v, e IN 1..1 OUTBOUND customer customer_orders
            RETURN {
                customer: customer.name,
                order: v.order_number,
                total: v.total,
                status: v.status
            }
    """
    cursor = db.aql.execute(query)
    results = list(cursor)
    print(f"\nJohn Smith's orders: {len(results)} found")
    for r in results:
        print(f"  - {r['order']}: ${r['total']:.2f} ({r['status']})")
    
    # Test 3: Find pizzas in an order
    query = """
    FOR order IN orders
        FILTER order._key == 'order_002'
        FOR pizza, e IN 1..1 OUTBOUND order order_items
            RETURN {
                order: order.order_number,
                pizza: pizza.name,
                quantity: e.quantity,
                price: e.price_each
            }
    """
    cursor = db.aql.execute(query)
    results = list(cursor)
    print(f"\nOrder ORD-2024-002 items: {len(results)} found")
    for r in results:
        print(f"  - {r['quantity']}x {r['pizza']} @ ${r['price']:.2f}")

if __name__ == "__main__":
    db = setup_pizza_database()
    verify_graph_relationships(db)