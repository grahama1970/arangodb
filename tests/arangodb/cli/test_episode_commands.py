"""
Real Tests for Episode Commands

This module tests all episode commands using real database connections
and actual episode management operations.
NO MOCKING - All tests use real components.
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typer.testing import CliRunner
from arangodb.cli.main import app
from arangodb.cli.db_connection import get_db_connection

runner = CliRunner()

@pytest.fixture(scope="module")
def setup_episode_test_data():
    """Setup test episodes and conversations"""
    db = get_db_connection()
    
    # Ensure collections exist
    collections = ["episodes", "conversations", "message_history"]
    for collection_name in collections:
        if not db.has_collection(collection_name):
            db.create_collection(collection_name)
    
    # Clear test data
    episodes = db.collection("episodes")
    conversations = db.collection("conversations")
    
    # Clear existing test episodes
    for key in ["test_episode_1", "test_episode_2", "test_episode_3"]:
        if episodes.has(key):
            episodes.delete(key)
    
    # Create test episodes
    test_episodes = [
        {
            "_key": "test_episode_1",
            "title": "Morning Planning Session",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None,  # Still active
            "event_type": "planning",
            "conversation_count": 3,
            "is_active": True,
            "metadata": {
                "location": "office",
                "participants": ["user"]
            }
        },
        {
            "_key": "test_episode_2",
            "title": "Code Review Discussion",
            "start_time": datetime.now(timezone.utc).replace(hour=10).isoformat(),
            "end_time": datetime.now(timezone.utc).replace(hour=11).isoformat(),
            "event_type": "review",
            "conversation_count": 5,
            "is_active": False,
            "metadata": {
                "project": "arangodb-cli",
                "language": "python"
            }
        },
        {
            "_key": "test_episode_3",
            "title": "Learning Session: Graph Databases",
            "start_time": datetime.now(timezone.utc).replace(hour=14).isoformat(),
            "end_time": None,
            "event_type": "learning",
            "conversation_count": 2,
            "is_active": True,
            "metadata": {
                "topic": "graphs",
                "difficulty": "intermediate"
            }
        }
    ]
    
    for episode in test_episodes:
        episodes.insert(episode)
    
    # Create test conversations linked to episodes
    test_conversations = [
        {
            "_key": "conv_ep1_1",
            "episode_id": "test_episode_1",
            "user_message": "What tasks do I have today?",
            "agent_response": "You have 3 meetings and 2 code reviews scheduled.",
            "timestamp": time.time(),
            "conversation_id": "morning_conv"
        },
        {
            "_key": "conv_ep2_1",
            "episode_id": "test_episode_2", 
            "user_message": "Show me the pull request changes",
            "agent_response": "The PR includes updates to the CLI consistency.",
            "timestamp": time.time() - 3600,
            "conversation_id": "review_conv"
        }
    ]
    
    for conv in test_conversations:
        if conversations.has(conv["_key"]):
            conversations.delete(conv["_key"])
        conversations.insert(conv)
    
    return db

class TestEpisodeCommands:
    """Test all episode commands with real data"""
    
    def test_episode_create_basic(self, setup_episode_test_data):
        """Test creating a new episode"""
        result = runner.invoke(app, [
            "episode", "create",
            "--title", "Test Debugging Session",
            "--event-type", "debugging",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["title"] == "Test Debugging Session"
        assert data["data"]["event_type"] == "debugging"
        assert data["data"]["is_active"] is True
        assert "_key" in data["data"]
    
    def test_episode_create_with_metadata(self, setup_episode_test_data):
        """Test creating episode with metadata"""
        result = runner.invoke(app, [
            "episode", "create",
            "--title", "Feature Development",
            "--event-type", "development",
            "--metadata", '{"feature": "authentication", "priority": "high"}',
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["metadata"]["feature"] == "authentication"
        assert data["data"]["metadata"]["priority"] == "high"
    
    def test_episode_list_all(self, setup_episode_test_data):
        """Test listing all episodes"""
        result = runner.invoke(app, [
            "episode", "list",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["episodes"]) >= 3
        
        # Verify episode structure
        episodes = data["data"]["episodes"]
        for episode in episodes:
            assert "title" in episode
            assert "event_type" in episode
            assert "is_active" in episode
    
    def test_episode_list_active_only(self, setup_episode_test_data):
        """Test listing only active episodes"""
        result = runner.invoke(app, [
            "episode", "list",
            "--active",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # All results should be active
        episodes = data["data"]["episodes"]
        assert all(ep["is_active"] is True for ep in episodes)
        assert len(episodes) >= 2  # We created 2 active episodes
    
    def test_episode_list_by_type(self, setup_episode_test_data):
        """Test listing episodes by event type"""
        result = runner.invoke(app, [
            "episode", "list",
            "--event-type", "planning",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        
        # All results should have correct event type
        episodes = data["data"]["episodes"]
        assert all(ep["event_type"] == "planning" for ep in episodes)
    
    def test_episode_get_by_id(self, setup_episode_test_data):
        """Test getting specific episode by ID"""
        result = runner.invoke(app, [
            "episode", "get",
            "--id", "test_episode_1",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["_key"] == "test_episode_1"
        assert data["data"]["title"] == "Morning Planning Session"
    
    def test_episode_get_conversations(self, setup_episode_test_data):
        """Test getting conversations for an episode"""
        result = runner.invoke(app, [
            "episode", "conversations",
            "--id", "test_episode_1",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["conversations"]) >= 1
        
        # Verify conversations belong to the episode
        conversations = data["data"]["conversations"]
        assert all(conv["episode_id"] == "test_episode_1" for conv in conversations)
    
    def test_episode_update_title(self, setup_episode_test_data):
        """Test updating episode title"""
        result = runner.invoke(app, [
            "episode", "update",
            "--id", "test_episode_2",
            "--title", "Updated Code Review",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["title"] == "Updated Code Review"
        # Other fields should remain unchanged
        assert data["data"]["event_type"] == "review"
    
    def test_episode_close(self, setup_episode_test_data):
        """Test closing an active episode"""
        # First create a new active episode
        create_result = runner.invoke(app, [
            "episode", "create",
            "--title", "Temporary Session",
            "--output", "json"
        ])
        
        create_data = json.loads(create_result.stdout)
        episode_id = create_data["data"]["_key"]
        
        # Now close it
        result = runner.invoke(app, [
            "episode", "close",
            "--id", episode_id,
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["is_active"] is False
        assert data["data"]["end_time"] is not None
    
    def test_episode_close_already_closed(self, setup_episode_test_data):
        """Test closing an already closed episode"""
        result = runner.invoke(app, [
            "episode", "close",
            "--id", "test_episode_2",  # Already closed
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is False
        assert "already closed" in data["error"].lower()
    
    def test_episode_current(self, setup_episode_test_data):
        """Test getting current active episode"""
        result = runner.invoke(app, [
            "episode", "current",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        
        if data["success"]:
            # Should return most recent active episode
            assert data["data"]["is_active"] is True
        else:
            # No active episodes
            assert "no active episode" in data["error"].lower()
    
    def test_episode_table_output(self, setup_episode_test_data):
        """Test episode commands with table output"""
        result = runner.invoke(app, [
            "episode", "list",
            "--output", "table"
        ])
        
        assert result.exit_code == 0
        # Table should have headers
        assert "Title" in result.stdout
        assert "Event Type" in result.stdout
        assert "Active" in result.stdout
    
    def test_episode_invalid_id(self, setup_episode_test_data):
        """Test getting episode with invalid ID"""
        result = runner.invoke(app, [
            "episode", "get",
            "--id", "non_existent_episode",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is False
        assert "not found" in data["error"].lower()
    
    def test_episode_list_with_limit(self, setup_episode_test_data):
        """Test listing episodes with limit"""
        result = runner.invoke(app, [
            "episode", "list",
            "--limit", "2",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["episodes"]) <= 2
    
    def test_episode_create_invalid_metadata(self, setup_episode_test_data):
        """Test creating episode with invalid metadata JSON"""
        result = runner.invoke(app, [
            "episode", "create", 
            "--title", "Test Episode",
            "--metadata", "{invalid json}",
            "--output", "json"
        ])
        
        # Should handle error gracefully
        assert result.exit_code != 0 or (result.exit_code == 0 and "error" in result.stdout)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-header"])