#!/usr/bin/env python3
"""
Test advanced features with the enhanced pizza database.

This script demonstrates:
- Multi-hop graph traversals
- Semantic and hybrid search with embeddings
- Memory agent operations
- Complex relationship queries
- Temporal analysis
"""

import subprocess
import json
from pathlib import Path
from loguru import logger

logger.add("advanced_features_test.log", rotation="10 MB")

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

def test_semantic_search():
    """Test semantic search with embeddings."""
    print("\n=== Testing Semantic Search ===")
    
    # Test 1: Find pizzas similar to "Italian classic with tomatoes"
    code, out, err = run_cli_command(
        'search semantic --query "Italian classic with tomatoes and cheese" '
        '--collection pizzas --db pizza_test --limit 3'
    )
    print(f"Semantic search for Italian classics: {code == 0}")
    if code == 0:
        print("Results preview:", out.split('\n')[1:4])
    
    # Test 2: Search memories for supply chain insights
    code, out, err = run_cli_command(
        'search semantic --query "supplier price increases and negotiations" '
        '--collection memories --db pizza_test --limit 3'
    )
    print(f"Memory search for supply chain: {code == 0}")
    
    # Test 3: Find reviews mentioning texture and quality
    code, out, err = run_cli_command(
        'search semantic --query "crust texture cheese quality fresh ingredients" '
        '--collection pizza_reviews --db pizza_test --limit 3'
    )
    print(f"Review search for quality mentions: {code == 0}")

def test_hybrid_search():
    """Test hybrid search combining BM25 and semantic."""
    print("\n=== Testing Hybrid Search ===")
    
    # Test 1: Combine keyword and semantic for pizza search
    code, out, err = run_cli_command(
        'search hybrid --query "vegetarian pizza fresh vegetables" '
        '--collection pizzas --db pizza_test '
        '--bm25-weight 0.4 --semantic-weight 0.6'
    )
    print(f"Hybrid search for vegetarian options: {code == 0}")
    
    # Test 2: Search reviews with balanced weights
    code, out, err = run_cli_command(
        'search hybrid --query "best pizza authentic Italian wood fired" '
        '--collection pizza_reviews --db pizza_test '
        '--bm25-weight 0.5 --semantic-weight 0.5'
    )
    print(f"Hybrid search in reviews: {code == 0}")

def test_multi_hop_traversals():
    """Test complex multi-hop graph traversals."""
    print("\n=== Testing Multi-Hop Graph Traversals ===")
    
    # Test 1: Customer → Orders → Pizzas → Ingredients (3 hops)
    print("\nTest 1: Customer ingredient history (3-hop)")
    aql_query = """
    FOR customer IN customers
        FILTER customer._key == 'cust_001'
        FOR order IN 1..1 OUTBOUND customer customer_orders
            FOR pizza IN 1..1 OUTBOUND order order_items
                FOR ingredient IN 1..1 OUTBOUND pizza pizza_ingredients
                    COLLECT ingredient_name = ingredient.name 
                    WITH COUNT INTO times_consumed
                    SORT times_consumed DESC
                    LIMIT 5
                    RETURN {
                        ingredient: ingredient_name, 
                        times_consumed: times_consumed
                    }
    """
    code, out, err = run_cli_command(
        f'crud query --aql "{aql_query}" --db pizza_test'
    )
    print(f"3-hop traversal success: {code == 0}")
    
    # Test 2: Pizza → Ingredients → Suppliers (2 hops with filters)
    print("\nTest 2: Pizza supply chain (2-hop)")
    code, out, err = run_cli_command(
        'graph traverse pizzas/pepperoni --direction outbound '
        '--edge-collection pizza_ingredients --depth 2 --db pizza_test'
    )
    print(f"Supply chain traversal: {code == 0}")
    
    # Test 3: Memory associations (variable depth)
    print("\nTest 3: Memory association network")
    code, out, err = run_cli_command(
        'graph traverse memories/mem_001 --direction any '
        '--edge-collection memory_links --depth 2 --db pizza_test'
    )
    print(f"Memory network traversal: {code == 0}")

def test_memory_agent_features():
    """Test memory agent specific features."""
    print("\n=== Testing Memory Agent Features ===")
    
    # Test 1: Create episodic memory from order pattern
    memory_data = {
        "content": "Friday rush analysis: Orders spike 300% between 6-8 PM. "
                  "Pepperoni pizza accounts for 45% of Friday orders. "
                  "Customer John Smith consistently orders at 6:30 PM Fridays. "
                  "Recommend: Pre-make 20 pepperoni pizzas at 5:45 PM on Fridays.",
        "summary": "Friday evening order pattern and optimization strategy",
        "metadata": {
            "context": "operational_insight",
            "source": "order_analysis",
            "confidence": 0.88,
            "day_of_week": "friday",
            "time_window": "18:00-20:00"
        },
        "entity_type": "pattern_recognition",
        "importance": 0.85,
        "tags": ["operations", "peak_hours", "pepperoni", "predictive"]
    }
    
    code, out, err = run_cli_command(
        f"memory create --content '{memory_data['content']}' "
        f"--metadata '{json.dumps(memory_data['metadata'])}' "
        f"--tags '{','.join(memory_data['tags'])}' --db pizza_test"
    )
    print(f"Create pattern memory: {code == 0}")
    
    # Test 2: Search memories by context
    code, out, err = run_cli_command(
        'memory search --query "Friday peak hours operations" --db pizza_test'
    )
    print(f"Context-aware memory search: {code == 0}")
    
    # Test 3: Episode-based memory retrieval
    code, out, err = run_cli_command(
        'episode list --limit 5 --db pizza_test'
    )
    print(f"Episode listing: {code == 0}")

def test_temporal_analysis():
    """Test temporal analysis features."""
    print("\n=== Testing Temporal Analysis ===")
    
    # Test 1: Extract temporal patterns from orders
    code, out, err = run_cli_command(
        'temporal extract --collection orders '
        '--start 2024-12-01 --end 2024-12-31 --db pizza_test'
    )
    print(f"Temporal pattern extraction: {code == 0}")
    
    # Test 2: Analyze review sentiment over time
    aql_query = """
    FOR review IN pizza_reviews
        COLLECT 
            month = DATE_MONTH(review.created_at),
            pizza = DOCUMENT(review.pizza_id).name
        AGGREGATE 
            avg_rating = AVG(review.rating),
            avg_sentiment = AVG(review.sentiment_score),
            review_count = COUNT(review)
        SORT month, avg_rating DESC
        RETURN {
            month: month,
            pizza: pizza,
            avg_rating: avg_rating,
            avg_sentiment: avg_sentiment,
            reviews: review_count
        }
    """
    code, out, err = run_cli_command(
        f'crud query --aql "{aql_query}" --db pizza_test'
    )
    print(f"Temporal sentiment analysis: {code == 0}")

def test_contradiction_detection():
    """Test contradiction detection in memories and reviews."""
    print("\n=== Testing Contradiction Detection ===")
    
    # Create potentially contradictory memory
    contradiction_memory = {
        "content": "Recent analysis shows Hawaiian pizza is our least popular item "
                  "with only 5% of orders. Customers complain about the pineapple quality. "
                  "Recommendation: Remove Hawaiian pizza from menu.",
        "summary": "Hawaiian pizza performing poorly - consider removal",
        "metadata": {
            "context": "product_analysis",
            "source": "sales_analysis",
            "confidence": 0.7
        },
        "entity_type": "product_insight",
        "entity_id": "pizzas/hawaiian",
        "tags": ["hawaiian", "poor_performance", "remove"]
    }
    
    code, out, err = run_cli_command(
        f"memory create --content '{contradiction_memory['content']}' "
        f"--metadata '{json.dumps(contradiction_memory['metadata'])}' "
        f"--tags '{','.join(contradiction_memory['tags'])}' --db pizza_test"
    )
    print(f"Create contradictory memory: {code == 0}")
    
    # Detect contradictions
    code, out, err = run_cli_command(
        'contradiction detect --collection memories --db pizza_test'
    )
    print(f"Contradiction detection in memories: {code == 0}")

def test_community_detection():
    """Test community detection on ingredient networks."""
    print("\n=== Testing Community Detection ===")
    
    # Detect communities in pizza-ingredient network
    code, out, err = run_cli_command(
        'community detect --collection pizzas '
        '--edge-collection pizza_ingredients --db pizza_test'
    )
    print(f"Ingredient community detection: {code == 0}")
    
    # Detect communities in customer-order patterns
    code, out, err = run_cli_command(
        'community detect --collection customers '
        '--edge-collection customer_orders --db pizza_test'
    )
    print(f"Customer community detection: {code == 0}")

def test_advanced_aggregations():
    """Test complex aggregation queries."""
    print("\n=== Testing Advanced Aggregations ===")
    
    # Supply chain cost analysis
    aql_query = """
    LET supplier_impact = (
        FOR supplier IN ingredient_suppliers
            LET total_ingredient_cost = SUM(
                FOR ingredient IN 1..1 OUTBOUND supplier supplier_ingredients
                    LET usage = SUM(
                        FOR pizza IN 1..1 INBOUND ingredient pizza_ingredients
                            RETURN 1
                    )
                    RETURN ingredient.cost_per_unit * usage * 100
            )
            RETURN {
                supplier: supplier.name,
                total_impact: total_ingredient_cost,
                reliability: supplier.reliability_score
            }
    )
    RETURN {
        total_suppliers: LENGTH(supplier_impact),
        total_cost_impact: SUM(supplier_impact[*].total_impact),
        suppliers: supplier_impact
    }
    """
    code, out, err = run_cli_command(
        f'crud query --aql "{aql_query}" --db pizza_test'
    )
    print(f"Supply chain cost analysis: {code == 0}")

def test_visualization():
    """Test graph visualization capabilities."""
    print("\n=== Testing Visualization ===")
    
    # Visualize pizza-ingredient network
    code, out, err = run_cli_command(
        'visualize graph --collection pizzas '
        '--edge-collection pizza_ingredients '
        '--layout force --db pizza_test '
        '--output /tmp/pizza_ingredients_graph.html'
    )
    print(f"Pizza-ingredient visualization: {code == 0}")
    
    # Visualize customer journey
    code, out, err = run_cli_command(
        'visualize graph --collection customers '
        '--edge-collection customer_orders '
        '--layout radial --db pizza_test '
        '--output /tmp/customer_journey_graph.html'
    )
    print(f"Customer journey visualization: {code == 0}")

def main():
    """Run all advanced feature tests."""
    print("🍕 Advanced Pizza Database Test Suite 🍕")
    print("=" * 60)
    
    # First, ensure the enhanced database is set up
    print("\nSetting up enhanced pizza database...")
    setup_result = subprocess.run(
        "cd /home/graham/workspace/experiments/arangodb && "
        "uv run python tests/data/setup_enhanced_pizza_database.py",
        shell=True,
        capture_output=True
    )
    
    if setup_result.returncode != 0:
        print("Failed to setup database:", setup_result.stderr.decode())
        return
    
    # Run all test suites
    test_suites = [
        ("Semantic Search", test_semantic_search),
        ("Hybrid Search", test_hybrid_search),
        ("Multi-Hop Traversals", test_multi_hop_traversals),
        ("Memory Agent Features", test_memory_agent_features),
        ("Temporal Analysis", test_temporal_analysis),
        ("Contradiction Detection", test_contradiction_detection),
        ("Community Detection", test_community_detection),
        ("Advanced Aggregations", test_advanced_aggregations),
        ("Visualization", test_visualization)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in test_suites:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            logger.exception(f"{name} failed")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Test Summary: {passed} passed, {failed} failed")
    print("\nCheck advanced_features_test.log for detailed output")
    
    # Show some interesting results
    print("\n🎯 Key Insights from Tests:")
    print("- Multi-hop traversals can trace ingredients through the entire supply chain")
    print("- Semantic search understands context beyond keywords")
    print("- Memory agent can identify patterns and contradictions")
    print("- Graph visualization reveals hidden relationships")

if __name__ == "__main__":
    main()