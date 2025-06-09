"""
Memory Agent Core Module
Module: __init__.py
Description: Package initialization and exports

This module provides memory management functionality for AI agents, including:
- Conversation storage and retrieval
- Semantic search over conversations
- Entity resolution
- Contradiction detection
- Temporal relationship tracking
- Memory graphs and connections

The memory agent stores and retrieves information about conversations, entities, 
and their relationships in ArangoDB.
"""

# Import and expose the main MemoryAgent class and utility functions
from .memory_agent import MemoryAgent
from .episode_manager import EpisodeManager
from .contradiction_logger import ContradictionLogger
from .message_history_config import (
    MESSAGE_COLLECTION_NAME,
    MESSAGE_TYPE_USER,
    MESSAGE_TYPE_AGENT,
    MESSAGE_TYPE_SYSTEM,
    MESSAGE_EDGE_COLLECTION_NAME,
    MESSAGE_GRAPH_NAME,
    RELATIONSHIP_TYPE_NEXT,
    RELATIONSHIP_TYPE_REFERS_TO
)

# Export named packages
__all__ = [
    "MemoryAgent",
    "EpisodeManager",
    "ContradictionLogger",
    "MESSAGE_COLLECTION_NAME",
    "MESSAGE_TYPE_USER",
    "MESSAGE_TYPE_AGENT",
    "MESSAGE_TYPE_SYSTEM",
    "MESSAGE_EDGE_COLLECTION_NAME",
    "MESSAGE_GRAPH_NAME",
    "RELATIONSHIP_TYPE_NEXT",
    "RELATIONSHIP_TYPE_REFERS_TO",
]