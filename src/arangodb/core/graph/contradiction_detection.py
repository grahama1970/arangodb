"""
Contradiction detection and resolution utilities for ArangoDB graph relationships.
Module: contradiction_detection.py
Description: Functions for contradiction detection operations

This module provides functions to detect and resolve contradictions in graph relationships.
It uses the bi-temporal data model to handle conflicting information efficiently.

Sample input:
    edge_doc = {
        "_from": "documents/123",
        "_to": "documents/456",
        "type": "RELATED_TO",
        "valid_at": "2023-01-01T00:00:00Z",
        "invalid_at": None,
        "attributes": {"confidence": 0.9}
    }

Expected output:
    contradictions = [
        {
            "_key": "789",
            "_from": "documents/123",
            "_to": "documents/456",
            "type": "RELATED_TO",
            "valid_at": "2022-01-01T00:00:00Z",
            "invalid_at": None,
            "attributes": {"confidence": 0.7}
        }
    ]
"""

import sys
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from loguru import logger

from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError

# Import enhanced_relationships to reuse temporal validation functions
try:
    # Try relative import first for core module usage
    from .enhanced_relationships import (
        validate_temporal_metadata,
        is_temporal_edge_valid,
        invalidate_edge
    )
except ImportError:
    try:
        # Try absolute import for package structure
        from arangodb.core.graph.enhanced_relationships import (
            validate_temporal_metadata,
            is_temporal_edge_valid,
            invalidate_edge
        )
    except ImportError:
        # If all imports fail, define simplified fallback versions
        logger.warning("Could not import from enhanced_relationships, using fallback implementations")
        
        def validate_temporal_metadata(valid_at, invalid_at=None):
            """Fallback temporal validation."""
            return True  # Basic validation
            
        def is_temporal_edge_valid(edge, valid_at, invalid_at=None):
            """Fallback temporal edge validation."""
            return True  # Basic validation
            
        def invalidate_edge(db=None, edge_collection=None, edge_key=None, invalid_from=None, reason=None, invalidated_by=None, edge=None):
            """Fallback edge invalidation."""
            if edge:
                edge["invalid_at"] = invalid_from or datetime.now(timezone.utc).isoformat()
                return edge
            else:
                # For the key-based version, we need to read the edge, update it, and return it
                if db and edge_collection and edge_key:
                    try:
                        edge_doc = db.collection(edge_collection).get(edge_key)
                        edge_doc["invalid_at"] = invalid_from or datetime.now(timezone.utc).isoformat()
                        if reason:
                            edge_doc["invalidation_reason"] = reason
                        db.collection(edge_collection).update(
                            {"_key": edge_key}, 
                            {"invalid_at": edge_doc["invalid_at"], "invalidation_reason": reason}
                        )
                        return edge_doc
                    except Exception as e:
                        logger.error(f"Failed to invalidate edge: {e}")
                        return None
                return None

def detect_contradicting_edges(
    db: StandardDatabase,
    edge_collection: str,
    from_id: str,
    to_id: str,
    relationship_type: Optional[str] = None,
    attributes_filter: Optional[Dict[str, Any]] = None,
    include_invalidated: bool = False
) -> List[Dict[str, Any]]:
    """
    Find potentially contradicting edges between the same vertices.
    
    Args:
        db: ArangoDB database handle
        edge_collection: Name of the edge collection
        from_id: ID of the source document (_id format)
        to_id: ID of the target document (_id format)
        relationship_type: Optional type of relationship to filter by
        attributes_filter: Optional dict of attributes to filter by
        include_invalidated: Whether to include already invalidated edges
        
    Returns:
        List of potentially contradicting edges
    """
    try:
        # Build AQL query
        filters = [
            "e._from == @from_id", 
            "e._to == @to_id"
        ]
        
        # Add type filter if provided
        if relationship_type is not None:
            filters.append("e.type == @relationship_type")
        
        # Filter out invalidated edges unless explicitly requested
        if not include_invalidated:
            filters.append("e.invalid_at == null")
        
        # Add attribute filters if provided
        if attributes_filter:
            for key, value in attributes_filter.items():
                if isinstance(value, str):
                    # String values need to be wrapped in quotes in the AQL
                    filters.append(f"e.attributes.{key} == @attr_{key}")
                else:
                    filters.append(f"e.attributes.{key} == @attr_{key}")
        
        # Combine all filters with AND
        filter_clause = " AND ".join(filters)
        
        # Complete query
        aql = f"""
        FOR e IN {edge_collection}
        FILTER {filter_clause}
        RETURN e
        """
        
        # Prepare bind variables
        bind_vars = {
            "from_id": from_id,
            "to_id": to_id
        }
        
        # Add relationship_type if provided
        if relationship_type is not None:
            bind_vars["relationship_type"] = relationship_type
        
        # Add attribute filter values if provided
        if attributes_filter:
            for key, value in attributes_filter.items():
                bind_vars[f"attr_{key}"] = value
        
        # Execute query
        cursor = db.aql.execute(
            aql,
            bind_vars=bind_vars
        )
        
        # Return list of edges
        contradicting_edges = list(cursor)
        
        logger.debug(f"Found {len(contradicting_edges)} potentially contradicting edges")
        return contradicting_edges
        
    except AQLQueryExecuteError as e:
        logger.error(f"AQL query error in detect_contradicting_edges: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to find contradicting edges: {e}")
        return []

def detect_temporal_contradictions(
    db: StandardDatabase,
    edge_collection: str,
    edge_doc: Dict[str, Any],
    exclude_keys: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Detect contradictions based on temporal overlap with existing edges.
    
    Args:
        db: ArangoDB database handle
        edge_collection: Name of the edge collection
        edge_doc: The new edge document to check for contradictions
        exclude_keys: Optional list of edge keys to exclude from contradiction check
        
    Returns:
        List of temporally contradicting edges
    """
    try:
        # Extract required fields from edge_doc
        from_id = edge_doc.get("_from")
        to_id = edge_doc.get("_to")
        relationship_type = edge_doc.get("type")
        valid_at = edge_doc.get("valid_at")
        invalid_at = edge_doc.get("invalid_at")
        
        # Validate edge doc contains required fields
        if not from_id or not to_id or not relationship_type or not valid_at:
            logger.error("Edge document missing required fields: _from, _to, type, valid_at")
            return []
        
        # First, get all potentially contradicting edges
        contradicting_edges = detect_contradicting_edges(
            db=db,
            edge_collection=edge_collection,
            from_id=from_id,
            to_id=to_id,
            relationship_type=relationship_type
        )
        
        # Filter out edges that should be excluded
        if exclude_keys:
            contradicting_edges = [
                edge for edge in contradicting_edges 
                if edge.get("_key") not in exclude_keys
            ]
        
        # Now filter for actual temporal contradictions
        temporal_contradictions = []
        
        for existing_edge in contradicting_edges:
            # Skip if this is the same edge (by key)
            if "_key" in edge_doc and existing_edge.get("_key") == edge_doc["_key"]:
                continue
            
            # Check for temporal overlap
            existing_valid_at = existing_edge.get("valid_at")
            existing_invalid_at = existing_edge.get("invalid_at")
            
            # Both edges must have valid_at to check for contradiction
            if not existing_valid_at:
                continue
            
            # Convert string timestamps to datetime objects
            valid_at_dt = datetime.fromisoformat(valid_at.replace('Z', '+00:00'))
            existing_valid_at_dt = datetime.fromisoformat(existing_valid_at.replace('Z', '+00:00'))
            
            # Convert invalid_at to datetime if not None
            invalid_at_dt = None
            if invalid_at:
                invalid_at_dt = datetime.fromisoformat(invalid_at.replace('Z', '+00:00'))
                
            existing_invalid_at_dt = None
            if existing_invalid_at:
                existing_invalid_at_dt = datetime.fromisoformat(existing_invalid_at.replace('Z', '+00:00'))
            
            # Check for temporal overlap:
            # 1. New edge starts before or at same time old edge ends, AND
            # 2. New edge ends after or at same time old edge starts
            # Note: If either edge has no end time (invalid_at is None), it's considered "still valid"
            has_overlap = True
            
            # If new edge starts after old edge ends, there's no overlap
            if existing_invalid_at_dt and valid_at_dt >= existing_invalid_at_dt:
                has_overlap = False
                
            # If new edge ends before old edge starts, there's no overlap
            if invalid_at_dt and existing_valid_at_dt >= invalid_at_dt:
                has_overlap = False
            
            if has_overlap:
                temporal_contradictions.append(existing_edge)
        
        logger.debug(f"Found {len(temporal_contradictions)} temporal contradictions out of {len(contradicting_edges)} potential contradictions")
        return temporal_contradictions
        
    except Exception as e:
        logger.error(f"Failed to detect temporal contradictions: {e}")
        return []

def resolve_contradiction(
    db: StandardDatabase,
    edge_collection: str,
    new_edge: Dict[str, Any],
    contradicting_edge: Dict[str, Any],
    strategy: str = "newest_wins",
    resolution_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolve a contradiction between two edges based on the specified strategy.
    
    Args:
        db: ArangoDB database handle
        edge_collection: Name of the edge collection
        new_edge: The new edge document
        contradicting_edge: The existing edge that contradicts the new one
        strategy: Resolution strategy (newest_wins, merge, split_timeline)
        resolution_reason: Optional reason for the resolution
        
    Returns:
        Dict with resolution info: {
            "action": str, 
            "resolved_edge": dict,
            "reason": str,
            "success": bool
        }
    """
    try:
        action = None
        resolved_edge = None
        reason = resolution_reason or "Automated contradiction resolution"
        success = False
        
        # Get the keys and timestamps
        new_key = new_edge.get("_key")
        contradicting_key = contradicting_edge.get("_key")
        
        # Verify both edges have required temporal fields
        new_edge_validation = validate_temporal_metadata(new_edge)
        if isinstance(new_edge_validation, tuple):
            is_valid_new = new_edge_validation[0]
        else:
            is_valid_new = new_edge_validation
            
        if not is_valid_new:
            return {
                "action": "error",
                "reason": "New edge has invalid temporal metadata",
                "success": False
            }
        
        contradicting_validation = validate_temporal_metadata(contradicting_edge)
        if isinstance(contradicting_validation, tuple):
            is_valid_contradicting = contradicting_validation[0]
        else:
            is_valid_contradicting = contradicting_validation
            
        if not is_valid_contradicting:
            return {
                "action": "error",
                "reason": "Contradicting edge has invalid temporal metadata",
                "success": False
            }
        
        # Get created_at timestamps for comparison
        new_created_at = datetime.fromisoformat(new_edge["created_at"].replace('Z', '+00:00'))
        contradicting_created_at = datetime.fromisoformat(contradicting_edge["created_at"].replace('Z', '+00:00'))
        
        # Strategy: Newest information wins (default)
        if strategy == "newest_wins":
            if new_created_at > contradicting_created_at:
                # New edge is newer, invalidate the old edge
                result = invalidate_edge(
                    db=db,
                    edge_collection=edge_collection,
                    edge_key=contradicting_key,
                    invalid_from=new_edge["valid_at"],
                    reason="Superseded by newer edge",
                    invalidated_by=new_key
                )
                
                if result:
                    action = "invalidate_old"
                    resolved_edge = result
                    success = True
                    reason = "New edge supersedes old edge (newer information)"
                else:
                    action = "error"
                    reason = "Failed to invalidate old edge"
            else:
                # Old edge is newer, don't invalidate it
                action = "keep_old"
                resolved_edge = contradicting_edge
                success = True
                reason = "Old edge kept (contains newer information)"
        
        # Strategy: Merge temporal ranges
        elif strategy == "merge":
            logger.debug(f"Merge strategy - new_edge type: {type(new_edge)}, content: {new_edge}")
            logger.debug(f"Merge strategy - contradicting_edge type: {type(contradicting_edge)}, content: {contradicting_edge}")
            
            # Determine the earliest valid_at and latest invalid_at
            new_valid_at = datetime.fromisoformat(new_edge["valid_at"].replace('Z', '+00:00'))
            contradicting_valid_at = datetime.fromisoformat(contradicting_edge["valid_at"].replace('Z', '+00:00'))
            
            # Take the earlier valid_at date
            earliest_valid_at = min(new_valid_at, contradicting_valid_at)
            logger.debug(f"new_valid_at: {new_valid_at}, contradicting_valid_at: {contradicting_valid_at}")
            logger.debug(f"earliest_valid_at: {earliest_valid_at}")
            
            # For invalid_at, take the later date, or None if either is None
            new_invalid_at = None
            contradicting_invalid_at = None
            
            if new_edge.get("invalid_at"):
                new_invalid_at = datetime.fromisoformat(new_edge["invalid_at"].replace('Z', '+00:00'))
            
            if contradicting_edge.get("invalid_at"):
                contradicting_invalid_at = datetime.fromisoformat(contradicting_edge["invalid_at"].replace('Z', '+00:00'))
            
            latest_invalid_at = None
            if new_invalid_at and contradicting_invalid_at:
                latest_invalid_at = max(new_invalid_at, contradicting_invalid_at)
            
            # Update the new edge with merged temporal range
            update_data = {
                "valid_at": earliest_valid_at.isoformat(),
                "invalid_at": latest_invalid_at.isoformat() if latest_invalid_at else None,
                "merged_from": [new_key, contradicting_key],
                "merging_reason": reason
            }
            
            # Update the new edge (if it exists in the database)
            if new_key:
                logger.debug(f"Update data: {update_data}")
                
                # Replace the document entirely
                merged_edge = new_edge.copy()
                merged_edge.update(update_data)
                
                # Make sure to preserve _from and _to fields from the original edge
                merged_edge["_from"] = new_edge["_from"]
                merged_edge["_to"] = new_edge["_to"]
                
                logger.debug(f"Merged edge before replace: {merged_edge}")
                
                # Remove system fields from the document to replace (but keep _from and _to)
                clean_merged_edge = {k: v for k, v in merged_edge.items() if not k.startswith("_")}
                
                # Ensure _from and _to are included
                clean_merged_edge["_from"] = merged_edge["_from"]
                clean_merged_edge["_to"] = merged_edge["_to"]
                
                # Add the _key to the document for replacement
                clean_merged_edge["_key"] = new_key
                
                result = db.collection(edge_collection).replace(
                    clean_merged_edge
                )
                
                logger.debug(f"Replace result type: {type(result)}, content: {result}")
                
                # Check if the replace was successful
                if result is not None:
                    # Get the updated document from the database to ensure we have the latest version
                    resolved_edge = db.collection(edge_collection).get(new_key)
                    logger.debug(f"Retrieved replaced edge: {resolved_edge}")
                    success = True
                else:
                    # Replace failed
                    logger.error(f"Failed to replace edge {new_key}")
                    success = False
            else:
                # If new edge doesn't have a key yet, just update the dict
                merged_edge = new_edge.copy()
                merged_edge.update(update_data)
                resolved_edge = merged_edge
                success = True
            
            # Invalidate the old edge
            invalidate_edge(
                db=db,
                edge_collection=edge_collection,
                edge_key=contradicting_key,
                invalid_from=earliest_valid_at.isoformat(),
                reason="Merged into a new edge",
                invalidated_by=new_key
            )
            
            action = "merge"
            reason = "Merged temporal information from both edges"
        
        # Strategy: Split the timeline
        elif strategy == "split_timeline":
            # Extract temporal info
            new_valid_at = datetime.fromisoformat(new_edge["valid_at"].replace('Z', '+00:00'))
            new_invalid_at = None
            if new_edge.get("invalid_at"):
                new_invalid_at = datetime.fromisoformat(new_edge["invalid_at"].replace('Z', '+00:00'))
                
            contradicting_valid_at = datetime.fromisoformat(contradicting_edge["valid_at"].replace('Z', '+00:00'))
            contradicting_invalid_at = None
            if contradicting_edge.get("invalid_at"):
                contradicting_invalid_at = datetime.fromisoformat(contradicting_edge["invalid_at"].replace('Z', '+00:00'))
            
            # Case 1: New edge starts before old edge
            if new_valid_at < contradicting_valid_at:
                # Adjust new edge to end when old edge starts
                if new_key:
                    db.collection(edge_collection).update(
                        new_key,
                        {"invalid_at": contradicting_valid_at.isoformat()}
                    )
                else:
                    new_edge["invalid_at"] = contradicting_valid_at.isoformat()
                
                action = "split_before"
                resolved_edge = new_edge
                success = True
                reason = "Split timeline - new edge valid before old edge"
            
            # Case 2: New edge starts after old edge
            elif new_valid_at > contradicting_valid_at:
                # Adjust old edge to end when new edge starts
                invalidate_edge(
                    db=db,
                    edge_collection=edge_collection,
                    edge_key=contradicting_key,
                    invalid_from=new_valid_at.isoformat(),
                    reason="Timeline split with new edge",
                    invalidated_by=new_key
                )
                
                action = "split_after"
                resolved_edge = new_edge
                success = True
                reason = "Split timeline - new edge valid after old edge"
            
            # Case 3: Both start at the same time
            else:
                # Default to newest wins for same start time
                return resolve_contradiction(
                    db=db,
                    edge_collection=edge_collection,
                    new_edge=new_edge,
                    contradicting_edge=contradicting_edge,
                    strategy="newest_wins",
                    resolution_reason=reason
                )
        
        # Unknown strategy
        else:
            action = "error"
            reason = f"Unknown contradiction resolution strategy: {strategy}"
        
        return {
            "action": action,
            "resolved_edge": resolved_edge,
            "reason": reason,
            "success": success
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to resolve contradiction: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "action": "error",
            "reason": f"Error resolving contradiction: {str(e)}",
            "success": False
        }

def resolve_all_contradictions(
    db: StandardDatabase,
    edge_collection: str,
    edge_doc: Dict[str, Any],
    strategy: str = "newest_wins",
    exclude_keys: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Detect and resolve all contradictions for a new edge.
    
    Args:
        db: ArangoDB database handle
        edge_collection: Name of the edge collection
        edge_doc: The new edge document
        strategy: Resolution strategy (newest_wins, merge, split_timeline)
        exclude_keys: Optional list of edge keys to exclude from contradiction check
        
    Returns:
        Tuple of (list of resolution results, overall success boolean)
    """
    try:
        # First, detect all contradictions
        contradictions = detect_temporal_contradictions(
            db=db,
            edge_collection=edge_collection,
            edge_doc=edge_doc,
            exclude_keys=exclude_keys
        )
        
        # If no contradictions, return empty results
        if not contradictions:
            return [], True
        
        # Resolve each contradiction
        resolution_results = []
        overall_success = True
        
        for contradicting_edge in contradictions:
            result = resolve_contradiction(
                db=db,
                edge_collection=edge_collection,
                new_edge=edge_doc,
                contradicting_edge=contradicting_edge,
                strategy=strategy
            )
            
            resolution_results.append(result)
            
            # Update overall success
            if not result["success"]:
                overall_success = False
        
        return resolution_results, overall_success
        
    except Exception as e:
        logger.error(f"Failed to resolve all contradictions: {e}")
        return [], False

async def resolve_contradiction_with_llm(
    db: StandardDatabase,
    edge_collection: str,
    new_edge: Dict[str, Any],
    contradicting_edge: Dict[str, Any],
    llm_client: Any,
    prompt_template: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolve contradiction using LLM to determine the best resolution strategy.
    
    Args:
        db: ArangoDB database handle
        edge_collection: Name of the edge collection
        new_edge: The new edge document
        contradicting_edge: The existing edge that contradicts the new one
        llm_client: Client for LLM API calls
        prompt_template: Optional custom prompt template
        
    Returns:
        Dict with resolution info
    """
    try:
        # Default prompt template
        if not prompt_template:
            prompt_template = """
            You are analyzing a knowledge graph contradiction between two relationship edges.
            
            Edge 1 (New): {new_edge_json}
            
            Edge 2 (Existing): {contradicting_edge_json}
            
            These edges connect the same entities with the same relationship type, but have different temporal validity periods.
            Please analyze the contradiction and determine the best resolution strategy:
            
            1. "newest_wins" - The most recently created edge supersedes the older one
            2. "merge" - Merge the temporal ranges of both edges
            3. "split_timeline" - Split the timeline between the two edges
            
            Respond with ONLY the name of the most appropriate strategy (newest_wins, merge, or split_timeline)
            and a brief reason, in this format:
            strategy: STRATEGY_NAME
            reason: BRIEF_REASON
            """
        
        # Format the prompt with edge data
        prompt = prompt_template.format(
            new_edge_json=json.dumps(new_edge, indent=2),
            contradicting_edge_json=json.dumps(contradicting_edge, indent=2)
        )
        
        # Call the LLM
        # This is a placeholder for the actual LLM call
        # The implementation will depend on the specific LLM client being used
        response = await llm_client.complete(prompt)
        
        # Parse the response to extract the strategy and reason
        response_text = response.choices[0].text.strip()
        
        # Extract strategy and reason
        strategy = "newest_wins"  # Default
        reason = "Default strategy: newest information wins"
        
        for line in response_text.split("\n"):
            if line.startswith("strategy:"):
                strategy = line.replace("strategy:", "").strip().lower()
            elif line.startswith("reason:"):
                reason = line.replace("reason:", "").strip()
        
        # Validate the strategy
        valid_strategies = ["newest_wins", "merge", "split_timeline"]
        if strategy not in valid_strategies:
            logger.warning(f"LLM returned invalid strategy: {strategy}, using default 'newest_wins'")
            strategy = "newest_wins"
        
        # Resolve using the selected strategy
        return resolve_contradiction(
            db=db,
            edge_collection=edge_collection,
            new_edge=new_edge,
            contradicting_edge=contradicting_edge,
            strategy=strategy,
            resolution_reason=f"LLM decision: {reason}"
        )
        
    except Exception as e:
        logger.error(f"Failed to resolve contradiction with LLM: {e}")
        return {
            "action": "error",
            "reason": f"Error in LLM-based resolution: {str(e)}",
            "success": False
        }

# Self-validation function
if __name__ == "__main__":
    import sys
    import os
    from arango import ArangoClient
    
    # Initialize logger
    logger.remove()
    logger.add(sys.stdout, level="DEBUG")
    
    # Configure ArangoDB connection parameters from environment
    host = os.getenv("ARANGO_HOST", "http://localhost:8529")
    username = os.getenv("ARANGO_USER", "root")
    password = os.getenv("ARANGO_PASSWORD", "openSesame")
    database_name = "graphiti_test"
    collection_name = "test_documents"
    edge_collection_name = "test_relationships"
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    try:
        # Connect to database
        logger.info("Connecting to ArangoDB...")
        client = ArangoClient(hosts=host)
        sys_db = client.db("_system", username=username, password=password)
        
        # Create test database if needed
        if not sys_db.has_database(database_name):
            sys_db.create_database(database_name)
        
        db = client.db(database_name, username=username, password=password)
        
        # Create collections if they don't exist
        if not db.has_collection(collection_name):
            db.create_collection(collection_name)
        
        if not db.has_collection(edge_collection_name):
            db.create_collection(edge_collection_name, edge=True)
        
        # Create test documents
        doc1 = {"name": "Test Document 1", "created_at": datetime.now(timezone.utc).isoformat()}
        doc2 = {"name": "Test Document 2", "created_at": datetime.now(timezone.utc).isoformat()}
        
        doc1_result = db.collection(collection_name).insert(doc1)
        doc2_result = db.collection(collection_name).insert(doc2)
        
        doc1_id = f"{collection_name}/{doc1_result['_key']}"
        doc2_id = f"{collection_name}/{doc2_result['_key']}"
        
        # Clean up any existing test relationships
        aql = f"""
        FOR e IN {edge_collection_name}
        FILTER e._from == @from_id AND e._to == @to_id
        REMOVE e IN {edge_collection_name}
        """
        
        db.aql.execute(
            aql,
            bind_vars={
                "from_id": doc1_id,
                "to_id": doc2_id
            }
        )
        
        # Test 1: Create edge with temporal metadata
        total_tests += 1
        logger.info("Test 1: Create original edge with temporal metadata")
        
        now = datetime.now(timezone.utc)
        one_month_ago = now - timedelta(days=30)
        
        original_edge = {
            "_from": doc1_id,
            "_to": doc2_id,
            "type": "TEST_RELATIONSHIP",
            "attributes": {"confidence": 0.7},
            "created_at": one_month_ago.isoformat(),
            "valid_at": one_month_ago.isoformat(),
            "invalid_at": None
        }
        
        original_result = db.collection(edge_collection_name).insert(original_edge)
        original_key = original_result["_key"]
        
        if not original_key:
            all_validation_failures.append("Test 1: Failed to create original edge")
        else:
            logger.info(f"Created original edge with key: {original_key}")
        
        # Test 2: Create contradicting edge
        total_tests += 1
        logger.info("Test 2: Create contradicting edge")
        
        new_edge = {
            "_from": doc1_id,
            "_to": doc2_id,
            "type": "TEST_RELATIONSHIP",
            "attributes": {"confidence": 0.9},
            "created_at": now.isoformat(),
            "valid_at": now.isoformat(),
            "invalid_at": None
        }
        
        new_result = db.collection(edge_collection_name).insert(new_edge)
        new_key = new_result["_key"]
        
        if not new_key:
            all_validation_failures.append("Test 2: Failed to create new edge")
        else:
            logger.info(f"Created new edge with key: {new_key}")
        
        # Test 3: Detect contradictions
        total_tests += 1
        logger.info("Test 3: Detect contradictions")
        
        # Get the new edge from the database to ensure it has all fields
        new_edge = db.collection(edge_collection_name).get(new_key)
        contradictions = detect_temporal_contradictions(
            db=db,
            edge_collection=edge_collection_name,
            edge_doc=new_edge,
            exclude_keys=None
        )
        
        # Should find the original edge as a contradiction
        if not contradictions or len(contradictions) != 1:
            all_validation_failures.append(f"Test 3: Failed to detect contradictions, found {len(contradictions)}")
        else:
            logger.info(f"Detected {len(contradictions)} contradictions")
        
        # Test 4: Resolve contradiction - newest wins
        total_tests += 1
        logger.info("Test 4: Resolve contradiction - newest wins")
        
        if contradictions:
            resolution = resolve_contradiction(
                db=db,
                edge_collection=edge_collection_name,
                new_edge=new_edge,
                contradicting_edge=contradictions[0],
                strategy="newest_wins"
            )
            
            if not resolution["success"]:
                all_validation_failures.append(f"Test 4: Failed to resolve contradiction: {resolution}")
            else:
                logger.info(f"Successfully resolved contradiction with action: {resolution['action']}")
                
                # Verify that the old edge was invalidated
                old_edge = db.collection(edge_collection_name).get(original_key)
                if old_edge.get("invalid_at") is None:
                    all_validation_failures.append("Test 4: Old edge was not properly invalidated")
                else:
                    logger.info(f"Verified old edge was invalidated at: {old_edge['invalid_at']}")
        else:
            all_validation_failures.append("Test 4: No contradictions to resolve")
        
        # Test 5: Create edge with different temporal range (shouldn't contradict)
        total_tests += 1
        logger.info("Test 5: Create edge with non-contradicting temporal range")
        
        two_months_ago = now - timedelta(days=60)
        six_weeks_ago = now - timedelta(days=42)
        
        non_contradicting_edge = {
            "_from": doc1_id,
            "_to": doc2_id,
            "type": "TEST_RELATIONSHIP",
            "attributes": {"confidence": 0.8},
            "created_at": now.isoformat(),
            "valid_at": two_months_ago.isoformat(),
            "invalid_at": six_weeks_ago.isoformat()  # Ends before other edges start
        }
        
        non_contradicting_result = db.collection(edge_collection_name).insert(non_contradicting_edge)
        non_contradicting_key = non_contradicting_result["_key"]
        
        if not non_contradicting_key:
            all_validation_failures.append("Test 5: Failed to create non-contradicting edge")
        else:
            logger.info(f"Created non-contradicting edge with key: {non_contradicting_key}")
            
            # Verify it doesn't contradict the new edge
            new_edge = db.collection(edge_collection_name).get(new_key)
            non_contradictions = detect_temporal_contradictions(
                db=db,
                edge_collection=edge_collection_name,
                edge_doc=new_edge,
                exclude_keys=[original_key]  # Exclude the already invalidated edge
            )
            
            if non_contradictions:
                all_validation_failures.append(f"Test 5: Incorrectly detected non-contradicting edge as contradiction")
            else:
                logger.info("Correctly found no contradictions with temporally separate edge")
        
        # Test 6: Resolve all contradictions
        total_tests += 1
        logger.info("Test 6: Test resolving all contradictions")
        
        # Create a new contradicting edge for this test
        another_edge = {
            "_from": doc1_id,
            "_to": doc2_id,
            "type": "ANOTHER_TEST",
            "attributes": {"confidence": 0.6},
            "created_at": now.isoformat(),
            "valid_at": now.isoformat(),
            "invalid_at": None
        }
        
        another_result = db.collection(edge_collection_name).insert(another_edge)
        another_key = another_result["_key"]
        
        if not another_key:
            all_validation_failures.append("Test 6: Failed to create another test edge")
        else:
            logger.info(f"Created another test edge with key: {another_key}")
            
            # Create a contradicting edge of the same type
            conflicting_another = {
                "_from": doc1_id,
                "_to": doc2_id,
                "type": "ANOTHER_TEST",
                "attributes": {"confidence": 0.95},
                "created_at": (now + timedelta(hours=1)).isoformat(),  # Newer
                "valid_at": (now - timedelta(days=7)).isoformat(),  # Starts earlier
                "invalid_at": None
            }
            
            conflicting_result = db.collection(edge_collection_name).insert(conflicting_another)
            conflicting_key = conflicting_result["_key"]
            
            # Get the edge from DB to ensure it has all fields
            conflicting_edge = db.collection(edge_collection_name).get(conflicting_key)
            
            # Resolve all contradictions
            resolutions, success = resolve_all_contradictions(
                db=db,
                edge_collection=edge_collection_name,
                edge_doc=conflicting_edge,
                strategy="newest_wins"
            )
            
            if not success or not resolutions:
                all_validation_failures.append(f"Test 6: Failed to resolve all contradictions")
            else:
                logger.info(f"Successfully resolved {len(resolutions)} contradictions")
                
                # Verify that the old edge was invalidated
                another_edge_updated = db.collection(edge_collection_name).get(another_key)
                if another_edge_updated.get("invalid_at") is None:
                    all_validation_failures.append("Test 6: Contradicting edge was not properly invalidated")
                else:
                    logger.info(f"Verified contradicting edge was invalidated at: {another_edge_updated['invalid_at']}")
        
        # Test 7: Test merging strategy
        total_tests += 1
        logger.info("Test 7: Test merging strategy")
        
        # Create two edges with different temporal ranges
        merge_edge1 = {
            "_from": doc1_id,
            "_to": doc2_id,
            "type": "MERGE_TEST",
            "attributes": {"confidence": 0.7},
            "created_at": now.isoformat(),
            "valid_at": (now - timedelta(days=10)).isoformat(),
            "invalid_at": (now + timedelta(days=10)).isoformat()
        }
        
        merge_edge2 = {
            "_from": doc1_id,
            "_to": doc2_id,
            "type": "MERGE_TEST",
            "attributes": {"confidence": 0.8},
            "created_at": now.isoformat(),
            "valid_at": (now - timedelta(days=5)).isoformat(),
            "invalid_at": (now + timedelta(days=20)).isoformat()
        }
        
        merge_result1 = db.collection(edge_collection_name).insert(merge_edge1)
        merge_key1 = merge_result1["_key"]
        
        merge_result2 = db.collection(edge_collection_name).insert(merge_edge2)
        merge_key2 = merge_result2["_key"]
        
        if not merge_key1 or not merge_key2:
            all_validation_failures.append("Test 7: Failed to create merge test edges")
        else:
            logger.info(f"Created merge test edges with keys: {merge_key1}, {merge_key2}")
            
            # Get edges from DB to ensure they have all fields
            edge1 = db.collection(edge_collection_name).get(merge_key1)
            edge2 = db.collection(edge_collection_name).get(merge_key2)
            
            # Resolve with merge strategy
            resolution = resolve_contradiction(
                db=db,
                edge_collection=edge_collection_name,
                new_edge=edge2,
                contradicting_edge=edge1,
                strategy="merge"
            )
            
            if not resolution["success"]:
                all_validation_failures.append(f"Test 7: Failed to resolve with merge strategy: {resolution}")
            else:
                logger.info(f"Successfully merged edges: {resolution['action']}")
                
                # Verify merged edge has correct temporal range
                resolved_edge = resolution["resolved_edge"]
                expected_valid_at = (now - timedelta(days=10)).isoformat()  # Earlier date
                expected_invalid_at = (now + timedelta(days=20)).isoformat()  # Later date
                
                if resolved_edge["valid_at"] != expected_valid_at:
                    all_validation_failures.append(f"Test 7: Merged edge has incorrect valid_at: {resolved_edge['valid_at']}, expected: {expected_valid_at}")
                
                if resolved_edge["invalid_at"] != expected_invalid_at:
                    all_validation_failures.append(f"Test 7: Merged edge has incorrect invalid_at: {resolved_edge['invalid_at']}, expected: {expected_invalid_at}")
                
                logger.info(f"Verified merged edge has correct temporal range")
        
        # Clean up test data
        logger.info("Cleaning up test data...")
        
        # Drop test database
        sys_db.delete_database(database_name)
        
        # Final validation result
        if all_validation_failures:
            logger.error(f" VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                logger.error(f"  - {failure}")
            sys.exit(1)  # Exit with error code
        else:
            logger.info(f" VALIDATION PASSED - All {total_tests} tests produced expected results")
            logger.info("Contradiction detection and resolution functionality is validated")
            sys.exit(0)  # Exit with success code
            
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        sys.exit(1)