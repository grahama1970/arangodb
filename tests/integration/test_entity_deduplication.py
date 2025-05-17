#!/usr/bin/env python3
"""
Integration test for automatic entity deduplication in Memory Agent.

This test verifies that the entity resolution is working correctly
during conversation storage and entities are being deduplicated
based on fuzzy matching and semantic similarity.
"""

import pytest
from datetime import datetime, timezone
from arangodb.core.arango_setup import connect_arango, ensure_database
from arangodb.core.memory.memory_agent import MemoryAgent


def test_entity_deduplication():
    """Test automatic entity deduplication during conversation storage."""
    # Connect to database
    client = connect_arango()
    db = ensure_database(client)
    
    # Create memory agent
    agent = MemoryAgent(db=db)
    
    # Test Case 1: Store conversation with entity "Python"
    result1 = agent.store_conversation(
        user_message="I'm learning Python programming",
        agent_response="Python is a great language for beginners"
    )
    assert result1['conversation_id'] is not None
    
    # Test Case 2: Store conversation with similar entity "python language"
    result2 = agent.store_conversation(
        user_message="Tell me about python language features",
        agent_response="Python language has dynamic typing and garbage collection"
    )
    assert result2['conversation_id'] is not None
    
    # Test Case 3: Store conversation with exact match "Python"
    result3 = agent.store_conversation(
        user_message="What frameworks exist for Python?",
        agent_response="Popular Python frameworks include Django and Flask"
    )
    assert result3['conversation_id'] is not None
    
    # Test Case 4: Check fuzzy matching with different case
    result4 = agent.store_conversation(
        user_message="PYTHON is case-sensitive in variables",
        agent_response="Yes, PYTHON distinguishes between uppercase and lowercase"
    )
    assert result4['conversation_id'] is not None
    
    # Check how many Python entities exist
    aql = """
    FOR entity IN agent_entities
    FILTER LOWER(entity.name) == "python" OR 
           LOWER(entity.name) == "python language" OR
           entity.name == "PYTHON"
    RETURN {
        name: entity.name,
        type: entity.type,
        _key: entity._key
    }
    """
    
    cursor = db.aql.execute(aql)
    entities = list(cursor)
    
    # Should have at most 2 entities if dedup works correctly
    # (Python and Python language may be treated as different enough)
    assert len(entities) <= 2, f"Expected at most 2 entities, found {len(entities)}: {entities}"
    
    # Check that case variations are being matched
    python_names = [e['name'] for e in entities]
    assert not ("PYTHON" in python_names and "Python" in python_names), \
        "PYTHON and Python should be deduplicated to the same entity"


def test_entity_name_normalization():
    """Test that entity names are normalized correctly."""
    # Connect to database
    client = connect_arango()
    db = ensure_database(client)
    
    # Create memory agent
    agent = MemoryAgent(db=db)
    
    # Test with variations of the same entity
    variations = [
        ("John Smith", "person"),
        ("JOHN SMITH", "PERSON"),
        ("john smith", "Person"),
        ("Smith, John", "person")  # Different format
    ]
    
    for name, entity_type in variations:
        agent.store_conversation(
            user_message=f"Tell me about {name}",
            agent_response=f"{name} is a {entity_type}"
        )
    
    # Check how many John Smith entities exist
    aql = """
    FOR entity IN agent_entities
    FILTER LOWER(entity.name) =~ "john" AND LOWER(entity.name) =~ "smith"
    RETURN {
        name: entity.name,
        type: entity.type,
        _key: entity._key
    }
    """
    
    cursor = db.aql.execute(aql)
    entities = list(cursor)
    
    # Should have at most 2 entities (allowing for format differences)
    assert len(entities) <= 2, f"Expected at most 2 entities, found {len(entities)}: {entities}"


if __name__ == "__main__":
    test_entity_deduplication()
    test_entity_name_normalization()
    print("✅ All entity deduplication tests passed!")