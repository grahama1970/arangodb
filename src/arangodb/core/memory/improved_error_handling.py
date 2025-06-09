"""
Error Handling Improvements for Memory Operations
Module: improved_error_handling.py
Description: Functions for improved error handling operations

This module provides enhanced error handling for memory operations in the ArangoDB Knowledge Graph System.
It contains function wrappers and decorators that can be imported and applied to existing functions.
"""

from ..utils.error_handler import (
    handle_db_errors, 
    handle_search_errors, 
    handle_llm_errors,
    with_error_handling,
    MemoryError,
    ConversationError,
    EpisodeError,
    EmbeddingError
)
from typing import Dict, Any, List, Optional, Callable
from loguru import logger
import functools

# Apply to memory agent methods
def enhanced_store_conversation(original_func):
    """
    Enhanced error handling for store_conversation method.
    
    Handles embedding errors gracefully and provides detailed error messages.
    """
    @functools.wraps(original_func)
    def wrapper(self, user_message, agent_response, conversation_id=None, episode_id=None, 
                metadata=None, point_in_time=None, auto_embed=True):
        
        # Validate inputs
        if not user_message:
            raise ConversationError("User message cannot be empty")
        if not agent_response:
            raise ConversationError("Agent response cannot be empty")
        
        # Handle embedding errors gracefully
        if auto_embed:
            try:
                from ..utils.embedding_utils import get_embedding
                # Test embedding generation to fail early if there's an issue
                get_embedding("Test embedding generation")
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}. Disabling auto-embedding.")
                auto_embed = False
        
        # Call original function with possibly modified auto_embed
        try:
            return original_func(self, user_message, agent_response, conversation_id, 
                               episode_id, metadata, point_in_time, auto_embed)
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            # Provide more specific error
            if "duplicate" in str(e).lower():
                raise ConversationError(f"Conversation already exists with ID: {conversation_id}")
            if "not found" in str(e).lower() and episode_id:
                raise EpisodeError(f"Episode not found with ID: {episode_id}")
            # Re-raise as ConversationError
            raise ConversationError(f"Failed to store conversation: {str(e)}")
    
    return wrapper

# Apply to compact_conversation
def enhanced_compact_conversation(original_func):
    """
    Enhanced error handling for compact_conversation method.
    
    Handles LLM errors gracefully and provides fallback strategies.
    """
    @functools.wraps(original_func)
    def wrapper(self, conversation_id=None, episode_id=None, 
                compaction_method="summarize", max_tokens=2000, min_overlap=100):
        
        # Validate inputs
        if not conversation_id and not episode_id:
            raise ConversationError("Either conversation_id or episode_id must be provided")
        
        # Check if messages exist before proceeding
        try:
            messages = self.retrieve_messages(conversation_id=conversation_id, episode_id=episode_id)
            if not messages:
                raise ConversationError(
                    f"No messages found for {'conversation_id: ' + conversation_id if conversation_id else 'episode_id: ' + episode_id}"
                )
        except Exception as e:
            logger.error(f"Failed to retrieve messages: {e}")
            raise ConversationError(f"Failed to retrieve messages: {str(e)}")
        
        # Validate compaction method
        valid_methods = ["summarize", "extract_key_points", "topic_model"]
        if compaction_method not in valid_methods:
            raise ValueError(
                f"Invalid compaction method: {compaction_method}. Valid methods: {', '.join(valid_methods)}"
            )
        
        # Call original function with additional error handling
        try:
            return original_func(self, conversation_id, episode_id, compaction_method, max_tokens, min_overlap)
        except Exception as e:
            logger.error(f"Failed to compact conversation: {e}")
            
            # Provide fallback options for specific errors
            if "LLM" in str(type(e)) or "model" in str(e).lower():
                logger.warning("LLM error encountered. Attempting fallback strategy.")
                try:
                    # Fallback to simpler compaction method
                    logger.info("Retrying with simplified compaction method and parameters")
                    return original_func(self, conversation_id, episode_id, "extract_key_points", 
                                        max_tokens // 2, min_overlap // 2)
                except Exception as fallback_error:
                    logger.error(f"Fallback compaction also failed: {fallback_error}")
                    raise ConversationError(
                        "Could not compact conversation. Both primary and fallback methods failed."
                    )
            
            # Re-raise as ConversationError with more context
            raise ConversationError(f"Conversation compaction failed: {str(e)}")
    
    return wrapper

# Apply to search_compactions
def enhanced_search_compactions(original_func):
    """
    Enhanced error handling for search_compactions method.
    
    Handles embedding and search errors gracefully.
    """
    @functools.wraps(original_func)
    def wrapper(self, query_text, min_score=0.75, top_n=5, 
                compaction_methods=None, conversation_id=None, episode_id=None):
        
        # Validate inputs
        if not query_text:
            raise ValueError("Query text cannot be empty")
        
        if min_score < 0 or min_score > 1:
            logger.warning(f"Invalid min_score: {min_score}. Setting to default: 0.75")
            min_score = 0.75
        
        if top_n < 1:
            logger.warning(f"Invalid top_n: {top_n}. Setting to default: 5")
            top_n = 5
        
        # Handle embedding errors gracefully
        try:
            from ..utils.embedding_utils import get_embedding
            # Test embedding generation to fail early if there's an issue
            get_embedding(query_text)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingError(
                f"Could not generate embedding for query: {str(e)}"
            )
        
        # Call original function with validated parameters
        try:
            return original_func(self, query_text, min_score, top_n, 
                                compaction_methods, conversation_id, episode_id)
        except Exception as e:
            logger.error(f"Failed to search compactions: {e}")
            
            # Provide more specific error
            if "embedding" in str(e).lower():
                raise EmbeddingError(f"Embedding error during search: {str(e)}")
            if "collection" in str(e).lower() and "not found" in str(e).lower():
                raise MemoryError("Compaction collection not found. No compactions have been created yet.")
            
            # Re-raise as MemoryError
            raise MemoryError(f"Failed to search compactions: {str(e)}")
    
    return wrapper

# Helper function to apply these enhancements to a memory agent instance
def enhance_memory_agent(memory_agent):
    """
    Apply enhanced error handling to a memory agent instance.
    
    Args:
        memory_agent: MemoryAgent instance to enhance
    
    Returns:
        Enhanced MemoryAgent instance
    """
    # Store original methods
    original_store_conversation = memory_agent.store_conversation
    original_compact_conversation = memory_agent.compact_conversation
    original_search_compactions = memory_agent.search_compactions
    
    # Replace with enhanced versions
    memory_agent.store_conversation = enhanced_store_conversation(original_store_conversation).__get__(memory_agent)
    memory_agent.compact_conversation = enhanced_compact_conversation(original_compact_conversation).__get__(memory_agent)
    memory_agent.search_compactions = enhanced_search_compactions(original_search_compactions).__get__(memory_agent)
    
    return memory_agent
