"""
Module: setup_pizza_db_simple.py

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
Simple setup script for pizza database without embedding dependencies.
"""

import json
from pathlib import Path
from arango import ArangoClient
from loguru import logger

logger.add("pizza_db_simple_setup.log", rotation="10 MB")

def setup_pizza_database():
    """Create and populate the pizza test database."""
    # Connect to ArangoDB
    client = ArangoClient(hosts='http://localhost:8529')
    sys_db = client.db('_system', username='root', password='root')
    
    # Create database if it doesn't exist
    db_name = 'pizza_test'
    if sys_db.has_database(db_name):
        sys_db.delete_database(db_name)
        print(f"Deleted existing database: {db_name}")
    
    sys_db.create_database(db_name)
    print(f"Created database: {db_name}")
    
    # Connect to the pizza database
    db = client.db(db_name, username='root', password='root')
    
    # Define all collections
    document_collections = [
        'pizzas', 'ingredients', 'customers', 'orders',
        'pizza_reviews', 'memories', 'ingredient_suppliers'
    ]
    
    edge_collections = [
        'pizza_ingredients', 'customer_orders', 'order_items',
        'review_edges', 'memory_links', 'supplier_ingredients'
    ]
    
    # Create document collections
    for coll_name in document_collections:
        db.create_collection(coll_name)
        print(f"Created document collection: {coll_name}")
    
    # Create edge collections
    for coll_name in edge_collections:
        db.create_collection(coll_name, edge=True)
        print(f"Created edge collection: {coll_name}")
    
    # Get data directory
    data_dir = Path(__file__).parent
    
    # Load data into collections
    collections_to_load = [
        # Document collections
        ('pizzas', 'pizzas.json'),
        ('ingredients', 'ingredients.json'),
        ('customers', 'customers.json'),
        ('orders', 'orders.json'),
        ('pizza_reviews', 'pizza_reviews.json'),
        ('memories', 'memories.json'),
        ('ingredient_suppliers', 'ingredient_suppliers.json'),
        # Edge collections
        ('pizza_ingredients', 'pizza_ingredients.json'),
        ('customer_orders', 'customer_orders.json'),
        ('order_items', 'order_items.json'),
        ('review_edges', 'review_edges.json'),
        ('memory_links', 'memory_links.json'),
        ('supplier_ingredients', 'supplier_ingredients.json')
    ]
    
    for coll_name, filename in collections_to_load:
        file_path = data_dir / filename
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            collection = db.collection(coll_name)
            result = collection.insert_many(data)
            print(f"Loaded {len(data)} documents into {coll_name}")
    
    print("\n Pizza database setup complete!")
    print(f"Database '{db_name}' is ready for testing")
    
    return db

if __name__ == "__main__":
    setup_pizza_database()