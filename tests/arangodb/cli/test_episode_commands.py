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

def parse_json_from_output(output):
    """Parse JSON from CLI output that may have success messages"""
    lines = output.strip().split('\n')
    json_str = None
    
    # Look for JSON object or array
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('{') or line.startswith('['):
            json_str = '\n'.join(lines[i:])
            break
    
    if json_str is None:
        raise ValueError(f"No JSON found in output: {output}")
    
    return json.loads(json_str)

@pytest.fixture(scope="module")
def setup_episode_test_data():
    """Setup test episodes and conversations"""
    db = get_db_connection()
    
    # Ensure collections exist
    collections = ["agent_episodes", "conversations", "message_history", "entities"]
    for collection_name in collections:
        if not db.has_collection(collection_name):
            db.create_collection(collection_name)
    
    # Clear test data
    episodes = db.collection("agent_episodes")
    conversations = db.collection("conversations")
    
    # Clear existing test episodes
    for key in ["test_episode_1", "test_episode_2", "test_episode_3"]:
        if episodes.has(key):
            episodes.delete(key)
    
    # Create test episodes
    test_episodes = [
        {
            "_key": "test_episode_1",
            "name": "Morning Planning Session",
            "description": "Daily planning and task review",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None,  # Still active
            "entity_count": 3,
            "relationship_count": 2,
            "metadata": {
                "user_id": "test_user",
                "session_id": "session_1",
                "location": "office",
                "participants": ["user"]
            }
        },
        {
            "_key": "test_episode_2",
            "name": "Code Review Discussion",
            "description": "Review of CLI consistency improvements",
            "start_time": datetime.now(timezone.utc).replace(hour=10).isoformat(),
            "end_time": datetime.now(timezone.utc).replace(hour=11).isoformat(),
            "entity_count": 5,
            "relationship_count": 4,
            "metadata": {
                "user_id": "test_user",
                "session_id": "session_2",
                "project": "arangodb-cli",
                "language": "python"
            }
        },
        {
            "_key": "test_episode_3",
            "name": "Learning Session: Graph Databases",
            "description": "Introduction to graph database concepts",
            "start_time": datetime.now(timezone.utc).replace(hour=14).isoformat(),
            "end_time": None,
            "entity_count": 2,
            "relationship_count": 1,
            "metadata": {
                "user_id": "test_user",
                "session_id": "session_3",
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
    
    # Create test entities
    entities = db.collection("entities")
    test_entities = [
        {
            "_key": "test_entity_1",
            "name": "Python",
            "type": "technology",
            "description": "Programming language"
        },
        {
            "_key": "test_entity_2", 
            "name": "ArangoDB",
            "type": "technology",
            "description": "Graph database system"
        },
        {
            "_key": "test_entity_3",
            "name": "Memory Bank",
            "type": "project",
            "description": "AI memory management system"
        }
    ]
    
    for entity in test_entities:
        if entities.has(entity["_key"]):
            entities.delete(entity["_key"])
        entities.insert(entity)
    
    return db

class TestEpisodeCommands:
    """Test all episode commands with real data"""
    
    def test_episode_create_basic(self, setup_episode_test_data):
        """Test creating a new episode"""
        result = runner.invoke(app, [
            "episode", "create",
            "Test Debugging Session",  # Name as positional argument
            "--description", "Debugging test failures",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = parse_json_from_output(result.stdout)
        assert data["name"] == "Test Debugging Session"
        assert data["description"] == "Debugging test failures"
        assert data["end_time"] is None  # Active episode
        assert "_key" in data
        assert "start_time" in data
    
    def test_episode_create_with_metadata(self, setup_episode_test_data):
        """Test creating episode with metadata"""
        result = runner.invoke(app, [
            "episode", "create",
            "Feature Development",  # Name as positional argument
            "--description", "Working on authentication feature",
            "--user", "dev_user",
            "--session", "dev_session",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = parse_json_from_output(result.stdout)
        assert data["name"] == "Feature Development"
        assert data["metadata"]["user_id"] == "dev_user"
        assert data["metadata"]["session_id"] == "dev_session"
    
    def test_episode_list_all(self, setup_episode_test_data):
        """Test listing all episodes"""
        result = runner.invoke(app, [
            "episode", "list",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        episodes = parse_json_from_output(result.stdout)
        assert isinstance(episodes, list)
        assert len(episodes) >= 3
        
        # Verify episode structure
        for episode in episodes:
            assert "name" in episode
            assert "_key" in episode
            assert "start_time" in episode
    
    def test_episode_list_active_only(self, setup_episode_test_data):
        """Test listing only active episodes"""
        result = runner.invoke(app, [
            "episode", "list",
            "--active",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        episodes = parse_json_from_output(result.stdout)
        assert isinstance(episodes, list)
        
        # All results should be active (no end_time)
        assert all(ep.get("end_time") is None for ep in episodes)
        assert len(episodes) >= 2  # We created 2 active episodes
    
    def test_episode_list_by_user(self, setup_episode_test_data):
        """Test listing episodes by user ID"""
        result = runner.invoke(app, [
            "episode", "list",
            "--user", "test_user",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        episodes = parse_json_from_output(result.stdout)
        assert isinstance(episodes, list)
        
        # All results should have the user_id in metadata
        for ep in episodes:
            assert ep.get("metadata", {}).get("user_id") == "test_user"
    
    def test_episode_get_by_id(self, setup_episode_test_data):
        """Test getting specific episode by ID"""
        result = runner.invoke(app, [
            "episode", "get",
            "test_episode_1",  # ID as positional argument
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = parse_json_from_output(result.stdout)
        assert data["_key"] == "test_episode_1"
        assert data["name"] == "Morning Planning Session"
        assert "entities" in data
        assert "relationships" in data
    
    def test_episode_search(self, setup_episode_test_data):
        """Test searching episodes by text query"""
        result = runner.invoke(app, [
            "episode", "search",
            "Planning",  # Search query as positional argument
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        episodes = parse_json_from_output(result.stdout)
        assert isinstance(episodes, list)
        assert len(episodes) >= 1
        
        # Verify search results contain the query
        for ep in episodes:
            assert "planning" in ep["name"].lower() or "planning" in ep.get("description", "").lower()
    
    def test_episode_end(self, setup_episode_test_data):
        """Test ending an active episode"""
        # First create a new active episode
        create_result = runner.invoke(app, [
            "episode", "create",
            "Temporary Session",
            "--output", "json"
        ])
        
        create_data = parse_json_from_output(create_result.stdout)
        episode_id = create_data["_key"]
        
        # Now end it
        result = runner.invoke(app, [
            "episode", "end",
            episode_id,  # ID as positional argument
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = parse_json_from_output(result.stdout)
        assert data["_key"] == episode_id
        assert data["end_time"] is not None
    
    def test_episode_delete(self, setup_episode_test_data):
        """Test deleting an episode"""
        # First create a new episode to delete
        create_result = runner.invoke(app, [
            "episode", "create",
            "Episode to Delete",
            "--output", "json"
        ])
        
        create_data = parse_json_from_output(create_result.stdout)
        episode_id = create_data["_key"]
        
        # Now delete it with force flag
        result = runner.invoke(app, [
            "episode", "delete",
            episode_id,  # ID as positional argument
            "--force",  # Skip confirmation
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = parse_json_from_output(result.stdout)
        assert data["status"] == "success"
        assert episode_id in data["message"]
    
    def test_episode_link_entity(self, setup_episode_test_data):
        """Test linking entity to episode"""
        # The entities collection and test entities are now guaranteed to exist
        db = setup_episode_test_data
        
        result = runner.invoke(app, [
            "episode", "link-entity",
            "test_episode_1",  # Episode ID
            "test_entity_1"    # Entity ID
        ])
        
        assert result.exit_code == 0
        assert "Linked entity" in result.stdout
    
    def test_episode_table_output(self, setup_episode_test_data):
        """Test episode commands with table output"""
        result = runner.invoke(app, [
            "episode", "list",
            "--output", "table"
        ])
        
        assert result.exit_code == 0
        # Table should have headers
        assert "Name" in result.stdout
        assert "Status" in result.stdout
        assert "Start Time" in result.stdout
    
    def test_episode_invalid_id(self, setup_episode_test_data):
        """Test getting episode with invalid ID"""
        result = runner.invoke(app, [
            "episode", "get",
            "non_existent_episode",  # ID as positional argument
            "--output", "json"
        ])
        
        # Should exit with error code
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()
    
    def test_episode_list_with_limit(self, setup_episode_test_data):
        """Test listing episodes with limit"""
        result = runner.invoke(app, [
            "episode", "list",
            "--limit", "2",
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        episodes = parse_json_from_output(result.stdout)
        assert isinstance(episodes, list)
        assert len(episodes) <= 2
    
    def test_episode_create_minimal(self, setup_episode_test_data):
        """Test creating episode with minimal parameters"""
        result = runner.invoke(app, [
            "episode", "create", 
            "Minimal Episode",  # Just the name
            "--output", "json"
        ])
        
        assert result.exit_code == 0
        data = parse_json_from_output(result.stdout)
        assert data["name"] == "Minimal Episode"
        assert "_key" in data
        assert "start_time" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-header"])