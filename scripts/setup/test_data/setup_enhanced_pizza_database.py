"""
Module: setup_enhanced_pizza_database.py
Description: Implementation of setup enhanced pizza database functionality

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
"""
Enhanced setup script for pizza-themed test database with rich relationships.

This creates a comprehensive test environment for:
- Multi-hop graph traversals
- Semantic and hybrid search
- Memory agent operations
- Complex relationship patterns
- Temporal data analysis
"""

import json
import os
import sys
from pathlib import Path
from arango import ArangoClient
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import embedding functions
if __name__ == "__main__":
    exec(open("embed_collections.py").read())

logger.add("pizza_db_enhanced_setup.log", rotation="10 MB")

def setup_enhanced_pizza_database():
    """Create and populate the enhanced pizza test database."""
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
            # Clear existing data
            collection.truncate()
            
            # Insert new data
            result = collection.insert_many(data)
            logger.info(f"Loaded {len(data)} documents into {coll_name}")
        else:
            logger.warning(f"Data file not found: {file_path}")
    
    # Create indexes for search operations
    create_search_indexes(db)
    
    # Create graphs for traversal
    create_graph_definitions(db)
    
    # Create views for ArangoSearch
    create_search_views(db)
    
    logger.info("Enhanced pizza database setup complete!")
    
    # Generate embeddings for searchable collections
    logger.info("\nGenerating embeddings for semantic search...")
    embedding_configs = [
        {
            "collection_name": "pizzas",
            "embedding_fields": ["name", "description", "tags"]
        },
        {
            "collection_name": "ingredients",
            "embedding_fields": ["name", "category", "tags"]
        },
        {
            "collection_name": "customers",
            "embedding_fields": ["name", "dietary_preferences", "tags"]
        },
        {
            "collection_name": "pizza_reviews",
            "embedding_fields": ["review_text", "summary", "tags"]
        },
        {
            "collection_name": "memories",
            "embedding_fields": ["content", "summary", "metadata.context", "tags"]
        }
    ]
    
    stats = embed_multiple_collections(db_name, embedding_configs)
    
    # Print summary statistics
    print_database_summary(db)
    
    return db

def create_search_indexes(db):
    """Create various indexes for efficient searching."""
    # Pizzas collection indexes
    pizzas = db.collection('pizzas')
    pizzas.add_fulltext_index(fields=['name', 'description'])
    pizzas.add_persistent_index(fields=['tags[*]'])
    pizzas.add_persistent_index(fields=['price'])
    pizzas.add_persistent_index(fields=['vegetarian', 'vegan'])
    logger.info("Created indexes on pizzas collection")
    
    # Reviews collection indexes
    reviews = db.collection('pizza_reviews')
    reviews.add_fulltext_index(fields=['review_text', 'summary'])
    reviews.add_persistent_index(fields=['rating'])
    reviews.add_persistent_index(fields=['sentiment_score'])
    reviews.add_persistent_index(fields=['created_at'])
    logger.info("Created indexes on pizza_reviews collection")
    
    # Memories collection indexes
    memories = db.collection('memories')
    memories.add_fulltext_index(fields=['content', 'summary'])
    memories.add_persistent_index(fields=['entity_type'])
    memories.add_persistent_index(fields=['importance'])
    memories.add_persistent_index(fields=['tags[*]'])
    memories.add_persistent_index(fields=['created_at', 'updated_at'])
    logger.info("Created indexes on memories collection")
    
    # Customers collection indexes
    customers = db.collection('customers')
    customers.add_persistent_index(fields=['email'], unique=True)
    customers.add_persistent_index(fields=['loyalty_points'])
    customers.add_persistent_index(fields=['tags[*]'])
    logger.info("Created indexes on customers collection")
    
    # Orders collection indexes
    orders = db.collection('orders')
    orders.add_persistent_index(fields=['status', 'order_date'])
    orders.add_persistent_index(fields=['total'])
    logger.info("Created indexes on orders collection")

def create_graph_definitions(db):
    """Create named graphs for efficient traversal."""
    # Pizza Knowledge Graph
    if not db.has_graph('pizza_knowledge_graph'):
        db.create_graph(
            name='pizza_knowledge_graph',
            edge_definitions=[
                {
                    'edge_collection': 'pizza_ingredients',
                    'from_vertex_collections': ['pizzas'],
                    'to_vertex_collections': ['ingredients']
                },
                {
                    'edge_collection': 'supplier_ingredients',
                    'from_vertex_collections': ['ingredient_suppliers'],
                    'to_vertex_collections': ['ingredients']
                }
            ]
        )
        logger.info("Created pizza_knowledge_graph")
    
    # Customer Journey Graph
    if not db.has_graph('customer_journey_graph'):
        db.create_graph(
            name='customer_journey_graph',
            edge_definitions=[
                {
                    'edge_collection': 'customer_orders',
                    'from_vertex_collections': ['customers'],
                    'to_vertex_collections': ['orders']
                },
                {
                    'edge_collection': 'order_items',
                    'from_vertex_collections': ['orders'],
                    'to_vertex_collections': ['pizzas']
                },
                {
                    'edge_collection': 'review_edges',
                    'from_vertex_collections': ['customers', 'pizza_reviews'],
                    'to_vertex_collections': ['pizza_reviews', 'pizzas']
                }
            ]
        )
        logger.info("Created customer_journey_graph")
    
    # Memory Association Graph
    if not db.has_graph('memory_association_graph'):
        db.create_graph(
            name='memory_association_graph',
            edge_definitions=[
                {
                    'edge_collection': 'memory_links',
                    'from_vertex_collections': ['memories'],
                    'to_vertex_collections': ['customers', 'pizzas', 'ingredients', 'memories']
                }
            ]
        )
        logger.info("Created memory_association_graph")

def create_search_views(db):
    """Create ArangoSearch views for advanced text search."""
    # Pizza search view
    if not hasattr(db, 'view') or not any(v['name'] == 'pizza_search_view' for v in db.views()):
        db.create_arangosearch_view(
            name='pizza_search_view',
            properties={
                'links': {
                    'pizzas': {
                        'analyzers': ['text_en'],
                        'includeAllFields': False,
                        'fields': {
                            'name': {},
                            'description': {},
                            'tags': {}
                        }
                    }
                }
            }
        )
        logger.info("Created pizza_search_view")
    
    # Review search view
    if not hasattr(db, 'view') or not any(v['name'] == 'review_search_view' for v in db.views()):
        db.create_arangosearch_view(
            name='review_search_view',
            properties={
                'links': {
                    'pizza_reviews': {
                        'analyzers': ['text_en'],
                        'includeAllFields': False,
                        'fields': {
                            'review_text': {},
                            'summary': {},
                            'tags': {}
                        }
                    }
                }
            }
        )
        logger.info("Created review_search_view")
    
    # Memory search view
    if not hasattr(db, 'view') or not any(v['name'] == 'memory_search_view' for v in db.views()):
        db.create_arangosearch_view(
            name='memory_search_view',
            properties={
                'links': {
                    'memories': {
                        'analyzers': ['text_en'],
                        'includeAllFields': False,
                        'fields': {
                            'content': {},
                            'summary': {},
                            'tags': {},
                            'metadata.context': {}
                        }
                    }
                }
            }
        )
        logger.info("Created memory_search_view")

def print_database_summary(db):
    """Print comprehensive database statistics."""
    print("\n" + "="*60)
    print("🍕 ENHANCED PIZZA DATABASE SUMMARY 🍕")
    print("="*60)
    
    # Collection counts
    print("\n📊 Collection Statistics:")
    collections = [
        'pizzas', 'ingredients', 'customers', 'orders',
        'pizza_reviews', 'memories', 'ingredient_suppliers',
        'pizza_ingredients', 'customer_orders', 'order_items',
        'review_edges', 'memory_links', 'supplier_ingredients'
    ]
    
    for coll_name in collections:
        if db.has_collection(coll_name):
            count = db.collection(coll_name).count()
            coll_type = "edge" if db.collection(coll_name).properties()['edge'] else "document"
            print(f"  {coll_name}: {count} {coll_type}s")
    
    # Graph statistics
    print("\n🌐 Graph Statistics:")
    graphs = ['pizza_knowledge_graph', 'customer_journey_graph', 'memory_association_graph']
    for graph_name in graphs:
        if db.has_graph(graph_name):
            print(f"  {graph_name}: ✓ active")
    
    # Sample queries
    print("\n🔍 Sample Query Results:")
    
    # Most reviewed pizza
    query = """
    FOR pizza IN pizzas
        LET review_count = LENGTH(
            FOR v IN 1..1 INBOUND pizza review_edges
                FILTER IS_DOCUMENT(v)
                RETURN v
        )
        SORT review_count DESC
        LIMIT 1
        RETURN {pizza: pizza.name, reviews: review_count}
    """
    cursor = db.aql.execute(query)
    result = list(cursor)
    if result:
        print(f"  Most reviewed pizza: {result[0]['pizza']} ({result[0]['reviews']} reviews)")
    
    # Customer with most orders
    query = """
    FOR customer IN customers
        LET order_count = LENGTH(
            FOR v IN 1..1 OUTBOUND customer customer_orders
                RETURN v
        )
        SORT order_count DESC
        LIMIT 1
        RETURN {customer: customer.name, orders: order_count}
    """
    cursor = db.aql.execute(query)
    result = list(cursor)
    if result:
        print(f"  Most frequent customer: {result[0]['customer']} ({result[0]['orders']} orders)")
    
    # Supply chain complexity
    query = """
    FOR supplier IN ingredient_suppliers
        LET ingredients_supplied = LENGTH(
            FOR v IN 1..1 OUTBOUND supplier supplier_ingredients
                RETURN v
        )
        RETURN {supplier: supplier.name, supplies: ingredients_supplied}
    """
    cursor = db.aql.execute(query)
    results = list(cursor)
    print(f"  Supply chain: {len(results)} suppliers providing ingredients")
    
    print("\n✅ Database ready for comprehensive testing!")
    print("="*60)

def demonstrate_complex_queries(db):
    """Demonstrate complex multi-hop queries."""
    print("\n" + "="*60)
    print("🔮 DEMONSTRATING COMPLEX QUERIES")
    print("="*60)
    
    # Query 1: Find all ingredients from pizzas a customer has ordered
    print("\n1️⃣ Customer's Ingredient History (3-hop traversal):")
    query = """
    FOR customer IN customers
        FILTER customer._key == 'cust_001'
        FOR order IN 1..1 OUTBOUND customer customer_orders
            FOR pizza IN 1..1 OUTBOUND order order_items
                FOR ingredient IN 1..1 OUTBOUND pizza pizza_ingredients
                    COLLECT ingredient_name = ingredient.name WITH COUNT INTO times_consumed
                    SORT times_consumed DESC
                    RETURN {ingredient: ingredient_name, times_consumed: times_consumed}
    """
    cursor = db.aql.execute(query)
    results = list(cursor)[:5]
    for r in results:
        print(f"  - {r['ingredient']}: consumed {r['times_consumed']} times")
    
    # Query 2: Find suppliers affected by a pizza's popularity
    print("\n2️⃣ Supply Chain Impact Analysis (4-hop traversal):")
    query = """
    FOR pizza IN pizzas
        FILTER pizza._key == 'pepperoni'
        LET order_count = LENGTH(
            FOR order IN 1..1 INBOUND pizza order_items
                RETURN order
        )
        FOR ingredient IN 1..1 OUTBOUND pizza pizza_ingredients
            FOR supplier IN 1..1 INBOUND ingredient supplier_ingredients
                RETURN {
                    pizza: pizza.name,
                    ingredient: ingredient.name,
                    supplier: supplier.name,
                    impact_score: order_count * ingredient.cost_per_unit
                }
    """
    cursor = db.aql.execute(query)
    results = list(cursor)
    for r in results:
        print(f"  - {r['supplier']} supplies {r['ingredient']} for {r['pizza']} (impact: ${r['impact_score']:.2f})")
    
    # Query 3: Memory-guided recommendations
    print("\n3️⃣ Memory-Guided Pizza Recommendations:")
    query = """
    FOR memory IN memories
        FILTER memory.entity_type == 'customer_profile'
        LET customer = FIRST(
            FOR c IN 1..1 OUTBOUND memory memory_links
                FILTER IS_DOCUMENT('customers/' + SPLIT(c._id, '/')[1])
                RETURN c
        )
        LET favorite_pizzas = (
            FOR pizza_ref IN memory.tags
                FILTER CONTAINS(pizza_ref, 'pizza') OR CONTAINS(pizza_ref, 'lover')
                RETURN pizza_ref
        )
        RETURN {
            customer: customer.name,
            preferences: memory.summary,
            recommended_tags: favorite_pizzas
        }
    """
    cursor = db.aql.execute(query)
    results = list(cursor)
    for r in results:
        if r['customer']:
            print(f"  - {r['customer']}: {r['preferences']}")

if __name__ == "__main__":
    # Setup the enhanced database
    db = setup_enhanced_pizza_database()
    
    # Demonstrate complex queries
    demonstrate_complex_queries(db)
    
    # Validate some embeddings
    print("\n🔍 Validating Embeddings:")
    for collection in ['pizzas', 'memories', 'pizza_reviews']:
        validate_embeddings('pizza_test', collection, sample_size=2)