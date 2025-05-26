"""
Unit tests for Community Detection module

Tests the core functionality of the CommunityDetector class including:
- Louvain algorithm implementation
- Modularity calculation
- Small community merging
- Database integration

NO MOCKING - Uses real test database connections per CLAUDE.md guidelines.
"""

import pytest
import uuid
from datetime import datetime
from arango.client import ArangoClient

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from arangodb.core.graph.community_detection import CommunityDetector


class TestCommunityDetector:
    """Test suite for CommunityDetector class"""
    
    @pytest.fixture
    def db(self):
        """Get real test database connection."""
        client = ArangoClient(hosts='http://localhost:8529')
        db = client.db('pizza_test', username='root', password='openSesame')
        
        # Ensure test collections exist
        collections = ['agent_entities', 'agent_relationships', 'agent_communities']
        for collection in collections:
            if not db.has_collection(collection):
                db.create_collection(collection)
        
        # Clear collections for test
        for collection in collections:
            db.collection(collection).truncate()
        
        yield db
        
        # Cleanup after test
        for collection in collections:
            db.collection(collection).truncate()
    
    @pytest.fixture
    def detector(self, db):
        """Create a CommunityDetector instance with real database"""
        return CommunityDetector(db)
    
    def test_init(self, db):
        """Test CommunityDetector initialization"""
        detector = CommunityDetector(db)
        assert detector.db == db
        assert detector.entities_collection == "agent_entities"
        assert detector.relationships_collection == "agent_relationships"
        assert detector.communities_collection == "agent_communities"
    
    def test_ensure_communities_collection(self, db):
        """Test communities collection creation"""
        # Test when collection doesn't exist
        if db.has_collection("agent_communities"):
            db.delete_collection("agent_communities")
        
        # Create detector - should create collection
        detector = CommunityDetector(db)
        assert db.has_collection("agent_communities")
        
        # Test when collection exists
        detector2 = CommunityDetector(db)
        # Should not fail, collection already exists
        assert db.has_collection("agent_communities")
    
    def test_build_adjacency_matrix(self, detector):
        """Test adjacency matrix construction"""
        # Mock entities
        entities = [
            {"_id": "agent_entities/1", "_key": "1", "name": "Entity1"},
            {"_id": "agent_entities/2", "_key": "2", "name": "Entity2"},
            {"_id": "agent_entities/3", "_key": "3", "name": "Entity3"}
        ]
        
        # Mock relationships
        relationships = [
            {"_from": "agent_entities/1", "_to": "agent_entities/2", "confidence": 0.9},
            {"_from": "agent_entities/2", "_to": "agent_entities/3", "confidence": 0.7},
            {"_from": "agent_entities/1", "_to": "agent_entities/3", "confidence": 0.5}
        ]
        
        adjacency = detector._build_adjacency_matrix(entities, relationships)
        
        # Verify adjacency matrix
        assert adjacency["1"]["2"] == 0.9
        assert adjacency["2"]["1"] == 0.9  # Undirected
        assert adjacency["2"]["3"] == 0.7
        assert adjacency["3"]["2"] == 0.7  # Undirected
        assert adjacency["1"]["3"] == 0.5
        assert adjacency["3"]["1"] == 0.5  # Undirected
    
    def test_calculate_modularity(self, detector):
        """Test modularity calculation"""
        # Simple test case with 2 communities
        communities = {
            "1": "A", "2": "A",  # Community A
            "3": "B", "4": "B"   # Community B
        }
        
        # Adjacency matrix with higher internal connectivity
        adjacency = {
            "1": {"2": 1.0, "3": 0.1, "4": 0.1},
            "2": {"1": 1.0, "3": 0.1, "4": 0.1},
            "3": {"1": 0.1, "2": 0.1, "4": 1.0},
            "4": {"1": 0.1, "2": 0.1, "3": 1.0}
        }
        
        modularity = detector._calculate_modularity(communities, adjacency)
        
        # Modularity should be positive for good community structure
        assert modularity > 0
        assert modularity <= 1
    
    def test_merge_small_communities(self, detector):
        """Test small community merging"""
        # Initial communities with one small community
        communities = {
            "1": "A", "2": "A", "3": "A",  # Community A (size 3)
            "4": "B",                      # Community B (size 1, too small)
            "5": "C", "6": "C"             # Community C (size 2)
        }
        
        # Adjacency matrix - entity 4 is most connected to community A
        adjacency = {
            "1": {"2": 1.0, "3": 1.0, "4": 0.8, "5": 0.1, "6": 0.1},
            "2": {"1": 1.0, "3": 1.0, "4": 0.7, "5": 0.1, "6": 0.1},
            "3": {"1": 1.0, "2": 1.0, "4": 0.6, "5": 0.1, "6": 0.1},
            "4": {"1": 0.8, "2": 0.7, "3": 0.6, "5": 0.2, "6": 0.2},
            "5": {"1": 0.1, "2": 0.1, "3": 0.1, "4": 0.2, "6": 1.0},
            "6": {"1": 0.1, "2": 0.1, "3": 0.1, "4": 0.2, "5": 1.0}
        }
        
        merged_communities = detector._merge_small_communities(communities, adjacency, min_size=2)
        
        # Entity 4 should be merged into community A
        assert merged_communities["4"] == "A"
        # Other assignments should remain the same
        assert merged_communities["1"] == "A"
        assert merged_communities["5"] == "C"
    
    def test_detect_communities(self, detector, db):
        """Test full community detection process with real database"""
        # Insert test entities
        entities_collection = db.collection("agent_entities")
        entities = [
            {"_key": "1", "name": "Python", "type": "language"},
            {"_key": "2", "name": "Django", "type": "framework"},
            {"_key": "3", "name": "Flask", "type": "framework"}
        ]
        for entity in entities:
            entities_collection.insert(entity)
        
        # Insert test relationships
        relationships_collection = db.collection("agent_relationships")
        relationships = [
            {"_from": "agent_entities/1", "_to": "agent_entities/2", "confidence": 0.9, "type": "uses"},
            {"_from": "agent_entities/1", "_to": "agent_entities/3", "confidence": 0.9, "type": "uses"}
        ]
        for rel in relationships:
            relationships_collection.insert(rel)
        
        # Run community detection
        communities = detector.detect_communities(min_size=1)
        
        # Verify results
        assert len(communities) == 3  # 3 entities
        assert len(set(communities.values())) >= 1  # At least 1 community
        
        # Verify database state
        communities_collection = db.collection("agent_communities")
        community_count = communities_collection.count()
        assert community_count > 0  # Communities were stored
        
        # Verify entities were updated with community assignments
        for entity_key in ["1", "2", "3"]:
            entity = entities_collection.get(entity_key)
            assert "community_id" in entity  # Entity has community assignment
    
    def test_get_community_for_entity(self, detector, db):
        """Test fetching community for a specific entity with real database"""
        # Insert test entity
        entities_collection = db.collection("agent_entities")
        entity = {"_key": "test_entity", "name": "Test Entity", "community_id": "community_123"}
        entities_collection.insert(entity)
        
        # Insert test community
        communities_collection = db.collection("agent_communities")
        community = {"_key": "community_123", "member_count": 5, "modularity": 0.75}
        communities_collection.insert(community)
        
        # Fetch community for entity
        result = detector.get_community_for_entity("test_entity")
        
        assert result is not None
        assert result["_key"] == "community_123"
        assert result["member_count"] == 5
    
    def test_get_all_communities(self, detector, db):
        """Test fetching all communities with real database"""
        # Insert test communities
        communities_collection = db.collection("agent_communities")
        communities = [
            {"_key": "community_1", "member_count": 3, "modularity": 0.6},
            {"_key": "community_2", "member_count": 5, "modularity": 0.8}
        ]
        for community in communities:
            communities_collection.insert(community)
        
        # Fetch all communities
        result = detector.get_all_communities()
        
        assert len(result) == 2
        result_keys = {c["_key"] for c in result}
        assert "community_1" in result_keys
        assert "community_2" in result_keys
    
    def test_empty_graph(self, detector, db):
        """Test community detection with empty graph using real database"""
        # Ensure collections are empty (already truncated in fixture)
        
        # Run community detection on empty graph
        communities = detector.detect_communities()
        
        assert communities == {}
        
        # Verify no communities were created
        communities_collection = db.collection("agent_communities")
        assert communities_collection.count() == 0
    
    def test_single_entity(self, detector, db):
        """Test community detection with single entity using real database"""
        # Insert single entity
        entities_collection = db.collection("agent_entities")
        entity = {"_key": "1", "name": "Entity1", "type": "test"}
        entities_collection.insert(entity)
        
        # Run community detection
        communities = detector.detect_communities(min_size=1)
        
        assert len(communities) == 1
        assert "1" in communities
        
        # Verify community was created
        communities_collection = db.collection("agent_communities")
        assert communities_collection.count() == 1