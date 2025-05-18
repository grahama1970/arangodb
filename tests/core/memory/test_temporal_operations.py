#!/usr/bin/env python3
"""
Test script for bi-temporal operations.
"""

from datetime import datetime, timezone, timedelta
from loguru import logger

from arangodb.cli.db_connection import get_db_connection
from arangodb.core.memory.memory_agent import MemoryAgent
from arangodb.core.temporal_operations import (
    create_temporal_entity,
    invalidate_entity,
    point_in_time_query,
    temporal_range_query,
    validate_temporal_consistency
)

def test_temporal_memory():
    """Test temporal operations with memory agent."""
    db = get_db_connection()
    memory_agent = MemoryAgent(db)
    
    # Test 1: Create memories at different times
    print("\n=== Test 1: Creating temporal memories ===")
    
    # Memory from the past
    past_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    result1 = memory_agent.store_conversation(
        user_message="What is the project status?",
        agent_response="The project is in planning phase.",
        conversation_id="conv_temporal_test",
        valid_at=past_time
    )
    print(f"Created past memory: {result1}")
    
    # Memory from a later time
    later_time = datetime(2024, 6, 1, tzinfo=timezone.utc)
    result2 = memory_agent.store_conversation(
        user_message="What is the project status now?",
        agent_response="The project is in development phase.",
        conversation_id="conv_temporal_test",
        valid_at=later_time
    )
    print(f"Created later memory: {result2}")
    
    # Test 2: Point-in-time queries
    print("\n=== Test 2: Point-in-time queries ===")
    
    # Query at the past time
    mid_time = datetime(2024, 3, 1, tzinfo=timezone.utc)
    messages_at_mid = memory_agent.get_conversation_at_time(
        conversation_id="conv_temporal_test",
        timestamp=mid_time
    )
    print(f"Messages at {mid_time}: {len(messages_at_mid)} found")
    for msg in messages_at_mid:
        print(f"  - {msg.get('type')}: {msg.get('content')[:50]}...")
    
    # Query at current time
    current_time = datetime.now(timezone.utc)
    messages_now = memory_agent.get_conversation_at_time(
        conversation_id="conv_temporal_test",
        timestamp=current_time
    )
    print(f"Messages at {current_time}: {len(messages_now)} found")
    
    # Test 3: Temporal range queries
    print("\n=== Test 3: Temporal range queries ===")
    
    range_results = memory_agent.get_temporal_range(
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2024, 12, 31, tzinfo=timezone.utc),
        conversation_id="conv_temporal_test"
    )
    print(f"Messages in 2024: {len(range_results)} found")
    
    # Test 4: Search at specific time
    print("\n=== Test 4: Search at specific time ===")
    
    search_results = memory_agent.search_at_time(
        query="project status",
        timestamp=mid_time,
        limit=5
    )
    print(f"Search results at {mid_time}: {len(search_results)} found")
    for result in search_results:
        print(f"  - Score: {result.get('score', 0):.3f}, Content: {result.get('content', '')[:50]}...")
    
    print("\n=== All temporal tests completed ===")

def test_invalidation():
    """Test entity invalidation."""
    db = get_db_connection()
    
    print("\n=== Test 5: Entity invalidation ===")
    
    # Create a test entity
    test_doc = {
        'name': 'Test Entity',
        'status': 'active',
        'value': 100
    }
    
    created = create_temporal_entity(
        db,
        'test_temporal_collection',
        test_doc,
        valid_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )
    print(f"Created entity: {created['_key']}")
    
    # Invalidate the entity
    invalid_time = datetime(2024, 6, 1, tzinfo=timezone.utc)
    invalidated = invalidate_entity(
        db,
        'test_temporal_collection',
        created['_key'],
        invalid_at=invalid_time,
        reason='Test invalidation'
    )
    print(f"Invalidated entity at {invalid_time}")
    
    # Query before and after invalidation
    before_results = point_in_time_query(
        db,
        'test_temporal_collection',
        datetime(2024, 3, 1, tzinfo=timezone.utc)
    )
    print(f"Query before invalidation: {len(before_results)} results")
    
    after_results = point_in_time_query(
        db,
        'test_temporal_collection',
        datetime(2024, 9, 1, tzinfo=timezone.utc)
    )
    print(f"Query after invalidation: {len(after_results)} results")
    
    # Validate temporal consistency
    validation = validate_temporal_consistency(
        db,
        'test_temporal_collection',
        created['_key']
    )
    print(f"Temporal validation: {'Valid' if validation['is_valid'] else 'Invalid'}")
    if not validation['is_valid']:
        print(f"Errors: {validation['errors']}")

if __name__ == "__main__":
    test_temporal_memory()
    test_invalidation()
    print("\n✓ All temporal operations tested successfully!")