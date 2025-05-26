# Task 032: Validate All CLI Commands with Pizza Database

**Database**: pizza_test (enhanced with embeddings)
**Goal**: Verify every CLI command produces real, expected results (including empty results for unrelated queries)

## Setup Command

```bash
cd /home/graham/workspace/experiments/arangodb
uv run python tests/data/setup_enhanced_pizza_database.py
```

## Task 1: CRUD Operations Validation

### Working Commands to Test

```bash
# List all pizzas - EXPECT: 5 pizzas with names, prices, descriptions
uv run python -m arangodb.cli crud list --collection pizzas --db pizza_test

# Get specific pizza - EXPECT: Full Margherita details with embedding
uv run python -m arangodb.cli crud get margherita --collection pizzas --db pizza_test

# Get non-existent pizza - EXPECT: Error or empty result
uv run python -m arangodb.cli crud get calzone --collection pizzas --db pizza_test

# Create new pizza - EXPECT: Success with returned document
uv run python -m arangodb.cli crud create --collection pizzas --db pizza_test --data '{"_key": "calzone", "name": "Calzone", "price": 11.99}'

# Update pizza - EXPECT: Updated document returned
uv run python -m arangodb.cli crud update calzone --collection pizzas --db pizza_test --data '{"price": 12.99}'

# Delete pizza - EXPECT: Deletion confirmation
uv run python -m arangodb.cli crud delete calzone --collection pizzas --db pizza_test
```

### Expected Results Structure
```json
{
  "pizzas_list": "5 documents with _key, name, price, description",
  "margherita_get": "Complete document with embedding array[1024]",
  "non_existent": "Document not found error",
  "create": "New document with _id, _key, _rev",
  "update": "Modified document with new price",
  "delete": "Deletion successful message"
}
```

## Task 2: Search Operations Validation

### BM25 Search Tests

```bash
# Search for "chicken" - EXPECT: BBQ Chicken pizza
uv run python -m arangodb.cli search bm25 --query "chicken" --collection pizzas --db pizza_test

# Search for "italian authentic" - EXPECT: Margherita
uv run python -m arangodb.cli search bm25 --query "italian authentic" --collection pizzas --db pizza_test

# Search for "sushi" - EXPECT: No results
uv run python -m arangodb.cli search bm25 --query "sushi tempura" --collection pizzas --db pizza_test
```

### Semantic Search Tests

```bash
# Semantic search for Italian classics - EXPECT: Margherita ranked high
uv run python -m arangodb.cli search semantic --query "traditional Italian pizza with tomatoes" --collection pizzas --db pizza_test

# Search memories for supply chain - EXPECT: mem_004 about mozzarella
uv run python -m arangodb.cli search semantic --query "supplier negotiations price increases" --collection memories --db pizza_test

# Search for unrelated concept - EXPECT: Low relevance or no results
uv run python -m arangodb.cli search semantic --query "quantum computing algorithms" --collection pizzas --db pizza_test
```

### Hybrid Search Tests

```bash
# Hybrid search for vegetarian - EXPECT: Margherita and Veggie Supreme
uv run python -m arangodb.cli search hybrid --query "vegetarian fresh vegetables" --collection pizzas --db pizza_test --bm25-weight 0.4 --semantic-weight 0.6

# Search reviews for quality - EXPECT: review_001, review_003
uv run python -m arangodb.cli search hybrid --query "authentic quality fresh" --collection pizza_reviews --db pizza_test
```

### Tag Search Tests

```bash
# Search by single tag - EXPECT: 2 pizzas (Margherita, Veggie Supreme)
uv run python -m arangodb.cli search tag --tags "vegetarian" --collection pizzas --db pizza_test

# Search by multiple tags - EXPECT: Only Margherita
uv run python -m arangodb.cli search tag --tags "italian,vegetarian" --match all --collection pizzas --db pizza_test

# Search non-existent tag - EXPECT: No results
uv run python -m arangodb.cli search tag --tags "gluten-free" --collection pizzas --db pizza_test
```

## Task 3: Graph Traversal Validation

### Single-Hop Traversals

```bash
# Pizza ingredients - EXPECT: 3 ingredients for Margherita
uv run python -m arangodb.cli graph traverse pizzas/margherita --direction outbound --edge-collection pizza_ingredients --db pizza_test

# Customer orders - EXPECT: 2 orders for cust_001
uv run python -m arangodb.cli graph traverse customers/cust_001 --direction outbound --edge-collection customer_orders --db pizza_test

# Invalid start node - EXPECT: Error
uv run python -m arangodb.cli graph traverse pizzas/sushi --direction outbound --edge-collection pizza_ingredients --db pizza_test
```

### Multi-Hop Traversals

```bash
# 2-hop: Customer -> Orders -> Pizzas - EXPECT: Pepperoni and BBQ Chicken for cust_001
uv run python -m arangodb.cli graph traverse customers/cust_001 --direction outbound --edge-collection customer_orders,order_items --depth 2 --db pizza_test

# 3-hop: Pizza -> Ingredients -> Suppliers - EXPECT: Supply chain for pepperoni
uv run python -m arangodb.cli graph traverse pizzas/pepperoni --direction outbound --edge-collection pizza_ingredients,supplier_ingredients --depth 2 --db pizza_test

# Memory associations - EXPECT: Related entities for mem_001
uv run python -m arangodb.cli graph traverse memories/mem_001 --direction any --edge-collection memory_links --depth 2 --db pizza_test
```

## Task 4: Memory Operations Validation

### Memory CRUD

```bash
# Create memory - EXPECT: New memory with embedding
uv run python -m arangodb.cli memory create --content "New insight: Gluten-free options needed. 15% of customers asked." --metadata '{"context": "customer_feedback", "confidence": 0.8}' --tags "gluten-free,opportunity" --db pizza_test

# List memories - EXPECT: 7+ memories including new one
uv run python -m arangodb.cli memory list --limit 10 --db pizza_test

# Search memories - EXPECT: Operational insights
uv run python -m arangodb.cli memory search --query "Friday peak hours operations" --db pizza_test

# Update memory - EXPECT: Updated document
uv run python -m arangodb.cli memory update mem_001 --content "Updated: John Smith now prefers BBQ Chicken over Pepperoni as of Dec 2024" --db pizza_test

# Delete memory - EXPECT: Deletion confirmation
uv run python -m arangodb.cli memory delete mem_007 --db pizza_test
```

## Task 5: Analysis Operations Validation

### Community Detection

```bash
# Ingredient communities - EXPECT: Clusters (Italian, American, etc.)
uv run python -m arangodb.cli community detect --collection pizzas --edge-collection pizza_ingredients --db pizza_test

# Customer communities - EXPECT: Customer segments
uv run python -m arangodb.cli community detect --collection customers --edge-collection customer_orders --db pizza_test
```

### Temporal Analysis

```bash
# Order patterns - EXPECT: Temporal insights from December 2024
uv run python -m arangodb.cli temporal extract --collection orders --start 2024-12-01 --end 2024-12-31 --db pizza_test

# Review trends - EXPECT: Sentiment over time
uv run python -m arangodb.cli temporal extract --collection pizza_reviews --start 2024-12-01 --end 2024-12-31 --db pizza_test
```

### Contradiction Detection

```bash
# Detect contradictions - EXPECT: Find Hawaiian pizza contradictions
uv run python -m arangodb.cli contradiction detect --collection memories --db pizza_test
```

## Task 6: Complex Query Validation

### Custom AQL Queries

```bash
# Most popular pizzas by orders
uv run python -m arangodb.cli crud query --aql "FOR order IN orders FOR pizza IN 1..1 OUTBOUND order order_items COLLECT p = pizza.name WITH COUNT INTO cnt SORT cnt DESC RETURN {pizza: p, orders: cnt}" --db pizza_test

# Supply chain analysis
uv run python -m arangodb.cli crud query --aql "FOR s IN ingredient_suppliers LET ing = (FOR i IN 1..1 OUTBOUND s supplier_ingredients RETURN i.name) RETURN {supplier: s.name, supplies: ing}" --db pizza_test

# Empty result query - EXPECT: Empty array
uv run python -m arangodb.cli crud query --aql "FOR p IN pizzas FILTER p.price > 100 RETURN p" --db pizza_test
```

## Task 7: Edge Cases and Error Handling

### Invalid Operations

```bash
# Non-existent collection - EXPECT: Collection not found error
uv run python -m arangodb.cli crud list --collection sandwiches --db pizza_test

# Invalid AQL - EXPECT: AQL syntax error
uv run python -m arangodb.cli crud query --aql "INVALID QUERY SYNTAX" --db pizza_test

# Wrong edge collection - EXPECT: No results or error
uv run python -m arangodb.cli graph traverse pizzas/margherita --direction outbound --edge-collection customer_orders --db pizza_test

# Semantic search on non-embedded collection - EXPECT: Error or fallback
uv run python -m arangodb.cli search semantic --query "test" --collection ingredient_suppliers --db pizza_test
```

## Validation Checklist

For each command, verify:
- [ ] Command executes without Python errors
- [ ] Returns expected document count
- [ ] Data structure matches schema
- [ ] Empty/no results for unrelated queries
- [ ] Appropriate error messages for invalid inputs
- [ ] Embeddings present where expected (1024 dimensions)
- [ ] Graph traversals return connected documents
- [ ] Temporal data parsed correctly
- [ ] Search relevance scores make sense

## Success Criteria

```python
# All tests pass when:
assert all([
    crud_operations_work,      # 6/6 CRUD commands succeed
    search_returns_relevant,   # 10/10 search queries return expected
    graph_traversals_correct,  # 6/6 traversals follow relationships  
    memory_agent_functional,   # 5/5 memory operations work
    analysis_produces_insights,# 3/3 analysis commands succeed
    complex_queries_work,      # 3/3 AQL queries return results
    errors_handled_gracefully  # 4/4 error cases handled properly
])
```

## Common Issues & Solutions

### Issue 1: No embeddings in results
```bash
# Solution: Run embed_collections.py first
uv run python tests/data/embed_collections.py
```

### Issue 2: Semantic search returns empty
```bash
# Solution: Check collection has embedding field
uv run python -m arangodb.cli crud get margherita --collection pizzas --db pizza_test | grep embedding
```

### Issue 3: Graph traversal depth confusion
```bash
# Solution: Use --depth flag correctly
# depth 1 = direct connections
# depth 2 = connections of connections
```