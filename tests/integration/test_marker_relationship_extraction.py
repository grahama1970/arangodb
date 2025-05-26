#!/usr/bin/env python3
"""
Test script for relationship extraction from Marker output.

This script loads a sample Marker output file and tests the relationship extraction
functionality with various approaches:
1. Text-based relationship extraction using patterns
2. Similarity-based relationship extraction
3. Entity extraction and validation

Usage:
    python test_marker_relationship_extraction.py [--marker-file PATH]
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import relationship extraction module
from arangodb.core.graph.relationship_extraction import RelationshipExtractor, EntityExtractor, RelationshipType
from arangodb.core.arango_setup import connect_arango, ensure_database, ensure_collection
from arangodb.core.utils.embedding_utils import get_embedding

# Test database name
TEST_DB_NAME = "marker_relationship_test"


async def setup_test_db():
    """Set up a test database for relationship extraction testing."""
    try:
        # Connect to ArangoDB
        client = connect_arango()
        
        # Get _system database
        sys_db = client.db(
            name="_system",
            username=os.getenv("ARANGO_USERNAME", "root"),
            password=os.getenv("ARANGO_PASSWORD", "openSesame"),
            verify=True
        )
        
        # Create test database if it doesn't exist
        if not sys_db.has_database(TEST_DB_NAME):
            logger.info(f"Creating test database: {TEST_DB_NAME}")
            sys_db.create_database(
                name=TEST_DB_NAME,
                users=[{
                    "username": os.getenv("ARANGO_USERNAME", "root"),
                    "password": os.getenv("ARANGO_PASSWORD", "openSesame"),
                    "active": True
                }]
            )
        
        # Connect to the test database
        db = client.db(
            name=TEST_DB_NAME,
            username=os.getenv("ARANGO_USERNAME", "root"),
            password=os.getenv("ARANGO_PASSWORD", "openSesame"),
            verify=True
        )
        
        # Create required collections
        collections = [
            ("document_objects", False),       # Document content elements
            ("content_relationships", True)    # Relationships between elements
        ]
        
        for name, is_edge in collections:
            if db.has_collection(name):
                db.collection(name).truncate()
            else:
                ensure_collection(db, name, is_edge_collection=is_edge)
        
        return db
    
    except Exception as e:
        logger.error(f"Error setting up test database: {e}")
        raise


def load_marker_output(file_path: str) -> Dict[str, Any]:
    """Load Marker output from a file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading Marker output: {e}")
        # Create a simple synthetic test document if file not found
        return create_synthetic_marker_output()


def create_synthetic_marker_output() -> Dict[str, Any]:
    """Create a synthetic Marker output for testing."""
    logger.info("Creating synthetic Marker output for testing")
    
    # Create a basic document structure
    document = {
        "document": {
            "title": "Test Document",
            "metadata": {
                "author": "Test Author",
                "date": "2023-01-01"
            }
        },
        "objects": [
            {
                "_key": "obj1",
                "_type": "section",
                "text": "Introduction to Graph Databases",
                "section_hash": "section1",
                "page_id": 1,
                "position": {"top": 100, "left": 100}
            },
            {
                "_key": "obj2",
                "_type": "text",
                "text": "Graph databases like ArangoDB are essential for knowledge management. They provide flexible storage for interconnected data.",
                "section_hash": "section1",
                "page_id": 1,
                "position": {"top": 150, "left": 100}
            },
            {
                "_key": "obj3",
                "_type": "text",
                "text": "Before using ArangoDB, you should understand basic graph theory concepts like nodes and edges.",
                "section_hash": "section1",
                "page_id": 1,
                "position": {"top": 200, "left": 100}
            },
            {
                "_key": "obj4",
                "_type": "section",
                "text": "ArangoDB Features",
                "section_hash": "section2",
                "page_id": 1,
                "position": {"top": 300, "left": 100}
            },
            {
                "_key": "obj5",
                "_type": "text",
                "text": "ArangoDB provides AQL for querying graph data efficiently. According to the ArangoDB documentation, AQL queries can traverse graphs quickly.",
                "section_hash": "section2",
                "page_id": 1,
                "position": {"top": 350, "left": 100}
            },
            {
                "_key": "obj6",
                "_type": "text",
                "text": "Recent studies have shown that proper indexing causes significant performance improvements in ArangoDB queries.",
                "section_hash": "section2",
                "page_id": 1,
                "position": {"top": 400, "left": 100}
            },
            {
                "_key": "obj7",
                "_type": "table",
                "text": "Table 1: ArangoDB Performance Comparison\nOperation | Time (ms) | Memory (MB)\nQuery | 50 | 100\nIndex | 10 | 150",
                "section_hash": "section2",
                "page_id": 1,
                "position": {"top": 450, "left": 100}
            },
            {
                "_key": "obj8",
                "_type": "text",
                "text": "As shown in Table 1, indexing improves query performance significantly.",
                "section_hash": "section2",
                "page_id": 1,
                "position": {"top": 500, "left": 100}
            }
        ]
    }
    
    return document


async def import_marker_objects(db, marker_data):
    """Import Marker objects into the ArangoDB test database."""
    # Import objects
    objects = marker_data.get("objects", [])
    
    for obj in objects:
        # Add document_id field
        obj["document_id"] = "test_doc"
        
        # Add the object to the database
        db.collection("document_objects").insert(obj)
    
    logger.info(f"Imported {len(objects)} objects into ArangoDB")
    return objects


async def add_embeddings(db, objects):
    """Add embeddings to text and table objects."""
    text_objects = [obj for obj in objects if obj.get("_type") in ["text", "table", "section"] and obj.get("text")]
    
    # Add embeddings
    for obj in text_objects:
        text = obj.get("text", "")
        
        if text.strip():
            # Get embedding - note: get_embedding is not an async function
            try:
                embedding = get_embedding(text)
                
                # Update object with embedding
                db.collection("document_objects").update({
                    "_key": obj["_key"],
                    "embedding": embedding
                })
                logger.debug(f"Added embedding for object {obj['_key']}")
            except Exception as e:
                logger.error(f"Error creating embedding for {obj['_key']}: {e}")
    
    logger.info(f"Added embeddings to {len(text_objects)} objects")


async def test_text_relationship_extraction(relationship_extractor, objects):
    """Test relationship extraction from text content."""
    logger.info("\n=== Testing Text-Based Relationship Extraction ===")
    
    # Track extraction results
    successful_extractions = 0
    total_attempts = 0
    relationship_types_found = set()
    
    # Process each text object
    text_objects = [obj for obj in objects if obj.get("_type") == "text" and obj.get("text")]
    
    for obj in text_objects:
        total_attempts += 1
        text = obj.get("text", "")
        
        # Extract relationships from text
        extracted_relationships = relationship_extractor.extract_relationships_from_text(
            text=text,
            source_doc=obj,
            relationship_types=[r.value for r in RelationshipType]
        )
        
        if extracted_relationships:
            successful_extractions += 1
            for rel in extracted_relationships:
                relationship_types_found.add(rel["type"])
                logger.info(f"  Type: {rel['type']}, Source: {rel.get('source')}, Target: {rel.get('target')}")
                logger.info(f"  Confidence: {rel.get('confidence'):.2f}, Rationale: {rel.get('rationale')[:50]}...")
    
    # Log summary
    logger.info(f"\nSummary:")
    logger.info(f"  - Processed {total_attempts} text objects")
    logger.info(f"  - Successfully extracted relationships from {successful_extractions} objects")
    logger.info(f"  - Found relationship types: {', '.join(relationship_types_found)}")
    
    # Validate success criteria
    if successful_extractions == 0:
        logger.error("❌ VALIDATION FAILED: No relationships extracted from any text objects")
        return False
    
    if len(relationship_types_found) < 2:
        logger.warning("⚠️ Found fewer than 2 relationship types")
    
    extraction_ratio = successful_extractions / total_attempts if total_attempts > 0 else 0
    logger.info(f"Extraction ratio: {extraction_ratio:.2f}")
    
    return extraction_ratio > 0


async def test_similarity_extraction(relationship_extractor, db, objects):
    """Test similarity-based relationship extraction."""
    logger.info("\n=== Testing Similarity-Based Relationship Extraction ===")
    
    # Filter objects with embeddings
    embedded_objects = []
    for obj in objects:
        # Check if the object has an embedding
        obj_with_embedding = db.collection("document_objects").get(obj["_key"])
        if obj_with_embedding and "embedding" in obj_with_embedding:
            embedded_objects.append(obj_with_embedding)
    
    if not embedded_objects:
        logger.error("❌ No objects with embeddings found")
        return False
    
    logger.info(f"Found {len(embedded_objects)} objects with embeddings")
    
    # Test similarity relationships
    similar_relationships = []
    for obj in embedded_objects[:3]:  # Test with first 3 objects
        relationships = relationship_extractor.infer_relationships_by_similarity(
            doc=obj,
            collection_name="document_objects",
            relationship_type="SIMILAR",
            min_similarity=0.7,  # Lower threshold for testing
            max_relationships=3,
            embedding_field="embedding"
        )
        
        similar_relationships.extend(relationships)
    
    # Log results
    if not similar_relationships:
        logger.error("❌ VALIDATION FAILED: No similarity relationships found")
        return False
    
    logger.info(f"Found {len(similar_relationships)} similarity relationships")
    for rel in similar_relationships:
        logger.info(f"  Similarity: {rel.get('confidence'):.2f}")
        logger.info(f"  Source: {rel.get('source')}, Target: {rel.get('target')}")
    
    return True


async def test_entity_extraction(objects):
    """Test entity extraction from text."""
    logger.info("\n=== Testing Entity Extraction ===")
    
    # Initialize entity extractor
    entity_extractor = EntityExtractor()
    
    # Collect all text for entity extraction
    all_text = ""
    for obj in objects:
        if obj.get("_type") in ["text", "section"] and obj.get("text"):
            all_text += obj.get("text", "") + " "
    
    # Extract entities
    entities = entity_extractor.extract_entities(all_text)
    
    # Log results
    if not entities:
        logger.error("❌ VALIDATION FAILED: No entities extracted")
        return False
    
    logger.info(f"Extracted {len(entities)} entities:")
    for entity in entities:
        logger.info(f"  Entity: {entity['name']}, Type: {entity['type']}, Confidence: {entity['confidence']}")
    
    # Validate entity types
    entity_types = {entity["type"] for entity in entities}
    logger.info(f"Found entity types: {', '.join(entity_types)}")
    
    return len(entities) > 0


async def test_relationship_creation(relationship_extractor, db):
    """Test relationship creation in ArangoDB."""
    logger.info("\n=== Testing Relationship Creation ===")
    
    # Get two document objects
    objects = list(db.collection("document_objects").all())
    if len(objects) < 2:
        logger.error("❌ Not enough objects for relationship creation test")
        return False
    
    source_obj = objects[0]
    target_obj = objects[1]
    
    # Create relationship
    try:
        relationship = relationship_extractor.create_document_relationship(
            source_id=source_obj["_id"],
            target_id=target_obj["_id"],
            relationship_type="SHARED_TOPIC",
            rationale="These document objects share a common topic and are semantically related according to content analysis.",
            confidence=0.85,
            metadata={
                "test_metadata": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Created relationship: {relationship['_id']}")
        logger.info(f"  Type: {relationship['type']}")
        logger.info(f"  Confidence: {relationship['confidence']}")
        
        # Verify the relationship exists in the database
        rel_in_db = db.collection("content_relationships").get(relationship["_key"])
        if not rel_in_db:
            logger.error("❌ VALIDATION FAILED: Relationship not found in database after creation")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ VALIDATION FAILED: Error creating relationship: {e}")
        return False


async def main():
    """Run the relationship extraction tests."""
    parser = argparse.ArgumentParser(description="Test relationship extraction from Marker output")
    parser.add_argument("--marker-file", help="Path to Marker output JSON file")
    
    args = parser.parse_args()
    
    # Configure logger
    logger.remove()  # Remove default logger
    logger.add(sys.stderr, level="INFO")  # Add standard error logger
    
    # Load Marker output
    marker_data = None
    if args.marker_file:
        marker_data = load_marker_output(args.marker_file)
    else:
        marker_data = create_synthetic_marker_output()
    
    # Setup test database
    try:
        logger.info("Setting up test database...")
        db = await setup_test_db()
        logger.info("Database setup complete")
        
        # Import objects
        objects = await import_marker_objects(db, marker_data)
        
        # Add embeddings
        await add_embeddings(db, objects)
        
        # Initialize relationship extractor
        relationship_extractor = RelationshipExtractor(
            db=db,
            edge_collection_name="content_relationships",
            entity_collection_name="document_objects"
        )
        
        # Track test results
        test_results = {}
        
        # Run tests
        test_results["text_extraction"] = await test_text_relationship_extraction(relationship_extractor, objects)
        test_results["similarity_extraction"] = await test_similarity_extraction(relationship_extractor, db, objects)
        test_results["entity_extraction"] = await test_entity_extraction(objects)
        test_results["relationship_creation"] = await test_relationship_creation(relationship_extractor, db)
        
        # Print summary
        logger.info("\n=== TEST SUMMARY ===")
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        if all_passed:
            logger.info("\n✅ ALL TESTS PASSED: Relationship extraction functionality works correctly with Marker output")
            return 0
        else:
            logger.error("\n❌ SOME TESTS FAILED: See log for details")
            return 1
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))