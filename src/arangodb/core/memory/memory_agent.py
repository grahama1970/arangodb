"""
Memory Agent Module

Provides the MemoryAgent class for managing conversational memory in ArangoDB with
temporal relationships and graph features.

Implements the Memory Interface specification.
"""

import os
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union, Tuple

from loguru import logger

from arango.database import StandardDatabase
from arango.exceptions import (
    DocumentInsertError,
    DocumentGetError,
    DocumentUpdateError,
    DocumentDeleteError,
    AQLQueryExecuteError
)

from arangodb.core.constants import (
    MEMORY_COLLECTION,
    MEMORY_MESSAGE_COLLECTION,
    MEMORY_EDGE_COLLECTION,
    MEMORY_VIEW_NAME,
    COMPACTED_SUMMARIES_COLLECTION,
    COMPACTED_SUMMARIES_VIEW,
    COMPACTION_EDGES_COLLECTION,
    MESSAGE_TYPE_USER,
    MESSAGE_TYPE_AGENT,
    RELATIONSHIP_TYPE_NEXT,
    CONFIG
)
from arangodb.core.temporal_operations import (
    create_temporal_entity,
    ensure_temporal_fields,
    point_in_time_query,
    temporal_range_query
)

from arangodb.core.field_constants import (
    TYPE_FIELD,
    CONTENT_FIELD,
    TIMESTAMP_FIELD,
    EMBEDDING_FIELD,
    CONVERSATION_ID_FIELD,
    EPISODE_ID_FIELD,
    METADATA_FIELD,
    FROM_FIELD,
    TO_FIELD,
    VALID_FROM_FIELD,
    VALID_TO_FIELD,
)

from arangodb.core.utils.embedding_utils import get_embedding
from arangodb.core.utils.workflow_tracking import WorkflowTracker

# Import compact_conversation function
from arangodb.core.memory.compact_conversation import compact_conversation

class MemoryAgent:
    """
    Enhanced Memory Agent for storing and retrieving LLM conversations with 
    Graphiti-inspired temporal features.
    
    This class handles:
    1. Storing user-agent message exchanges in ArangoDB with temporal metadata
    2. Embedding messages for semantic search
    3. Creating bi-temporal relationships between messages
    4. Detecting and resolving contradicting information
    5. Searching for relevant past conversations with temporal constraints
    6. Compacting conversations for efficient storage and retrieval
    """
    
    def __init__(self, db: StandardDatabase):
        """
        Initialize the Memory Agent with a database connection.
        
        Args:
            db: An active ArangoDB database connection
        """
        self.db = db
        self.setup_collections()
    
    def setup_collections(self):
        """
        Ensure all required collections and views exist.
        Creates them if they don't exist.
        """
        # Check and create collections
        required_collections = [
            (MEMORY_COLLECTION, False),
            (MEMORY_MESSAGE_COLLECTION, False),
            (MEMORY_EDGE_COLLECTION, True),
            (COMPACTED_SUMMARIES_COLLECTION, False),
            (COMPACTION_EDGES_COLLECTION, True)
        ]
        
        for coll_name, is_edge in required_collections:
            if not self.db.has_collection(coll_name):
                logger.info(f"Creating collection: {coll_name} (edge={is_edge})")
                self.db.create_collection(coll_name, edge=is_edge)
        
        # Check and create views
        required_views = [
            MEMORY_VIEW_NAME,
            COMPACTED_SUMMARIES_VIEW
        ]
        
        existing_views = [view['name'] for view in self.db.views()]
        
        for view_name in required_views:
            if view_name not in existing_views:
                if view_name == MEMORY_VIEW_NAME:
                    logger.info(f"Creating search view: {view_name}")
                    self.db.create_arangosearch_view(
                        view_name,
                        {
                            "links": {
                                MEMORY_MESSAGE_COLLECTION: {
                                    "includeAllFields": False,
                                    "fields": {
                                        "content": {
                                            "analyzers": ["text_en"]
                                        },
                                        EMBEDDING_FIELD: {
                                            "analyzers": ["identity"]
                                        }
                                    }
                                }
                            }
                        }
                    )
                elif view_name == COMPACTED_SUMMARIES_VIEW:
                    logger.info(f"Creating search view: {view_name}")
                    self.db.create_arangosearch_view(
                        view_name,
                        {
                            "links": {
                                COMPACTED_SUMMARIES_COLLECTION: {
                                    "includeAllFields": False,
                                    "fields": {
                                        "content": {
                                            "analyzers": ["text_en"]
                                        },
                                        EMBEDDING_FIELD: {
                                            "analyzers": ["identity"]
                                        }
                                    }
                                }
                            }
                        }
                    )
    
    def store_conversation(
        self,
        user_message: str,
        agent_response: str,
        conversation_id: Optional[str] = None,
        episode_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        point_in_time: Optional[datetime] = None,
        valid_at: Optional[datetime] = None,
        auto_embed: bool = True
    ) -> Dict[str, Any]:
        """
        Store a user-agent message exchange with temporal metadata.
        
        Args:
            user_message: The user's message text
            agent_response: The agent's response text
            conversation_id: ID to group related messages (generated if None)
            episode_id: Optional episode ID to group conversations
            metadata: Optional additional metadata
            point_in_time: Override timestamp (uses current time if None)
            valid_at: When the conversation actually occurred (defaults to point_in_time)
            auto_embed: Whether to automatically generate embeddings
            
        Returns:
            Dict with the created message IDs and metadata
        """
        # Generate conversation_id if not provided
        if not conversation_id:
            conversation_id = f"conv_{uuid.uuid4().hex[:10]}"
            
        # Use current time if point_in_time not provided
        if not point_in_time:
            point_in_time = datetime.now(timezone.utc)
            
        # Valid time defaults to point_in_time
        if not valid_at:
            valid_at = point_in_time
            
        # Process user message
        user_msg_doc = {
            TYPE_FIELD: MESSAGE_TYPE_USER,
            CONTENT_FIELD: user_message,
            CONVERSATION_ID_FIELD: conversation_id,
            TIMESTAMP_FIELD: point_in_time.isoformat(),
            METADATA_FIELD: metadata or {}
        }
        
        # Add episode_id if provided
        if episode_id:
            user_msg_doc[EPISODE_ID_FIELD] = episode_id
            
        # Add temporal fields
        user_msg_doc = ensure_temporal_fields(user_msg_doc, valid_at)
            
        # Generate embedding for user message if auto_embed
        if auto_embed:
            try:
                user_msg_doc[EMBEDDING_FIELD] = get_embedding(user_message)
            except Exception as e:
                logger.warning(f"Failed to generate embedding for user message: {e}")
        
        # Store user message
        try:
            user_result = self.db.collection(MEMORY_MESSAGE_COLLECTION).insert(user_msg_doc)
            user_msg_id = user_result["_id"]
        except Exception as e:
            logger.error(f"Failed to store user message: {e}")
            raise
            
        # Process agent response
        agent_msg_doc = {
            TYPE_FIELD: MESSAGE_TYPE_AGENT,
            CONTENT_FIELD: agent_response,
            CONVERSATION_ID_FIELD: conversation_id,
            TIMESTAMP_FIELD: point_in_time.isoformat(),
            METADATA_FIELD: metadata or {}
        }
        
        # Add episode_id if provided
        if episode_id:
            agent_msg_doc[EPISODE_ID_FIELD] = episode_id
            
        # Add temporal fields
        agent_msg_doc = ensure_temporal_fields(agent_msg_doc, valid_at)
            
        # Generate embedding for agent response if auto_embed
        if auto_embed:
            try:
                agent_msg_doc[EMBEDDING_FIELD] = get_embedding(agent_response)
            except Exception as e:
                logger.warning(f"Failed to generate embedding for agent response: {e}")
                
        # Store agent response
        try:
            agent_result = self.db.collection(MEMORY_MESSAGE_COLLECTION).insert(agent_msg_doc)
            agent_msg_id = agent_result["_id"]
        except Exception as e:
            logger.error(f"Failed to store agent message: {e}")
            # Try to clean up the user message
            try:
                self.db.collection(MEMORY_MESSAGE_COLLECTION).delete(user_msg_id)
            except:
                pass
            raise
            
        # Create relationship between messages
        edge_doc = {
            FROM_FIELD: user_msg_id,
            TO_FIELD: agent_msg_id,
            TYPE_FIELD: RELATIONSHIP_TYPE_NEXT,
            VALID_FROM_FIELD: point_in_time.isoformat(),
            VALID_TO_FIELD: "9999-12-31T23:59:59Z",  # Far future
            TIMESTAMP_FIELD: point_in_time.isoformat(),
            METADATA_FIELD: {
                CONVERSATION_ID_FIELD: conversation_id
            }
        }
        
        # Add episode_id to edge if provided
        if episode_id:
            edge_doc[METADATA_FIELD][EPISODE_ID_FIELD] = episode_id
            
        # Add temporal fields to edge
        edge_doc = ensure_temporal_fields(edge_doc, valid_at)
            
        try:
            edge_result = self.db.collection(MEMORY_EDGE_COLLECTION).insert(edge_doc)
        except Exception as e:
            logger.error(f"Failed to create message relationship: {e}")
            # Clean up the messages
            try:
                self.db.collection(MEMORY_MESSAGE_COLLECTION).delete(user_msg_id)
                self.db.collection(MEMORY_MESSAGE_COLLECTION).delete(agent_msg_id)
            except:
                pass
            raise
            
        return {
            "conversation_id": conversation_id,
            "episode_id": episode_id,
            "user_message_id": user_msg_id,
            "agent_message_id": agent_msg_id,
            "relationship_id": edge_result["_id"],
            "timestamp": point_in_time
        }
        
    def retrieve_messages(
        self,
        conversation_id: Optional[str] = None,
        episode_id: Optional[str] = None,
        limit: int = 100,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve message history for a conversation or episode.
        
        Args:
            conversation_id: ID of the conversation to retrieve
            episode_id: ID of the episode to retrieve
            limit: Maximum number of messages to return
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of message documents sorted by timestamp
        """
        if not conversation_id and not episode_id:
            raise ValueError("Either conversation_id or episode_id must be provided")
            
        # Build the query
        query = "FOR m IN @@collection"
        bind_vars = {"@collection": MEMORY_MESSAGE_COLLECTION}
        
        # Add filters
        filters = []
        if conversation_id:
            filters.append("m.conversation_id == @conversation_id")
            bind_vars["conversation_id"] = conversation_id
            
        if episode_id:
            filters.append("m.episode_id == @episode_id")
            bind_vars["episode_id"] = episode_id
            
        if filters:
            query += f" FILTER {' AND '.join(filters)}"
            
        # Add sorting and limit
        query += " SORT m.timestamp ASC LIMIT @limit"
        bind_vars["limit"] = limit
        
        # Project the desired fields
        if include_metadata:
            query += " RETURN m"
        else:
            query += " RETURN KEEP(m, '_id', '_key', 'type', 'content', 'conversation_id', 'episode_id', 'timestamp')"
            
        try:
            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}")
            raise
            
    def start_new_episode(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Start a new conversation episode.
        
        Args:
            name: Name/title of the episode
            description: Optional description
            metadata: Optional additional metadata
            timestamp: Override timestamp (uses current time if None)
            
        Returns:
            Newly created episode ID
        """
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
            
        episode_doc = {
            "type": "episode",
            "name": name,
            "description": description or "",
            "created_at": timestamp,
            "updated_at": timestamp,
            "metadata": metadata or {}
        }
        
        # Generate a predictable episode ID
        episode_id = f"ep_{uuid.uuid4().hex[:10]}"
        episode_doc["_key"] = episode_id
        
        try:
            result = self.db.collection(MEMORY_COLLECTION).insert(episode_doc)
            logger.info(f"Created new episode: {name} ({episode_id})")
            return episode_id
        except Exception as e:
            logger.error(f"Failed to create episode: {e}")
            raise
    
    # Add the compact_conversation method - delegate to the imported function
    def compact_conversation(self, **kwargs):
        """
        Create a compact representation of a conversation or episode.
        See full documentation in compact_conversation.py
        """
        return compact_conversation(self, **kwargs)
    
    def search_compactions(
        self,
        query_text: str,
        min_score: float = 0.75,
        top_n: int = 5,
        compaction_methods: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        episode_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for relevant compactions using semantic similarity.
        
        Args:
            query_text: The search query text
            min_score: Minimum similarity score (0.0-1.0)
            top_n: Maximum number of results to return
            compaction_methods: Filter by specific compaction methods
            conversation_id: Filter by conversation ID
            episode_id: Filter by episode ID
            
        Returns:
            Dict with search results and metadata
        """
        import time
        start_time = time.time()
        
        # Generate embedding for query
        query_embedding = get_embedding(query_text)
        
        # Build AQL query with filters
        aql = """
        FOR doc IN @@view
            SEARCH ANALYZER(
                VECTOR_DISTANCE(doc.@embedding_field, @query_vector) < @threshold,
                "identity"
            )
        """
        
        # Add filters if provided
        bind_vars = {
            "@view": COMPACTED_SUMMARIES_VIEW,
            "embedding_field": EMBEDDING_FIELD,
            "query_vector": query_embedding,
            "threshold": 1.0 - min_score  # Convert similarity to distance
        }
        
        filter_conditions = []
        
        if compaction_methods:
            filter_conditions.append("doc.compaction_method IN @methods")
            bind_vars["methods"] = compaction_methods
            
        if conversation_id:
            filter_conditions.append("doc.conversation_id == @conversation_id")
            bind_vars["conversation_id"] = conversation_id
            
        if episode_id:
            filter_conditions.append("doc.episode_id == @episode_id")
            bind_vars["episode_id"] = episode_id
        
        # Add filter conditions to query
        if filter_conditions:
            aql += " FILTER " + " AND ".join(filter_conditions)
        
        # Complete the query
        aql += """
            SORT VECTOR_DISTANCE(doc.@embedding_field, @query_vector) ASC
            LIMIT @top_n
            LET similarity_score = 1.0 - VECTOR_DISTANCE(doc.@embedding_field, @query_vector)
            RETURN MERGE(doc, { similarity_score: similarity_score })
        """
        bind_vars["top_n"] = top_n
        
        # Execute the query
        try:
            cursor = self.db.aql.execute(aql, bind_vars=bind_vars)
            results = list(cursor)
        except Exception as e:
            logger.error(f"Error searching compactions: {e}")
            raise
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        return {
            "results": results,
            "total": len(results),
            "time": elapsed_time,
            "query": query_text
        }
    
    def get_workflow_data(self, workflow_id: str) -> Dict[str, Any]:
        """
        Retrieve workflow tracking data for a specific workflow.
        
        Args:
            workflow_id: ID of the workflow to retrieve
            
        Returns:
            Dict with workflow tracking data or empty dict if not found
        """
        try:
            # This is a placeholder - in a real implementation, you would
            # retrieve the workflow data from a storage location
            # For now, we return a simple structure with basic info
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "elapsed_time": 0.0,
                "steps": []
            }
        except Exception as e:
            logger.error(f"Error retrieving workflow data: {e}")
            return {}
    
    def search(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        n_results: int = 10,
        point_in_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant memories using semantic similarity.
        
        Args:
            query: Search query text
            conversation_id: Optional filter by conversation ID
            n_results: Number of results to return
            point_in_time: Optional temporal filter - returns records valid at this time
            
        Returns:
            List of matching message documents with scores
        """
        try:
            # Generate embedding for the query
            query_embedding = get_embedding(query)
            
            # Check if we can use vector search (no filters)
            can_use_vector_search = (conversation_id is None and point_in_time is None)
            
            if can_use_vector_search:
                # Try APPROX_NEAR_COSINE for simple queries without filters
                logger.info("Using APPROX_NEAR_COSINE vector search")
                
                # Use collection directly for vector search
                aql = f"""
                FOR doc IN {MEMORY_MESSAGE_COLLECTION}
                    LET score = APPROX_NEAR_COSINE(doc.embedding, @query_embedding)
                    SORT score DESC
                    LIMIT @n_results
                    RETURN MERGE(doc, {{
                        score: score
                    }})
                """
                
                bind_vars = {
                    "query_embedding": query_embedding,
                    "n_results": n_results
                }
                
                try:
                    cursor = self.db.aql.execute(aql, bind_vars=bind_vars)
                    results = list(cursor)
                    
                    # Normalize scores from [-1, 1] to [0, 1] for consistency
                    for result in results:
                        result['score'] = (result['score'] + 1) / 2
                    
                    return results
                    
                except Exception as vector_error:
                    logger.warning(f"Vector search failed: {vector_error}, falling back to text search")
                    # Fall through to text search
            
            # Use text search for complex queries with filters
            # or as fallback if vector search fails
            logger.info("Using text search with BM25")
            aql = f"""
            FOR doc IN {MEMORY_VIEW_NAME}
                SEARCH ANALYZER(doc.content IN TOKENS(@query, "text_en"), "text_en")
            """
            
            # Add filters
            bind_vars = {
                "query": query
            }
            
            filters = []
            if conversation_id:
                filters.append("doc.conversation_id == @conversation_id")
                bind_vars["conversation_id"] = conversation_id
                
            if point_in_time:
                # Add temporal filters for bi-temporal model
                # Document must be:
                # 1. Created before or at the point in time
                # 2. Valid at the point in time
                # 3. Not invalidated before the point in time
                filters.append("doc.created_at <= @point_in_time")
                filters.append("doc.valid_at <= @point_in_time")
                filters.append("(doc.invalid_at == null OR doc.invalid_at > @point_in_time)")
                bind_vars["point_in_time"] = point_in_time.isoformat()
                
            if filters:
                aql += " FILTER " + " AND ".join(filters)
                
            # Sort by relevance and limit results
            aql += f"""
                SORT BM25(doc) DESC
                LIMIT @n_results
                RETURN MERGE(doc, {{
                    score: BM25(doc)
                }})
            """
            bind_vars["n_results"] = n_results
            
            # Execute query
            cursor = self.db.aql.execute(aql, bind_vars=bind_vars)
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise
    
    def get_conversation_history(
        self,
        conversation_id: str,
        n_results: int = 50,
        chronological: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation
            n_results: Maximum number of messages to return
            chronological: If True, sort oldest first; if False, newest first
            
        Returns:
            List of messages in the conversation
        """
        try:
            return self.retrieve_messages(
                conversation_id=conversation_id,
                limit=n_results,
                include_metadata=True
            )
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            raise
    
    def search_at_time(
        self,
        query: str,
        timestamp: datetime,
        search_type: str = "hybrid",
        conversation_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for messages valid at a specific point in time.
        
        Args:
            query: The search query
            timestamp: The point in time to search at
            search_type: Type of search (semantic, bm25, hybrid)
            conversation_id: Optional conversation ID filter
            limit: Maximum number of results
            
        Returns:
            List of search results valid at the specified time
        """
        # Use the point_in_time parameter of the search method
        return self.search(
            query=query,
            conversation_id=conversation_id,
            n_results=limit,
            point_in_time=timestamp
        )
    
    def get_conversation_at_time(
        self,
        conversation_id: str,
        timestamp: datetime,
        include_invalid: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get the state of a conversation at a specific point in time.
        
        Args:
            conversation_id: The conversation ID
            timestamp: The point in time to retrieve the conversation at
            include_invalid: Whether to include invalidated messages
            
        Returns:
            List of messages valid at the specified time
        """
        filters = {'conversation_id': conversation_id}
        
        results = point_in_time_query(
            self.db,
            MEMORY_MESSAGE_COLLECTION,
            timestamp,
            filters=filters
        )
        
        # Sort by timestamp for proper ordering
        results.sort(key=lambda x: x.get('timestamp', ''))
        
        return results
    
    def get_temporal_range(
        self,
        start_time: datetime,
        end_time: datetime,
        conversation_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages within a temporal range.
        
        Args:
            start_time: Start of the time range
            end_time: End of the time range
            conversation_id: Optional conversation ID filter
            filters: Additional filters to apply
            
        Returns:
            List of messages within the time range
        """
        # Build filters
        query_filters = filters or {}
        if conversation_id:
            query_filters['conversation_id'] = conversation_id
            
        results = temporal_range_query(
            self.db,
            MEMORY_MESSAGE_COLLECTION,
            start_time,
            end_time,
            filters=query_filters
        )
        
        # Sort by timestamp
        results.sort(key=lambda x: x.get('timestamp', ''))
        
        return results
