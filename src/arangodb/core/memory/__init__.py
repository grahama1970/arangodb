"""
Memory Agent Core Module

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

# Entity and contradiction modules will be implemented in future refactoring
# For now, we'll keep these commented out
"""
from arangodb.core.memory.entity import (
    resolve_entities,
    find_entity_matches,
    add_entity,
)

from arangodb.core.memory.contradiction import (
    detect_contradictions,
    resolve_contradictions,
)
"""

# Export named packages
__all__ = [
    "MemoryAgent",
]