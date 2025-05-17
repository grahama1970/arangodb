"""
Contradiction logger for tracking and managing detected contradictions in the graph.

This module provides utilities for logging contradictions, their resolutions, and
providing insights into the graph's consistency state.

Sample usage:
    logger = ContradictionLogger(db)
    logger.log_contradiction(new_edge, existing_edge, resolution)
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from arango.database import StandardDatabase
from loguru import logger


class ContradictionLogger:
    """Logger for tracking contradictions in the knowledge graph."""
    
    def __init__(self, db: StandardDatabase, collection: str = "agent_contradiction_log"):
        """
        Initialize the contradiction logger.
        
        Args:
            db: ArangoDB database connection
            collection: Collection name for contradiction logs
        """
        self.db = db
        self.collection = collection
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the contradiction log collection exists."""
        if not self.db.has_collection(self.collection):
            self.db.create_collection(self.collection)
            logger.info(f"Created contradiction log collection: {self.collection}")
    
    def log_contradiction(
        self,
        new_edge: Dict[str, Any],
        existing_edge: Dict[str, Any],
        resolution: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """
        Log a detected contradiction and its resolution.
        
        Args:
            new_edge: The new edge that caused the contradiction
            existing_edge: The existing edge that contradicts
            resolution: Resolution result from resolve_contradiction
            context: Optional context about where the contradiction was detected
            
        Returns:
            Key of the created log entry
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "new_edge": {
                "from": new_edge.get("_from"),
                "to": new_edge.get("_to"),
                "type": new_edge.get("type"),
                "valid_at": new_edge.get("valid_at"),
                "attributes": new_edge.get("attributes", {})
            },
            "existing_edge": {
                "key": existing_edge.get("_key"),
                "from": existing_edge.get("_from"),
                "to": existing_edge.get("_to"),
                "type": existing_edge.get("type"),
                "valid_at": existing_edge.get("valid_at"),
                "invalid_at": existing_edge.get("invalid_at"),
                "attributes": existing_edge.get("attributes", {})
            },
            "resolution": {
                "action": resolution.get("action"),
                "strategy": resolution.get("strategy", "unknown"),
                "reason": resolution.get("reason"),
                "success": resolution.get("success", False)
            },
            "context": context or "unspecified",
            "status": "resolved" if resolution.get("success") else "failed"
        }
        
        # Insert the log entry
        result = self.db.collection(self.collection).insert(log_entry)
        logger.debug(f"Logged contradiction: {result['_key']}")
        
        return result["_key"]
    
    def get_contradictions(
        self,
        entity_id: Optional[str] = None,
        edge_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query contradiction logs with various filters.
        
        Args:
            entity_id: Filter by entity ID (either from or to)
            edge_type: Filter by edge type
            status: Filter by resolution status
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            limit: Maximum number of results
            
        Returns:
            List of contradiction log entries
        """
        filters = []
        bind_vars = {}
        
        # Add entity filter
        if entity_id:
            filters.append(
                "(c.new_edge.from == @entity_id OR c.new_edge.to == @entity_id OR "
                "c.existing_edge.from == @entity_id OR c.existing_edge.to == @entity_id)"
            )
            bind_vars["entity_id"] = entity_id
        
        # Add edge type filter
        if edge_type:
            filters.append(
                "(c.new_edge.type == @edge_type OR c.existing_edge.type == @edge_type)"
            )
            bind_vars["edge_type"] = edge_type
        
        # Add status filter
        if status:
            filters.append("c.status == @status")
            bind_vars["status"] = status
        
        # Add time filters
        if start_time:
            filters.append("c.timestamp >= @start_time")
            bind_vars["start_time"] = start_time.isoformat()
        
        if end_time:
            filters.append("c.timestamp <= @end_time")
            bind_vars["end_time"] = end_time.isoformat()
        
        # Build query
        filter_clause = " AND ".join(filters) if filters else "true"
        
        aql = f"""
        FOR c IN {self.collection}
        FILTER {filter_clause}
        SORT c.timestamp DESC
        LIMIT {limit}
        RETURN c
        """
        
        cursor = self.db.aql.execute(aql, bind_vars=bind_vars)
        return list(cursor)
    
    def get_contradiction_summary(self) -> Dict[str, Any]:
        """
        Get a summary of contradiction statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        aql = f"""
        LET total = LENGTH({self.collection})
        LET resolved = LENGTH(
            FOR c IN {self.collection}
            FILTER c.status == "resolved"
            RETURN 1
        )
        LET failed = LENGTH(
            FOR c IN {self.collection}
            FILTER c.status == "failed"
            RETURN 1
        )
        LET by_type = (
            FOR c IN {self.collection}
            COLLECT edge_type = c.new_edge.type WITH COUNT INTO count
            RETURN {{type: edge_type, count: count}}
        )
        LET by_action = (
            FOR c IN {self.collection}
            COLLECT action = c.resolution.action WITH COUNT INTO count  
            RETURN {{action: action, count: count}}
        )
        
        RETURN {{
            total: total,
            resolved: resolved,
            failed: failed,
            success_rate: total > 0 ? resolved / total : 0,
            by_edge_type: by_type,
            by_resolution_action: by_action
        }}
        """
        
        cursor = self.db.aql.execute(aql)
        result = next(cursor, None)
        
        return result or {
            "total": 0,
            "resolved": 0, 
            "failed": 0,
            "success_rate": 0.0,
            "by_edge_type": [],
            "by_resolution_action": []
        }


# Validation function
if __name__ == "__main__":
    import sys
    from arango import ArangoClient
    
    # Initialize logger
    logger.remove()
    logger.add(sys.stdout, level="DEBUG")
    
    # Connect to database
    host = "http://localhost:8529"
    username = "root"
    password = "openSesame"
    database_name = "agent_memory_test"
    
    try:
        # Connect to ArangoDB
        client = ArangoClient(hosts=host)
        sys_db = client.db("_system", username=username, password=password)
        
        # Create test database if needed
        if not sys_db.has_database(database_name):
            sys_db.create_database(database_name)
        
        db = client.db(database_name, username=username, password=password)
        
        # Create logger instance
        logger_instance = ContradictionLogger(db)
        
        # Test logging a contradiction
        new_edge = {
            "_from": "entities/123",
            "_to": "entities/456",
            "type": "WORKS_FOR",
            "valid_at": datetime.now(timezone.utc).isoformat()
        }
        
        existing_edge = {
            "_key": "789",
            "_from": "entities/123",
            "_to": "entities/456",
            "type": "WORKS_FOR",
            "valid_at": "2023-01-01T00:00:00Z"
        }
        
        resolution = {
            "action": "invalidate_old",
            "strategy": "newest_wins",
            "reason": "New edge supersedes old edge",
            "success": True
        }
        
        log_key = logger_instance.log_contradiction(
            new_edge, existing_edge, resolution, "test validation"
        )
        
        logger.info(f"Created log entry: {log_key}")
        
        # Test querying contradictions
        logs = logger_instance.get_contradictions()
        logger.info(f"Found {len(logs)} contradiction logs")
        
        # Get summary
        summary = logger_instance.get_contradiction_summary()
        logger.info(f"Contradiction summary: {json.dumps(summary, indent=2)}")
        
        # Clean up
        sys_db.delete_database(database_name)
        
        logger.info("✅ VALIDATION PASSED - Contradiction logger working correctly")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)