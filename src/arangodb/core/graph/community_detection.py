"""
Community detection algorithms for entity graph analysis.

This module implements community detection using the Louvain algorithm to automatically
group related entities in the knowledge graph. Communities help organize and understand
the structure of stored knowledge.

External Documentation:
- Louvain Algorithm: https://en.wikipedia.org/wiki/Louvain_method
- ArangoDB Graph Algorithms: https://www.arangodb.com/docs/stable/graphs.html

Sample Input:
{
    "entities": ["Python", "Django", "Flask", "PostgreSQL"],
    "relationships": [
        {"from": "Python", "to": "Django", "type": "framework_for"},
        {"from": "Python", "to": "Flask", "type": "framework_for"}
    ]
}

Expected Output:
{
    "communities": {
        "community_001": ["Python", "Django", "Flask"],
        "community_002": ["PostgreSQL"]
    },
    "modularity": 0.82
}
"""

from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
import uuid

from arango.database import Database
from arango.exceptions import ArangoError
from loguru import logger

# Use the correct collection names for the Graphiti-compatible implementation
ENTITIES_COLLECTION = "agent_entities"
RELATIONSHIPS_COLLECTION = "agent_relationships"


class CommunityDetector:
    """Detect and manage communities in entity graphs."""
    
    def __init__(self, db: Database):
        """Initialize community detector with database connection."""
        self.db = db
        self.entities_collection = ENTITIES_COLLECTION  # "agent_entities"
        self.relationships_collection = RELATIONSHIPS_COLLECTION  # "agent_relationships"  
        self.communities_collection = "agent_communities"
        
        # Ensure communities collection exists
        self._ensure_communities_collection()
    
    def _ensure_communities_collection(self):
        """Create communities collection if it doesn't exist."""
        if not self.db.has_collection(self.communities_collection):
            self.db.create_collection(self.communities_collection)
            logger.info(f"Created collection: {self.communities_collection}")
    
    def detect_communities(self, min_size: int = 3, resolution: float = 1.0) -> Dict[str, str]:
        """
        Detect communities using simplified Louvain algorithm.
        
        Args:
            min_size: Minimum community size to keep
            resolution: Resolution parameter (higher = more communities)
            
        Returns:
            Mapping of entity_id to community_id
        """
        logger.info(f"Starting community detection with min_size={min_size}, resolution={resolution}")
        
        # Get graph data
        entities = self._get_all_entities()
        relationships = self._get_all_relationships()
        
        if not entities:
            logger.warning("No entities found for community detection")
            return {}
        
        # Build adjacency matrix
        adjacency = self._build_adjacency_matrix(entities, relationships)
        
        # Initialize: each entity in its own community
        communities = {entity['_key']: entity['_key'] for entity in entities}
        
        # Iterate until convergence
        improved = True
        iteration = 0
        best_modularity = self._calculate_modularity(communities, adjacency)
        
        while improved and iteration < 100:  # Max iterations to prevent infinite loops
            improved = False
            iteration += 1
            
            # For each entity, try moving it to neighboring communities
            for entity_key in adjacency:
                current_community = communities[entity_key]
                best_community = current_community
                best_gain = 0
                
                # Get neighboring communities
                neighbor_communities = set()
                for neighbor in adjacency[entity_key]:
                    neighbor_communities.add(communities[neighbor])
                
                # Try each neighboring community
                for neighbor_community in neighbor_communities:
                    if neighbor_community == current_community:
                        continue
                    
                    # Calculate modularity gain
                    communities[entity_key] = neighbor_community
                    new_modularity = self._calculate_modularity(communities, adjacency)
                    gain = new_modularity - best_modularity
                    
                    if gain > best_gain:
                        best_gain = gain
                        best_community = neighbor_community
                
                # Move to best community if improvement found
                if best_gain > 0:
                    communities[entity_key] = best_community
                    best_modularity += best_gain
                    improved = True
                else:
                    communities[entity_key] = current_community
            
            logger.debug(f"Iteration {iteration}: Modularity = {best_modularity:.4f}")
        
        # Merge small communities
        final_communities = self._merge_small_communities(communities, adjacency, min_size)
        
        # Store communities in database
        self._store_communities(final_communities)
        
        logger.info(f"Community detection complete: {len(set(final_communities.values()))} communities found")
        return final_communities
    
    def _get_all_entities(self) -> List[Dict]:
        """Get all entities from database."""
        try:
            query = f"FOR e IN {self.entities_collection} RETURN e"
            return list(self.db.aql.execute(query))
        except ArangoError as e:
            logger.error(f"Error fetching entities: {e}")
            return []
    
    def _get_all_relationships(self) -> List[Dict]:
        """Get all relationships from database."""
        try:
            query = f"FOR r IN {self.relationships_collection} RETURN r"
            return list(self.db.aql.execute(query))
        except ArangoError as e:
            logger.error(f"Error fetching relationships: {e}")
            return []
    
    def _build_adjacency_matrix(self, entities: List[Dict], relationships: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Build adjacency matrix from entities and relationships."""
        adjacency = defaultdict(lambda: defaultdict(float))
        
        # Map full IDs to keys for easier lookup
        id_to_key = {e['_id']: e['_key'] for e in entities}
        
        for rel in relationships:
            from_key = id_to_key.get(rel['_from'])
            to_key = id_to_key.get(rel['_to'])
            
            if from_key and to_key:
                weight = rel.get('confidence', 1.0)
                adjacency[from_key][to_key] += weight
                adjacency[to_key][from_key] += weight  # Undirected graph
        
        return dict(adjacency)
    
    def _calculate_modularity(self, communities: Dict[str, str], adjacency: Dict[str, Dict[str, float]]) -> float:
        """Calculate modularity score for current community assignment."""
        if not adjacency:
            return 0.0
        
        # Calculate total edge weight
        total_weight = sum(sum(neighbors.values()) for neighbors in adjacency.values()) / 2
        
        if total_weight == 0:
            return 0.0
        
        # Group entities by community
        community_groups = defaultdict(list)
        for entity, community in communities.items():
            community_groups[community].append(entity)
        
        modularity = 0.0
        
        # Calculate modularity for each community
        for community_entities in community_groups.values():
            # Sum of internal edges
            internal_edges = 0
            degree_sum = 0
            
            for entity in community_entities:
                for neighbor, weight in adjacency.get(entity, {}).items():
                    degree_sum += weight
                    if neighbor in community_entities:
                        internal_edges += weight
            
            # Modularity contribution
            modularity += internal_edges / (2 * total_weight)
            modularity -= (degree_sum / (2 * total_weight)) ** 2
        
        return modularity
    
    def _merge_small_communities(self, communities: Dict[str, str], adjacency: Dict[str, Dict[str, float]], 
                                min_size: int) -> Dict[str, str]:
        """Merge communities smaller than min_size with their most connected neighbor."""
        # Count community sizes
        community_sizes = defaultdict(int)
        for community in communities.values():
            community_sizes[community] += 1
        
        # Find small communities
        small_communities = {c for c, size in community_sizes.items() if size < min_size}
        
        if not small_communities:
            return communities
        
        # Merge small communities
        final_communities = communities.copy()
        
        for small_community in small_communities:
            # Find entities in this community
            entities_in_community = [e for e, c in communities.items() if c == small_community]
            
            # Find most connected neighboring community
            neighbor_connections = defaultdict(float)
            
            for entity in entities_in_community:
                for neighbor, weight in adjacency.get(entity, {}).items():
                    neighbor_community = communities[neighbor]
                    if neighbor_community != small_community:
                        neighbor_connections[neighbor_community] += weight
            
            # Merge with most connected neighbor
            if neighbor_connections:
                best_neighbor = max(neighbor_connections.items(), key=lambda x: x[1])[0]
                for entity in entities_in_community:
                    final_communities[entity] = best_neighbor
                
                logger.debug(f"Merged small community {small_community} into {best_neighbor}")
        
        return final_communities
    
    def _store_communities(self, communities: Dict[str, str]):
        """Store community assignments in database."""
        # Group entities by community
        community_groups = defaultdict(list)
        for entity, community in communities.items():
            community_groups[community].append(entity)
        
        # Clear existing communities
        try:
            self.db.collection(self.communities_collection).truncate()
        except ArangoError as e:
            logger.error(f"Error clearing communities: {e}")
        
        # Store each community
        for community_id, entity_ids in community_groups.items():
            try:
                # Get entity names for description
                entity_names = []
                for entity_id in entity_ids[:5]:  # First 5 entities
                    try:
                        entity = self.db.collection(self.entities_collection).get(entity_id)
                        if entity:
                            entity_names.append(entity.get('name', entity_id))
                    except:
                        entity_names.append(entity_id)
                
                community_doc = {
                    "_key": f"community_{uuid.uuid4().hex[:8]}",
                    "original_id": community_id,
                    "member_count": len(entity_ids),
                    "member_ids": entity_ids,
                    "sample_members": entity_names,
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "algorithm": "louvain",
                        "modularity_score": self._calculate_modularity(communities, 
                                                                      self._build_adjacency_matrix(
                                                                          self._get_all_entities(), 
                                                                          self._get_all_relationships()))
                    }
                }
                
                self.db.collection(self.communities_collection).insert(community_doc)
                
                # Update entities with community assignment
                for entity_id in entity_ids:
                    try:
                        self.db.collection(self.entities_collection).update({
                            "_key": entity_id,
                            "community_id": community_doc["_key"]
                        })
                    except ArangoError as e:
                        logger.error(f"Error updating entity {entity_id}: {e}")
                
            except ArangoError as e:
                logger.error(f"Error storing community {community_id}: {e}")
    
    def get_community_for_entity(self, entity_id: str) -> Optional[Dict]:
        """Get community information for a specific entity."""
        try:
            entity = self.db.collection(self.entities_collection).get(entity_id)
            if entity and 'community_id' in entity:
                return self.db.collection(self.communities_collection).get(entity['community_id'])
        except ArangoError as e:
            logger.error(f"Error getting community for entity {entity_id}: {e}")
        return None
    
    def get_all_communities(self) -> List[Dict]:
        """Get all communities with their metadata."""
        try:
            query = f"FOR c IN {self.communities_collection} RETURN c"
            return list(self.db.aql.execute(query))
        except ArangoError as e:
            logger.error(f"Error fetching communities: {e}")
            return []


if __name__ == "__main__":
    # Validation code
    from arango import ArangoClient
    
    # Connect to database using defaults from constants
    client = ArangoClient(hosts='http://localhost:8529')
    db = client.db("memory_bank", username="root", password="openSesame")
    
    # Create test data
    logger.info("Creating test entities and relationships...")
    
    # Create test collections if they don't exist
    if not db.has_collection(ENTITIES_COLLECTION):
        db.create_collection(ENTITIES_COLLECTION)
    if not db.has_collection(RELATIONSHIPS_COLLECTION):
        db.create_collection(RELATIONSHIPS_COLLECTION, edge=True)
    
    # Clear existing test data  
    entities_col = db.collection(ENTITIES_COLLECTION)
    relationships_col = db.collection(RELATIONSHIPS_COLLECTION)
    
    # Create test entities
    test_entities = [
        {"_key": "python", "name": "Python", "type": "programming_language"},
        {"_key": "java", "name": "Java", "type": "programming_language"},
        {"_key": "django", "name": "Django", "type": "framework"},
        {"_key": "flask", "name": "Flask", "type": "framework"},
        {"_key": "spring", "name": "Spring", "type": "framework"},
        {"_key": "postgres", "name": "PostgreSQL", "type": "database"},
        {"_key": "mysql", "name": "MySQL", "type": "database"},
    ]
    
    for entity in test_entities:
        try:
            entities_col.insert(entity)
        except:
            pass  # Entity might already exist
    
    # Create test relationships
    test_relationships = [
        {"_from": f"{ENTITIES_COLLECTION}/python", "_to": f"{ENTITIES_COLLECTION}/django", 
         "type": "framework_for", "confidence": 0.9},
        {"_from": f"{ENTITIES_COLLECTION}/python", "_to": f"{ENTITIES_COLLECTION}/flask", 
         "type": "framework_for", "confidence": 0.9},
        {"_from": f"{ENTITIES_COLLECTION}/django", "_to": f"{ENTITIES_COLLECTION}/flask", 
         "type": "same_ecosystem", "confidence": 0.8},
        {"_from": f"{ENTITIES_COLLECTION}/java", "_to": f"{ENTITIES_COLLECTION}/spring", 
         "type": "framework_for", "confidence": 0.9},
        {"_from": f"{ENTITIES_COLLECTION}/django", "_to": f"{ENTITIES_COLLECTION}/postgres", 
         "type": "uses", "confidence": 0.4},
        {"_from": f"{ENTITIES_COLLECTION}/spring", "_to": f"{ENTITIES_COLLECTION}/mysql", 
         "type": "uses", "confidence": 0.4},
    ]
    
    for rel in test_relationships:
        try:
            relationships_col.insert(rel)
        except:
            pass  # Relationship might already exist
    
    # Run community detection
    detector = CommunityDetector(db)
    communities = detector.detect_communities(min_size=2)
    
    # Validate results
    logger.info("\n=== Community Detection Results ===")
    logger.info(f"Total entities: {len(communities)}")
    logger.info(f"Total communities: {len(set(communities.values()))}")
    
    # Group entities by community
    community_groups = defaultdict(list)
    for entity, community in communities.items():
        community_groups[community].append(entity)
    
    for community_id, entities in community_groups.items():
        logger.info(f"\nCommunity {community_id}:")
        logger.info(f"  Members: {', '.join(entities)}")
    
    # Check if communities make sense
    python_community = communities.get('python')
    django_community = communities.get('django')
    flask_community = communities.get('flask')
    
    if python_community == django_community == flask_community:
        logger.success("✓ Python frameworks grouped correctly")
    else:
        logger.error("✗ Python frameworks not in same community")
    
    java_community = communities.get('java')
    spring_community = communities.get('spring')
    
    if java_community == spring_community:
        logger.success("✓ Java frameworks grouped correctly")
    else:
        logger.error("✗ Java frameworks not in same community")
    
    # Get all communities from database
    all_communities = detector.get_all_communities()
    logger.info(f"\n=== Stored Communities ===")
    for community in all_communities:
        logger.info(f"Community {community['_key']}: {community['member_count']} members")
        logger.info(f"  Sample members: {', '.join(community['sample_members'])}")
        logger.info(f"  Modularity: {community['metadata']['modularity_score']:.4f}")
    
    logger.info("\n✓ Community detection validation complete")