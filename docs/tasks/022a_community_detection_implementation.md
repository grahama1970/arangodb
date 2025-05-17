# Task 022a: Community Detection Implementation Guide

## Overview
This document provides detailed implementation guidance for adding community detection to our ArangoDB memory system, bringing us closer to Graphiti parity.

## Technical Approach

### 1. Algorithm Selection
For community detection, we'll implement the Louvain algorithm, which is:
- Fast and scalable
- Produces hierarchical communities
- Well-suited for sparse graphs
- Available in ArangoDB's graph algorithms

### 2. Database Schema Updates

#### New Collection: agent_communities
```javascript
{
  "_key": "community_001",
  "name": "Python Programming Community",
  "description": "Entities related to Python programming concepts",
  "level": 0,  // Hierarchy level
  "parent_community": null,  // For hierarchical communities
  "member_count": 42,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "metadata": {
    "algorithm": "louvain",
    "modularity_score": 0.82
  }
}
```

#### Updated agent_entities Collection
Add community membership field:
```javascript
{
  "_key": "entity_123",
  "name": "Python",
  // ... existing fields ...
  "community_id": "community_001",
  "community_scores": {
    "community_001": 0.95,  // Confidence scores
    "community_002": 0.15
  }
}
```

### 3. Implementation Files

#### `/src/arangodb/core/graph/community_detection.py`
```python
"""Community detection algorithms for entity graph analysis."""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from arango.database import Database
from loguru import logger

class CommunityDetector:
    """Detect and manage communities in entity graphs."""
    
    def __init__(self, db: Database):
        self.db = db
        self.entities_collection = "agent_entities"
        self.relationships_collection = "agent_relationships"
        self.communities_collection = "agent_communities"
        
    def detect_communities(self, min_size: int = 3) -> Dict[str, str]:
        """
        Detect communities using Louvain algorithm.
        
        Args:
            min_size: Minimum community size to keep
            
        Returns:
            Mapping of entity_id to community_id
        """
        # Run Louvain algorithm
        query = """
        FOR vertex IN agent_entities
            FOR edge IN agent_relationships
                FILTER edge._from == vertex._id OR edge._to == vertex._id
                RETURN {
                    vertex: vertex._key,
                    edge: edge._key,
                    weight: edge.confidence || 1.0
                }
        """
        
        # Process results and assign communities
        # Implementation details...
        
    def merge_small_communities(self, threshold: int = 3):
        """Merge communities smaller than threshold."""
        pass
        
    def calculate_modularity(self) -> float:
        """Calculate modularity score for current community assignment."""
        pass
        
    def assign_entity_to_community(self, entity_id: str, community_id: str):
        """Assign an entity to a community."""
        pass

if __name__ == "__main__":
    # Validation code
    from arango import ArangoClient
    
    client = ArangoClient()
    db = client.db("_system", username="root", password="password")
    
    detector = CommunityDetector(db)
    communities = detector.detect_communities()
    
    print(f"Detected {len(set(communities.values()))} communities")
    print(f"Modularity score: {detector.calculate_modularity()}")
```

#### `/src/arangodb/community_building.py` (update)
```python
"""Community building and management functionality."""
# Add imports
from arangodb.core.graph.community_detection import CommunityDetector

# Update existing functions to integrate with community detection
def build_communities(db: Database, force_rebuild: bool = False):
    """Build or rebuild community structure."""
    detector = CommunityDetector(db)
    
    # Check if rebuild needed
    if not force_rebuild and _communities_exist(db):
        logger.info("Communities already exist, skipping rebuild")
        return
    
    # Detect communities
    logger.info("Starting community detection...")
    communities = detector.detect_communities()
    
    # Store results
    _store_communities(db, communities)
    
    # Update entities with community assignments
    _update_entity_communities(db, communities)
    
    logger.info(f"Community building complete: {len(set(communities.values()))} communities created")
```

### 4. CLI Integration

#### `/src/arangodb/cli/graph_commands.py` (update)
```python
"""Graph-related CLI commands."""
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def detect_communities(
    min_size: int = typer.Option(3, help="Minimum community size"),
    rebuild: bool = typer.Option(False, help="Force rebuild communities")
):
    """Detect and build communities in the entity graph."""
    from arangodb.core.graph.community_detection import CommunityDetector
    from arangodb.cli.db_connection import get_db
    
    db = get_db()
    detector = CommunityDetector(db)
    
    if rebuild:
        console.print("[yellow]Rebuilding communities...[/yellow]")
    
    communities = detector.detect_communities(min_size=min_size)
    
    # Display results
    table = Table(title="Community Detection Results")
    table.add_column("Community ID", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Key Entities", style="yellow")
    
    # Group entities by community
    community_groups = {}
    for entity, community in communities.items():
        if community not in community_groups:
            community_groups[community] = []
        community_groups[community].append(entity)
    
    for community_id, entities in community_groups.items():
        key_entities = ", ".join(entities[:3])
        if len(entities) > 3:
            key_entities += f" (+{len(entities)-3} more)"
        table.add_row(community_id, str(len(entities)), key_entities)
    
    console.print(table)
    console.print(f"\n[green]Total communities: {len(community_groups)}[/green]")

@app.command()
def show_community(community_id: str):
    """Show details of a specific community."""
    # Implementation...
```

### 5. Validation Script
Create `/src/arangodb/validate_community_detection.py`:
```python
"""Validate community detection functionality."""
import json
from datetime import datetime
from arango import ArangoClient
from loguru import logger

from arangodb.core.graph.community_detection import CommunityDetector
from arangodb.core.db_operations import (
    create_entity,
    create_relationship,
    get_entity_by_id
)

def create_test_graph(db):
    """Create test entities and relationships."""
    # Create entities for three distinct communities
    
    # Community 1: Programming Languages
    python = create_entity(db, "Python", entity_type="programming_language")
    java = create_entity(db, "Java", entity_type="programming_language")
    javascript = create_entity(db, "JavaScript", entity_type="programming_language")
    
    # Community 2: Web Frameworks
    django = create_entity(db, "Django", entity_type="framework")
    flask = create_entity(db, "Flask", entity_type="framework")
    react = create_entity(db, "React", entity_type="framework")
    
    # Community 3: Databases
    postgres = create_entity(db, "PostgreSQL", entity_type="database")
    mysql = create_entity(db, "MySQL", entity_type="database")
    mongodb = create_entity(db, "MongoDB", entity_type="database")
    
    # Create relationships within communities
    create_relationship(db, python["_key"], django["_key"], "framework_for")
    create_relationship(db, python["_key"], flask["_key"], "framework_for")
    create_relationship(db, javascript["_key"], react["_key"], "framework_for")
    
    # Create cross-community relationships (weaker)
    create_relationship(db, django["_key"], postgres["_key"], "uses", confidence=0.5)
    create_relationship(db, flask["_key"], mysql["_key"], "compatible_with", confidence=0.3)
    
    return {
        "programming": [python, java, javascript],
        "frameworks": [django, flask, react],
        "databases": [postgres, mysql, mongodb]
    }

def validate_communities(detector, test_entities):
    """Validate that communities are correctly detected."""
    communities = detector.detect_communities(min_size=2)
    
    # Check that entities in same category are in same community
    category_communities = {}
    
    for category, entities in test_entities.items():
        communities_in_category = set()
        for entity in entities:
            community = communities.get(entity["_key"])
            communities_in_category.add(community)
        
        category_communities[category] = communities_in_category
        
        if len(communities_in_category) == 1:
            logger.success(f"✓ {category}: All entities in same community")
        else:
            logger.error(f"✗ {category}: Entities split across {len(communities_in_category)} communities")
    
    # Calculate modularity
    modularity = detector.calculate_modularity()
    logger.info(f"Modularity score: {modularity:.3f}")
    
    if modularity > 0.3:
        logger.success("✓ Good modularity score (>0.3)")
    else:
        logger.warning("⚠ Low modularity score (<0.3)")
    
    return len(set(communities.values()))

if __name__ == "__main__":
    # Connect to database
    client = ArangoClient()
    db = client.db("memory_agent_demo", username="root", password="root_password")
    
    logger.info("Starting community detection validation")
    
    # Create test data
    test_entities = create_test_graph(db)
    logger.info("Created test graph with 9 entities and relationships")
    
    # Test community detection
    detector = CommunityDetector(db)
    num_communities = validate_communities(detector, test_entities)
    
    logger.info(f"Final result: {num_communities} communities detected")
    
    # Test CLI command
    import subprocess
    result = subprocess.run(["uv", "run", "arangomem", "graph", "detect-communities"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.success("✓ CLI command executed successfully")
    else:
        logger.error(f"✗ CLI command failed: {result.stderr}")
```

### 6. Integration Points

#### Memory Agent Integration
Update `/src/arangodb/memory_agent/memory_agent.py`:
```python
def store_conversation(self, ...):
    """Store conversation with community detection."""
    # ... existing code ...
    
    # After creating entities, run community detection
    if self.auto_detect_communities:
        detector = CommunityDetector(self.db)
        communities = detector.detect_communities()
        
        # Update entities with community assignments
        for entity_id, community_id in communities.items():
            detector.assign_entity_to_community(entity_id, community_id)
```

### 7. Testing Strategy
1. Unit tests for community detection algorithm
2. Integration tests with real graph data
3. Performance tests with large graphs
4. CLI command tests
5. Memory Agent integration tests

### 8. Documentation Updates
- Add community detection to README
- Create usage examples
- Document CLI commands
- Add API documentation

## Implementation Checklist
- [ ] Create database schema updates
- [ ] Implement CommunityDetector class
- [ ] Update community_building.py
- [ ] Add CLI commands
- [ ] Create validation script
- [ ] Integrate with Memory Agent
- [ ] Write tests
- [ ] Update documentation
- [ ] Performance optimization
- [ ] Code review

## Next Steps
After implementing community detection:
1. Move to Task 2: Contradiction Resolution
2. Use communities for better contradiction detection
3. Leverage community structure for search improvements