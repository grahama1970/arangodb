"""
Validation script for Memory commands with real ArangoDB connection

This script tests all memory operations with actual data to verify:
1. Real connections to ArangoDB work
2. Memory agent stores conversations correctly
3. Search and retrieval functions work
4. Temporal queries function properly
5. Both JSON and table output formats work
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import memory agent
from arangodb.core.memory.memory_agent import MemoryAgent

# Import db connection
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.constants import (
    MEMORY_MESSAGE_COLLECTION,
    MEMORY_COLLECTION,
    MEMORY_EDGE_COLLECTION
)

# For rich table display
from rich.console import Console
from rich.table import Table

console = Console()


def test_store_conversation(agent):
    """Test storing a conversation"""
    logger.info("Testing STORE CONVERSATION")
    
    try:
        # Test conversation data
        conversation_id = "test_conv_001"
        user_message = "How do I optimize database queries?"
        agent_response = "To optimize database queries, consider indexing frequently searched fields, using query analyzers, and batching operations."
        metadata = {
            "topic": "database optimization",
            "session": "test_session",
            "user_id": "test_user"
        }
        
        # Store the conversation
        result = agent.store_conversation(
            conversation_id=conversation_id,
            user_message=user_message,
            agent_response=agent_response,
            metadata=metadata
        )
        
        if not result:
            return False, "Failed to store conversation - no result returned"
        
        # The result might be a list of message keys or a more complex structure
        logger.info(f"Store conversation result: {result}")
        
        # Check if result is a dictionary with expected keys
        if isinstance(result, dict):
            if 'user_key' not in result or 'agent_key' not in result:
                return False, f"Result missing expected keys. Got: {result.keys()}"
            
            user_key = result['user_key']
            agent_key = result['agent_key']
            memory_key = result.get('memory_key')
            
            if not user_key or not agent_key:
                return False, "Missing message keys in result"
            
            logger.info(f"Successfully stored conversation: {conversation_id}")
            return True, (conversation_id, user_key, agent_key)
        else:
            return False, f"Unexpected result format: {type(result)}"
        
    except Exception as e:
        return False, f"Store conversation failed: {str(e)}"


def test_retrieve_messages(db, conversation_id):
    """Test retrieving conversation messages using direct DB query"""
    logger.info(f"Testing RETRIEVE MESSAGES for conversation: {conversation_id}")
    
    try:
        # Retrieve messages directly from database - use agent_messages collection
        messages_coll = db.collection('agent_messages')
        messages = list(messages_coll.find({'conversation_id': conversation_id}))
        
        if not isinstance(messages, list):
            return False, f"Retrieved messages not a list: {type(messages)}"
        
        if len(messages) == 0:
            return False, "No messages retrieved"
        
        # Check message structure
        for msg in messages:
            required_fields = ['content', 'conversation_id', 'timestamp']
            missing_fields = [field for field in required_fields if field not in msg]
            
            if missing_fields:
                return False, f"Message missing fields: {missing_fields}"
        
        logger.info(f"Successfully retrieved {len(messages)} messages")
        return True, messages
        
    except Exception as e:
        return False, f"Retrieve messages failed: {str(e)}"


def test_search_memory(agent):
    """Test memory search functionality using temporal_search method"""
    logger.info("Testing SEARCH MEMORY")
    
    try:
        # Search for database-related conversations using temporal_search without time constraint
        query = "database optimization queries"
        results = agent.temporal_search(
            query_text=query,
            point_in_time=None,  # No temporal constraint
            top_n=5
        )
        
        if not isinstance(results, dict):
            return False, f"Search results not a dict: {type(results)}"
        
        # Check result structure
        if 'results' not in results:
            return False, "Search results missing 'results' key"
        
        if 'query' not in results:
            return False, "Search results missing 'query' key"
        
        result_count = len(results['results'])
        logger.info(f"Successfully searched memory, found {result_count} results")
        return True, results
        
    except Exception as e:
        return False, f"Search memory failed: {str(e)}"


def test_temporal_search(agent, reference_time=None):
    """Test temporal search functionality"""
    logger.info("Testing TEMPORAL SEARCH")
    
    try:
        # If no reference time provided, use now
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        
        # Search with temporal constraints using the temporal_search method
        results = agent.temporal_search(
            query_text="optimization",
            point_in_time=reference_time,
            top_n=5
        )
        
        if not isinstance(results, dict):
            return False, f"Temporal search results not a dict: {type(results)}"
        
        logger.info(f"Successfully performed temporal search")
        return True, results
        
    except Exception as e:
        return False, f"Temporal search failed: {str(e)}"


def test_context_retrieval(db, agent, conversation_id):
    """Test context retrieval for a conversation using direct DB queries"""
    logger.info(f"Testing CONTEXT RETRIEVAL for conversation: {conversation_id}")
    
    try:
        # Get messages directly - use agent_messages collection
        messages_coll = db.collection('agent_messages')
        messages = list(messages_coll.find({'conversation_id': conversation_id}))
        
        # Try to find related memories using temporal search
        if messages:
            first_message = messages[0]
            timestamp = first_message.get('timestamp')
            
            # Convert timestamp string to datetime if needed
            if isinstance(timestamp, str):
                # Parse ISO format timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    # Try another format or use current time
                    timestamp = datetime.now(timezone.utc)
            
            # Use temporal search to find related memories
            related = agent.temporal_search(
                query_text=first_message.get('content', ''),
                point_in_time=timestamp,
                top_n=5
            )
            
            context = {
                'messages': messages,
                'related_memories': related.get('results', []),
                'conversation_id': conversation_id
            }
        else:
            context = {
                'messages': [],
                'related_memories': [],
                'conversation_id': conversation_id
            }
        
        logger.info("Successfully retrieved conversation context")
        return True, context
        
    except Exception as e:
        return False, f"Context retrieval failed: {str(e)}"


def display_results_table(results):
    """Display results in a rich table format"""
    table = Table(title="Memory Operations Validation Results")
    table.add_column("Operation", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    for operation, status, details in results:
        status_symbol = "✅" if status else "❌"
        table.add_row(operation, status_symbol, str(details))
    
    console.print(table)


def display_results_json(results):
    """Display results in JSON format"""
    json_results = {
        "validation_results": [
            {
                "operation": op,
                "status": "passed" if status else "failed",
                "details": str(details)
            }
            for op, status, details in results
        ],
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for _, status, _ in results if status),
            "failed": sum(1 for _, status, _ in results if not status)
        }
    }
    console.print(json.dumps(json_results, indent=2))


def cleanup_test_data(db, conversation_id):
    """Clean up test conversation data"""
    try:
        # Delete test messages from agent_messages collection
        messages_coll = db.collection('agent_messages')
        cursor = db.aql.execute(
            'FOR msg IN @@collection FILTER msg.conversation_id == @conv_id RETURN msg._key',
            bind_vars={
                '@collection': 'agent_messages',
                'conv_id': conversation_id
            }
        )
        
        for key in cursor:
            messages_coll.delete(key)
            logger.info(f"Cleaned up message: {key}")
            
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time} {level} {message}")
    
    # Track all results
    results = []
    test_conversation_id = None
    
    try:
        # Get database connection and create memory agent
        db = get_db_connection()
        agent = MemoryAgent(db=db)
        logger.info(f"Connected to ArangoDB and initialized MemoryAgent")
        
        # Test 1: Store conversation
        success, result = test_store_conversation(agent)
        if success:
            test_conversation_id, user_key, agent_key = result
            results.append(("STORE CONVERSATION", success, f"Stored with ID: {test_conversation_id}"))
        else:
            results.append(("STORE CONVERSATION", success, result))
        
        if test_conversation_id:
            # Test 2: Retrieve messages
            success, result = test_retrieve_messages(db, test_conversation_id)
            results.append(("RETRIEVE MESSAGES", success, 
                          f"Retrieved {len(result)} messages" if success else result))
            
            # Test 3: Search memory
            success, result = test_search_memory(agent)
            results.append(("SEARCH MEMORY", success, 
                          f"Found {len(result['results'])} results" if success else result))
            
            # Test 4: Temporal search
            success, result = test_temporal_search(agent)
            results.append(("TEMPORAL SEARCH", success, 
                          "Temporal search successful" if success else result))
            
            # Test 5: Context retrieval
            success, result = test_context_retrieval(db, agent, test_conversation_id)
            results.append(("CONTEXT RETRIEVAL", success, 
                          f"Retrieved context with {len(result['messages'])} messages" if success else result))
            
            # Cleanup
            cleanup_test_data(db, test_conversation_id)
        
        # Display results in both formats
        console.print("\n[bold]Table Format:[/bold]")
        display_results_table(results)
        
        console.print("\n[bold]JSON Format:[/bold]")
        display_results_json(results)
        
        # Final result
        failures = [r for r in results if not r[1]]
        if failures:
            console.print(f"\n❌ VALIDATION FAILED - {len(failures)} of {len(results)} tests failed")
            for op, _, details in failures:
                console.print(f"  - {op}: {details}")
            sys.exit(1)
        else:
            console.print(f"\n✅ VALIDATION PASSED - All {len(results)} tests produced expected results")
            console.print("Memory operations are working correctly with real ArangoDB connection")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error during validation: {e}")
        logger.error(traceback.format_exc())
        console.print(f"\n❌ VALIDATION FAILED - Fatal error: {e}")
        sys.exit(1)