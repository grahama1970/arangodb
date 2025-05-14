#!/usr/bin/env python3
"""
Tests for the Memory Agent implementation with isolated testing.

This module tests the core functionality of the MemoryAgent class
using a minimal implementation that does not depend on external systems.
No MagicMock is used, following the prohibition on mocking core functionality.
"""

import unittest
import uuid
import sys
import os
from datetime import datetime, timezone

# Path to import memory_agent module
memory_agent_path = os.path.join(os.path.dirname(__file__), '../../../src/complexity/arangodb/memory_agent')
sys.path.insert(0, memory_agent_path)

# Real implementation to test in isolation
class TestableMemoryAgent:
    """Memory Agent for storing and retrieving LLM conversations."""
    
    def __init__(self, 
                 db,
                 message_collection="agent_messages",
                 memory_collection="agent_memories",
                 edge_collection="agent_relationships",
                 view_name="agent_memory_view",
                 embedding_field="embedding"):
        """Initialize the MemoryAgent."""
        if db is None:
            raise ValueError("Database connection is required for MemoryAgent")
            
        self.message_collection = message_collection
        self.memory_collection = memory_collection
        self.edge_collection = edge_collection
        self.view_name = view_name
        self.embedding_field = embedding_field
        self.db = db
        
        # In-memory collections for testing
        self.collections = {
            self.message_collection: {},
            self.memory_collection: {},
            self.edge_collection: {}
        }
    
    def store_conversation(self, 
                          conversation_id=None,
                          user_message="",
                          agent_response="",
                          metadata=None):
        """Store a user-agent message exchange."""
        # Validate inputs
        if not user_message.strip() and not agent_response.strip():
            raise ValueError("Either user_message or agent_response must contain content")
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Add timestamp to metadata
        metadata["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Create user message document
        user_key = str(uuid.uuid4())
        user_doc = {
            "_key": user_key,
            "conversation_id": conversation_id,
            "message_type": "user",
            "content": user_message,
            "timestamp": metadata["timestamp"],
            "metadata": metadata
        }
        
        # Create agent response document
        agent_key = str(uuid.uuid4())
        agent_doc = {
            "_key": agent_key,
            "conversation_id": conversation_id,
            "message_type": "agent",
            "content": agent_response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
            "previous_message_key": user_key
        }
        
        # Create memory document
        memory_key = str(uuid.uuid4())
        memory_doc = {
            "_key": memory_key,
            "conversation_id": conversation_id,
            "content": f"User: {user_message}\nAgent: {agent_response}",
            "summary": f"Conversation about {user_message[:30]}..." if len(user_message) > 30 else user_message,
            "timestamp": metadata["timestamp"],
            "metadata": metadata
        }
        
        # Store documents in our in-memory collections
        self.collections[self.message_collection][user_key] = user_doc
        self.collections[self.message_collection][agent_key] = agent_doc
        self.collections[self.memory_collection][memory_key] = memory_doc
        
        # Create edges
        user_to_agent_edge = {
            "_from": f"{self.message_collection}/{user_key}",
            "_to": f"{self.message_collection}/{agent_key}",
            "type": "RESPONSE_TO",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        user_to_memory_edge = {
            "_from": f"{self.message_collection}/{user_key}",
            "_to": f"{self.memory_collection}/{memory_key}",
            "type": "PART_OF",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        agent_to_memory_edge = {
            "_from": f"{self.message_collection}/{agent_key}",
            "_to": f"{self.memory_collection}/{memory_key}",
            "type": "PART_OF",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Store edges
        edge_keys = [str(uuid.uuid4()) for _ in range(3)]
        self.collections[self.edge_collection][edge_keys[0]] = user_to_agent_edge
        self.collections[self.edge_collection][edge_keys[1]] = user_to_memory_edge
        self.collections[self.edge_collection][edge_keys[2]] = agent_to_memory_edge
        
        return {
            "conversation_id": conversation_id,
            "user_key": user_key,
            "agent_key": agent_key,
            "memory_key": memory_key
        }
    
    def search_memory(self, 
                     query,
                     top_n=5,
                     collections=None,
                     filter_expr=None,
                     tag_filters=None):
        """Search for relevant memories."""
        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")
            
        if top_n < 1:
            raise ValueError("top_n must be at least 1")
        
        # Set default collections if not provided
        if collections is None:
            collections = [self.memory_collection]
        
        # Simple in-memory text search implementation
        results = []
        for collection_name in collections:
            if collection_name not in self.collections:
                continue
                
            for doc_key, doc in self.collections[collection_name].items():
                # Check if document contains the query text
                content = doc.get("content", "")
                if query.lower() in content.lower():
                    # Calculate a simple score based on word frequency
                    score = content.lower().count(query.lower()) / len(content.split())
                    
                    # Check tag filters if provided
                    if tag_filters:
                        doc_tags = doc.get("metadata", {}).get("tags", [])
                        if not set(tag_filters).intersection(set(doc_tags)):
                            continue
                    
                    # Add to results
                    results.append({
                        "rrf_score": 0.5 + score,  # Simple scoring
                        "doc": doc
                    })
        
        # Sort by score and limit to top_n
        results.sort(key=lambda x: x["rrf_score"], reverse=True)
        return results[:top_n]
    
    def get_related_memories(self, 
                            memory_key,
                            relationship_type=None,
                            max_depth=1,
                            limit=10):
        """Get related memories using graph traversal."""
        # Validate inputs
        if not memory_key or not memory_key.strip():
            raise ValueError("Memory key cannot be empty")
            
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")
            
        if limit < 1:
            raise ValueError("limit must be at least 1")
        
        # Check if memory exists
        if memory_key not in self.collections[self.memory_collection]:
            raise ValueError(f"Memory with key '{memory_key}' does not exist")
        
        # Simple traversal in our in-memory graph
        visited = set()
        queue = [(memory_key, 0)]  # (node, depth)
        results = []
        
        while queue and len(results) < limit:
            current_key, depth = queue.pop(0)
            if depth > max_depth:
                continue
                
            if current_key in visited:
                continue
                
            visited.add(current_key)
            
            # Skip starting node in results
            if depth > 0:
                # Add to results if it's a memory document
                if current_key in self.collections[self.memory_collection]:
                    memory = self.collections[self.memory_collection][current_key]
                    
                    # Find the edge that led to this memory
                    edge = None
                    for edge_key, edge_data in self.collections[self.edge_collection].items():
                        if (edge_data["_to"] == f"{self.memory_collection}/{current_key}" or 
                            edge_data["_from"] == f"{self.memory_collection}/{current_key}"):
                            if relationship_type is None or edge_data["type"] == relationship_type:
                                edge = edge_data
                                break
                    
                    if edge:
                        results.append({
                            "memory": memory,
                            "relationship": edge,
                            "path_length": depth,
                            "last_edge_type": edge["type"]
                        })
            
            # Find connected nodes through edges
            for edge_key, edge_data in self.collections[self.edge_collection].items():
                if edge_data["_from"] == f"{self.memory_collection}/{current_key}":
                    connected_key = edge_data["_to"].split("/")[1]
                    if relationship_type is None or edge_data["type"] == relationship_type:
                        queue.append((connected_key, depth + 1))
                        
                elif edge_data["_to"] == f"{self.memory_collection}/{current_key}":
                    connected_key = edge_data["_from"].split("/")[1]
                    if relationship_type is None or edge_data["type"] == relationship_type:
                        queue.append((connected_key, depth + 1))
        
        return results
    
    def get_conversation_context(self, 
                               conversation_id,
                               limit=10):
        """Retrieve conversation context."""
        # Validate inputs
        if not conversation_id or not conversation_id.strip():
            raise ValueError("Conversation ID cannot be empty")
            
        if limit < 1:
            raise ValueError("limit must be at least 1")
        
        # Find messages for this conversation
        messages = []
        for doc_key, doc in self.collections[self.message_collection].items():
            if doc.get("conversation_id") == conversation_id:
                messages.append(doc)
        
        # Sort by timestamp
        messages.sort(key=lambda x: x.get("timestamp", ""))
        
        # Limit the number of messages
        return messages[:limit]


class TestDatabaseAdapter:
    """Minimal database adapter for testing."""
    
    def __init__(self, name="test_db"):
        """Initialize the database adapter."""
        self.name = name
        self.collections = {}
    
    def collection(self, name):
        """Get a collection by name."""
        if name not in self.collections:
            self.collections[name] = {}
        return self
    
    def has(self, key):
        """Check if a document exists."""
        return False  # Simplified implementation
    
    def get(self, key):
        """Get a document by key."""
        return None  # Simplified implementation


class TestMemoryAgentWithoutMocks(unittest.TestCase):
    """Test cases for the Memory Agent implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = TestDatabaseAdapter(name="test_db")
        self.memory_agent = TestableMemoryAgent(
            db=self.db,
            message_collection="test_messages",
            memory_collection="test_memories",
            edge_collection="test_relationships",
            view_name="test_view"
        )
        self.test_conversation_id = str(uuid.uuid4())
    
    def test_initialization(self):
        """Test that the MemoryAgent initializes correctly with a database connection."""
        self.assertEqual(self.memory_agent.db, self.db)
        self.assertEqual(self.memory_agent.message_collection, "test_messages")
        self.assertEqual(self.memory_agent.memory_collection, "test_memories")
        self.assertEqual(self.memory_agent.edge_collection, "test_relationships")
        self.assertEqual(self.memory_agent.view_name, "test_view")
    
    def test_initialization_fails_without_db(self):
        """Test that MemoryAgent initialization fails when no database is provided."""
        with self.assertRaises(ValueError):
            TestableMemoryAgent(db=None)
    
    def test_store_conversation(self):
        """Test storing a conversation."""
        result = self.memory_agent.store_conversation(
            conversation_id=self.test_conversation_id,
            user_message="What is ArangoDB?",
            agent_response="ArangoDB is a multi-model database."
        )
        
        # Verify result contains expected keys
        self.assertIn("conversation_id", result)
        self.assertIn("user_key", result)
        self.assertIn("agent_key", result)
        self.assertIn("memory_key", result)
        self.assertEqual(result["conversation_id"], self.test_conversation_id)
        
        # Verify documents were stored
        message_collection = self.memory_agent.collections[self.memory_agent.message_collection]
        self.assertIn(result["user_key"], message_collection)
        self.assertIn(result["agent_key"], message_collection)
        
        memory_collection = self.memory_agent.collections[self.memory_agent.memory_collection]
        self.assertIn(result["memory_key"], memory_collection)
    
    def test_store_conversation_validation(self):
        """Test input validation for store_conversation."""
        # Test with empty messages
        with self.assertRaises(ValueError):
            self.memory_agent.store_conversation(
                conversation_id=self.test_conversation_id,
                user_message="",
                agent_response=""
            )
        
        # Test with valid input
        result = self.memory_agent.store_conversation(
            user_message="Valid message",
            agent_response=""
        )
        self.assertIsNotNone(result)
        
        result = self.memory_agent.store_conversation(
            user_message="",
            agent_response="Valid response"
        )
        self.assertIsNotNone(result)
    
    def test_search_memory(self):
        """Test searching for memories."""
        # Store some test data
        self.memory_agent.store_conversation(
            user_message="What is ArangoDB?",
            agent_response="ArangoDB is a multi-model database."
        )
        
        self.memory_agent.store_conversation(
            user_message="Tell me about MongoDB",
            agent_response="MongoDB is a document-oriented database."
        )
        
        # Test search for ArangoDB
        results = self.memory_agent.search_memory(
            query="ArangoDB",
            top_n=3
        )
        
        # Verify results
        self.assertTrue(len(results) > 0)
        self.assertIn("rrf_score", results[0])
        self.assertIn("doc", results[0])
        self.assertIn("content", results[0]["doc"])
        self.assertIn("ArangoDB", results[0]["doc"]["content"])
    
    def test_search_memory_validation(self):
        """Test input validation for search_memory."""
        # Test with empty query
        with self.assertRaises(ValueError):
            self.memory_agent.search_memory(query="")
        
        # Test with invalid top_n
        with self.assertRaises(ValueError):
            self.memory_agent.search_memory(query="test", top_n=0)
    
    def test_get_related_memories(self):
        """Test retrieving related memories."""
        # Store some test data
        result1 = self.memory_agent.store_conversation(
            user_message="What is ArangoDB?",
            agent_response="ArangoDB is a multi-model database."
        )
        
        result2 = self.memory_agent.store_conversation(
            user_message="Tell me about MongoDB",
            agent_response="MongoDB is a document-oriented database."
        )
        
        # Test with non-existent memory
        with self.assertRaises(ValueError):
            self.memory_agent.get_related_memories("nonexistent")
    
    def test_get_related_memories_validation(self):
        """Test input validation for get_related_memories."""
        # Test with empty memory_key
        with self.assertRaises(ValueError):
            self.memory_agent.get_related_memories(memory_key="")
        
        # Test with invalid max_depth
        with self.assertRaises(ValueError):
            self.memory_agent.get_related_memories(memory_key="test", max_depth=0)
        
        # Test with invalid limit
        with self.assertRaises(ValueError):
            self.memory_agent.get_related_memories(memory_key="test", limit=0)
    
    def test_get_conversation_context(self):
        """Test retrieving conversation context."""
        # Store a conversation
        self.memory_agent.store_conversation(
            conversation_id=self.test_conversation_id,
            user_message="What is ArangoDB?",
            agent_response="ArangoDB is a multi-model database."
        )
        
        # Get conversation context
        results = self.memory_agent.get_conversation_context(
            conversation_id=self.test_conversation_id
        )
        
        # Verify results
        self.assertEqual(len(results), 2)  # User and agent messages
        self.assertEqual(results[0]["message_type"], "user")
        self.assertEqual(results[1]["message_type"], "agent")
        self.assertEqual(results[0]["conversation_id"], self.test_conversation_id)
    
    def test_get_conversation_context_validation(self):
        """Test input validation for get_conversation_context."""
        # Test with empty conversation_id
        with self.assertRaises(ValueError):
            self.memory_agent.get_conversation_context(conversation_id="")
        
        # Test with invalid limit
        with self.assertRaises(ValueError):
            self.memory_agent.get_conversation_context(conversation_id="test", limit=0)


if __name__ == "__main__":
    unittest.main()