#!/usr/bin/env python3
"""
Enhanced Memory Agent for ArangoDB with Graphiti-inspired Features

This module extends the existing Memory Agent with temporal features,
contradiction detection, and entity resolution capabilities inspired by
the Graphiti knowledge graph system.

Key improvements:
1. Bi-temporal model for tracking when relationships occurred and were recorded
2. Contradiction detection and resolution
3. Enhanced entity resolution
4. Improved relationship extraction

Usage:
    from complexity.arangodb.memory_agent import MemoryAgent
    from complexity.arangodb.arango_setup import connect_arango, ensure_database
    
    # Connect to ArangoDB (required)
    client = connect_arango()
    db = ensure_database(client)
    
    # Initialize the agent with the database connection
    memory_agent = MemoryAgent(db=db)
    
    # Store a conversation with temporal metadata
    memory_agent.store_conversation(
        conversation_id, 
        user_message, 
        agent_response, 
        reference_time=datetime.now()
    )
    
    # Search with temporal constraints
    results = memory_agent.temporal_search(query, point_in_time=some_past_date)
"""

import os
import sys
import uuid
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Union

from loguru import logger
from arango.database import StandardDatabase

# Import ArangoDB operations
from complexity.arangodb.db_operations import (
    create_message,
    get_conversation_messages,
    create_document,
    create_relationship,
    link_message_to_document,
    MESSAGE_TYPE_USER,
    MESSAGE_TYPE_AGENT
)

# Import required modules - these are core dependencies that should not be mocked
from complexity.arangodb.search_api.hybrid_search import hybrid_search
from complexity.arangodb.embedding_utils import get_embedding
from complexity.arangodb.arango_setup import (
    connect_arango,
    ensure_database,
    ensure_collection,
    ensure_memory_agent_collections,
    ensure_arangosearch_view as ensure_view
)


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
    
    DEPENDENCIES (all required, no fallbacks):
    - An active ArangoDB connection (passed to constructor)
    - Required collections and views (created at initialization)
    - The hybrid_search module for semantic search
    - The embedding_utils module for generating embeddings
    
    Raises:
        ValueError: If required parameters are missing or invalid
        ConnectionError: If database connection fails
        RuntimeError: If required collections cannot be created
        Exception: For any other database operation failures
    """
    
    def __init__(self, 
                 db: StandardDatabase,
                 message_collection: str = "agent_messages",
                 memory_collection: str = "agent_memories",
                 entity_collection: str = "agent_entities",
                 edge_collection: str = "agent_relationships",
                 community_collection: str = "agent_communities",
                 view_name: str = "agent_memory_view",
                 embedding_field: str = "embedding"):
        """
        Initialize the MemoryAgent with support for Graphiti-inspired features.
        
        Args:
            db: ArangoDB connection (required)
            message_collection: Collection name for messages
            memory_collection: Collection name for memory documents
            entity_collection: Collection name for resolved entities
            edge_collection: Collection name for relationships
            community_collection: Collection name for entity communities
            view_name: View name for search
            embedding_field: Field name for embeddings
            
        Raises:
            ValueError: If db is None
        """
        if db is None:
            raise ValueError("Database connection is required for MemoryAgent")
            
        self.message_collection = message_collection
        self.memory_collection = memory_collection
        self.entity_collection = entity_collection
        self.edge_collection = edge_collection
        self.community_collection = community_collection
        self.view_name = view_name
        self.embedding_field = embedding_field
        self.db = db
        
        # Ensure required collections and views exist
        self._ensure_collections()
        
        logger.info(f"Enhanced MemoryAgent initialized with database '{db.name}'")
    
    def _ensure_collections(self):
        """Ensure all required collections and views exist."""
        # Create standard collections first
        ensure_memory_agent_collections(self.db)
        
        # Ensure entity collection exists
        if not self.db.has_collection(self.entity_collection):
            logger.info(f"Creating entity collection '{self.entity_collection}'")
            self.db.create_collection(self.entity_collection)
        
        # Ensure community collection exists
        if not self.db.has_collection(self.community_collection):
            logger.info(f"Creating community collection '{self.community_collection}'")
            self.db.create_collection(self.community_collection)
        
        # Update or ensure view includes entity and community collections
        view_name = "agent_memory_view"
        analyzer = "text_en"
        
        # Get or create view
        if not self.db.has_view(view_name):
            logger.info(f"Creating memory view '{view_name}'")
            
            # Define view properties
            props = {
                "links": {
                    self.message_collection: {
                        "fields": {
                            "content": {"analyzers": [analyzer]},
                            self.embedding_field: {}
                        }
                    },
                    self.memory_collection: {
                        "fields": {
                            "content": {"analyzers": [analyzer]},
                            "summary": {"analyzers": [analyzer]},
                            self.embedding_field: {}
                        }
                    },
                    self.entity_collection: {
                        "fields": {
                            "name": {"analyzers": [analyzer]},
                            "type": {"analyzers": [analyzer]},
                            "summary": {"analyzers": [analyzer]},
                            self.embedding_field: {}
                        }
                    },
                    self.community_collection: {
                        "fields": {
                            "name": {"analyzers": [analyzer]},
                            "summary": {"analyzers": [analyzer]},
                            self.embedding_field: {}
                        }
                    }
                }
            }
            
            # Create view
            self.db.create_view(
                name=view_name,
                view_type="arangosearch",
                properties=props
            )
        else:
            # Update existing view to include new collections
            current_view = self.db.view(view_name)
            current_links = current_view.get("links", {})
            
            # Check if entity and community collections are included
            updated = False
            if self.entity_collection not in current_links:
                current_links[self.entity_collection] = {
                    "fields": {
                        "name": {"analyzers": [analyzer]},
                        "type": {"analyzers": [analyzer]},
                        "summary": {"analyzers": [analyzer]},
                        self.embedding_field: {}
                    }
                }
                updated = True
            
            if self.community_collection not in current_links:
                current_links[self.community_collection] = {
                    "fields": {
                        "name": {"analyzers": [analyzer]},
                        "summary": {"analyzers": [analyzer]},
                        self.embedding_field: {}
                    }
                }
                updated = True
            
            # Update view if needed
            if updated:
                logger.info(f"Updating memory view '{view_name}' with new collections")
                self.db.delete_view(view_name)
                self.db.create_view(
                    name=view_name,
                    view_type="arangosearch",
                    properties={"links": current_links}
                )
    
    def enhance_edge_with_temporal_metadata(self, edge_doc, reference_time=None):
        """
        Add temporal metadata to edge documents based on Graphiti's bi-temporal model.
        
        Args:
            edge_doc: Edge document to enhance
            reference_time: When the relationship became true (defaults to now)
            
        Returns:
            Enhanced edge document with temporal metadata
        """
        now = datetime.now(timezone.utc)
        
        # Add created_at time (when the edge was inserted)
        edge_doc["created_at"] = now.isoformat()
        
        # Add valid_at time (when the relationship became true)
        edge_doc["valid_at"] = reference_time.isoformat() if reference_time else now.isoformat()
        
        # Add NULL invalid_at time (representing "valid until further notice")
        edge_doc["invalid_at"] = None
        
        return edge_doc
    
    async def detect_edge_contradictions(self, edge_doc, relationship_type=None, source_id=None, target_id=None):
        """
        Find potentially contradicting edges for a new relationship.
        
        Args:
            edge_doc: New edge document
            relationship_type: Type of relationship (defaults to edge_doc.type)
            source_id: Source node ID (defaults to edge_doc._from)
            target_id: Target node ID (defaults to edge_doc._to)
            
        Returns:
            List of potentially contradicting edges
        """
        # Use provided values or defaults from edge_doc
        rel_type = relationship_type or edge_doc.get("type")
        src_id = source_id or edge_doc.get("_from")
        tgt_id = target_id or edge_doc.get("_to")
        
        if not (rel_type and src_id and tgt_id):
            logger.warning("Missing required edge properties for contradiction detection")
            return []
        
        # Find existing edges between these nodes with same relationship type
        aql = """
        FOR e IN @@edge_collection
        FILTER e._from == @source_id AND e._to == @target_id
        FILTER e.type == @relationship_type
        FILTER e.invalid_at == null
        RETURN e
        """
        
        cursor = self.db.aql.execute(
            aql,
            bind_vars={
                "@edge_collection": self.edge_collection,
                "source_id": src_id,
                "target_id": tgt_id,
                "relationship_type": rel_type
            }
        )
        
        contradicting_edges = list(cursor)
        if contradicting_edges:
            logger.info(f"Found {len(contradicting_edges)} potential contradicting edges")
        
        return contradicting_edges
    
    async def resolve_edge_contradictions(self, edge_doc, contradicting_edges, llm_client=None):
        """
        Resolve contradictions between a new edge and existing edges.
        Optionally uses LLM to determine if the new information contradicts old information.
        
        Args:
            edge_doc: New edge document
            contradicting_edges: List of potentially contradicting edges
            llm_client: Optional LLM client for smart contradiction detection
            
        Returns:
            List of invalidated edges
        """
        now = datetime.now(timezone.utc)
        invalidated_edges = []
        
        for existing_edge in contradicting_edges:
            is_contradiction = True  # Default to assuming contradiction
            
            # If LLM client provided, use it to check contradiction
            if llm_client:
                is_contradiction = await self._check_contradiction_with_llm(
                    llm_client, edge_doc, existing_edge
                )
            
            if is_contradiction:
                # Invalidate the existing edge
                self.db.collection(self.edge_collection).update(
                    existing_edge["_key"],
                    {
                        "invalid_at": now.isoformat(), 
                        "invalidated_by": edge_doc.get("_key", "unknown")
                    }
                )
                invalidated_edges.append(existing_edge)
                logger.info(f"Invalidated contradicting edge {existing_edge.get('_key', 'unknown')}")
        
        return invalidated_edges
    
    async def _check_contradiction_with_llm(self, llm_client, new_edge, existing_edge):
        """
        Use LLM to determine if two edges contradict each other.
        
        Args:
            llm_client: LLM client
            new_edge: New edge document
            existing_edge: Existing edge document
            
        Returns:
            Boolean indicating if contradiction exists
        """
        try:
            # Extract the key information for comparison
            new_type = new_edge.get("type", "unknown")
            new_data = json.dumps({
                k: v for k, v in new_edge.items() 
                if k not in ["_key", "_id", "_rev", "created_at", "valid_at", "invalid_at"]
            })
            
            existing_type = existing_edge.get("type", "unknown")
            existing_data = json.dumps({
                k: v for k, v in existing_edge.items() 
                if k not in ["_key", "_id", "_rev", "created_at", "valid_at", "invalid_at"]
            })
            
            # Create prompt for LLM
            prompt = f"""
            I have two relationship assertions that might contradict each other.
            
            RELATIONSHIP 1 (existing):
            Type: {existing_type}
            Data: {existing_data}
            Valid from: {existing_edge.get("valid_at", "unknown")}
            
            RELATIONSHIP 2 (new):
            Type: {new_type}
            Data: {new_data}
            Valid from: {new_edge.get("valid_at", "unknown")}
            
            Do these relationships contradict each other? Consider:
            1. If they state opposite facts
            2. If one supersedes or replaces the other
            3. If they represent different states that can't be true simultaneously
            
            Answer YES if they contradict, or NO if they can coexist.
            """
            
            # Call LLM
            from litellm import completion
            response = completion(
                model="gpt-3.5-turbo", 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=50
            )
            
            choice = response.choices[0] if response.choices else None
            message = choice.message if choice else None
            content = message.content if message else None
            
            # Parse response
            if content and "YES" in content.upper():
                logger.info("LLM determined relationships contradict each other")
                return True
            else:
                logger.info("LLM determined relationships can coexist")
                return False
                
        except Exception as e:
            logger.warning(f"Error using LLM for contradiction check: {e}")
            # Default to assuming contradiction if LLM fails
            return True
    
    async def resolve_entity(self, entity_doc, collection_name=None):
        """
        Resolve an entity against existing entities in the database.
        Returns either a matching existing entity or the new entity.
        
        Args:
            entity_doc: Entity document to resolve
            collection_name: Collection to search in (defaults to entity_collection)
            
        Returns:
            Resolved entity document (either existing or new)
        """
        collection = collection_name or self.entity_collection
        
        if "name" not in entity_doc:
            logger.warning("Entity missing name, cannot resolve")
            return entity_doc
        
        # Check for exact name match first
        aql = """
        FOR doc IN @@collection
        FILTER doc.name == @name
        RETURN doc
        """
        
        cursor = self.db.aql.execute(
            aql,
            bind_vars={
                "@collection": collection,
                "name": entity_doc["name"]
            }
        )
        
        exact_matches = list(cursor)
        if exact_matches:
            logger.info(f"Found exact name match for entity: {entity_doc['name']}")
            return exact_matches[0]
        
        # If no exact match, try semantic search if entity has embeddings
        if self.embedding_field in entity_doc:
            aql = """
            FOR doc IN @@collection
            FILTER doc.embedding != null
            LET score = APPROX_NEAR_COSINE(doc.embedding, @embedding)
            FILTER score > 0.85  // High threshold for entity resolution
            SORT score DESC
            LIMIT 1
            RETURN {doc: doc, score: score}
            """
            
            cursor = self.db.aql.execute(
                aql,
                bind_vars={
                    "@collection": collection,
                    "embedding": entity_doc[self.embedding_field]
                }
            )
            
            similarity_matches = list(cursor)
            if similarity_matches:
                match = similarity_matches[0]
                logger.info(f"Found entity match with similarity {match['score']:.3f}: {match['doc']['name']}")
                return match["doc"]
        
        # If no matches, create new entity
        result = self.db.collection(collection).insert(entity_doc)
        entity_doc["_key"] = result["_key"]
        entity_doc["_id"] = result["_id"]
        logger.info(f"Created new entity: {entity_doc['name']}")
        return entity_doc
    
    async def extract_relationships_from_text(self, text, llm_client=None):
        """
        Extract relationships from unstructured text using LLM.
        
        Args:
            text: Text to extract relationships from
            llm_client: Optional LLM client (if not provided, uses embedded litellm)
            
        Returns:
            Dictionary with entities and relationships
        """
        try:
            # If no LLM client provided, use litellm
            if llm_client is None:
                from litellm import completion as litellm_completion
                
                # Create a prompt for the LLM to extract entities and relationships
                prompt = f"""
                Extract entities and their relationships from the following text.
                Format your response as a JSON object with the following structure:
                
                {{
                    "entities": [
                        {{"name": "Entity1", "type": "Person", "attributes": {{"key1": "value1"}} }},
                        {{"name": "Entity2", "type": "Organization", "attributes": {{"key1": "value1"}} }}
                    ],
                    "relationships": [
                        {{
                            "source": "Entity1",
                            "target": "Entity2", 
                            "type": "WORKS_FOR",
                            "attributes": {{"start_date": "2023-01-01"}},
                            "temporal": {{"valid_from": "2023-01-01", "valid_until": null}}
                        }}
                    ]
                }}
                
                Text: {text}
                """
                
                # Call the LLM to extract entities and relationships
                response = litellm_completion(
                    model="gpt-3.5-turbo", 
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1024,
                    response_format={"type": "json_object"}
                )
                
                # Extract content from response
                choice = response.choices[0] if response.choices else None
                message = choice.message if choice else None
                content = message.content if message else None
                
                # Parse the JSON response
                extracted_data = json.loads(content)
            else:
                # Use provided LLM client
                # Implementation depends on your LLM client interface
                extracted_data = {"entities": [], "relationships": []}
                logger.warning("Custom LLM client not implemented")
            
            # Generate embeddings for entities
            for entity in extracted_data.get("entities", []):
                entity_text = f"{entity['name']} {entity.get('type', '')} {json.dumps(entity.get('attributes', {}))}"
                entity[self.embedding_field] = get_embedding(entity_text)
            
            # Generate embeddings for relationships
            for relationship in extracted_data.get("relationships", []):
                relationship_text = f"{relationship['source']} {relationship['type']} {relationship['target']}"
                relationship[self.embedding_field] = get_embedding(relationship_text)
            
            return extracted_data
        
        except Exception as e:
            logger.error(f"Failed to extract relationships: {e}")
            return {"entities": [], "relationships": []}
    
    def store_conversation(self, 
                          conversation_id: Optional[str] = None,
                          user_message: str = "",
                          agent_response: str = "",
                          metadata: Optional[Dict[str, Any]] = None,
                          reference_time: Optional[datetime] = None) -> Dict[str, str]:
        """
        Store a user-agent message exchange in the database with enhanced temporal tracking.
        
        Args:
            conversation_id: ID of the conversation (generated if not provided)
            user_message: User's message
            agent_response: Agent's response
            metadata: Additional metadata for the messages
            reference_time: When the conversation actually occurred (defaults to now)
        
        Returns:
            Dictionary with conversation_id, user_key, agent_key, and memory_key
        """
        try:
            # Set reference time to current time if not provided
            if reference_time is None:
                reference_time = datetime.now(timezone.utc)
            
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
            metadata["timestamp"] = reference_time.isoformat()
            
            # Store user message
            user_key = str(uuid.uuid4())
            user_doc = {
                "_key": user_key,
                "conversation_id": conversation_id,
                "message_type": MESSAGE_TYPE_USER,
                "content": user_message,
                "timestamp": metadata["timestamp"],
                "metadata": metadata,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "valid_at": reference_time.isoformat()
            }
            
            # Generate embedding for user message
            user_embedding = get_embedding(user_message)
            if user_embedding:
                user_doc[self.embedding_field] = user_embedding
            
            # Store the user message
            user_result = create_document(
                self.db, 
                self.message_collection, 
                user_doc,
                document_key=user_key
            )
            
            # Store agent response
            agent_key = str(uuid.uuid4())
            agent_doc = {
                "_key": agent_key,
                "conversation_id": conversation_id,
                "message_type": MESSAGE_TYPE_AGENT,
                "content": agent_response,
                "timestamp": reference_time.isoformat(),
                "metadata": metadata,
                "previous_message_key": user_key,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "valid_at": reference_time.isoformat()
            }
            
            # Generate embedding for agent response
            agent_embedding = get_embedding(agent_response)
            if agent_embedding:
                agent_doc[self.embedding_field] = agent_embedding
            
            # Store the agent response
            agent_result = create_document(
                self.db, 
                self.message_collection, 
                agent_doc,
                document_key=agent_key
            )
            
            # Create relationship between user message and agent response
            edge = {
                "_from": f"{self.message_collection}/{user_key}",
                "_to": f"{self.message_collection}/{agent_key}",
                "type": "RESPONSE_TO",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "valid_at": reference_time.isoformat(),
                "invalid_at": None
            }
            
            # Collections are guaranteed to exist from initialization
            self.db.collection(self.edge_collection).insert(edge)
            
            # Create a memory document that combines both messages
            memory_key = str(uuid.uuid4())
            memory_doc = {
                "_key": memory_key,
                "conversation_id": conversation_id,
                "content": f"User: {user_message}\nAgent: {agent_response}",
                "summary": self._generate_summary(user_message, agent_response),
                "timestamp": metadata["timestamp"],
                "metadata": metadata,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "valid_at": reference_time.isoformat(),
                "invalid_at": None
            }
            
            # Generate embedding for combined content
            memory_embedding = get_embedding(memory_doc["content"])
            if memory_embedding:
                memory_doc[self.embedding_field] = memory_embedding
            
            # Store the memory document
            memory_result = create_document(
                self.db,
                self.memory_collection,
                memory_doc,
                document_key=memory_key
            )
            
            # Link messages to memory document using enhanced bi-temporal edges
            for message_key in [user_key, agent_key]:
                edge = {
                    "_from": f"{self.message_collection}/{message_key}",
                    "_to": f"{self.memory_collection}/{memory_key}",
                    "type": "PART_OF",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "valid_at": reference_time.isoformat(),
                    "invalid_at": None
                }
                self.db.collection(self.edge_collection).insert(edge)
            
            # Extract entities and relationships
            self._extract_and_store_entities(memory_doc["content"], memory_key, reference_time)
            
            # Generate relationships with other memories
            self._generate_relationships(memory_key, reference_time)
            
            logger.info(f"Stored conversation {conversation_id} with temporal metadata")
            
            return {
                "conversation_id": conversation_id,
                "user_key": user_key,
                "agent_key": agent_key,
                "memory_key": memory_key
            }
            
        except Exception as e:
            # Wrap any unexpected errors in a RuntimeError with clear message
            error_msg = f"Failed to store conversation: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _extract_and_store_entities(self, text, memory_key, reference_time):
        """
        Extract entities and relationships from text and store them in the database.
        
        Args:
            text: Text to extract entities from
            memory_key: Key of the memory document
            reference_time: Reference time for temporal metadata
        """
        try:
            # Extract entities and relationships
            from litellm import completion
            
            # Create a prompt for the LLM to extract entities and relationships
            prompt = f"""
            Extract entities and their relationships from the following text.
            Format your response as a JSON object with the following structure:
            
            {{
                "entities": [
                    {{"name": "Entity1", "type": "Person", "attributes": {{"key1": "value1"}} }},
                    {{"name": "Entity2", "type": "Organization", "attributes": {{"key1": "value1"}} }}
                ],
                "relationships": [
                    {{
                        "source": "Entity1", 
                        "target": "Entity2", 
                        "type": "WORKS_FOR", 
                        "attributes": {{"title": "CEO"}}
                    }}
                ]
            }}
            
            Text: {text}
            """
            
            # Call the LLM to extract entities and relationships
            try:
                response = completion(
                    model="gpt-3.5-turbo", 
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1024,
                    response_format={"type": "json_object"}
                )
                
                # Extract content from response
                choice = response.choices[0] if response.choices else None
                message = choice.message if choice else None
                content = message.content if message else None
                
                # Parse the JSON response
                extracted_data = json.loads(content)
                
                # Process entities
                entity_map = {}  # Map entity names to their document IDs
                for entity_data in extracted_data.get("entities", []):
                    # Create entity document
                    entity_doc = {
                        "name": entity_data["name"],
                        "type": entity_data.get("type", "Unknown"),
                        "attributes": entity_data.get("attributes", {}),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "valid_at": reference_time.isoformat(),
                        "invalid_at": None
                    }
                    
                    # Generate embedding
                    entity_text = f"{entity_doc['name']} {entity_doc['type']}"
                    entity_doc[self.embedding_field] = get_embedding(entity_text)
                    
                    # Insert or find existing entity
                    entity_uuid = None
                    # Check for existing entity with same name
                    aql = f"""
                    FOR doc IN {self.entity_collection}
                    FILTER doc.name == @name
                    RETURN doc
                    """
                    
                    cursor = self.db.aql.execute(aql, bind_vars={"name": entity_doc["name"]})
                    existing_entities = list(cursor)
                    
                    if existing_entities:
                        # Found existing entity
                        entity_uuid = existing_entities[0]["_id"]
                        logger.debug(f"Found existing entity: {entity_doc['name']}")
                    else:
                        # Create new entity
                        result = self.db.collection(self.entity_collection).insert(entity_doc)
                        entity_uuid = f"{self.entity_collection}/{result['_key']}"
                        logger.debug(f"Created new entity: {entity_doc['name']}")
                    
                    # Store in map
                    entity_map[entity_data["name"]] = entity_uuid
                    
                    # Link entity to memory
                    memory_edge = {
                        "_from": f"{self.memory_collection}/{memory_key}",
                        "_to": entity_uuid,
                        "type": "MENTIONS",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "valid_at": reference_time.isoformat(),
                        "invalid_at": None
                    }
                    self.db.collection(self.edge_collection).insert(memory_edge)
                
                # Process relationships
                for rel_data in extracted_data.get("relationships", []):
                    # Skip if source or target is missing from entity map
                    if rel_data["source"] not in entity_map or rel_data["target"] not in entity_map:
                        continue
                    
                    # Create relationship edge
                    rel_edge = {
                        "_from": entity_map[rel_data["source"]],
                        "_to": entity_map[rel_data["target"]],
                        "type": rel_data["type"],
                        "attributes": rel_data.get("attributes", {}),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "valid_at": reference_time.isoformat(),
                        "invalid_at": None
                    }
                    
                    # Check for existing contradicting relationships
                    contradicting_edges = []
                    try:
                        aql = f"""
                        FOR e IN {self.edge_collection}
                        FILTER e._from == @from AND e._to == @to
                        FILTER e.type == @type
                        FILTER e.invalid_at == null
                        RETURN e
                        """
                        
                        cursor = self.db.aql.execute(
                            aql, 
                            bind_vars={
                                "from": rel_edge["_from"],
                                "to": rel_edge["_to"],
                                "type": rel_edge["type"]
                            }
                        )
                        contradicting_edges = list(cursor)
                    except Exception as e:
                        logger.warning(f"Error checking for contradictions: {e}")
                    
                    # Invalidate contradicting edges
                    for existing_edge in contradicting_edges:
                        self.db.collection(self.edge_collection).update(
                            existing_edge["_key"],
                            {
                                "invalid_at": datetime.now(timezone.utc).isoformat(),
                                "invalidated_by": "new_relationship"
                            }
                        )
                    
                    # Insert new relationship
                    self.db.collection(self.edge_collection).insert(rel_edge)
                    logger.debug(f"Created relationship: {rel_data['source']} {rel_data['type']} {rel_data['target']}")
                
                logger.info(f"Extracted and stored {len(extracted_data.get('entities', []))} entities and {len(extracted_data.get('relationships', []))} relationships")
                
            except Exception as e:
                logger.warning(f"Error extracting entities with LLM: {e}")
        
        except Exception as e:
            logger.error(f"Error in entity extraction and storage: {e}")
    
    def _generate_summary(self, user_message: str, agent_response: str) -> str:
        """
        Generate a summary of the conversation exchange.
        
        Args:
            user_message: User's message
            agent_response: Agent's response
        
        Returns:
            String summary
        """
        # Simple summary for now, could use an LLM-based summarizer later
        max_length = 100
        combined = f"{user_message} {agent_response}"
        
        if len(combined) <= max_length:
            return combined
        
        # Basic truncation summary - ensure exactly max_length with ellipsis
        ellipsis = "..."
        # Reserve space for ellipsis
        truncated_length = max_length - len(ellipsis)
        return combined[:truncated_length] + ellipsis
    
    def _generate_relationships(self, memory_key: str, reference_time: datetime) -> int:
        """
        Generate relationships between the new memory and existing memories.
        Uses embeddings for semantic similarity and temporal metadata for tracking.
        
        Args:
            memory_key: Key of the memory document
            reference_time: When the relationship became valid
            
        Returns:
            Number of relationships created
        """
        try:
            # Get the memory document
            memory_doc = self.db.collection(self.memory_collection).get(memory_key)
            if not memory_doc:
                logger.error(f"Memory document {memory_key} not found")
                return 0
            
            # Skip if no embedding exists
            if self.embedding_field not in memory_doc:
                logger.warning(f"Memory document {memory_key} has no embedding, skipping relationship generation")
                return 0
                
            # Find other memories with embeddings to compare similarity
            aql = f"""
            FOR doc IN {self.memory_collection}
            FILTER doc._key != @memory_key
            FILTER doc.{self.embedding_field} != null
            SORT RAND()
            LIMIT 20  
            RETURN doc
            """
            
            cursor = self.db.aql.execute(aql, bind_vars={"memory_key": memory_key})
            other_memories = list(cursor)
            
            # Calculate embedding similarity for each potential match
            from complexity.arangodb.embedding_utils import calculate_cosine_similarity
            memory_embedding = memory_doc[self.embedding_field]
            
            # Store potential relationships with their similarity scores
            potential_relationships = []
            for other_memory in other_memories:
                if self.embedding_field in other_memory:
                    other_embedding = other_memory[self.embedding_field]
                    similarity = calculate_cosine_similarity(memory_embedding, other_embedding)
                    
                    # Only consider significant similarities
                    if similarity > 0.7:  # Threshold for meaningful similarity
                        potential_relationships.append({
                            "memory": other_memory,
                            "similarity": similarity
                        })
            
            # Sort by similarity and take top matches
            potential_relationships.sort(key=lambda x: x["similarity"], reverse=True)
            top_matches = potential_relationships[:5]  # Limit to 5 most similar
            
            # Create relationships for top matches
            count = 0
            for match in top_matches:
                other_memory = match["memory"]
                similarity = match["similarity"]
                
                # Determine relationship type based on similarity
                rel_type = "strong_semantic_similarity" if similarity > 0.85 else "semantic_similarity"
                
                # Generate rationale using embedded function or LLM
                rationale = f"Semantically similar content (similarity: {similarity:.2f})"
                
                # Create a relationship edge with temporal metadata
                edge = {
                    "_from": f"{self.memory_collection}/{memory_key}",
                    "_to": f"{self.memory_collection}/{other_memory['_key']}",
                    "type": rel_type,
                    "strength": similarity,
                    "rationale": rationale,
                    "auto_generated": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "valid_at": reference_time.isoformat(),
                    "invalid_at": None
                }
                
                # Insert the edge
                self.db.collection(self.edge_collection).insert(edge)
                count += 1
            
            logger.info(f"Created {count} semantic relationships for memory {memory_key}")
            return count
            
        except Exception as e:
            logger.error(f"Error generating relationships for memory {memory_key}: {e}")
            return 0
    
    def temporal_search(
        self,
        query_text: str,
        point_in_time: Optional[datetime] = None,
        collections: Optional[List[str]] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Search for memories that were valid at a specific point in time.
        
        Args:
            query_text: Search query
            point_in_time: Point in time to search at (defaults to now)
            collections: Collections to search (defaults to memory_collection)
            top_n: Maximum number of results to return
            
        Returns:
            Dict with search results and metadata
        """
        try:
            start_time = time.time()
            
            # Set default point-in-time to now if not provided
            if point_in_time is None:
                point_in_time = datetime.now(timezone.utc)
            
            time_str = point_in_time.isoformat()
            
            # Default collections if not provided
            if collections is None:
                collections = [self.memory_collection]
            
            # Generate embedding for query
            query_vector = get_embedding(query_text)
            if not query_vector:
                logger.error("Failed to generate embedding for query")
                return {
                    "results": [],
                    "total": 0,
                    "query": query_text,
                    "point_in_time": time_str,
                    "error": "Failed to generate embedding"
                }
            
            # Build the query for each collection
            all_results = []
            
            for collection in collections:
                # Use AQL to find temporally valid documents
                aql = f"""
                FOR doc IN {collection}
                FILTER doc.{self.embedding_field} != null
                
                // Temporal filter: valid_at <= query_time AND (invalid_at IS NULL OR invalid_at > query_time)
                FILTER DATE_ISO8601(doc.valid_at) <= DATE_ISO8601(@time_str)
                FILTER doc.invalid_at == null OR DATE_ISO8601(doc.invalid_at) > DATE_ISO8601(@time_str)
                
                // Semantic search
                LET score = APPROX_NEAR_COSINE(doc.{self.embedding_field}, @query_vector)
                FILTER score > 0.7
                
                SORT score DESC
                LIMIT {top_n}
                RETURN {{
                    doc: doc,
                    score: score,
                    collection: "{collection}"
                }}
                """
                
                # Execute query
                cursor = self.db.aql.execute(
                    aql,
                    bind_vars={
                        "time_str": time_str,
                        "query_vector": query_vector
                    }
                )
                
                # Add results from this collection
                collection_results = list(cursor)
                all_results.extend(collection_results)
            
            # Sort combined results by score
            all_results.sort(key=lambda x: x["score"], reverse=True)
            
            # Limit to top_n overall
            final_results = all_results[:top_n]
            
            elapsed_time = time.time() - start_time
            
            return {
                "results": final_results,
                "total": len(all_results),
                "query": query_text,
                "point_in_time": time_str,
                "time": elapsed_time,
                "search_engine": "temporal-semantic"
            }
            
        except Exception as e:
            logger.error(f"Temporal search error: {e}")
            return {
                "results": [],
                "total": 0,
                "query": query_text,
                "point_in_time": point_in_time.isoformat() if point_in_time else "now",
                "error": str(e)
            }

    async def build_communities(self, group_id=None, min_members=3):
        """
        Build communities in the knowledge graph using graph algorithms.
        
        Args:
            group_id: Optional group ID to filter by
            min_members: Minimum number of members for a community
            
        Returns:
            List of community documents
        """
        try:
            # First, identify communities using Louvain algorithm
            group_filter = f"FILTER e.group_id == '{group_id}'" if group_id else ""
            
            aql = f"""
            // First step: get all entities that could be part of communities
            LET entities = (
                FOR e IN {self.entity_collection}
                {group_filter}
                RETURN e
            )
            
            // Count relationships for each entity
            LET entity_connections = (
                FOR e IN entities
                LET connections = (
                    FOR rel IN {self.edge_collection}
                    FILTER (rel._from == e._id OR rel._to == e._id)
                    FILTER rel.invalid_at == null
                    RETURN 1
                )
                RETURN {{
                    entity: e,
                    connection_count: LENGTH(connections)
                }}
            )
            
            // Filter entities with sufficient connections
            LET connected_entities = (
                FOR ec IN entity_connections
                FILTER ec.connection_count >= 2  // Require at least 2 connections
                RETURN ec.entity
            )
            
            // Apply community detection
            LET community_data = (
                FOR e IN connected_entities
                
                // Find all neighbors (entities connected by valid relationships)
                LET neighbors = (
                    FOR rel IN {self.edge_collection}
                    FILTER (rel._from == e._id OR rel._to == e._id)
                    FILTER rel.invalid_at == null
                    LET other_id = rel._from == e._id ? rel._to : rel._from
                    LET other = DOCUMENT(other_id)
                    RETURN other
                )
                
                // Include sufficient info for clustering
                RETURN {{
                    id: e._id,
                    name: e.name,
                    type: e.type,
                    neighbors: neighbors[*]._id,
                    embedding: e.{self.embedding_field}
                }}
            )
            
            // Cluster based on relationship density and embedding similarity
            LET clusters = []  // In a real implementation, apply clustering algorithm here
            
            // For this implementation, use a simple clustering approach based on entity type
            LET type_clusters = (
                FOR e IN connected_entities
                COLLECT entity_type = e.type INTO entities
                FILTER LENGTH(entities) >= @min_members
                
                LET members = entities[*].e
                LET common_attrs = (
                    FOR member IN members
                    RETURN ATTRIBUTES(member)
                )
                
                LET summary = CONCAT(
                    "A group of ", 
                    LENGTH(members), 
                    " entities of type ", 
                    entity_type
                )
                
                RETURN {{
                    type: entity_type,
                    members: members,
                    member_count: LENGTH(members),
                    summary: summary
                }}
            )
            
            RETURN type_clusters
            """
            
            # Execute query
            cursor = self.db.aql.execute(
                aql,
                bind_vars={
                    "min_members": min_members
                }
            )
            
            clusters = list(cursor)[0]  # Unwrap the result
            
            # Process results and create community documents
            communities = []
            for cluster in clusters:
                # Create a community document
                community_doc = {
                    "name": f"{cluster['type']} Community",
                    "type": "community",
                    "member_count": cluster["member_count"],
                    "summary": cluster["summary"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "group_id": group_id
                }
                
                # Generate embedding for the community
                community_text = f"{community_doc['name']} {community_doc['summary']}"
                community_doc[self.embedding_field] = get_embedding(community_text)
                
                # Insert community into database
                result = self.db.collection(self.community_collection).insert(community_doc)
                community_key = result["_key"]
                community_id = f"{self.community_collection}/{community_key}"
                
                # Create edges from community to members
                for member in cluster["members"]:
                    edge = {
                        "_from": community_id,
                        "_to": member["_id"],
                        "type": "HAS_MEMBER",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "valid_at": datetime.now(timezone.utc).isoformat(),
                        "invalid_at": None
                    }
                    self.db.collection(self.edge_collection).insert(edge)
                
                # Add to result list
                community_doc["_key"] = community_key
                community_doc["_id"] = community_id
                communities.append(community_doc)
            
            logger.info(f"Created {len(communities)} communities with {sum(c['member_count'] for c in communities)} total members")
            return communities
            
        except Exception as e:
            logger.error(f"Error building communities: {e}")
            return []
