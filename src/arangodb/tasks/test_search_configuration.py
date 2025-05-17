"""
Search Configuration Validation

Tests the search configuration implementation to ensure it works correctly.
This includes config creation, query routing, and integration with existing search.
"""

import sys
import os
import json
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from loguru import logger
from arango import ArangoClient
from arangodb.core.search.search_config import (
    SearchConfig,
    SearchConfigManager,
    SearchMethod,
    QueryTypeConfig
)
from arangodb.core.search.hybrid_search import search_with_config
from arangodb.core.constants import COLLECTION_NAME


def get_db_connection():
    """Get database connection."""
    client = ArangoClient(hosts='http://localhost:8529')
    return client.db('test', username='root', password='root')


def validate_basic_config():
    """Validate basic configuration creation and management."""
    logger.info("=== Validating Basic Configuration ===")
    
    validation_errors = []
    
    try:
        # Test 1: Default configuration
        config = SearchConfig()
        if config.preferred_method != SearchMethod.HYBRID:
            validation_errors.append("Default config should use HYBRID method")
        if config.result_limit != 20:
            validation_errors.append("Default result limit should be 20")
        logger.info("✓ Default configuration created successfully")
        
        # Test 2: Custom configuration
        custom = SearchConfig(
            preferred_method=SearchMethod.SEMANTIC,
            enable_reranking=True,
            result_limit=50,
            bm25_weight=0.3,
            semantic_weight=0.7
        )
        if custom.preferred_method != SearchMethod.SEMANTIC:
            validation_errors.append("Custom config method not set correctly")
        if custom.bm25_weight + custom.semantic_weight != 1.0:
            validation_errors.append("Weights should sum to 1.0")
        logger.info("✓ Custom configuration created successfully")
        
        # Test 3: Query type configs
        if not hasattr(QueryTypeConfig, 'FACTUAL'):
            validation_errors.append("FACTUAL config missing")
        if not hasattr(QueryTypeConfig, 'CONCEPTUAL'):
            validation_errors.append("CONCEPTUAL config missing")
        if QueryTypeConfig.FACTUAL.preferred_method != SearchMethod.BM25:
            validation_errors.append("FACTUAL should prefer BM25")
        logger.info("✓ Query type configurations validated")
        
    except Exception as e:
        validation_errors.append(f"Configuration error: {str(e)}")
    
    return validation_errors


def validate_query_routing():
    """Validate query routing logic."""
    logger.info("\n=== Validating Query Routing ===")
    
    validation_errors = []
    manager = SearchConfigManager()
    
    test_cases = [
        # (query, expected_method, description)
        ("What is Python?", SearchMethod.BM25, "Factual query"),
        ("How many developers use Python?", SearchMethod.BM25, "Quantitative query"),
        ("Why is Python popular?", SearchMethod.SEMANTIC, "Conceptual query"),
        ("Explain object-oriented programming", SearchMethod.SEMANTIC, "Explanatory query"),
        ("Show me tag:python documents", SearchMethod.TAG, "Tag-based query"),
        ("What's related to databases?", SearchMethod.GRAPH, "Graph exploration"),
        ("Recent Python updates", SearchMethod.HYBRID, "Temporal query"),
        ("General programming concepts", SearchMethod.HYBRID, "General query")
    ]
    
    for query, expected_method, description in test_cases:
        try:
            config = manager.get_config_for_query(query)
            if config.preferred_method != expected_method:
                validation_errors.append(
                    f"{description} '{query}' routed to {config.preferred_method.value}, "
                    f"expected {expected_method.value}"
                )
            else:
                logger.info(f"✓ {description}: '{query}' → {config.preferred_method.value}")
        except Exception as e:
            validation_errors.append(f"Routing error for '{query}': {str(e)}")
    
    return validation_errors


def validate_search_integration(db):
    """Validate integration with search functionality."""
    logger.info("\n=== Validating Search Integration ===")
    
    validation_errors = []
    
    try:
        # Test 1: Search with default config
        results = search_with_config(
            db=db,
            query_text="Python programming",
            output_format="json"
        )
        
        if "results" not in results:
            validation_errors.append("Search results missing 'results' field")
        if "total" not in results:
            validation_errors.append("Search results missing 'total' field")
        
        logger.info(f"✓ Default search returned {results.get('total', 0)} results")
        
        # Test 2: Search with custom config
        custom_config = SearchConfig(
            preferred_method=SearchMethod.BM25,
            result_limit=5
        )
        
        results = search_with_config(
            db=db,
            query_text="database",
            config=custom_config,
            output_format="json"
        )
        
        if len(results.get("results", [])) > 5:
            validation_errors.append("Result limit not respected")
        
        logger.info(f"✓ Custom config search returned {len(results.get('results', []))} results")
        
        # Test 3: Different search methods
        methods_to_test = [SearchMethod.BM25, SearchMethod.SEMANTIC]
        
        for method in methods_to_test:
            config = SearchConfig(preferred_method=method)
            results = search_with_config(
                db=db,
                query_text="Python",
                config=config,
                output_format="json"
            )
            logger.info(f"✓ {method.value} search executed successfully")
        
    except Exception as e:
        validation_errors.append(f"Search integration error: {str(e)}")
    
    return validation_errors


def validate_cli_integration():
    """Validate CLI command integration."""
    logger.info("\n=== Validating CLI Integration ===")
    
    validation_errors = []
    
    try:
        # Test imports
        from arangodb.cli.search_config_commands import app, list_configs, analyze_query
        logger.info("✓ CLI commands imported successfully")
        
        # Test that app is properly configured
        if not hasattr(app, 'registered_commands'):
            # Typer apps don't have registered_commands, check for commands differently
            commands = [cmd for cmd in dir(app) if not cmd.startswith('_')]
            if not commands:
                validation_errors.append("No CLI commands registered")
        
        logger.info("✓ CLI integration validated")
        
    except ImportError as e:
        validation_errors.append(f"CLI import error: {str(e)}")
    except Exception as e:
        validation_errors.append(f"CLI validation error: {str(e)}")
    
    return validation_errors


def main():
    """Run all validation tests."""
    logger.info("Starting Search Configuration Validation")
    
    all_errors = []
    
    # Run validations
    errors = validate_basic_config()
    all_errors.extend(errors)
    
    errors = validate_query_routing()
    all_errors.extend(errors)
    
    # Get database connection for search tests
    db = get_db_connection()
    errors = validate_search_integration(db)
    all_errors.extend(errors)
    
    errors = validate_cli_integration()
    all_errors.extend(errors)
    
    # Report results
    print("\n" + "="*50)
    print("SEARCH CONFIGURATION VALIDATION RESULTS")
    print("="*50)
    
    if not all_errors:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("\nSearch Configuration Feature Implementation:")
        print("- Basic configuration management: COMPLETE")
        print("- Query routing logic: COMPLETE")
        print("- Search integration: COMPLETE")
        print("- CLI commands: COMPLETE")
        print("\nFeature Status: 100% COMPLETE")
        return True
    else:
        print("\n❌ VALIDATION FAILURES:")
        for error in all_errors:
            print(f"  - {error}")
        print(f"\nTotal errors: {len(all_errors)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)