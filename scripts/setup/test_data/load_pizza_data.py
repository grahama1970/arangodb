"""
Module: load_pizza_data.py

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

#!/usr/bin/env python3
"""Load pizza test data into memory_bank database

This script loads the pizza-themed test data into the memory_bank database
for testing D3 visualizations and other features.
"""

import os
import sys
import json
from pathlib import Path
from arango import ArangoClient
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from arangodb.core.utils.embedding_utils import get_embedding_model


def load_pizza_data():
    """Load pizza test data into memory_bank database"""
    # Connect to ArangoDB
    client = ArangoClient(hosts="http://localhost:8529")
    
    # Get credentials from environment
    username = os.getenv("ARANGO_USER", "root")
    password = os.getenv("ARANGO_PASSWORD", "openSesame")
    db_name = os.getenv("ARANGO_DB_NAME", "memory_bank")
    
    db = client.db(db_name, username=username, password=password)
    logger.info(f"Connected to database: {db_name}")
    
    # Initialize embedding model
    embedder = get_embedding_model()
    logger.info("Initialized embedding model")
    
    # Define collections to create
    document_collections = [
        "pizzas",
        "ingredients", 
        "customers",
        "orders",
        "pizza_reviews",
        "ingredient_suppliers"
    ]
    
    edge_collections = [
        "pizza_ingredients",
        "customer_orders",
        "order_items",
        "review_edges",
        "supplier_ingredients"
    ]
    
    # Create collections
    for collection in document_collections:
        if not db.has_collection(collection):
            db.create_collection(collection)
            logger.info(f"Created document collection: {collection}")
    
    for collection in edge_collections:
        if not db.has_collection(collection):
            db.create_collection(collection, edge=True)
            logger.info(f"Created edge collection: {collection}")
    
    # Load data from JSON files
    data_dir = Path(__file__).parent.parent / "tests" / "data"
    
    # Collections that need embeddings
    embed_configs = {
        "pizzas": ["name", "description"],
        "ingredients": ["name", "category"],
        "customers": ["name", "email"],
        "orders": ["status"],
        "pizza_reviews": ["comment"],
        "ingredient_suppliers": ["company_name", "location"]
    }
    
    # Load and insert data with embeddings
    for collection_name in document_collections:
        json_file = data_dir / f"{collection_name}.json"
        if json_file.exists():
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            collection = db.collection(collection_name)
            
            # Add embeddings if needed
            if collection_name in embed_configs:
                fields = embed_configs[collection_name]
                for doc in data:
                    # Create text for embedding
                    text_parts = []
                    for field in fields:
                        if field in doc and doc[field]:
                            text_parts.append(str(doc[field]))
                    
                    if text_parts:
                        text = " ".join(text_parts)
                        doc["embedding"] = embedder.embed(text)
                        doc["embedding_text"] = text
            
            # Insert documents
            result = collection.insert_many(data)
            logger.info(f"Inserted {len(result)} documents into {collection_name}")
    
    # Load edge data
    for collection_name in edge_collections:
        json_file = data_dir / f"{collection_name}.json"
        if json_file.exists():
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            collection = db.collection(collection_name)
            result = collection.insert_many(data)
            logger.info(f"Inserted {len(result)} edges into {collection_name}")
    
    # Create indexes for better performance
    logger.info("Creating indexes...")
    
    # Text indexes for BM25 search
    if db.collection("pizzas").properties()["type"] == 2:  # Document collection
        try:
            db.collection("pizzas").add_fulltext_index(fields=["name", "description"])
            logger.info("Created fulltext index on pizzas")
        except Exception as e:
            logger.warning(f"Fulltext index may already exist: {e}")
    
    if db.collection("ingredients").properties()["type"] == 2:
        try:
            db.collection("ingredients").add_fulltext_index(fields=["name", "category"])
            logger.info("Created fulltext index on ingredients")
        except Exception as e:
            logger.warning(f"Fulltext index may already exist: {e}")
    
    # Verify data
    logger.info("\nVerifying loaded data:")
    for collection_name in document_collections + edge_collections:
        if db.has_collection(collection_name):
            count = db.collection(collection_name).count()
            logger.info(f"  {collection_name}: {count} documents")
    
    # Test a simple graph query
    logger.info("\nTesting graph query...")
    query = """
    FOR pizza IN pizzas
    LIMIT 1
    LET ingredients = (
        FOR v, e IN 1..1 OUTBOUND pizza pizza_ingredients
        RETURN v.name
    )
    RETURN {
        pizza: pizza.name,
        ingredients: ingredients
    }
    """
    
    cursor = db.aql.execute(query)
    result = list(cursor)
    if result:
        logger.info(f"Sample pizza with ingredients: {result[0]}")
    
    logger.info("\n Pizza data loaded successfully!")
    return True


if __name__ == "__main__":
    try:
        load_pizza_data()
    except Exception as e:
        logger.error(f"Failed to load pizza data: {e}")
        exit(1)