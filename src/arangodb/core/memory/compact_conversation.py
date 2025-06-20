"""
Conversation Compaction Module
Module: compact_conversation.py
Description: Functions for compact conversation operations

This module provides functionality for creating compact representations of
conversations using LLMs. It handles chunking of large conversations,
supports different compaction methods, and embeds the results for semantic search.

Key features:
1. Support for various compaction methods (summarize, extract_key_points, topic_model)
2. Handling of conversations of any length through chunking
3. Embedding generation for semantic search
4. Integration with workflow tracking for progress monitoring
5. Redis-based caching for LLM calls using LiteLLM
"""

import os
import json
import itertools
import textwrap
import uuid
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timezone
import time

from loguru import logger

# Import and initialize LiteLLM cache
from arangodb.core.utils.initialize_litellm_cache import initialize_litellm_cache

# Initialize LiteLLM cache early to ensure all LLM calls are cached
initialize_litellm_cache()

from arangodb.core.llm_utils import get_llm_client, extract_llm_response, extract_rationale
from arangodb.core.utils.embedding_utils import get_embedding
from arangodb.core.utils.text_chunker import TextChunker, count_tokens_with_tiktoken
from arangodb.core.utils.workflow_logger import WorkflowLogger as WorkflowTracker
from arangodb.core.constants import (
    COMPACTED_SUMMARIES_COLLECTION,
    COMPACTED_SUMMARIES_VIEW,
    COMPACTION_EDGES_COLLECTION,
    EMBEDDING_FIELD,
    CONFIG
)

def compact_conversation(
    self, 
    conversation_id: str = None, 
    episode_id: str = None,
    compaction_method: str = "summarize",
    max_tokens: int = 2000,
    min_overlap: int = 100
) -> Dict[str, Any]:
    """
    Create a compact representation of a conversation or episode.
    
    Uses a multi-step chunking and summarization process to handle conversations
    of any length. Takes advantage of the TextChunker utility for token-aware
    chunking and the workflow tracking for monitoring progress.
    
    Args:
        conversation_id: ID of the specific conversation to compact
        episode_id: ID of the episode to compact (all conversations)
        compaction_method: Method to use for compaction
            - "summarize": Generate a concise summary
            - "extract_key_points": Extract key points and decisions
            - "topic_model": Identify main topics with brief summary of each
        max_tokens: Maximum number of tokens per chunk for processing
        min_overlap: Minimum token overlap between chunks
        
    Returns:
        Dict with compaction results including the compacted text and metadata
    """
    # Start workflow tracking
    workflow_id = f"compaction_{uuid.uuid4().hex[:8]}"
    workflow = WorkflowTracker(name=f"Conversation Compaction ({compaction_method})", workflow_id=workflow_id)
    workflow.start_step("retrieve_messages")
    
    # 1. Retrieve the full conversation
    messages = self.retrieve_messages(conversation_id=conversation_id, episode_id=episode_id)
    
    if not messages:
        workflow.fail_step("retrieve_messages", error="No messages found")
        raise ValueError(f"No messages found for the specified conversation/episode")
    
    workflow.complete_step("retrieve_messages", metadata={"message_count": len(messages)})
    workflow.start_step("format_conversation")
    
    # 2. Format the conversation as text
    conversation_text = self._format_conversation_for_compaction(messages)
    
    # Get some initial token metrics
    model_name = CONFIG["llm"]["model"]
    token_count = count_tokens_with_tiktoken(conversation_text, model=model_name)
    
    workflow.complete_step("format_conversation", metadata={
        "character_count": len(conversation_text),
        "token_count": token_count,
        "model_name": model_name
    })
    
    # 3. Initialize the LLM client
    workflow.start_step("initialize_llm")
    llm_client = get_llm_client(provider=None, for_rationale=True)
    workflow.complete_step("initialize_llm")
    
    # 4. Process the conversation
    if token_count > max_tokens:
        workflow.start_step("chunked_processing")
        
        # Use TextChunker for token-aware chunking
        chunker = TextChunker(
            max_tokens=max_tokens,
            min_overlap=min_overlap,
            model_name=model_name
        )
        
        # Create a mock repo link and file path for the chunker
        repo_link = f"memory://conversations/{conversation_id or episode_id}"
        file_path = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Chunk the conversation
        chunks = chunker.chunk_text(conversation_text, repo_link, file_path)
        
        workflow.log_data({
            "chunks_created": len(chunks),
            "average_chunk_tokens": sum(c["code_token_count"] for c in chunks) / len(chunks) if chunks else 0
        })
        
        # Process each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            workflow.start_step(f"process_chunk_{i+1}")
            
            # Get the chunk content
            chunk_content = chunk["code"]
            chunk_section = chunk["description"] or "Conversation"
            
            # Create the prompt based on compaction method
            if compaction_method == "summarize":
                prompt = f"""
                Summarize the following conversation segment while preserving all key information:
                
                CONVERSATION SEGMENT {i+1}/{len(chunks)}:
                {chunk_content}
                
                Your summary should be concise but comprehensive, capturing the main topics, 
                decisions, and important details discussed. Focus on the substance of the 
                conversation rather than formatting details.
                """
            elif compaction_method == "extract_key_points":
                prompt = f"""
                Extract the key points and decisions from the following conversation segment:
                
                CONVERSATION SEGMENT {i+1}/{len(chunks)}:
                {chunk_content}
                
                Format your response as a list of key points, focusing on:
                - Main questions or problems discussed
                - Solutions or approaches suggested
                - Decisions made or conclusions reached
                - Action items or next steps
                - Important facts or information shared
                """
            elif compaction_method == "topic_model":
                prompt = f"""
                Identify the main topics discussed in this conversation segment:
                
                CONVERSATION SEGMENT {i+1}/{len(chunks)}:
                {chunk_content}
                
                Format your response with a main heading for each topic, followed by 
                a concise explanation of what was discussed about that topic. Include any 
                conclusions or decisions related to each topic.
                """
            
            # Process this chunk
            try:
                response = llm_client(prompt)
                
                # Try to extract rationale content first (for Gemini models)
                try:
                    chunk_summary = extract_rationale(response)
                except:
                    # Fall back to standard response extraction
                    chunk_summary = extract_llm_response(response)
                
                # Add to our collection of summaries
                chunk_summaries.append({
                    "summary": chunk_summary,
                    "chunk_index": i,
                    "token_count": count_tokens_with_tiktoken(chunk_summary, model=model_name),
                    "section": chunk_section
                })
                
                workflow.complete_step(f"process_chunk_{i+1}", metadata={
                    "chunk_tokens": chunk["code_token_count"],
                    "summary_tokens": count_tokens_with_tiktoken(chunk_summary, model=model_name)
                })
            except Exception as e:
                workflow.fail_step(f"process_chunk_{i+1}", error=str(e))
                logger.error(f"Error processing chunk {i+1}: {e}")
                # Continue with other chunks despite the error
        
        # Integrate the summaries if we have multiple chunks
        if len(chunk_summaries) > 1:
            workflow.start_step("integrate_summaries")
            
            # Combine the chunk summaries
            combined_summaries = "\n\n".join([
                f"SEGMENT {s['chunk_index']+1} - {s['section']}:\n{s['summary']}" 
                for s in chunk_summaries
            ])
            
            # Create an integration prompt based on the compaction method
            if compaction_method == "summarize":
                integration_prompt = f"""
                Below are summaries of different segments of a conversation.
                Create a unified summary that integrates these segments
                into a coherent whole:
                
                {combined_summaries}
                
                Your response should be a single coherent summary that captures 
                the full conversation flow and key information across all segments.
                Avoid phrases like "In Segment 1..." or other references to the segmentation.
                """
            elif compaction_method == "extract_key_points":
                integration_prompt = f"""
                Below are key points extracted from different segments of a conversation.
                Create a unified list of key points that integrates these segments
                without redundancy:
                
                {combined_summaries}
                
                Your response should be a single coherent list of key points that captures 
                the most important information across all segments. Combine similar points
                and organize them logically. Avoid phrases like "In Segment 1..." or other 
                references to the segmentation.
                """
            elif compaction_method == "topic_model":
                integration_prompt = f"""
                Below are topic models from different segments of a conversation.
                Create a unified topic model that integrates these segments:
                
                {combined_summaries}
                
                Your response should identify the main topics across the entire conversation
                and provide a concise summary of each. Merge similar topics from different
                segments and show how topics evolved throughout the conversation.
                Avoid phrases like "In Segment 1..." or other references to the segmentation.
                """
            
            # Generate the final integrated summary
            try:
                response = llm_client(integration_prompt)
                
                # Try to extract rationale content first
                try:
                    final_summary = extract_rationale(response)
                except:
                    # Fall back to standard response extraction
                    final_summary = extract_llm_response(response)
                
                workflow.complete_step("integrate_summaries", metadata={
                    "input_tokens": count_tokens_with_tiktoken(combined_summaries, model=model_name),
                    "output_tokens": count_tokens_with_tiktoken(final_summary, model=model_name)
                })
                
                compact_text = final_summary
            except Exception as e:
                workflow.fail_step("integrate_summaries", error=str(e))
                logger.error(f"Error integrating summaries: {e}")
                
                # Fallback: just concatenate the summaries
                compact_text = "CONSOLIDATED SUMMARIES (integration failed):\n\n" + combined_summaries
        else:
            # For a single chunk, just use its summary
            compact_text = chunk_summaries[0]["summary"] if chunk_summaries else "No summary generated"
            
        workflow.complete_step("chunked_processing")
    else:
        # For shorter conversations that fit within token limits, do direct processing
        workflow.start_step("direct_processing")
        
        # Create prompt based on method
        if compaction_method == "summarize":
            prompt = f"""
            Summarize the following conversation while preserving all key information:
            
            {conversation_text}
            
            Your summary should be concise but comprehensive, capturing the main topics, 
            decisions, and important details discussed. Focus on the substance of the 
            conversation rather than formatting details.
            """
        elif compaction_method == "extract_key_points":
            prompt = f"""
            Extract the key points and decisions from the following conversation:
            
            {conversation_text}
            
            Format your response as a list of key points, focusing on:
            - Main questions or problems discussed
            - Solutions or approaches suggested
            - Decisions made or conclusions reached
            - Action items or next steps
            - Important facts or information shared
            """
        elif compaction_method == "topic_model":
            prompt = f"""
            Identify the main topics discussed in this conversation and provide 
            a brief summary of each:
            
            {conversation_text}
            
            Format your response with a main heading for each topic, followed by 
            a concise explanation of what was discussed about that topic. Include any 
            conclusions or decisions related to each topic.
            """
        
        # Generate the compacted representation
        try:
            response = llm_client(prompt)
            
            # Try to extract rationale content first
            try:
                compact_text = extract_rationale(response)
            except:
                # Fall back to standard response extraction
                compact_text = extract_llm_response(response)
            
            workflow.complete_step("direct_processing", metadata={
                "input_tokens": token_count,
                "output_tokens": count_tokens_with_tiktoken(compact_text, model=model_name)
            })
        except Exception as e:
            workflow.fail_step("direct_processing", error=str(e))
            logger.error(f"Error in direct processing: {e}")
            raise
    
    # 5. Generate embedding for semantic search
    workflow.start_step("generate_embedding")
    try:
        embedding = get_embedding(compact_text)
        workflow.complete_step("generate_embedding", metadata={
            "embedding_dimensions": len(embedding)
        })
    except Exception as e:
        workflow.fail_step("generate_embedding", error=str(e))
        logger.error(f"Error generating embedding: {e}")
        raise
    
    # Collect all associated message IDs
    message_ids = [msg.get("_id") for msg in messages]
    message_keys = [msg.get("_key") for msg in messages]
    
    # 6. Collect tags if available
    workflow.start_step("collect_metadata")
    all_tags = set()
    for msg in messages:
        if msg.get("metadata", {}).get("tags"):
            all_tags.update(msg["metadata"]["tags"])
    
    # 7. Prepare the compaction document
    timestamp = datetime.now(timezone.utc).isoformat()
    compact_doc = {
        "type": "compaction",
        "compaction_method": compaction_method,
        "content": compact_text,
        "conversation_id": conversation_id,
        "episode_id": episode_id,
        "message_ids": message_ids,  # Store all message IDs for reference
        "message_count": len(messages),
        "created_at": timestamp,
        "updated_at": timestamp,
        EMBEDDING_FIELD: embedding,  # Add embedding for semantic search
        "tags": list(all_tags) if all_tags else [],
        "metadata": {
            "original_content_length": len(conversation_text),
            "compacted_length": len(compact_text),
            "original_token_count": token_count,
            "compacted_token_count": count_tokens_with_tiktoken(compact_text, model=model_name),
            "reduction_ratio": 1 - (len(compact_text) / max(1, len(conversation_text))),
            "source_messages": message_keys,
            "chunked_processing": token_count > max_tokens,
            "workflow_id": workflow_id
        }
    }
    workflow.complete_step("collect_metadata")
    
    # 8. Store the compaction document
    workflow.start_step("store_compaction")
    try:
        db = self.db
        compaction_collection = db.collection(COMPACTED_SUMMARIES_COLLECTION)
        result = compaction_collection.insert(compact_doc)
        compaction_id = result["_id"]
        logger.info(f"Created compaction document with ID: {compaction_id}")
        
        # Create relationships between compaction and original messages
        edge_result = self._create_compaction_relationships(compaction_id, message_ids)
        
        workflow.complete_step("store_compaction", metadata={
            "compaction_id": compaction_id,
            "edges_created": edge_result["edges_created"]
        })
        
        # 9. Return the complete compaction document with workflow data
        final_result = compaction_collection.get(result["_key"])
        final_result["workflow_summary"] = workflow.get_summary()
        
        workflow.complete_workflow()
        
        return final_result
        
    except Exception as e:
        workflow.fail_step("store_compaction", error=str(e))
        workflow.fail_workflow(error=str(e))
        logger.error(f"Failed to store compaction: {e}")
        raise

def _format_conversation_for_compaction(self, messages: List[Dict[str, Any]]) -> str:
    """Format messages into a text representation for compaction."""
    # Sort messages by timestamp if available
    sorted_messages = sorted(
        messages, 
        key=lambda msg: msg.get("timestamp", ""),
        reverse=False
    )
    
    # Build conversation text
    conversation_parts = []
    for msg in sorted_messages:
        msg_type = msg.get("type", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        
        # Format the timestamp if present
        time_str = ""
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = f"[{dt.strftime('%Y-%m-%d %H:%M:%S')}] "
            except (ValueError, TypeError):
                # If timestamp parsing fails, just use it as-is
                time_str = f"[{timestamp}] "
        
        if msg_type == "user":
            conversation_parts.append(f"{time_str}User: {content}")
        elif msg_type == "agent":
            conversation_parts.append(f"{time_str}Agent: {content}")
        else:
            conversation_parts.append(f"{time_str}{msg_type.capitalize()}: {content}")
    
    # Join with double newlines for clear separation
    return "\n\n".join(conversation_parts)

def _create_compaction_relationships(self, compaction_id: str, message_ids: List[str]):
    """Create graph relationships between compaction and messages"""
    db = self.db
    edge_collection = db.collection(COMPACTION_EDGES_COLLECTION)
    
    edges_created = 0
    errors = []
    
    # Create edges from compaction to each message
    for msg_id in message_ids:
        edge = {
            "_from": compaction_id,
            "_to": msg_id,
            "type": "summarizes",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        try:
            edge_collection.insert(edge)
            edges_created += 1
        except Exception as e:
            errors.append(f"Failed to create edge from {compaction_id} to {msg_id}: {e}")
            logger.warning(f"Failed to create edge from {compaction_id} to {msg_id}: {e}")
            
    logger.info(f"Created {edges_created} relationship edges for compaction {compaction_id}")
    
    return {
        "edges_created": edges_created,
        "total_messages": len(message_ids),
        "errors": errors if errors else None
    }
