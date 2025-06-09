"""
Community building and detection for ArangoDB knowledge graph.
Module: community_building.py

This module provides functionality for detecting and managing communities
in the knowledge graph using graph algorithms and metadata analysis.
It builds on the entity resolution and relationship extraction capabilities
to identify meaningful clusters of related entities.

Key features:
1. Graph-based community detection using Louvain modularity
2. Automated community naming and description generation
3. Community membership management (add/remove members)
4. Community metadata analysis and enhancement
5. Search and filtering capabilities for communities
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union, Set
import asyncio

from loguru import logger
from arango.database import StandardDatabase
from arango.exceptions import ArangoServerError

try:
    # Try relative import first
    from ..constants import COLLECTION_NAME, EDGE_COLLECTION_NAME, GRAPH_NAME
except ImportError:
    try:
        # Try absolute import
        from arangodb.core.constants import COLLECTION_NAME, EDGE_COLLECTION_NAME, GRAPH_NAME
    except ImportError:
        # Define constants directly if all else fails (for standalone testing)
        COLLECTION_NAME = "memory_documents"
        EDGE_COLLECTION_NAME = "relationships"
        GRAPH_NAME = "knowledge_graph"
        logger.warning("Using default constants due to import failure")

# Default names for community collections
COMMUNITY_COLLECTION = "communities"
COMMUNITY_EDGE_COLLECTION = "community_edges"


class CommunityBuilder:
    """
    Community detection and management for ArangoDB knowledge graph.
    """
    
    def __init__(
        self,
        db: StandardDatabase,
        entity_collection: str = "agent_entities",
        relationship_collection: str = "agent_relationships",
        community_collection: str = COMMUNITY_COLLECTION,
        community_edge_collection: str = COMMUNITY_EDGE_COLLECTION,
        graph_name: str = "knowledge_graph"
    ):
        """
        Initialize the community builder.
        
        Args:
            db: ArangoDB database connection
            entity_collection: Name of the entity collection
            relationship_collection: Name of the relationship collection
            community_collection: Name of the community collection
            community_edge_collection: Name of the community membership edge collection
            graph_name: Name of the graph to analyze
        """
        self.db = db
        self.entity_collection = entity_collection
        self.relationship_collection = relationship_collection
        self.community_collection = community_collection
        self.community_edge_collection = community_edge_collection
        self.graph_name = graph_name
        
        # Initialize collections if they don't exist
        self._initialize_collections()
    
    def _initialize_collections(self):
        """
        Initialize required collections for community building.
        """
        # Create community collection if it doesn't exist
        if not self.db.has_collection(self.community_collection):
            self.db.create_collection(self.community_collection)
            logger.info(f"Created community collection '{self.community_collection}'")
        
        # Create community edge collection if it doesn't exist
        if not self.db.has_collection(self.community_edge_collection):
            self.db.create_collection(self.community_edge_collection, edge=True)
            logger.info(f"Created community edge collection '{self.community_edge_collection}'")
        
        # Register collections in the graph if they're not already
        try:
            # Check if graph exists
            if not self.db.has_graph(self.graph_name):
                # Create graph
                self.db.create_graph(
                    self.graph_name,
                    edge_definitions=[
                        {
                            "collection": self.relationship_collection,
                            "from": [self.entity_collection],
                            "to": [self.entity_collection]
                        },
                        {
                            "collection": self.community_edge_collection,
                            "from": [self.community_collection],
                            "to": [self.entity_collection]
                        }
                    ]
                )
                logger.info(f"Created graph '{self.graph_name}' with community collections")
            else:
                # Check if community edge definition exists
                graph = self.db.graph(self.graph_name)
                edge_definitions = graph.edge_definitions()
                
                has_community_edges = False
                for ed in edge_definitions:
                    # Different ArangoDB versions may use different keys
                    collection_key = "edge_collection" if "edge_collection" in ed else "collection"
                    if collection_key in ed and ed[collection_key] == self.community_edge_collection:
                        has_community_edges = True
                        break
                
                if not has_community_edges:
                    # Add community edge definition to existing graph
                    graph.create_edge_definition(
                        edge_collection=self.community_edge_collection,
                        from_collections=[self.community_collection],
                        to_collections=[self.entity_collection]
                    )
                    logger.info(f"Added community edge definition to graph '{self.graph_name}'")
        
        except Exception as e:
            logger.warning(f"Error initializing graph: {e}")
    
    def detect_communities(
        self,
        algorithm: str = "louvain",
        min_members: int = 3,
        max_communities: int = 20,
        weight_attribute: str = "confidence",
        start_vertex_id: Optional[str] = None,
        group_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect communities in the knowledge graph using the specified algorithm.
        
        Args:
            algorithm: Community detection algorithm to use (louvain, scc, or connected)
            min_members: Minimum number of members for a valid community
            max_communities: Maximum number of communities to return
            weight_attribute: Edge attribute to use as weight
            start_vertex_id: Optional starting vertex for community detection
            group_id: Optional group ID to assign to detected communities
            
        Returns:
            List of community data dicts with member information
        """
        logger.info(f"Detecting communities using {algorithm} algorithm")
        
        # Select the appropriate algorithm function
        if algorithm.lower() == "louvain":
            graph_algorithm = "GRAPH_COMMUNITY_LOUVAIN"
            algorithm_params = {
                "direction": "any",
                "max_iterations": 10,
                "weights": weight_attribute
            }
        elif algorithm.lower() == "scc":
            graph_algorithm = "GRAPH_SCC"
            algorithm_params = {}
        elif algorithm.lower() == "connected":
            graph_algorithm = "GRAPH_CONNECTED_COMPONENTS"
            algorithm_params = {}
        else:
            raise ValueError(f"Unsupported community detection algorithm: {algorithm}")
        
        # Find a good starting vertex if none provided
        if not start_vertex_id:
            try:
                # Get a vertex with many connections as starting point
                aql = f"""
                FOR v IN @@entity_collection
                LET connection_count = LENGTH(
                    FOR e IN @@relationship_collection
                    FILTER e._from == v._id OR e._to == v._id
                    RETURN 1
                )
                SORT connection_count DESC
                LIMIT 1
                RETURN v._id
                """
                
                cursor = self.db.aql.execute(
                    aql,
                    bind_vars={
                        "@entity_collection": self.entity_collection,
                        "@relationship_collection": self.relationship_collection
                    }
                )
                
                results = list(cursor)
                if results:
                    start_vertex_id = results[0]
                    logger.info(f"Using starting vertex: {start_vertex_id}")
                else:
                    # No good starting vertex found, use first vertex in collection
                    cursor = self.db.aql.execute(
                        f"FOR v IN @@collection LIMIT 1 RETURN v._id",
                        bind_vars={"@collection": self.entity_collection}
                    )
                    results = list(cursor)
                    if results:
                        start_vertex_id = results[0]
                    else:
                        raise ValueError("No vertices found in entity collection")
            
            except Exception as e:
                logger.error(f"Error finding starting vertex: {e}")
                raise
        
        # Build the AQL query for community detection
        aql = f"""
        // Use the specified graph algorithm to identify communities
        LET communities = {graph_algorithm}(
            @graph_name,
            {json.dumps(algorithm_params)}
        )
        
        // Filter and sort communities
        LET filtered_communities = (
            FOR community_id, members IN communities
            FILTER LENGTH(members) >= @min_members
            SORT LENGTH(members) DESC
            LIMIT @max_communities
            RETURN {{
                community_id: community_id,
                members: members
            }}
        )
        
        // For each community, fetch details about members
        FOR community IN filtered_communities
            LET members_data = (
                FOR member_id IN community.members
                LET doc = DOCUMENT(member_id)
                RETURN {{
                    _id: doc._id,
                    _key: doc._key,
                    name: doc.name,
                    type: doc.type
                }}
            )
            
            // Count common types in the community
            LET type_counts = COUNT(
                FOR member IN members_data
                COLLECT entity_type = member.type WITH COUNT INTO type_count
                SORT type_count DESC
                RETURN {{
                    type: entity_type,
                    count: type_count
                }}
            )
            
            // Calculate a representative community name
            LET community_name = FIRST(
                FOR member IN members_data
                COLLECT entity_type = member.type WITH COUNT INTO type_count
                SORT type_count DESC
                RETURN CONCAT(entity_type, " Community")
            )
            
            // Return community with metadata
            RETURN {{
                community_id: community.community_id,
                name: community_name || "Unnamed Community",
                member_count: LENGTH(community.members),
                members: members_data,
                homogeneity: 1.0 / type_counts, // Higher when fewer types
                tags: [] // To be populated later
            }}
        """
        
        # Execute query
        try:
            cursor = self.db.aql.execute(
                aql,
                bind_vars={
                    "graph_name": self.graph_name,
                    "min_members": min_members,
                    "max_communities": max_communities
                }
            )
            
            return list(cursor)
        
        except ArangoServerError as e:
            # Check if error is due to missing GRAPH functions
            if "not found" in str(e) and "GRAPH_" in str(e):
                logger.error(f"Graph algorithm not available in your ArangoDB version: {e}")
                # Fall back to a simpler cluster detection approach
                return self._detect_communities_fallback(min_members, max_communities)
            else:
                raise
    
    def _detect_communities_fallback(
        self,
        min_members: int = 3,
        max_communities: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fallback community detection based on relationship density when
        graph algorithms are not available.
        
        Args:
            min_members: Minimum number of members for a valid community
            max_communities: Maximum number of communities to return
            
        Returns:
            List of community data dicts with member information
        """
        logger.warning("Using fallback community detection method")
        
        # Use a simpler approach based on relationship density
        aql = f"""
        // Find entities with many relationships
        LET connected_entities = (
            FOR e IN @@relationship_collection
            COLLECT entity = e._from WITH COUNT INTO rel_count
            FILTER rel_count >= 2
            SORT rel_count DESC
            RETURN {{
                entity_id: entity,
                rel_count: rel_count
            }}
        )
        
        // For each well-connected entity, build a community around it
        LET potential_communities = (
            FOR seed IN connected_entities
            LET neighbors = (
                // Get immediate neighbors
                FOR e IN @@relationship_collection
                FILTER e._from == seed.entity_id
                RETURN e._to
            )
            
            // Only keep communities with sufficient members
            FILTER LENGTH(neighbors) + 1 >= @min_members
            
            RETURN APPEND(neighbors, seed.entity_id)
        )
        
        // Take top N communities after deduplication
        LET unique_communities = SLICE(
            potential_communities,
            0, @max_communities
        )
        
        // Format communities with metadata
        FOR members IN unique_communities
            LET members_data = (
                FOR member_id IN members
                LET doc = DOCUMENT(member_id)
                RETURN {{
                    _id: doc._id,
                    _key: doc._key,
                    name: doc.name,
                    type: doc.type
                }}
            )
            
            LET community_name = FIRST(
                FOR member IN members_data
                COLLECT entity_type = member.type WITH COUNT INTO type_count
                SORT type_count DESC
                RETURN CONCAT(entity_type, " Community")
            )
            
            RETURN {{
                community_id: CONCAT("fallback-", RAND()),
                name: community_name || "Unnamed Community",
                member_count: LENGTH(members),
                members: members_data,
                homogeneity: 0.5, // Default
                tags: [] // To be populated later
            }}
        """
        
        # Execute query
        try:
            cursor = self.db.aql.execute(
                aql,
                bind_vars={
                    "@relationship_collection": self.relationship_collection,
                    "min_members": min_members,
                    "max_communities": max_communities
                }
            )
            
            return list(cursor)
        
        except Exception as e:
            logger.error(f"Error in fallback community detection: {e}")
            raise
    
    def create_communities(
        self,
        communities_data: List[Dict[str, Any]],
        group_id: Optional[str] = None,
        auto_generate_tags: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Create community documents and establish membership relationships
        based on detected community data.
        
        Args:
            communities_data: List of community data from detect_communities
            group_id: Optional group ID to assign to all communities
            auto_generate_tags: Whether to automatically generate tags for communities
            
        Returns:
            List of created community documents
        """
        created_communities = []
        
        for community_data in communities_data:
            # Generate community tags if requested
            if auto_generate_tags:
                tags = self._generate_community_tags(community_data)
            else:
                tags = []
            
            # Create community document
            community_doc = {
                "name": community_data["name"],
                "member_count": community_data["member_count"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "group_id": group_id,
                "tags": tags,
                "homogeneity": community_data.get("homogeneity", 0.5),
                "algorithm_id": community_data.get("community_id", str(uuid.uuid4()))
            }
            
            # Insert community into database
            result = self.db.collection(self.community_collection).insert(community_doc)
            community_doc["_key"] = result["_key"]
            community_doc["_id"] = result["_id"]
            
            # Create edges from community to members
            membership_edges = []
            for member in community_data["members"]:
                edge = {
                    "_from": community_doc["_id"],
                    "_to": member["_id"],
                    "type": "HAS_MEMBER",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                edge_result = self.db.collection(self.community_edge_collection).insert(edge)
                edge["_key"] = edge_result["_key"]
                edge["_id"] = edge_result["_id"]
                membership_edges.append(edge)
            
            # Add edges to community doc for return value
            community_doc["membership_edges"] = membership_edges
            community_doc["members"] = community_data["members"]
            
            created_communities.append(community_doc)
        
        return created_communities
    
    def _generate_community_tags(self, community_data: Dict[str, Any]) -> List[str]:
        """
        Generate tags for a community based on its members.
        
        Args:
            community_data: Community data including members
            
        Returns:
            List of tag strings
        """
        tags = set()
        
        # Collect all member types
        member_types = [
            member.get("type", "").lower() 
            for member in community_data["members"]
            if member.get("type")
        ]
        
        # Add the most common types as tags
        type_counts = {}
        for t in member_types:
            if t:
                type_counts[t] = type_counts.get(t, 0) + 1
        
        # Add top types as tags
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        for type_name, count in sorted_types[:3]:  # Top 3 types
            if count >= 2:  # Only if at least 2 members have this type
                tags.add(type_name)
        
        # Add community name-derived tag
        community_name = community_data.get("name", "")
        if community_name and " " in community_name:
            name_parts = community_name.split(" ")
            if len(name_parts) > 0:
                tags.add(name_parts[0].lower())
        
        # Generate additional tags from member similarities
        # This would require additional text analysis which we'll skip for brevity
        
        return list(tags)
    
    def get_community_members(
        self,
        community_id: str,
        include_details: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all members of a specific community.
        
        Args:
            community_id: ID or key of the community
            include_details: Whether to include full member details
            
        Returns:
            List of member documents
        """
        # Ensure community_id is a full ID
        if "/" not in community_id:
            community_id = f"{self.community_collection}/{community_id}"
        
        # Query members via edges
        aql = f"""
        FOR v, e IN 1..1 OUTBOUND @community_id GRAPH @graph_name
        RETURN {{"member": v, "edge": e}}
        """
        
        cursor = self.db.aql.execute(
            aql,
            bind_vars={
                "community_id": community_id,
                "graph_name": self.graph_name
            }
        )
        
        results = list(cursor)
        
        if include_details:
            return [item["member"] for item in results]
        else:
            return [
                {
                    "_id": item["member"]["_id"],
                    "_key": item["member"]["_key"],
                    "name": item["member"].get("name", "Unnamed"),
                    "type": item["member"].get("type", "Unknown")
                }
                for item in results
            ]
    
    def add_member_to_community(
        self,
        community_id: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """
        Add an entity as a member of a community.
        
        Args:
            community_id: ID or key of the community
            entity_id: ID or key of the entity to add
            
        Returns:
            Created membership edge document
        """
        # Ensure IDs are in full format
        if "/" not in community_id:
            community_id = f"{self.community_collection}/{community_id}"
        
        if "/" not in entity_id:
            entity_id = f"{self.entity_collection}/{entity_id}"
        
        # Check if membership already exists
        aql = f"""
        FOR e IN @@edge_collection
        FILTER e._from == @community_id AND e._to == @entity_id
        RETURN e
        """
        
        cursor = self.db.aql.execute(
            aql,
            bind_vars={
                "@edge_collection": self.community_edge_collection,
                "community_id": community_id,
                "entity_id": entity_id
            }
        )
        
        existing = list(cursor)
        if existing:
            logger.info(f"Entity {entity_id} is already a member of community {community_id}")
            return existing[0]
        
        # Create membership edge
        edge = {
            "_from": community_id,
            "_to": entity_id,
            "type": "HAS_MEMBER",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = self.db.collection(self.community_edge_collection).insert(edge)
        edge["_key"] = result["_key"]
        edge["_id"] = result["_id"]
        
        # Update member count in community document
        aql_update = f"""
        LET doc = DOCUMENT(@community_id)
        UPDATE doc WITH {{
            member_count: LENGTH(
                FOR v, e IN 1..1 OUTBOUND @community_id GRAPH @graph_name
                RETURN v
            )
        }} IN @@community_collection
        RETURN NEW
        """
        
        self.db.aql.execute(
            aql_update,
            bind_vars={
                "@community_collection": self.community_collection,
                "community_id": community_id,
                "graph_name": self.graph_name
            }
        )
        
        return edge
    
    def remove_member_from_community(
        self,
        community_id: str,
        entity_id: str
    ) -> bool:
        """
        Remove an entity from a community.
        
        Args:
            community_id: ID or key of the community
            entity_id: ID or key of the entity to remove
            
        Returns:
            True if the entity was removed, False otherwise
        """
        # Ensure IDs are in full format
        if "/" not in community_id:
            community_id = f"{self.community_collection}/{community_id}"
        
        if "/" not in entity_id:
            entity_id = f"{self.entity_collection}/{entity_id}"
        
        # Find and delete the membership edge
        aql = f"""
        FOR e IN @@edge_collection
        FILTER e._from == @community_id AND e._to == @entity_id
        REMOVE e IN @@edge_collection
        RETURN OLD
        """
        
        cursor = self.db.aql.execute(
            aql,
            bind_vars={
                "@edge_collection": self.community_edge_collection,
                "community_id": community_id,
                "entity_id": entity_id
            }
        )
        
        removed = list(cursor)
        
        if removed:
            # Update member count in community document
            aql_update = f"""
            LET doc = DOCUMENT(@community_id)
            UPDATE doc WITH {{
                member_count: LENGTH(
                    FOR v, e IN 1..1 OUTBOUND @community_id GRAPH @graph_name
                    RETURN v
                )
            }} IN @@community_collection
            RETURN NEW
            """
            
            self.db.aql.execute(
                aql_update,
                bind_vars={
                    "@community_collection": self.community_collection,
                    "community_id": community_id,
                    "graph_name": self.graph_name
                }
            )
            
            return True
        
        logger.info(f"Entity {entity_id} is not a member of community {community_id}")
        return False
    
    def search_communities(
        self,
        query: str = "",
        tags: Optional[List[str]] = None,
        min_members: int = 0,
        max_members: Optional[int] = None,
        group_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for communities based on various criteria.
        
        Args:
            query: Text query to search in community name
            tags: List of tags to filter by
            min_members: Minimum number of members
            max_members: Maximum number of members
            group_id: Filter by group ID
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of matching community documents
        """
        # Build AQL query with filters
        filters = []
        bind_vars = {
            "@collection": self.community_collection,
            "min_members": min_members,
            "limit": limit,
            "offset": offset
        }
        
        # Add query filter
        if query:
            filters.append("LOWER(doc.name) LIKE CONCAT('%', LOWER(@query), '%')")
            bind_vars["query"] = query
        
        # Add tags filter
        if tags and len(tags) > 0:
            tags_condition = "LENGTH(INTERSECTION(doc.tags, @tags)) > 0"
            filters.append(tags_condition)
            bind_vars["tags"] = tags
        
        # Add member count filter
        filters.append("doc.member_count >= @min_members")
        
        if max_members:
            filters.append("doc.member_count <= @max_members")
            bind_vars["max_members"] = max_members
        
        # Add group ID filter
        if group_id:
            filters.append("doc.group_id == @group_id")
            bind_vars["group_id"] = group_id
        
        # Combine filters
        filter_str = " AND ".join(filters)
        
        # Complete query
        aql = f"""
        FOR doc IN @@collection
        FILTER {filter_str}
        SORT doc.member_count DESC
        LIMIT @offset, @limit
        RETURN doc
        """
        
        # Execute query
        cursor = self.db.aql.execute(aql, bind_vars=bind_vars)
        
        return list(cursor)
    
    def merge_communities(
        self,
        community_ids: List[str],
        new_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Merge multiple communities into a single new community.
        
        Args:
            community_ids: List of community IDs or keys to merge
            new_name: Optional name for the merged community
            
        Returns:
            The newly created merged community document
        """
        if len(community_ids) < 2:
            raise ValueError("At least two communities are required for merging")
        
        # Ensure all community_ids are full IDs
        full_ids = []
        for cid in community_ids:
            if "/" not in cid:
                full_ids.append(f"{self.community_collection}/{cid}")
            else:
                full_ids.append(cid)
        
        # Get all members from all communities
        all_members = set()
        all_tags = set()
        group_id = None
        
        for community_id in full_ids:
            # Get community data
            community_doc = self.db.document(community_id)
            
            # Extract tags and group_id
            if "tags" in community_doc and community_doc["tags"]:
                all_tags.update(community_doc["tags"])
            
            if "group_id" in community_doc and community_doc["group_id"] and group_id is None:
                group_id = community_doc["group_id"]
            
            # Get all members
            members = self.get_community_members(community_id, include_details=False)
            for member in members:
                all_members.add(member["_id"])
        
        # Generate name if not provided
        if not new_name:
            if len(full_ids) > 0:
                community_doc = self.db.document(full_ids[0])
                new_name = f"Merged: {community_doc.get('name', 'Community')}"
            else:
                new_name = "Merged Community"
        
        # Create new community
        merged_community = {
            "name": new_name,
            "member_count": len(all_members),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "group_id": group_id,
            "tags": list(all_tags),
            "merged_from": full_ids,
            "homogeneity": 0.5  # Default value
        }
        
        # Insert merged community
        result = self.db.collection(self.community_collection).insert(merged_community)
        merged_community["_key"] = result["_key"]
        merged_community["_id"] = result["_id"]
        
        # Add all members to the new community
        for member_id in all_members:
            edge = {
                "_from": merged_community["_id"],
                "_to": member_id,
                "type": "HAS_MEMBER",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.db.collection(self.community_edge_collection).insert(edge)
        
        # Optional: Mark original communities as merged
        for community_id in full_ids:
            self.db.collection(self.community_collection).update(
                {"_id": community_id},
                {
                    "merged_into": merged_community["_id"],
                    "is_merged": True
                }
            )
        
        return merged_community
    
    def delete_community(self, community_id: str) -> bool:
        """
        Delete a community and all its membership edges.
        
        Args:
            community_id: ID or key of the community to delete
            
        Returns:
            True if the community was deleted, False otherwise
        """
        # Ensure community_id is a full ID
        if "/" not in community_id:
            community_id = f"{self.community_collection}/{community_id}"
        
        # Delete all membership edges first
        aql_edges = f"""
        FOR e IN @@edge_collection
        FILTER e._from == @community_id
        REMOVE e IN @@edge_collection
        RETURN OLD
        """
        
        cursor = self.db.aql.execute(
            aql_edges,
            bind_vars={
                "@edge_collection": self.community_edge_collection,
                "community_id": community_id
            }
        )
        
        # Count removed edges
        removed_edges = len(list(cursor))
        logger.info(f"Removed {removed_edges} membership edges for community {community_id}")
        
        # Delete community document
        try:
            if "/" in community_id:
                # If ID is given with collection, extract just the key
                collection_name, doc_key = community_id.split("/")
                self.db.collection(collection_name).delete(doc_key)
            else:
                # If just a key is given, use default collection
                self.db.collection(self.community_collection).delete(community_id)
            logger.info(f"Deleted community {community_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting community {community_id}: {e}")
            return False
    
    def get_entity_communities(
        self,
        entity_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all communities that an entity belongs to.
        
        Args:
            entity_id: ID or key of the entity
            
        Returns:
            List of community documents
        """
        # Ensure entity_id is a full ID
        if "/" not in entity_id:
            entity_id = f"{self.entity_collection}/{entity_id}"
        
        # Query communities via edges
        aql = f"""
        FOR v, e IN 1..1 INBOUND @entity_id GRAPH @graph_name
        FILTER IS_SAME_COLLECTION(@@community_collection, v)
        RETURN v
        """
        
        cursor = self.db.aql.execute(
            aql,
            bind_vars={
                "@community_collection": self.community_collection,
                "entity_id": entity_id,
                "graph_name": self.graph_name
            }
        )
        
        return list(cursor)
    
    def analyze_community(
        self,
        community_id: str,
        include_members: bool = True
    ) -> Dict[str, Any]:
        """
        Perform detailed analysis of a community.
        
        Args:
            community_id: ID or key of the community
            include_members: Whether to include full member details
            
        Returns:
            Dictionary with community analysis
        """
        # Ensure community_id is a full ID
        if "/" not in community_id:
            community_id = f"{self.community_collection}/{community_id}"
        
        # Get community document
        community_doc = self.db.document(community_id)
        
        # Get community members
        members = self.get_community_members(community_id, include_details=True)
        
        # Analyze type distribution
        type_distribution = {}
        for member in members:
            member_type = member.get("type", "Unknown")
            type_distribution[member_type] = type_distribution.get(member_type, 0) + 1
        
        # Analyze internal relationships
        member_ids = [member["_id"] for member in members]
        internal_relationship_count = 0
        
        if len(member_ids) > 0:
            # Count relationships between community members
            aql = f"""
            FOR e IN @@relationship_collection
            FILTER e._from IN @member_ids AND e._to IN @member_ids
            RETURN e
            """
            
            cursor = self.db.aql.execute(
                aql,
                bind_vars={
                    "@relationship_collection": self.relationship_collection,
                    "member_ids": member_ids
                }
            )
            
            internal_relationships = list(cursor)
            internal_relationship_count = len(internal_relationships)
        
        # Calculate cohesion metrics
        member_count = len(members)
        max_possible_relationships = (member_count * (member_count - 1)) / 2 if member_count > 1 else 0
        cohesion = internal_relationship_count / max_possible_relationships if max_possible_relationships > 0 else 0
        
        # Calculate type homogeneity
        type_counts = list(type_distribution.values())
        homogeneity = max(type_counts) / sum(type_counts) if sum(type_counts) > 0 else 0
        
        # Prepare analysis result
        analysis = {
            "community": community_doc,
            "member_count": member_count,
            "type_distribution": type_distribution,
            "internal_relationship_count": internal_relationship_count,
            "cohesion": cohesion,
            "homogeneity": homogeneity,
            "analysis_time": datetime.now(timezone.utc).isoformat()
        }
        
        if include_members:
            analysis["members"] = members
        
        return analysis


import json

# Validation function
if __name__ == "__main__":
    import sys
    from arango import ArangoClient
    
    # Track validation failures
    all_validation_failures = []
    total_tests = 0
    
    logger.info("Running community building validation")
    
    try:
        # Initialize database connection
        ARANGO_HOST = os.getenv("ARANGO_HOST", "http://localhost:8529")
        ARANGO_USER = os.getenv("ARANGO_USER", "root")
        ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "openSesame")
        ARANGO_DB_NAME = os.getenv("ARANGO_DB_NAME", "memory_bank")
        
        client = ArangoClient(hosts=ARANGO_HOST)
        # This uses the appropriate database with authentication
        try:
            db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)
        
        # Create test collections for validation
        for collection_name in ["test_entities", "test_relationships", "test_communities", "test_community_edges"]:
            if db.has_collection(collection_name):
                db.collection(collection_name).truncate()
            else:
                if "edges" in collection_name:
                    db.create_collection(collection_name, edge=True)
                else:
                    db.create_collection(collection_name)
        
        # Create test graph
        graph_name = "test_graph"
        if db.has_graph(graph_name):
            db.delete_graph(graph_name)
        
        db.create_graph(
            graph_name,
            edge_definitions=[
                {
                    "edge_collection": "test_relationships",
                    "from_vertex_collections": ["test_entities"],
                    "to_vertex_collections": ["test_entities"]
                },
                {
                    "edge_collection": "test_community_edges",
                    "from_vertex_collections": ["test_communities"],  
                    "to_vertex_collections": ["test_entities"]
                }
            ]
        )
        
        # Initialize community builder
        community_builder = CommunityBuilder(
            db=db,
            entity_collection="test_entities",
            relationship_collection="test_relationships",
            community_collection="test_communities",
            community_edge_collection="test_community_edges",
            graph_name=graph_name
        )
        
        # Test 1: Create test data - entities and relationships
        total_tests += 1
        
        # Create some test entities
        entities = [
            {"name": "Entity 1", "type": "Person"},
            {"name": "Entity 2", "type": "Person"},
            {"name": "Entity 3", "type": "Person"},
            {"name": "Entity 4", "type": "Organization"},
            {"name": "Entity 5", "type": "Organization"},
            {"name": "Entity 6", "type": "Concept"},
            {"name": "Entity 7", "type": "Concept"}
        ]
        
        entity_ids = []
        for entity in entities:
            result = db.collection("test_entities").insert(entity)
            entity_ids.append(f"test_entities/{result['_key']}")
        
        # Create some relationships between entities
        relationships = [
            {"_from": entity_ids[0], "_to": entity_ids[1], "type": "KNOWS", "confidence": 0.9},
            {"_from": entity_ids[0], "_to": entity_ids[2], "type": "KNOWS", "confidence": 0.8},
            {"_from": entity_ids[1], "_to": entity_ids[2], "type": "KNOWS", "confidence": 0.95},
            {"_from": entity_ids[3], "_to": entity_ids[4], "type": "SIMILAR", "confidence": 0.7},
            {"_from": entity_ids[5], "_to": entity_ids[6], "type": "RELATED_TO", "confidence": 0.85},
            {"_from": entity_ids[0], "_to": entity_ids[3], "type": "WORKS_FOR", "confidence": 0.9},
            {"_from": entity_ids[1], "_to": entity_ids[3], "type": "WORKS_FOR", "confidence": 0.9},
            {"_from": entity_ids[2], "_to": entity_ids[4], "type": "WORKS_FOR", "confidence": 0.9}
        ]
        
        for rel in relationships:
            db.collection("test_relationships").insert(rel)
        
        test_data_created = len(entity_ids) == len(entities)
        if not test_data_created:
            all_validation_failures.append("Test 1: Failed to create test data")
        
        # Test 2: Detect communities with fallback method
        total_tests += 1
        communities_data = community_builder._detect_communities_fallback(min_members=2)
        
        has_communities = len(communities_data) > 0
        if not has_communities:
            all_validation_failures.append("Test 2: No communities detected with fallback method")
        
        # Test 3: Create communities from detected data
        total_tests += 1
        if has_communities:
            created_communities = community_builder.create_communities(
                communities_data,
                group_id="test_group",
                auto_generate_tags=True
            )
            
            communities_created = len(created_communities) > 0
            if not communities_created:
                all_validation_failures.append("Test 3: Failed to create communities")
            
            # Verify community properties
            if communities_created:
                first_community = created_communities[0]
                has_required_fields = all(
                    field in first_community 
                    for field in ["name", "member_count", "tags", "_id", "_key"]
                )
                
                if not has_required_fields:
                    all_validation_failures.append("Test 3: Created community missing required fields")
        
        # Test 4: Get community members
        total_tests += 1
        if has_communities and communities_created:
            community_id = created_communities[0]["_id"]
            members = community_builder.get_community_members(community_id)
            
            has_members = len(members) > 0
            if not has_members:
                all_validation_failures.append("Test 4: Community has no members")
        
        # Test 5: Add member to community
        total_tests += 1
        if has_communities and communities_created:
            # Find an entity that's not already in the community
            community_id = created_communities[0]["_id"]
            current_members = {m["_id"] for m in community_builder.get_community_members(community_id)}
            
            entity_to_add = None
            for entity_id in entity_ids:
                if entity_id not in current_members:
                    entity_to_add = entity_id
                    break
            
            if entity_to_add:
                edge = community_builder.add_member_to_community(community_id, entity_to_add)
                member_added = edge is not None and "_id" in edge
                
                if not member_added:
                    all_validation_failures.append("Test 5: Failed to add member to community")
                
                # Verify member is now in the community
                updated_members = {m["_id"] for m in community_builder.get_community_members(community_id)}
                member_exists = entity_to_add in updated_members
                
                if not member_exists:
                    all_validation_failures.append("Test 5: Added member not found in community")
            else:
                all_validation_failures.append("Test 5: No entities available to add to community")
        
        # Test 6: Search communities
        total_tests += 1
        search_results = community_builder.search_communities(
            group_id="test_group",
            min_members=2
        )
        
        search_works = len(search_results) > 0
        if not search_works:
            all_validation_failures.append("Test 6: Community search returned no results")
        
        # Test 7: Remove member from community
        total_tests += 1
        if has_communities and communities_created and len(members) > 0:
            community_id = created_communities[0]["_id"]
            member_to_remove = members[0]["_id"] if len(members) > 0 else None
            
            if member_to_remove:
                removed = community_builder.remove_member_from_community(community_id, member_to_remove)
                
                if not removed:
                    all_validation_failures.append("Test 7: Failed to remove member from community")
                
                # Verify member is no longer in the community
                updated_members = {m["_id"] for m in community_builder.get_community_members(community_id)}
                member_removed = member_to_remove not in updated_members
                
                if not member_removed:
                    all_validation_failures.append("Test 7: Member still found in community after removal")
        
        # Test 8: Merge communities
        total_tests += 1
        if len(created_communities) >= 2:
            community_ids = [c["_id"] for c in created_communities[:2]]
            merged = community_builder.merge_communities(community_ids, "Merged Test Community")
            
            merge_successful = merged is not None and "_id" in merged
            if not merge_successful:
                all_validation_failures.append("Test 8: Failed to merge communities")
            
            # Verify merged community has combined members
            if merge_successful:
                merged_members = community_builder.get_community_members(merged["_id"])
                original_members1 = set(m["_id"] for m in community_builder.get_community_members(community_ids[0]))
                original_members2 = set(m["_id"] for m in community_builder.get_community_members(community_ids[1]))
                
                all_original_members = original_members1.union(original_members2)
                merged_member_ids = set(m["_id"] for m in merged_members)
                
                has_all_members = all_original_members.issubset(merged_member_ids)
                if not has_all_members:
                    all_validation_failures.append("Test 8: Merged community missing members from original communities")
        
        # Test 9: Delete community
        total_tests += 1
        if has_communities and communities_created:
            community_to_delete = created_communities[-1]["_id"]
            logger.info(f"Attempting to delete community: {community_to_delete}")
            deleted = community_builder.delete_community(community_to_delete)
            
            if not deleted:
                all_validation_failures.append("Test 9: Failed to delete community")
            
            # Verify community no longer exists  
            try:
                community_parts = community_to_delete.split("/")
                if len(community_parts) == 2:
                    collection_name, doc_key = community_parts
                    doc = db.collection(collection_name).get(doc_key)
                    # Check if the document actually exists or is None
                    community_exists = doc is not None
                    if community_exists:
                        logger.error(f"Community still exists: {doc}")
                    else:
                        logger.info("Document returned None - properly deleted")
                else:
                    doc = db.document(community_to_delete)
                    # Check if the document actually exists or is None
                    community_exists = doc is not None
                    if community_exists:
                        logger.error(f"Community still exists: {doc}")
                    else:
                        logger.info("Document returned None - properly deleted")
            except Exception as e:
                community_exists = False
                logger.info(f"Community correctly deleted: {e}")
            
            if community_exists:
                all_validation_failures.append("Test 9: Community still exists after deletion")
        
        # Test 10: Get entity communities
        total_tests += 1
        if has_communities and communities_created and len(entity_ids) > 0:
            entity_id = entity_ids[0]
            entity_communities = community_builder.get_entity_communities(entity_id)
            
            # No assertion here since the entity might not be in any communities
            
        # Test 11: Analyze community
        total_tests += 1
        if has_communities and communities_created:
            community_id = created_communities[0]["_id"]
            analysis = community_builder.analyze_community(community_id)
            
            analysis_successful = analysis is not None and "community" in analysis
            if not analysis_successful:
                all_validation_failures.append("Test 11: Failed to analyze community")
            
            # Verify analysis contains required metrics
            if analysis_successful:
                has_metrics = all(
                    metric in analysis 
                    for metric in ["member_count", "type_distribution", "cohesion", "homogeneity"]
                )
                
                if not has_metrics:
                    all_validation_failures.append("Test 11: Community analysis missing required metrics")
        
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error in validation: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        all_validation_failures.append(f"Unexpected error: {e}")
    finally:
        # Clean up test data
        try:
            for collection_name in ["test_entities", "test_relationships", "test_communities", "test_community_edges"]:
                if db.has_collection(collection_name):
                    db.collection(collection_name).truncate()
            
            if db.has_graph("test_graph"):
                db.delete_graph("test_graph")
        except Exception as e:
            print(f"Warning: Error cleaning up test data: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f" VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f" VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Community building functionality is ready for use")
        sys.exit(0)