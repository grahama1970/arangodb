"""Module docstring"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))



    #!/usr/bin/env python3
    """Create a self-contained pizza test database for CLI testing

    This creates a separate 'pizza_test' database with simple, debuggable data
    specifically for testing all ArangoDB CLI commands and functionality.
    """

    import os
    import sys
    import json
    from pathlib import Path
    from arango import ArangoClient
    from loguru import logger

    logger.add("pizza_db_setup.log", rotation="10 MB")


    def create_pizza_test_database():
        """Create a self-contained pizza test database"""

        # Connect to ArangoDB system database
        client = ArangoClient(hosts="http://localhost:8529")
        username = os.getenv("ARANGO_USER", "root")
        password = os.getenv("ARANGO_PASSWORD", "openSesame")

        sys_db = client.db("_system", username=username, password=password)

        # Create pizza_test database
        db_name = "pizza_test"

        # Drop if exists
        if sys_db.has_database(db_name):
            sys_db.delete_database(db_name)
            logger.info(f"Dropped existing {db_name} database")

            # Create fresh database
            sys_db.create_database(db_name)
            logger.info(f"Created {db_name} database")

            # Connect to pizza_test database
            db = client.db(db_name, username=username, password=password)

            # Create collections
            collections = {
            # Document collections
            "pizzas": False,
            "ingredients": False,
            "customers": False,
            "orders": False,
            "reviews": False,
            "stores": False,
            # Edge collections
            "pizza_ingredients": True,
            "customer_orders": True,
            "order_items": True,
            "review_for": True,
            "works_at": True
            }

            for collection_name, is_edge in collections.items():
                db.create_collection(collection_name, edge=is_edge)
                logger.info(f"Created {'edge' if is_edge else 'document'} collection: {collection_name}")

                # Insert test data
                logger.info("\nInserting test data...")

                # Pizzas
                pizzas_data = [
                {"_key": "margherita", "name": "Margherita", "price": 12.99, "category": "classic", "description": "Fresh mozzarella, tomato sauce, and basil"},
                {"_key": "pepperoni", "name": "Pepperoni", "price": 14.99, "category": "classic", "description": "Pepperoni, mozzarella, and tomato sauce"},
                {"_key": "hawaiian", "name": "Hawaiian", "price": 15.99, "category": "specialty", "description": "Ham, pineapple, and mozzarella"},
                {"_key": "veggie", "name": "Veggie Deluxe", "price": 13.99, "category": "vegetarian", "description": "Bell peppers, mushrooms, onions, olives"},
                {"_key": "meat_lovers", "name": "Meat Lovers", "price": 17.99, "category": "specialty", "description": "Pepperoni, sausage, bacon, ham"}
                ]
                db.collection("pizzas").insert_many(pizzas_data)

                # Ingredients
                ingredients_data = [
                {"_key": "mozzarella", "name": "Mozzarella", "category": "cheese", "cost": 2.50},
                {"_key": "tomato_sauce", "name": "Tomato Sauce", "category": "sauce", "cost": 1.00},
                {"_key": "pepperoni", "name": "Pepperoni", "category": "meat", "cost": 3.00},
                {"_key": "ham", "name": "Ham", "category": "meat", "cost": 2.50},
                {"_key": "pineapple", "name": "Pineapple", "category": "topping", "cost": 1.50},
                {"_key": "mushrooms", "name": "Mushrooms", "category": "vegetable", "cost": 1.75},
                {"_key": "basil", "name": "Fresh Basil", "category": "herb", "cost": 0.50},
                {"_key": "bacon", "name": "Bacon", "category": "meat", "cost": 3.50},
                {"_key": "sausage", "name": "Italian Sausage", "category": "meat", "cost": 3.25}
                ]
                db.collection("ingredients").insert_many(ingredients_data)

                # Customers
                customers_data = [
                {"_key": "john_doe", "name": "John Doe", "email": "john@example.com", "phone": "555-0101", "member_since": "2023-01-15"},
                {"_key": "jane_smith", "name": "Jane Smith", "email": "jane@example.com", "phone": "555-0102", "member_since": "2023-02-20"},
                {"_key": "bob_johnson", "name": "Bob Johnson", "email": "bob@example.com", "phone": "555-0103", "member_since": "2023-03-10"},
                {"_key": "alice_brown", "name": "Alice Brown", "email": "alice@example.com", "phone": "555-0104", "member_since": "2023-04-05"}
                ]
                db.collection("customers").insert_many(customers_data)

                # Stores
                stores_data = [
                {"_key": "downtown", "name": "Pizza Palace Downtown", "address": "123 Main St", "phone": "555-1000"},
                {"_key": "uptown", "name": "Pizza Palace Uptown", "address": "456 Oak Ave", "phone": "555-2000"}
                ]
                db.collection("stores").insert_many(stores_data)

                # Orders
                orders_data = [
                {"_key": "order_001", "order_date": "2024-01-10", "total": 28.98, "status": "delivered", "store": "downtown"},
                {"_key": "order_002", "order_date": "2024-01-11", "total": 14.99, "status": "delivered", "store": "uptown"},
                {"_key": "order_003", "order_date": "2024-01-12", "total": 31.98, "status": "preparing", "store": "downtown"}
                ]
                db.collection("orders").insert_many(orders_data)

                # Reviews
                reviews_data = [
                {"_key": "review_001", "rating": 5, "comment": "Best pizza in town!", "date": "2024-01-11"},
                {"_key": "review_002", "rating": 4, "comment": "Great taste, fast delivery", "date": "2024-01-12"},
                {"_key": "review_003", "rating": 3, "comment": "Good but a bit pricey", "date": "2024-01-13"}
                ]
                db.collection("reviews").insert_many(reviews_data)

                # Edge data: Pizza ingredients
                pizza_ingredients_edges = [
                {"_from": "pizzas/margherita", "_to": "ingredients/mozzarella", "amount": "200g"},
                {"_from": "pizzas/margherita", "_to": "ingredients/tomato_sauce", "amount": "100ml"},
                {"_from": "pizzas/margherita", "_to": "ingredients/basil", "amount": "10g"},
                {"_from": "pizzas/pepperoni", "_to": "ingredients/mozzarella", "amount": "200g"},
                {"_from": "pizzas/pepperoni", "_to": "ingredients/tomato_sauce", "amount": "100ml"},
                {"_from": "pizzas/pepperoni", "_to": "ingredients/pepperoni", "amount": "150g"},
                {"_from": "pizzas/hawaiian", "_to": "ingredients/mozzarella", "amount": "200g"},
                {"_from": "pizzas/hawaiian", "_to": "ingredients/ham", "amount": "100g"},
                {"_from": "pizzas/hawaiian", "_to": "ingredients/pineapple", "amount": "150g"},
                {"_from": "pizzas/meat_lovers", "_to": "ingredients/pepperoni", "amount": "100g"},
                {"_from": "pizzas/meat_lovers", "_to": "ingredients/sausage", "amount": "100g"},
                {"_from": "pizzas/meat_lovers", "_to": "ingredients/bacon", "amount": "80g"},
                {"_from": "pizzas/meat_lovers", "_to": "ingredients/ham", "amount": "80g"}
                ]
                db.collection("pizza_ingredients").insert_many(pizza_ingredients_edges)

                # Edge data: Customer orders
                customer_orders_edges = [
                {"_from": "customers/john_doe", "_to": "orders/order_001", "payment_method": "credit_card"},
                {"_from": "customers/jane_smith", "_to": "orders/order_002", "payment_method": "cash"},
                {"_from": "customers/bob_johnson", "_to": "orders/order_003", "payment_method": "credit_card"}
                ]
                db.collection("customer_orders").insert_many(customer_orders_edges)

                # Edge data: Order items
                order_items_edges = [
                {"_from": "orders/order_001", "_to": "pizzas/margherita", "quantity": 1, "price": 12.99},
                {"_from": "orders/order_001", "_to": "pizzas/hawaiian", "quantity": 1, "price": 15.99},
                {"_from": "orders/order_002", "_to": "pizzas/pepperoni", "quantity": 1, "price": 14.99},
                {"_from": "orders/order_003", "_to": "pizzas/meat_lovers", "quantity": 1, "price": 17.99},
                {"_from": "orders/order_003", "_to": "pizzas/veggie", "quantity": 1, "price": 13.99}
                ]
                db.collection("order_items").insert_many(order_items_edges)

                # Edge data: Reviews
                review_for_edges = [
                {"_from": "reviews/review_001", "_to": "pizzas/margherita", "verified_purchase": True},
                {"_from": "reviews/review_002", "_to": "pizzas/pepperoni", "verified_purchase": True},
                {"_from": "reviews/review_003", "_to": "pizzas/meat_lovers", "verified_purchase": False}
                ]
                db.collection("review_for").insert_many(review_for_edges)

                # Create indexes
                logger.info("\nCreating indexes...")

                # Hash indexes for lookups
                db.collection("pizzas").add_hash_index(fields=["category"])
                db.collection("ingredients").add_hash_index(fields=["category"])
                db.collection("orders").add_hash_index(fields=["status"])

                # Fulltext indexes for search (one field at a time)
                db.collection("pizzas").add_fulltext_index(fields=["description"])
                db.collection("reviews").add_fulltext_index(fields=["comment"])

                # Create a view for popular pizzas
                db.create_view(
                name="popular_pizzas_view",
                view_type="arangosearch",
                properties={
                "links": {
                "orders": {
                "fields": {}
                },
                "order_items": {
                "fields": {}
                },
                "pizzas": {
                "fields": {
                "name": {"analyzers": ["identity"]},
                "category": {"analyzers": ["identity"]}
                }
                }
                }
                }
                )

                logger.info("\n✅ Pizza test database created successfully!")
                logger.info(f"Database: {db_name}")
                logger.info("Collections created:")
                for collection_name in collections:
                    count = db.collection(collection_name).count()
                    logger.info(f"  - {collection_name}: {count} documents")

                    # Test some queries
                    logger.info("\nTesting sample queries...")

                    # Test 1: Find all ingredients for Margherita pizza
                    query1 = """
                    FOR pizza IN pizzas
                    FILTER pizza._key == "margherita"
                    FOR ingredient IN 1..1 OUTBOUND pizza pizza_ingredients
                    RETURN {
                    pizza: pizza.name,
                    ingredient: ingredient.name,
                    category: ingredient.category
                    }
                    """
                    result = list(db.aql.execute(query1))
                    logger.info(f"Margherita ingredients: {result}")

                    # Test 2: Find customer orders
                    query2 = """
                    FOR customer IN customers
                    FILTER customer._key == "john_doe"
                    FOR order IN 1..1 OUTBOUND customer customer_orders
                    RETURN {
                    customer: customer.name,
                    order_id: order._key,
                    total: order.total,
                    status: order.status
                    }
                    """
                    result = list(db.aql.execute(query2))
                    logger.info(f"John Doe's orders: {result}")

                    return db_name


                    if __name__ == "__main__":
                        try:
                            db_name = create_pizza_test_database()
                            print(f"\n✅ Successfully created test database: {db_name}")
                            print("\nYou can now test CLI commands with:")
                            print(f'export ARANGO_DB_NAME="{db_name}"')
                            print("uv run python -m arangodb.cli [command]")
                        except Exception as e:
                            logger.error(f"Failed to create test database: {e}")
                            exit(1)