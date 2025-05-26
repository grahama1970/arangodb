# 🍕 Pizza Test Database

This directory contains a pizza-themed test database for the ArangoDB Memory Bank project. The database demonstrates all features of the CLI and core modules with easy-to-understand data.

## Database Structure

### Document Collections

1. **pizzas** - Pizza menu items
   - Fields: name, description, price, calories, tags, allergens
   - Example: Margherita, Pepperoni, Hawaiian

2. **ingredients** - Pizza ingredients inventory
   - Fields: name, category, cost, nutritional info, supplier
   - Example: Mozzarella, Tomato Sauce, Pepperoni

3. **customers** - Customer profiles
   - Fields: name, email, address, dietary preferences, loyalty points
   - Example: John Smith (VIP customer), Maria Garcia (vegetarian)

4. **orders** - Customer orders
   - Fields: order_number, customer_id, items, total, status
   - Example: ORD-2024-001 (delivered), ORD-2024-004 (preparing)

### Edge Collections

1. **pizza_ingredients** - Links pizzas to their ingredients
   - Edges: pizzas → ingredients
   - Fields: quantity, unit, preparation method
   - Example: Margherita → Mozzarella (150g, shredded)

2. **customer_orders** - Links customers to their orders
   - Edges: customers → orders
   - Fields: relationship type, timestamp
   - Example: John Smith → ORD-2024-001

3. **order_items** - Links orders to pizzas
   - Edges: orders → pizzas
   - Fields: quantity, customizations, price
   - Example: ORD-2024-002 → Margherita (1x, extra basil)

## Graph Relationships

```
Customers --places--> Orders --contains--> Pizzas --made_with--> Ingredients
```

## Usage

### Setup Database
```bash
cd /home/graham/workspace/experiments/arangodb
uv run python tests/data/setup_pizza_database.py
```

### Run Test Suite
```bash
uv run python tests/data/test_pizza_cli.py
```

### Example Queries

1. **Find ingredients for a pizza:**
```bash
uv run python -m arangodb.cli graph traverse pizzas/margherita \
  --direction outbound --edge-collection pizza_ingredients --db pizza_test
```

2. **Search for vegetarian pizzas:**
```bash
uv run python -m arangodb.cli search tag --tags "vegetarian" \
  --collection pizzas --db pizza_test
```

3. **Get customer order history:**
```bash
uv run python -m arangodb.cli graph traverse customers/cust_001 \
  --direction outbound --edge-collection customer_orders --db pizza_test
```

## Test Coverage

This database tests:
- ✅ CRUD operations (create, read, update, delete)
- ✅ Search functionality (BM25, semantic, hybrid, tags)
- ✅ Graph traversals (multi-hop, filtered)
- ✅ Memory operations (customer preferences)
- ✅ Community detection (ingredient clusters)
- ✅ Temporal analysis (order patterns)
- ✅ Complex aggregations (spending analysis)

## Sample Insights

The test data reveals:
- Pepperoni is the most popular pizza (appears in multiple orders)
- John Smith is a VIP customer with 42 total orders
- Vegetarian options include Margherita and Veggie Supreme
- Hawaiian pizza is controversial (lower popularity score)
- Most orders are delivered within 45 minutes