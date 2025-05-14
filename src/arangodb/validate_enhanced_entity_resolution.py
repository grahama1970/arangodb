#!/usr/bin/env python3
"""
Validation script for enhanced entity resolution functionality.

This script demonstrates and tests the enhanced entity resolution functionality,
which includes:
1. Exact name matching with normalization and variants
2. Semantic similarity matching
3. Attribute merging with different strategies
4. Confidence scoring for entity matches
5. CLI commands for entity resolution

Usage:
    python -m arangodb.validate_enhanced_entity_resolution
"""

import sys
import json
from datetime import datetime, timezone
from loguru import logger

# Import ArangoDB setup functions
try:
    from arangodb.arango_setup import connect_arango, ensure_database
    from arangodb.config import COLLECTION_NAME
    from arangodb.enhanced_entity_resolution import (
        normalize_name,
        get_name_variants,
        find_exact_entity_matches,
        find_similar_entity_matches,
        merge_entity_attributes,
        calculate_entity_match_confidence,
        resolve_entity
    )
except ImportError:
    from src.arangodb.arango_setup import connect_arango, ensure_database
    from src.arangodb.config import COLLECTION_NAME
    from src.arangodb.enhanced_entity_resolution import (
        normalize_name,
        get_name_variants,
        find_exact_entity_matches,
        find_similar_entity_matches,
        merge_entity_attributes,
        calculate_entity_match_confidence,
        resolve_entity
    )

def main():
    """Main validation function for enhanced entity resolution."""
    # Initialize logger
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    try:
        # Connect to database
        logger.info("Connecting to ArangoDB...")
        client = connect_arango()
        db = ensure_database(client)
        
        # Create test collection
        test_collection = "test_entity_resolution"
        if db.has_collection(test_collection):
            db.delete_collection(test_collection)
        
        db.create_collection(test_collection)
        
        # Test 1: Create test entities with various name formats
        total_tests += 1
        logger.info("Test 1: Creating test entities with different name formats")
        
        test_entities = [
            {
                "name": "John Smith",
                "type": "Person",
                "attributes": {
                    "age": 30,
                    "occupation": "Software Engineer",
                    "location": "New York"
                }
            },
            {
                "name": "JOHN SMITH",  # Uppercase variation
                "type": "Person",
                "attributes": {
                    "age": 32,
                    "company": "Acme Corp",
                    "skills": ["Python", "JavaScript"]
                }
            },
            {
                "name": "Smith, John",  # Reversed name format
                "type": "Person",
                "attributes": {
                    "education": "Computer Science",
                    "languages": ["English", "Spanish"]
                }
            },
            {
                "name": "Jane Doe",  # Different person
                "type": "Person",
                "attributes": {
                    "age": 28,
                    "occupation": "Data Scientist"
                }
            },
            {
                "name": "Acme Corporation",  # Organization
                "type": "Organization",
                "attributes": {
                    "industry": "Technology",
                    "employees": 500,
                    "founded": 2005
                }
            }
        ]
        
        # Insert test entities
        inserted_keys = []
        for entity in test_entities:
            result = db.collection(test_collection).insert(entity)
            inserted_keys.append(result["_key"])
        
        if len(inserted_keys) != len(test_entities):
            all_validation_failures.append(f"Test 1: Failed to insert all test entities. Expected {len(test_entities)}, got {len(inserted_keys)}")
        else:
            logger.info(f"Successfully inserted {len(inserted_keys)} test entities")
        
        # Test 2: Name normalization and variants
        total_tests += 1
        logger.info("Test 2: Testing name normalization and variants")
        
        # Test name normalization
        test_names = [
            ("John Smith", "john smith"),
            ("JOHN SMITH", "john smith"),
            ("John  Smith", "john smith"),
            ("Smith, John", "smith john"),
            ("John-Smith", "john smith")
        ]
        
        for original, expected in test_names:
            normalized = normalize_name(original)
            if normalized != expected:
                all_validation_failures.append(f"Test 2a: Name normalization failed. Expected '{expected}' for '{original}', got '{normalized}'")
        
        # Test name variants
        test_name = "John A. Smith"
        variants = get_name_variants(test_name)
        
        expected_variants = ["John A. Smith", "john a smith", "Smith, John A.", "John Smith"]
        missing_variants = []
        
        for expected in expected_variants:
            if not any(v.lower() == expected.lower() for v in variants):
                missing_variants.append(expected)
        
        if missing_variants:
            all_validation_failures.append(f"Test 2b: Missing expected name variants: {missing_variants}")
        
        # Test 3: Exact name matching
        total_tests += 1
        logger.info("Test 3: Testing exact name matching")
        
        # Create test search entity
        search_entity = {
            "name": "John Smith",
            "type": "Person"
        }
        
        matches = find_exact_entity_matches(db, search_entity, test_collection)
        
        # Should match 3 entities with different case and format of "John Smith"
        if len(matches) != 3:
            all_validation_failures.append(f"Test 3: Expected 3 exact name matches, got {len(matches)}")
        else:
            logger.info(f"Successfully found {len(matches)} exact name matches")
        
        # Test 4: Semantic similarity matching
        total_tests += 1
        logger.info("Test 4: Testing semantic similarity matching")
        
        # Add embeddings to entities for semantic matching
        # In a real scenario, these would be generated from the entity text
        # Here we'll use dummy embeddings with known similarity
        
        # Update entities with embeddings
        john_smith_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        jane_doe_embedding = [0.9, 0.8, 0.7, 0.6, 0.5]
        
        # Update the first three entities with similar embeddings
        for i in range(3):
            # Slightly vary the embedding for each John Smith entity
            variation = [x + (i * 0.01) for x in john_smith_embedding]
            db.collection(test_collection).update(inserted_keys[i], {"embedding": variation})
        
        # Update Jane Doe with a different embedding
        db.collection(test_collection).update(inserted_keys[3], {"embedding": jane_doe_embedding})
        
        # Update Acme Corporation with yet another embedding
        db.collection(test_collection).update(inserted_keys[4], {"embedding": [0.5, 0.5, 0.5, 0.5, 0.5]})
        
        # Create a test entity with embedding similar to John Smith
        test_entity = {
            "name": "Johnny Smith",  # Slightly different name
            "type": "Person",
            "embedding": [0.11, 0.21, 0.31, 0.41, 0.51]  # Similar to John Smith
        }
        
        # Find semantically similar entities
        matches = find_similar_entity_matches(
            db, 
            test_entity, 
            test_collection,
            min_similarity=0.9  # High threshold
        )
        
        # Should find the John Smith entities (which have similar embeddings)
        if len(matches) < 2:
            all_validation_failures.append(f"Test 4: Expected at least 2 semantic similarity matches, got {len(matches)}")
        else:
            logger.info(f"Successfully found {len(matches)} semantic similarity matches")
            
            # Check that all matches have confidence scores
            if not all("_confidence" in match for match in matches):
                all_validation_failures.append("Test 4: Not all matches have confidence scores")
        
        # Test 5: Attribute merging
        total_tests += 1
        logger.info("Test 5: Testing attribute merging strategies")
        
        entity1 = {
            "name": "Test Person",
            "type": "Person",
            "attributes": {
                "age": 30,
                "occupation": "Engineer",
                "skills": ["Python", "Java"]
            }
        }
        
        entity2 = {
            "name": "Test Person",
            "type": "Person",
            "attributes": {
                "age": 31,  # Different age
                "occupation": "Engineer",  # Same occupation
                "location": "New York",  # New attribute
                "skills": ["Python", "JavaScript"]  # Different skills
            }
        }
        
        # Test union strategy
        merged_union = merge_entity_attributes(entity2, entity1, "union")
        expected_union_attrs = {
            "age": 31,  # Takes from entity2 (overrides)
            "occupation": "Engineer",
            "skills": ["Python", "JavaScript"],  # Takes from entity2 (overrides)
            "location": "New York"  # Added from entity2
        }
        
        if merged_union["attributes"] != expected_union_attrs:
            all_validation_failures.append(f"Test 5a: Union merge failed. Expected {expected_union_attrs}, got {merged_union['attributes']}")
        
        # Test prefer_existing strategy
        merged_prefer_existing = merge_entity_attributes(entity2, entity1, "prefer_existing")
        expected_prefer_existing_attrs = {
            "age": 30,  # Keeps from entity1
            "occupation": "Engineer",
            "skills": ["Python", "Java"],  # Keeps from entity1
            "location": "New York"  # Added from entity2 (doesn't exist in entity1)
        }
        
        if merged_prefer_existing["attributes"] != expected_prefer_existing_attrs:
            all_validation_failures.append(f"Test 5b: prefer_existing merge failed. Expected {expected_prefer_existing_attrs}, got {merged_prefer_existing['attributes']}")
        
        # Test prefer_new strategy
        merged_prefer_new = merge_entity_attributes(entity2, entity1, "prefer_new")
        expected_prefer_new_attrs = {
            "age": 31,  # Takes from entity2
            "occupation": "Engineer",
            "skills": ["Python", "JavaScript"],  # Takes from entity2
            "location": "New York"  # Added from entity2
        }
        
        if merged_prefer_new["attributes"] != expected_prefer_new_attrs:
            all_validation_failures.append(f"Test 5c: prefer_new merge failed. Expected {expected_prefer_new_attrs}, got {merged_prefer_new['attributes']}")
        
        # Test intersection strategy
        merged_intersection = merge_entity_attributes(entity2, entity1, "intersection")
        expected_intersection_attrs = {
            "age": 31,  # Takes from entity2 but exists in both
            "occupation": "Engineer",  # Exists in both
            "skills": ["Python", "JavaScript"]  # Takes from entity2 but exists in both
        }
        
        if merged_intersection["attributes"] != expected_intersection_attrs:
            all_validation_failures.append(f"Test 5d: intersection merge failed. Expected {expected_intersection_attrs}, got {merged_intersection['attributes']}")
        
        # Test 6: Confidence calculation
        total_tests += 1
        logger.info("Test 6: Testing confidence scoring")
        
        entity1 = {
            "name": "John A. Smith",
            "type": "Person",
            "attributes": {"age": 30},
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        
        # Exact name match, all attributes match
        entity2 = entity1.copy()
        confidence = calculate_entity_match_confidence(entity1, entity2)
        if confidence < 0.95:
            all_validation_failures.append(f"Test 6a: Expected confidence near 1.0 for identical entities, got {confidence}")
        
        # Similar name, some attributes match
        entity3 = {
            "name": "John Smith",  # Similar name
            "type": "Person",  # Same type
            "attributes": {"age": 31},  # Different age
            "embedding": [0.11, 0.21, 0.31, 0.41, 0.51]  # Similar embedding
        }
        
        confidence = calculate_entity_match_confidence(entity1, entity3)
        if confidence < 0.7:
            all_validation_failures.append(f"Test 6b: Expected confidence above 0.7 for similar entities, got {confidence}")
        
        # Different name, different type
        entity4 = {
            "name": "Acme Corp",  # Different name
            "type": "Organization",  # Different type
            "attributes": {"employees": 500},  # Different attributes
            "embedding": [0.9, 0.8, 0.7, 0.6, 0.5]  # Different embedding
        }
        
        confidence = calculate_entity_match_confidence(entity1, entity4)
        if confidence > 0.5:
            all_validation_failures.append(f"Test 6c: Expected confidence below 0.5 for different entities, got {confidence}")
        
        # Test 7: Full entity resolution
        total_tests += 1
        logger.info("Test 7: Testing full entity resolution")
        
        # First, create a new entity to serve as the base
        base_entity = {
            "name": "Dr. John Smith",
            "type": "Person",
            "attributes": {
                "age": 35,
                "occupation": "Physician",
                "specialty": "Cardiology"
            },
            "embedding": [0.12, 0.22, 0.32, 0.42, 0.52]  # Similar to John Smith
        }
        
        # Insert it into the database
        result = db.collection(test_collection).insert(base_entity)
        base_key = result["_key"]
        
        # Now create a new entity that should match and merge with the base
        new_entity = {
            "name": "John Smith, MD",  # Different format but same person
            "type": "Person",
            "attributes": {
                "hospital": "City Hospital",  # New attribute
                "languages": ["English", "Spanish"]  # New attribute
            },
            "embedding": [0.13, 0.23, 0.33, 0.43, 0.53]  # Similar to John Smith
        }
        
        # Resolve the entity
        resolved, matches, merged = resolve_entity(
            db,
            new_entity,
            test_collection,
            auto_merge=True
        )
        
        if not merged:
            all_validation_failures.append("Test 7a: Entity resolution did not result in a merge")
        else:
            logger.info("Successfully merged entities during resolution")
            
            # Check that attributes were properly merged
            if "hospital" not in resolved["attributes"] or "specialty" not in resolved["attributes"]:
                all_validation_failures.append(f"Test 7b: Merged entity missing expected attributes: {resolved['attributes']}")
            
            # Check that merge history was recorded
            if "_merge_history" not in resolved or not resolved["_merge_history"]:
                all_validation_failures.append("Test 7c: Merged entity missing merge history")
        
        # Clean up
        db.delete_collection(test_collection)
        logger.info("Cleaned up test collection")
        
        # Final validation result
        if all_validation_failures:
            logger.error(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                logger.error(f"  - {failure}")
            sys.exit(1)  # Exit with error code
        else:
            logger.info(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            logger.info("Enhanced entity resolution module is validated")
            sys.exit(0)  # Exit with success code
            
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()