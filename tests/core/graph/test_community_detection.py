"""
Unit tests for Community Detection module

Tests the core functionality of the CommunityDetector class including:
- Louvain algorithm implementation
- Modularity calculation
- Small community merging
- Database integration
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from arangodb.core.graph.community_detection import CommunityDetector


class TestCommunityDetector:
    """Test suite for CommunityDetector class"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection"""
        mock = Mock()
        mock.has_collection = Mock(return_value=True)
        mock.collection = Mock()
        mock.aql = Mock()
        return mock
    
    @pytest.fixture
    def detector(self, mock_db):
        """Create a CommunityDetector instance with mock database"""
        return CommunityDetector(mock_db)
    
    def test_init(self, mock_db):
        """Test CommunityDetector initialization"""
        detector = CommunityDetector(mock_db)
        assert detector.db == mock_db
        assert detector.entities_collection == "agent_entities"
        assert detector.relationships_collection == "agent_relationships"
        assert detector.communities_collection == "agent_communities"
    
    def test_ensure_communities_collection(self, mock_db):
        """Test communities collection creation"""
        # Test when collection doesn't exist
        mock_db.has_collection.return_value = False
        mock_db.create_collection = Mock()
        
        detector = CommunityDetector(mock_db)
        mock_db.create_collection.assert_called_once_with("agent_communities")
        
        # Test when collection exists
        mock_db.reset_mock()
        mock_db.has_collection.return_value = True
        
        detector = CommunityDetector(mock_db)
        mock_db.create_collection.assert_not_called()
    
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
    
    def test_detect_communities(self, detector, mock_db):
        """Test full community detection process"""
        # Mock entities and relationships
        entities = [
            {"_id": "agent_entities/1", "_key": "1", "name": "Python"},
            {"_id": "agent_entities/2", "_key": "2", "name": "Django"},
            {"_id": "agent_entities/3", "_key": "3", "name": "Flask"}
        ]
        
        relationships = [
            {"_from": "agent_entities/1", "_to": "agent_entities/2", "confidence": 0.9},
            {"_from": "agent_entities/1", "_to": "agent_entities/3", "confidence": 0.9}
        ]
        
        # Mock AQL queries
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(entities))
        mock_db.aql.execute.side_effect = [
            Mock(__iter__=lambda x: iter(entities)),      # _get_all_entities
            Mock(__iter__=lambda x: iter(relationships)), # _get_all_relationships
            Mock(__iter__=lambda x: iter(entities)),      # For modularity calculation
            Mock(__iter__=lambda x: iter(relationships))  # For modularity calculation
        ]
        
        # Mock collection operations
        mock_collection = Mock()
        mock_collection.truncate = Mock()
        mock_collection.insert = Mock()
        mock_collection.update = Mock()
        mock_db.collection.return_value = mock_collection
        
        # Run community detection
        communities = detector.detect_communities(min_size=2)
        
        # Verify results
        assert len(communities) == 3  # 3 entities
        assert len(set(communities.values())) <= 3  # At most 3 communities
        
        # Verify database operations
        mock_collection.truncate.assert_called_once()  # Communities cleared
        assert mock_collection.insert.call_count > 0    # Communities stored
    
    def test_get_community_for_entity(self, detector, mock_db):
        """Test fetching community for a specific entity"""
        # Mock entity with community assignment
        entity = {"_key": "1", "community_id": "community_123"}
        community = {"_key": "community_123", "member_count": 5}
        
        mock_collection = Mock()
        mock_collection.get.side_effect = [entity, community]
        mock_db.collection.return_value = mock_collection
        
        result = detector.get_community_for_entity("1")
        
        assert result == community
        assert mock_collection.get.call_count == 2
    
    def test_get_all_communities(self, detector, mock_db):
        """Test fetching all communities"""
        communities = [
            {"_key": "community_1", "member_count": 3},
            {"_key": "community_2", "member_count": 5}
        ]
        
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(communities))
        mock_db.aql.execute.return_value = mock_cursor
        
        result = detector.get_all_communities()
        
        assert result == communities
        assert mock_db.aql.execute.called
    
    def test_empty_graph(self, detector, mock_db):
        """Test community detection with empty graph"""
        # Mock empty results
        mock_db.aql.execute.side_effect = [
            Mock(__iter__=lambda x: iter([])),  # No entities
            Mock(__iter__=lambda x: iter([]))   # No relationships
        ]
        
        communities = detector.detect_communities()
        
        assert communities == {}
    
    def test_single_entity(self, detector, mock_db):
        """Test community detection with single entity"""
        entities = [{"_id": "agent_entities/1", "_key": "1", "name": "Entity1"}]
        
        mock_db.aql.execute.side_effect = [
            Mock(__iter__=lambda x: iter(entities)),  # Single entity
            Mock(__iter__=lambda x: iter([]))         # No relationships
        ]
        
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        
        communities = detector.detect_communities(min_size=1)
        
        assert len(communities) == 1
        assert "1" in communities