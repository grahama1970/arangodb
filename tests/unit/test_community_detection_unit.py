#!/usr/bin/env python3
"""
Unit tests for Community Detection using real database

This script validates the core functionality of the CommunityDetector class.
NO MOCKING - Uses real test database connections per CLAUDE.md guidelines.
"""

import sys
import os
from loguru import logger
from arango import ArangoClient

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Import community detection module
from arangodb.core.graph.community_detection import CommunityDetector

# Set test database
os.environ['ARANGO_DB_NAME'] = 'pizza_test'


def get_test_db():
    """Get real test database connection"""
    client = ArangoClient(hosts='http://localhost:8529')
    db = client.db('pizza_test', username='root', password='openSesame')
    
    # Ensure test collections exist
    for coll in ['agent_entities', 'agent_relationships', 'agent_communities']:
        if not db.has_collection(coll):
            if coll == 'agent_relationships':
                db.create_collection(coll, edge=True)
            else:
                db.create_collection(coll)
    
    return db


def test_init():
    """Test CommunityDetector initialization with real database"""
    print("\n1. Testing initialization...")
    
    # Get real test database
    db = get_test_db()
    
    # Create detector with real database
    detector = CommunityDetector(db)
    
    # Verify properties
    assert detector.db == db
    assert detector.entities_collection == "agent_entities"
    assert detector.relationships_collection == "agent_relationships"
    assert detector.communities_collection == "agent_communities"
    print("✓ Initialization test passed")


def test_adjacency_matrix():
    """Test adjacency matrix construction with real data"""
    print("\n2. Testing adjacency matrix...")
    
    # Get real test database
    db = get_test_db()
    detector = CommunityDetector(db)
    
    # Clear test collections
    db.collection('agent_entities').truncate()
    db.collection('agent_relationships').truncate()
    
    # Insert real test entities
    entities_coll = db.collection('agent_entities')
    entities_coll.insert({'_key': '1', 'name': 'Entity1'})
    entities_coll.insert({'_key': '2', 'name': 'Entity2'})
    entities_coll.insert({'_key': '3', 'name': 'Entity3'})
    
    # Insert real test relationships
    relationships_coll = db.collection('agent_relationships')
    relationships_coll.insert({
        '_from': 'agent_entities/1',
        '_to': 'agent_entities/2',
        'confidence': 0.9
    })
    relationships_coll.insert({
        '_from': 'agent_entities/2',
        '_to': 'agent_entities/3',
        'confidence': 0.7
    })
    
    # Get real data from database
    entities = list(entities_coll.all())
    relationships = list(relationships_coll.all())
    
    # Build adjacency matrix
    adjacency = detector._build_adjacency_matrix(entities, relationships)
    
    # Verify results
    assert adjacency["1"]["2"] == 0.9
    assert adjacency["2"]["1"] == 0.9  # Undirected
    assert adjacency["2"]["3"] == 0.7
    assert adjacency["3"]["2"] == 0.7  # Undirected
    print("✓ Adjacency matrix test passed")


def test_modularity():
    """Test modularity calculation with real data"""
    print("\n3. Testing modularity calculation...")
    
    # Get real test database
    db = get_test_db()
    detector = CommunityDetector(db)
    
    # Clear and set up test data
    db.collection('agent_entities').truncate()
    db.collection('agent_relationships').truncate()
    
    # Insert entities for two communities
    entities_coll = db.collection('agent_entities')
    entities_coll.insert({'_key': '1', 'name': 'Entity1'})
    entities_coll.insert({'_key': '2', 'name': 'Entity2'})
    entities_coll.insert({'_key': '3', 'name': 'Entity3'})
    entities_coll.insert({'_key': '4', 'name': 'Entity4'})
    
    # Insert relationships with good community structure
    relationships_coll = db.collection('agent_relationships')
    # Strong connections within communities
    relationships_coll.insert({'_from': 'agent_entities/1', '_to': 'agent_entities/2', 'confidence': 1.0})
    relationships_coll.insert({'_from': 'agent_entities/3', '_to': 'agent_entities/4', 'confidence': 1.0})
    # Weak connections between communities
    relationships_coll.insert({'_from': 'agent_entities/1', '_to': 'agent_entities/3', 'confidence': 0.1})
    relationships_coll.insert({'_from': 'agent_entities/1', '_to': 'agent_entities/4', 'confidence': 0.1})
    relationships_coll.insert({'_from': 'agent_entities/2', '_to': 'agent_entities/3', 'confidence': 0.1})
    relationships_coll.insert({'_from': 'agent_entities/2', '_to': 'agent_entities/4', 'confidence': 0.1})
    
    # Test communities
    communities = {
        "1": "A", "2": "A",  # Community A
        "3": "B", "4": "B"   # Community B
    }
    
    # Build adjacency matrix from real data
    entities = list(entities_coll.all())
    relationships = list(relationships_coll.all())
    adjacency = detector._build_adjacency_matrix(entities, relationships)
    
    # Calculate modularity
    modularity = detector._calculate_modularity(communities, adjacency)
    
    # Verify result
    assert modularity > 0
    assert modularity <= 1
    print(f"✓ Modularity test passed (score: {modularity:.3f})")


def test_small_community_merging():
    """Test merging of small communities with real data"""
    print("\n4. Testing small community merging...")
    
    # Get real test database
    db = get_test_db()
    detector = CommunityDetector(db)
    
    # Initial communities with one small community
    communities = {
        "1": "A", "2": "A", "3": "A",  # Community A (size 3)
        "4": "B",                      # Community B (size 1, too small)
        "5": "C", "6": "C"             # Community C (size 2)
    }
    
    # Adjacency - entity 4 is most connected to community A
    adjacency = {
        "1": {"2": 1.0, "3": 1.0, "4": 0.8, "5": 0.1, "6": 0.1},
        "2": {"1": 1.0, "3": 1.0, "4": 0.7, "5": 0.1, "6": 0.1},
        "3": {"1": 1.0, "2": 1.0, "4": 0.6, "5": 0.1, "6": 0.1},
        "4": {"1": 0.8, "2": 0.7, "3": 0.6, "5": 0.2, "6": 0.2},
        "5": {"1": 0.1, "2": 0.1, "3": 0.1, "4": 0.2, "6": 1.0},
        "6": {"1": 0.1, "2": 0.1, "3": 0.1, "4": 0.2, "5": 1.0}
    }
    
    # Merge small communities
    merged = detector._merge_small_communities(communities, adjacency, min_size=2)
    
    # Verify entity 4 was merged into community A
    assert merged["4"] == "A"
    assert merged["1"] == "A"
    assert merged["5"] == "C"
    print("✓ Small community merging test passed")


def test_empty_graph():
    """Test with empty graph using real database"""
    print("\n5. Testing empty graph...")
    
    # Get real test database
    db = get_test_db()
    
    # Clear all test collections
    db.collection('agent_entities').truncate()
    db.collection('agent_relationships').truncate()
    db.collection('agent_communities').truncate()
    
    detector = CommunityDetector(db)
    
    # Detect communities in empty graph
    communities = detector.detect_communities()
    
    # Should return empty dict
    assert communities == {}
    print("✓ Empty graph test passed")


def run_all_tests():
    """Run all unit tests"""
    print("=== Community Detection Unit Tests ===")
    
    try:
        test_init()
        test_adjacency_matrix()
        test_modularity()
        test_small_community_merging()
        test_empty_graph()
        
        print("\n✓ All unit tests passed!")
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)