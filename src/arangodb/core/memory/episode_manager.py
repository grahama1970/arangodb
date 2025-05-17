"""
Episode Manager for ArangoDB Memory System

This module provides episode management functionality for grouping conversations
and interactions into temporal contexts. Episodes enable the memory system to
maintain conversation continuity and retrieve context-aware information.

Sample input:
    episode_data = {
        "name": "Discussion about Python frameworks",
        "description": "User asked about Django vs Flask comparison",
        "start_time": datetime.now(),
        "metadata": {"user_id": "user123", "session_id": "sess456"}
    }

Expected output:
    episode = {
        "_key": "episode_789",
        "name": "Discussion about Python frameworks",
        "description": "User asked about Django vs Flask comparison",
        "start_time": "2024-01-17T10:00:00Z",
        "end_time": None,
        "entity_count": 0,
        "relationship_count": 0,
        "metadata": {"user_id": "user123", "session_id": "sess456"},
        "created_at": "2024-01-17T10:00:00Z"
    }
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, DocumentInsertError

# Collection names
EPISODES_COLLECTION = "agent_episodes"
EPISODE_ENTITIES_COLLECTION = "agent_episode_entities"
EPISODE_RELATIONSHIPS_COLLECTION = "agent_episode_relationships"


class EpisodeManager:
    """Manages episodes for temporal grouping of conversations and interactions."""
    
    def __init__(self, db: StandardDatabase):
        """Initialize the Episode Manager with database connection.
        
        Args:
            db: ArangoDB database instance
        """
        self.db = db
        self._ensure_collections()
        self._ensure_indexes()
    
    def _ensure_collections(self):
        """Ensure required collections exist."""
        collections = [
            EPISODES_COLLECTION,
            EPISODE_ENTITIES_COLLECTION,
            EPISODE_RELATIONSHIPS_COLLECTION
        ]
        
        for collection_name in collections:
            if not self.db.has_collection(collection_name):
                self.db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
    
    def _ensure_indexes(self):
        """Ensure proper indexes for efficient queries."""
        # Episode indexes
        episodes = self.db.collection(EPISODES_COLLECTION)
        episodes.add_persistent_index(fields=["start_time"], unique=False)
        episodes.add_persistent_index(fields=["end_time"], unique=False)
        episodes.add_persistent_index(fields=["metadata.user_id"], unique=False)
        
        # Episode-entity link indexes
        episode_entities = self.db.collection(EPISODE_ENTITIES_COLLECTION)
        episode_entities.add_persistent_index(fields=["episode_id"], unique=False)
        episode_entities.add_persistent_index(fields=["entity_id"], unique=False)
        episode_entities.add_persistent_index(
            fields=["episode_id", "entity_id"], 
            unique=True
        )
        
        # Episode-relationship link indexes
        episode_rels = self.db.collection(EPISODE_RELATIONSHIPS_COLLECTION)
        episode_rels.add_persistent_index(fields=["episode_id"], unique=False)
        episode_rels.add_persistent_index(fields=["relationship_id"], unique=False)
    
    def create_episode(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a new episode.
        
        Args:
            name: Name/title of the episode
            description: Optional description
            metadata: Optional metadata (user_id, session_id, etc.)
            start_time: Optional start time (defaults to now)
        
        Returns:
            Created episode document
        """
        episode_key = f"episode_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        episode_doc = {
            "_key": episode_key,
            "name": name,
            "description": description or "",
            "start_time": (start_time or now).isoformat(),
            "end_time": None,
            "entity_count": 0,
            "relationship_count": 0,
            "metadata": metadata or {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        try:
            result = self.db.collection(EPISODES_COLLECTION).insert(episode_doc)
            episode_doc["_id"] = result["_id"]
            episode_doc["_rev"] = result["_rev"]
            logger.info(f"Created episode: {episode_key}")
            return episode_doc
        except DocumentInsertError as e:
            logger.error(f"Failed to create episode: {e}")
            raise
    
    def end_episode(self, episode_id: str, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Mark an episode as ended.
        
        Args:
            episode_id: Episode ID (can be _key or _id)
            end_time: Optional end time (defaults to now)
        
        Returns:
            Updated episode document
        """
        # Handle both _key and _id formats
        episode_key = episode_id.split("/")[-1] if "/" in episode_id else episode_id
        
        update_doc = {
            "end_time": (end_time or datetime.now(timezone.utc)).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            result = self.db.collection(EPISODES_COLLECTION).update(
                {"_key": episode_key},
                update_doc,
                return_new=True
            )
            logger.info(f"Ended episode: {episode_key}")
            return result["new"]
        except AQLQueryExecuteError as e:
            logger.error(f"Failed to end episode: {e}")
            raise
    
    def link_entity_to_episode(self, episode_id: str, entity_id: str) -> bool:
        """Link an entity to an episode.
        
        Args:
            episode_id: Episode ID
            entity_id: Entity ID
        
        Returns:
            True if linked successfully
        """
        episode_key = episode_id.split("/")[-1] if "/" in episode_id else episode_id
        entity_key = entity_id.split("/")[-1] if "/" in entity_id else entity_id
        
        link_doc = {
            "_key": f"{episode_key}_{entity_key}",
            "episode_id": f"{EPISODES_COLLECTION}/{episode_key}",
            "entity_id": entity_id,
            "linked_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.db.collection(EPISODE_ENTITIES_COLLECTION).insert(link_doc)
            
            # Update episode entity count
            self._increment_episode_count(episode_key, "entity_count")
            
            logger.debug(f"Linked entity {entity_key} to episode {episode_key}")
            return True
        except DocumentInsertError:
            # Link might already exist
            return True
        except Exception as e:
            logger.error(f"Failed to link entity to episode: {e}")
            return False
    
    def link_relationship_to_episode(self, episode_id: str, relationship_id: str) -> bool:
        """Link a relationship to an episode.
        
        Args:
            episode_id: Episode ID
            relationship_id: Relationship ID
        
        Returns:
            True if linked successfully
        """
        episode_key = episode_id.split("/")[-1] if "/" in episode_id else episode_id
        rel_key = relationship_id.split("/")[-1] if "/" in relationship_id else relationship_id
        
        link_doc = {
            "_key": f"{episode_key}_{rel_key}",
            "episode_id": f"{EPISODES_COLLECTION}/{episode_key}",
            "relationship_id": relationship_id,
            "linked_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.db.collection(EPISODE_RELATIONSHIPS_COLLECTION).insert(link_doc)
            
            # Update episode relationship count
            self._increment_episode_count(episode_key, "relationship_count")
            
            logger.debug(f"Linked relationship {rel_key} to episode {episode_key}")
            return True
        except DocumentInsertError:
            # Link might already exist
            return True
        except Exception as e:
            logger.error(f"Failed to link relationship to episode: {e}")
            return False
    
    def _increment_episode_count(self, episode_key: str, count_field: str):
        """Increment a count field in an episode document."""
        query = """
        FOR episode IN @@collection
            FILTER episode._key == @key
            UPDATE episode WITH {
                @field: episode[@field] + 1,
                updated_at: @updated_at
            } IN @@collection
        """
        
        try:
            self.db.aql.execute(
                query,
                bind_vars={
                    "@collection": EPISODES_COLLECTION,
                    "key": episode_key,
                    "field": count_field,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            )
        except AQLQueryExecuteError as e:
            logger.error(f"Failed to increment {count_field}: {e}")
    
    def get_episode(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """Get an episode by ID.
        
        Args:
            episode_id: Episode ID (_key or _id)
        
        Returns:
            Episode document or None
        """
        episode_key = episode_id.split("/")[-1] if "/" in episode_id else episode_id
        
        try:
            episode = self.db.collection(EPISODES_COLLECTION).get(episode_key)
            return episode
        except Exception:
            return None
    
    def get_active_episodes(
        self, 
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get active (not ended) episodes.
        
        Args:
            user_id: Optional user ID filter
            limit: Maximum number of episodes to return
        
        Returns:
            List of active episodes
        """
        query = """
        FOR episode IN @@collection
            FILTER episode.end_time == null
            {}
            SORT episode.start_time DESC
            LIMIT @limit
            RETURN episode
        """
        
        user_filter = "FILTER episode.metadata.user_id == @user_id" if user_id else ""
        query = query.format(user_filter)
        
        bind_vars = {
            "@collection": EPISODES_COLLECTION,
            "limit": limit
        }
        
        if user_id:
            bind_vars["user_id"] = user_id
        
        try:
            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            return list(cursor)
        except AQLQueryExecuteError as e:
            logger.error(f"Failed to get active episodes: {e}")
            return []
    
    def search_episodes(
        self,
        query_text: str,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search episodes by text and filters.
        
        Args:
            query_text: Text to search in name and description
            time_range: Optional (start, end) datetime tuple
            user_id: Optional user ID filter
            limit: Maximum number of results
        
        Returns:
            List of matching episodes
        """
        # Build filter conditions
        filters = []
        bind_vars = {
            "@collection": EPISODES_COLLECTION,
            "limit": limit
        }
        
        # Text search
        if query_text:
            filters.append("""
                (CONTAINS(LOWER(episode.name), LOWER(@query_text)) OR
                 CONTAINS(LOWER(episode.description), LOWER(@query_text)))
            """)
            bind_vars["query_text"] = query_text
        
        # Time range filter
        if time_range:
            start_time, end_time = time_range
            filters.append("episode.start_time >= @start_time")
            filters.append("(episode.end_time <= @end_time OR episode.end_time == null)")
            bind_vars["start_time"] = start_time.isoformat()
            bind_vars["end_time"] = end_time.isoformat()
        
        # User filter
        if user_id:
            filters.append("episode.metadata.user_id == @user_id")
            bind_vars["user_id"] = user_id
        
        # Build query
        filter_clause = f"FILTER {' AND '.join(filters)}" if filters else ""
        
        query = f"""
        FOR episode IN @@collection
            {filter_clause}
            SORT episode.start_time DESC
            LIMIT @limit
            RETURN episode
        """
        
        try:
            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            return list(cursor)
        except AQLQueryExecuteError as e:
            logger.error(f"Failed to search episodes: {e}")
            return []
    
    def get_episode_entities(self, episode_id: str) -> List[Dict[str, Any]]:
        """Get all entities linked to an episode.
        
        Args:
            episode_id: Episode ID
        
        Returns:
            List of entity documents
        """
        episode_key = episode_id.split("/")[-1] if "/" in episode_id else episode_id
        
        query = """
        FOR link IN @@link_collection
            FILTER link.episode_id == @episode_id
            FOR entity IN agent_entities
                FILTER entity._id == link.entity_id
                RETURN entity
        """
        
        bind_vars = {
            "@link_collection": EPISODE_ENTITIES_COLLECTION,
            "episode_id": f"{EPISODES_COLLECTION}/{episode_key}"
        }
        
        try:
            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            return list(cursor)
        except AQLQueryExecuteError as e:
            logger.error(f"Failed to get episode entities: {e}")
            return []
    
    def get_episode_relationships(self, episode_id: str) -> List[Dict[str, Any]]:
        """Get all relationships linked to an episode.
        
        Args:
            episode_id: Episode ID
        
        Returns:
            List of relationship documents
        """
        episode_key = episode_id.split("/")[-1] if "/" in episode_id else episode_id
        
        query = """
        FOR link IN @@link_collection
            FILTER link.episode_id == @episode_id
            FOR rel IN agent_relationships
                FILTER rel._id == link.relationship_id
                RETURN rel
        """
        
        bind_vars = {
            "@link_collection": EPISODE_RELATIONSHIPS_COLLECTION,
            "episode_id": f"{EPISODES_COLLECTION}/{episode_key}"
        }
        
        try:
            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            return list(cursor)
        except AQLQueryExecuteError as e:
            logger.error(f"Failed to get episode relationships: {e}")
            return []
    
    def delete_episode(self, episode_id: str) -> bool:
        """Delete an episode and its links.
        
        Args:
            episode_id: Episode ID
        
        Returns:
            True if deleted successfully
        """
        episode_key = episode_id.split("/")[-1] if "/" in episode_id else episode_id
        episode_full_id = f"{EPISODES_COLLECTION}/{episode_key}"
        
        try:
            # Delete entity links
            self.db.aql.execute(
                "FOR link IN @@collection FILTER link.episode_id == @episode_id REMOVE link IN @@collection",
                bind_vars={
                    "@collection": EPISODE_ENTITIES_COLLECTION,
                    "episode_id": episode_full_id
                }
            )
            
            # Delete relationship links
            self.db.aql.execute(
                "FOR link IN @@collection FILTER link.episode_id == @episode_id REMOVE link IN @@collection",
                bind_vars={
                    "@collection": EPISODE_RELATIONSHIPS_COLLECTION,
                    "episode_id": episode_full_id
                }
            )
            
            # Delete episode
            self.db.collection(EPISODES_COLLECTION).delete(episode_key)
            
            logger.info(f"Deleted episode: {episode_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete episode: {e}")
            return False


# Validation and testing
if __name__ == "__main__":
    from arangodb.core.arango_setup import connect_arango, ensure_database
    
    # Connect to database
    client = connect_arango()
    db = ensure_database(client)
    
    # Initialize episode manager
    episode_manager = EpisodeManager(db)
    
    # Test episode creation
    episode = episode_manager.create_episode(
        name="Test Episode",
        description="Testing episode functionality",
        metadata={"user_id": "test_user", "session_id": "test_session"}
    )
    
    print("Created episode:")
    print(json.dumps(episode, indent=2))
    
    # Test getting active episodes
    active_episodes = episode_manager.get_active_episodes()
    print(f"\nActive episodes: {len(active_episodes)}")
    
    # Test episode search
    search_results = episode_manager.search_episodes("Test")
    print(f"\nSearch results: {len(search_results)}")
    
    # Test ending episode
    ended_episode = episode_manager.end_episode(episode["_key"])
    print("\nEnded episode:")
    print(json.dumps(ended_episode, indent=2))
    
    # Clean up
    episode_manager.delete_episode(episode["_key"])
    print("\nDeleted test episode")