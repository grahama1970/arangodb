#!/usr/bin/env python3
"""
Simplified unit tests for Community Detection

This script validates the core functionality of the CommunityDetector class.
"""

import sys
from loguru import logger
from unittest.mock import Mock

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Import community detection module
from src.arangodb.core.graph.community_detection import CommunityDetector


def test_init():
    """Test CommunityDetector initialization"""
    print("\n1. Testing initialization...")
    
    # Create mock database
    mock_db = Mock()
    mock_db.has_collection = Mock(return_value=True)
    
    # Create detector
    detector = CommunityDetector(mock_db)
    
    # Verify properties
    assert detector.db == mock_db
    assert detector.entities_collection == "agent_entities"
    assert detector.relationships_collection == "agent_relationships"
    assert detector.communities_collection == "agent_communities"
    print("✓ Initialization test passed")


def test_adjacency_matrix():
    """Test adjacency matrix construction"""
    print("\n2. Testing adjacency matrix...")
    
    # Create detector with mock database
    mock_db = Mock()
    detector = CommunityDetector(mock_db)
    
    # Test data
    entities = [
        {"_id": "agent_entities/1", "_key": "1"},
        {"_id": "agent_entities/2", "_key": "2"},
        {"_id": "agent_entities/3", "_key": "3"}
    ]
    
    relationships = [
        {"_from": "agent_entities/1", "_to": "agent_entities/2", "confidence": 0.9},
        {"_from": "agent_entities/2", "_to": "agent_entities/3", "confidence": 0.7}
    ]
    
    # Build adjacency matrix
    adjacency = detector._build_adjacency_matrix(entities, relationships)
    
    # Verify results
    assert adjacency["1"]["2"] == 0.9
    assert adjacency["2"]["1"] == 0.9  # Undirected
    assert adjacency["2"]["3"] == 0.7
    assert adjacency["3"]["2"] == 0.7  # Undirected
    print("✓ Adjacency matrix test passed")


def test_modularity():
    """Test modularity calculation"""
    print("\n3. Testing modularity calculation...")
    
    # Create detector
    mock_db = Mock()
    detector = CommunityDetector(mock_db)
    
    # Test communities
    communities = {
        "1": "A", "2": "A",  # Community A
        "3": "B", "4": "B"   # Community B
    }
    
    # Test adjacency with good community structure
    adjacency = {
        "1": {"2": 1.0, "3": 0.1, "4": 0.1},
        "2": {"1": 1.0, "3": 0.1, "4": 0.1},
        "3": {"1": 0.1, "2": 0.1, "4": 1.0},
        "4": {"1": 0.1, "2": 0.1, "3": 1.0}
    }
    
    # Calculate modularity
    modularity = detector._calculate_modularity(communities, adjacency)
    
    # Verify result
    assert modularity > 0
    assert modularity <= 1
    print(f"✓ Modularity test passed (score: {modularity:.3f})")


def test_small_community_merging():
    """Test merging of small communities"""
    print("\n4. Testing small community merging...")
    
    # Create detector
    mock_db = Mock()
    detector = CommunityDetector(mock_db)
    
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
    """Test with empty graph"""
    print("\n5. Testing empty graph...")
    
    # Create detector with mock database
    mock_db = Mock()
    mock_db.aql = Mock()
    mock_db.aql.execute = Mock(side_effect=[
        Mock(__iter__=lambda x: iter([])),  # No entities
        Mock(__iter__=lambda x: iter([]))   # No relationships
    ])
    
    detector = CommunityDetector(mock_db)
    
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