"""
Enhanced relationship operations for ArangoDB with temporal metadata support.

This module provides enhanced relationship operations for ArangoDB,
including bi-temporal metadata support inspired by the Graphiti knowledge
graph framework. It enables tracking both when relationships were created
and when they were valid in the real world.

Key features:
1. Bi-temporal metadata - Track both creation time and validity period
2. Contradiction detection and resolution
3. Temporal validity filters
4. Relationship management compatibility with CLI commands
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
import re
from typing import Dict, Any, List, Optional, Tuple, Union

from loguru import logger
from arango.database import StandardDatabase
try:
    # Try absolute import first
    from arangodb.db_operations import create_relationship, delete_relationship_by_key
except ImportError:
    # Fall back to relative import
    from src.arangodb.db_operations import create_relationship, delete_relationship_by_key

# ISO-8601 pattern with timezone
ISO8601_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
ISO8601_REGEX = re.compile(ISO8601_PATTERN)

def enhance_edge_with_temporal_metadata(
    edge_doc: Dict[str, Any], 
    reference_time: Optional[Union[datetime, str]] = None,
    valid_until: Optional[Union[datetime, str]] = None,
    source_document: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add or enhance temporal metadata in edge documents based on Graphiti's bi-temporal model.
    
    Args:
        edge_doc: Edge document to enhance
        reference_time: When the relationship became true in the real world (defaults to now)
        valid_until: When the relationship stopped being true (None means still valid)
        source_document: Source document for provenance tracking
        
    Returns:
        Enhanced edge document with temporal metadata
    """
    now = datetime.now(timezone.utc)
    
    # Create a copy of the edge document to avoid modifying the original
    enhanced_doc = edge_doc.copy()
    
    # 1. Add created_at time (when the edge was inserted into the database)
    enhanced_doc["created_at"] = now.isoformat()
    
    # 2. Add valid_at time (when the relationship became true in the real world)
    if reference_time is not None:
        # If reference_time is a string, ensure it's in ISO format
        if isinstance(reference_time, str):
            if not ISO8601_REGEX.match(reference_time):
                try:
                    # Try to parse and convert to ISO format
                    parsed_time = datetime.fromisoformat(reference_time.replace('Z', '+00:00'))
                    enhanced_doc["valid_at"] = parsed_time.isoformat()
                except ValueError:
                    logger.warning(f"Invalid reference_time format: {reference_time}, using current time")
                    enhanced_doc["valid_at"] = now.isoformat()
            else:
                enhanced_doc["valid_at"] = reference_time
        else:
            # If it's a datetime object, convert to ISO format
            enhanced_doc["valid_at"] = reference_time.isoformat()
    else:
        # Default to current time if not provided
        enhanced_doc["valid_at"] = now.isoformat()
    
    # 3. Add NULL invalid_at time (representing "valid until further notice")
    # or set the specified invalidation time
    if valid_until is not None:
        # If valid_until is a string, ensure it's in ISO format
        if isinstance(valid_until, str):
            if not ISO8601_REGEX.match(valid_until):
                try:
                    # Try to parse and convert to ISO format
                    parsed_time = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
                    enhanced_doc["invalid_at"] = parsed_time.isoformat()
                except ValueError:
                    logger.warning(f"Invalid valid_until format: {valid_until}, setting to NULL")
                    enhanced_doc["invalid_at"] = None
            else:
                enhanced_doc["invalid_at"] = valid_until
        else:
            # If it's a datetime object, convert to ISO format
            enhanced_doc["invalid_at"] = valid_until.isoformat()
    else:
        enhanced_doc["invalid_at"] = None
    
    # 4. Add provenance information if source document is provided
    if source_document is not None:
        if "_id" in source_document:
            enhanced_doc["source_id"] = source_document["_id"]
        if "_key" in source_document:
            enhanced_doc["source_key"] = source_document["_key"]
    
    # 5. Add confidence score if not present (default to 1.0)
    if "confidence" not in enhanced_doc:
        enhanced_doc["confidence"] = 1.0
        
    return enhanced_doc

def is_temporal_edge_valid(
    edge: Dict[str, Any],
    point_in_time: Optional[Union[datetime, str]] = None
) -> bool:
    """
    Check if an edge is valid at a specific point in time.
    
    Args:
        edge: Edge document with temporal metadata
        point_in_time: Point in time to check validity (defaults to now)
        
    Returns:
        True if edge is valid at the specified time, False otherwise
    """
    # Default to current time if not provided
    if point_in_time is None:
        point_in_time = datetime.now(timezone.utc)
        
    # Convert string time to datetime if needed
    if isinstance(point_in_time, str):
        try:
            point_in_time = datetime.fromisoformat(point_in_time.replace('Z', '+00:00'))
        except ValueError:
            logger.error(f"Invalid point_in_time format: {point_in_time}")
            return False
    
    # Get valid_at from edge
    valid_at = edge.get("valid_at")
    if valid_at is None:
        logger.warning("Edge missing valid_at timestamp")
        return False
        
    # Convert valid_at to datetime
    try:
        valid_at_dt = datetime.fromisoformat(valid_at.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        logger.error(f"Invalid valid_at format: {valid_at}")
        return False
    
    # Get invalid_at from edge
    invalid_at = edge.get("invalid_at")
    invalid_at_dt = None
    
    # Convert invalid_at to datetime if not None
    if invalid_at is not None:
        try:
            invalid_at_dt = datetime.fromisoformat(invalid_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logger.error(f"Invalid invalid_at format: {invalid_at}")
            return False
    
    # Check if edge is valid at point_in_time
    # Edge is valid if:
    # 1. point_in_time is at or after valid_at, AND
    # 2. (invalid_at is None OR point_in_time is before invalid_at)
    is_valid = (
        point_in_time >= valid_at_dt and 
        (invalid_at_dt is None or point_in_time < invalid_at_dt)
    )
    
    return is_valid

def validate_temporal_metadata(edge: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate temporal metadata format in an edge document.
    
    Args:
        edge: Edge document with temporal metadata
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if required fields are present
    if "created_at" not in edge:
        return False, "Missing required field: created_at"
    if "valid_at" not in edge:
        return False, "Missing required field: valid_at"
    if "invalid_at" not in edge and edge.get("invalid_at") is not None:
        # invalid_at can be None (still valid) but should be present
        return False, "Missing field: invalid_at"
    
    # Validate created_at format
    created_at = edge.get("created_at")
    if created_at is not None and not ISO8601_REGEX.match(created_at):
        return False, f"Invalid created_at format: {created_at}"
    
    # Validate valid_at format
    valid_at = edge.get("valid_at")
    if valid_at is not None and not ISO8601_REGEX.match(valid_at):
        return False, f"Invalid valid_at format: {valid_at}"
    
    # Validate invalid_at format if present and not None
    invalid_at = edge.get("invalid_at")
    if invalid_at is not None and not ISO8601_REGEX.match(invalid_at):
        return False, f"Invalid invalid_at format: {invalid_at}"
    
    # Validate temporal logic
    try:
        valid_at_dt = datetime.fromisoformat(valid_at.replace('Z', '+00:00'))
        
        if invalid_at is not None:
            invalid_at_dt = datetime.fromisoformat(invalid_at.replace('Z', '+00:00'))
            # invalid_at must be after valid_at
            if invalid_at_dt <= valid_at_dt:
                return False, f"invalid_at ({invalid_at}) must be after valid_at ({valid_at})"
    except Exception as e:
        return False, f"Error parsing timestamps: {str(e)}"
    
    return True, None

def invalidate_edge(
    db: StandardDatabase,
    edge_collection: str,
    edge_key: str,
    invalid_from: Optional[Union[datetime, str]] = None,
    reason: Optional[str] = None,
    invalidated_by: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Mark an edge as invalid from a specific point in time.
    
    Args:
        db: ArangoDB database handle
        edge_collection: Name of the edge collection
        edge_key: Key of the edge to invalidate
        invalid_from: When the edge became invalid (defaults to now)
        reason: Reason for invalidation
        invalidated_by: ID of the entity that invalidated this edge
        
    Returns:
        Updated edge document or None if update failed
    """
    try:
        # Default to current time if not provided
        if invalid_from is None:
            invalid_from = datetime.now(timezone.utc)
        
        # Convert to ISO string if datetime
        if isinstance(invalid_from, datetime):
            invalid_from_str = invalid_from.isoformat()
        else:
            invalid_from_str = invalid_from
        
        # Prepare update data
        update_data = {
            "invalid_at": invalid_from_str
        }
        
        # Add invalidation reason if provided
        if reason is not None:
            update_data["invalidation_reason"] = reason
        
        # Add invalidated_by reference if provided
        if invalidated_by is not None:
            update_data["invalidated_by"] = invalidated_by
        
        # Update the edge in the database
        edge_coll = db.collection(edge_collection)
        result = edge_coll.update(edge_key, update_data, return_new=True)
        
        logger.info(f"Invalidated edge {edge_key} in {edge_collection}")
        return result.get("new") if "new" in result else None
        
    except Exception as e:
        logger.error(f"Failed to invalidate edge: {e}")
        return None

def find_contradicting_edges(
    db: StandardDatabase, 
    edge_collection: str,
    from_id: str,
    to_id: str,
    relationship_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find potentially contradicting edges between the same vertices.
    
    Args:
        db: ArangoDB database handle
        edge_collection: Name of the edge collection
        from_id: ID of the source document (_id format)
        to_id: ID of the target document (_id format)
        relationship_type: Optional type of relationship to filter by
        
    Returns:
        List of contradicting edges
    """
    try:
        # Build AQL query
        aql = f"""
        FOR e IN {edge_collection}
        FILTER e._from == @from_id AND e._to == @to_id
        """
        
        # Add type filter if provided
        if relationship_type is not None:
            aql += f"\nFILTER e.type == @relationship_type"
        
        # Only include edges that are still valid
        aql += f"\nFILTER e.invalid_at == null"
        
        # Complete query
        aql += f"\nRETURN e"
        
        # Prepare bind variables
        bind_vars = {
            "from_id": from_id,
            "to_id": to_id
        }
        
        # Add relationship_type if provided
        if relationship_type is not None:
            bind_vars["relationship_type"] = relationship_type
        
        # Execute query
        cursor = db.aql.execute(
            aql,
            bind_vars=bind_vars
        )
        
        # Return list of edges
        return list(cursor)
        
    except Exception as e:
        logger.error(f"Failed to find contradicting edges: {e}")
        return []

def create_temporal_relationship(
    db: StandardDatabase, 
    edge_collection: str,
    from_id: str,
    to_id: str,
    relationship_type: str,
    attributes: Optional[Dict[str, Any]] = None,
    reference_time: Optional[Union[datetime, str]] = None,
    valid_until: Optional[Union[datetime, str]] = None,
    check_contradictions: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Create a relationship with temporal metadata, handling contradictions.
    
    Args:
        db: ArangoDB database handle
        edge_collection: Name of the edge collection
        from_id: ID of the source document (_id format)
        to_id: ID of the target document (_id format)
        relationship_type: Type of relationship
        attributes: Additional attributes for the relationship
        reference_time: When the relationship became true (defaults to now)
        valid_until: When the relationship stopped being true (None means still valid)
        check_contradictions: Whether to check for and resolve contradictions
        
    Returns:
        Created edge document or None if creation failed
    """
    try:
        # Create edge document
        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "type": relationship_type,
            **(attributes or {})
        }
        
        # Add temporal metadata
        edge_doc = enhance_edge_with_temporal_metadata(
            edge_doc, 
            reference_time=reference_time,
            valid_until=valid_until
        )
        
        # Check for contradictions if enabled
        if check_contradictions:
            contradictions = find_contradicting_edges(
                db, 
                edge_collection, 
                from_id, 
                to_id, 
                relationship_type
            )
            
            # Handle contradictions
            if contradictions:
                logger.info(f"Found {len(contradictions)} potentially contradicting edges")
                for contradiction in contradictions:
                    # Invalidate each contradicting edge
                    invalidate_edge(
                        db,
                        edge_collection,
                        contradiction["_key"],
                        invalid_from=edge_doc["valid_at"],
                        reason="Superseded by new relationship",
                        invalidated_by="new_edge"
                    )
        
        # Create the edge
        edge_coll = db.collection(edge_collection)
        result = edge_coll.insert(edge_doc, return_new=True)
        
        # Get the result
        created_edge = result.get("new") if "new" in result else None
        
        # Update invalidated_by with the actual key of the new edge
        if check_contradictions and contradictions and created_edge:
            for contradiction in contradictions:
                db.collection(edge_collection).update(
                    contradiction["_key"],
                    {"invalidated_by": created_edge["_key"]}
                )
        
        logger.info(f"Created temporal relationship in {edge_collection}: {result.get('_key', result)}")
        return created_edge
        
    except Exception as e:
        logger.error(f"Failed to create temporal relationship: {e}")
        return None

def search_temporal_relationships(
    db: StandardDatabase,
    edge_collection: str,
    point_in_time: Optional[Union[datetime, str]] = None,
    from_id: Optional[str] = None,
    to_id: Optional[str] = None,
    relationship_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Search for relationships that were valid at a specific point in time.
    
    Args:
        db: ArangoDB database handle
        edge_collection: Name of the edge collection
        point_in_time: Point in time to search at (defaults to now)
        from_id: Optional filter by source document ID
        to_id: Optional filter by target document ID
        relationship_type: Optional filter by relationship type
        limit: Maximum number of results to return
        
    Returns:
        List of edges valid at the specified point in time
    """
    try:
        # Default to current time if not provided
        if point_in_time is None:
            point_in_time = datetime.now(timezone.utc)
        
        # Convert to ISO string if datetime
        if isinstance(point_in_time, datetime):
            time_str = point_in_time.isoformat()
        else:
            time_str = point_in_time
        
        # Start building AQL query
        aql = f"""
        FOR e IN {edge_collection}
        """
        
        # Add filters
        filters = []
        
        # Filter by _from if provided
        if from_id is not None:
            filters.append("e._from == @from_id")
        
        # Filter by _to if provided
        if to_id is not None:
            filters.append("e._to == @to_id")
        
        # Filter by type if provided
        if relationship_type is not None:
            filters.append("e.type == @relationship_type")
        
        # Temporal filter:
        # valid_at <= query_time AND (invalid_at IS NULL OR invalid_at > query_time)
        filters.append("DATE_ISO8601(e.valid_at) <= DATE_ISO8601(@time_str)")
        filters.append("e.invalid_at == null OR DATE_ISO8601(e.invalid_at) > DATE_ISO8601(@time_str)")
        
        # Add all filters to query
        if filters:
            aql += "\nFILTER " + " AND ".join(filters)
        
        # Complete the query
        aql += f"""
        SORT e.valid_at DESC
        LIMIT {limit}
        RETURN e
        """
        
        # Prepare bind variables
        bind_vars = {
            "time_str": time_str
        }
        
        # Add from_id if provided
        if from_id is not None:
            bind_vars["from_id"] = from_id
        
        # Add to_id if provided
        if to_id is not None:
            bind_vars["to_id"] = to_id
        
        # Add relationship_type if provided
        if relationship_type is not None:
            bind_vars["relationship_type"] = relationship_type
        
        # Execute query
        cursor = db.aql.execute(
            aql,
            bind_vars=bind_vars
        )
        
        # Return list of edges
        return list(cursor)
        
    except Exception as e:
        logger.error(f"Failed to search temporal relationships: {e}")
        return []

# Preserve the existing CLI-compatible functions
def create_edge_from_cli(
    db: StandardDatabase,
    from_key: str,
    to_key: str,
    collection: str,
    edge_collection: str,
    edge_type: str,
    rationale: str,
    attributes: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a relationship edge using CLI-friendly parameters with temporal metadata.
    
    This function bridges the gap between the CLI graph command parameters
    and the underlying relationship creation function.
    
    Args:
        db: ArangoDB database handle
        from_key: Key of the source document
        to_key: Key of the target document
        collection: Name of the document collection
        edge_collection: Name of the edge collection
        edge_type: Type of relationship
        rationale: Reason for the relationship
        attributes: Additional properties for the edge
        
    Returns:
        Optional[Dict[str, Any]]: The created edge document if successful, None otherwise
    """
    try:
        # Prepare from_id and to_id
        from_id = f"{collection}/{from_key}"
        to_id = f"{collection}/{to_key}"
        
        # Prepare attributes
        edge_attributes = attributes or {}
        edge_attributes["rationale"] = rationale
        
        # Create temporal relationship
        return create_temporal_relationship(
            db=db,
            edge_collection=edge_collection,
            from_id=from_id,
            to_id=to_id,
            relationship_type=edge_type,
            attributes=edge_attributes,
            check_contradictions=True
        )
        
    except Exception as e:
        logger.error(f"Failed to create edge from CLI: {e}")
        return None

def delete_edge_from_cli(
    db: StandardDatabase,
    edge_key: str,
    edge_collection: str
) -> bool:
    """
    Delete a relationship edge using CLI-friendly parameters.
    
    Args:
        db: ArangoDB database handle
        edge_key: Key of the edge to delete
        edge_collection: Name of the edge collection
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Delete the edge directly using ArangoDB collection API
        edge_coll = db.collection(edge_collection)
        result = edge_coll.delete(edge_key, ignore_missing=True)
        
        logger.info(f"Deleted edge from {edge_collection}: {edge_key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete edge: {e}")
        return False

# Example validation function
if __name__ == "__main__":
    # Initialize logger
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    import json
    from arangodb.arango_setup import connect_arango, ensure_database
    
    # Connect to database
    try:
        client = connect_arango()
        db = ensure_database(client)
        
        # Define test edge collection
        edge_collection = "test_relationships"
        
        # Ensure edge collection exists
        if not db.has_collection(edge_collection):
            db.create_collection(edge_collection, edge=True)
            
        # Define test documents collection
        doc_collection = "test_documents"
        
        # Ensure document collection exists
        if not db.has_collection(doc_collection):
            db.create_collection(doc_collection)
            
            # Create test documents
            source_doc = {"name": "Source Document", "content": "Test source document"}
            target_doc = {"name": "Target Document", "content": "Test target document"}
            
            source_result = db.collection(doc_collection).insert(source_doc)
            target_result = db.collection(doc_collection).insert(target_doc)
            
            source_key = source_result["_key"]
            target_key = target_result["_key"]
        else:
            # Get test documents or create them if they don't exist
            source_query = f"FOR doc IN {doc_collection} FILTER doc.name == 'Source Document' RETURN doc"
            source_cursor = db.aql.execute(source_query)
            source_docs = list(source_cursor)
            
            if source_docs:
                source_key = source_docs[0]["_key"]
            else:
                source_doc = {"name": "Source Document", "content": "Test source document"}
                source_result = db.collection(doc_collection).insert(source_doc)
                source_key = source_result["_key"]
                
            target_query = f"FOR doc IN {doc_collection} FILTER doc.name == 'Target Document' RETURN doc"
            target_cursor = db.aql.execute(target_query)
            target_docs = list(target_cursor)
            
            if target_docs:
                target_key = target_docs[0]["_key"]
            else:
                target_doc = {"name": "Target Document", "content": "Test target document"}
                target_result = db.collection(doc_collection).insert(target_doc)
                target_key = target_result["_key"]
        
        # Track validation failures
        all_validation_failures = []
        total_tests = 0
        
        # Test 1: Create edge with temporal metadata
        total_tests += 1
        logger.info("Test 1: Creating edge with temporal metadata")
        
        # Create test edge
        test_edge = {
            "_from": f"{doc_collection}/{source_key}",
            "_to": f"{doc_collection}/{target_key}",
            "type": "TEST_RELATIONSHIP",
            "attributes": {"test": True}
        }
        
        # Enhance edge with temporal metadata
        enhanced_edge = enhance_edge_with_temporal_metadata(test_edge)
        
        # Verify temporal fields were added
        if "created_at" not in enhanced_edge or "valid_at" not in enhanced_edge or "invalid_at" not in enhanced_edge:
            all_validation_failures.append("Test 1: Missing temporal fields in enhanced edge")
        
        # Test 2: Validate temporal metadata
        total_tests += 1
        logger.info("Test 2: Validating temporal metadata")
        
        is_valid, error = validate_temporal_metadata(enhanced_edge)
        
        if not is_valid:
            all_validation_failures.append(f"Test 2: Temporal validation failed: {error}")
        
        # Test 3: Check edge validity
        total_tests += 1
        logger.info("Test 3: Checking edge validity")
        
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=1)
        past = now - timedelta(days=1)
        
        # Edge should be valid now and in the future (since invalid_at is None)
        is_valid_now = is_temporal_edge_valid(enhanced_edge, now)
        is_valid_future = is_temporal_edge_valid(enhanced_edge, future)
        
        if not is_valid_now or not is_valid_future:
            all_validation_failures.append(f"Test 3: Edge validity check failed for current or future time")
        
        # Test 4: Create relationship in database
        total_tests += 1
        logger.info("Test 4: Creating relationship in database")
        
        # Delete any existing test edges first
        clean_query = f"""
        FOR e IN {edge_collection}
        FILTER e._from == @from_id AND e._to == @to_id
        REMOVE e IN {edge_collection}
        """
        db.aql.execute(
            clean_query, 
            bind_vars={
                "from_id": f"{doc_collection}/{source_key}",
                "to_id": f"{doc_collection}/{target_key}"
            }
        )
        
        # Create relationship with temporal metadata
        created_edge = create_temporal_relationship(
            db=db,
            edge_collection=edge_collection,
            from_id=f"{doc_collection}/{source_key}",
            to_id=f"{doc_collection}/{target_key}",
            relationship_type="TEST_RELATIONSHIP",
            attributes={"test": True}
        )
        
        if created_edge is None or "created_at" not in created_edge or "valid_at" not in created_edge:
            all_validation_failures.append("Test 4: Failed to create relationship in database")
        
        # Test 5: Find relationship in database
        total_tests += 1
        logger.info("Test 5: Finding relationship in database")
        
        # Find relationship with temporal search
        edges = search_temporal_relationships(
            db=db,
            edge_collection=edge_collection,
            from_id=f"{doc_collection}/{source_key}",
            to_id=f"{doc_collection}/{target_key}",
            relationship_type="TEST_RELATIONSHIP"
        )
        
        if not edges:
            all_validation_failures.append("Test 5: Failed to find relationship in database")
        
        # Test 6: Create contradicting relationship
        total_tests += 1
        logger.info("Test 6: Creating contradicting relationship")
        
        # Create contradicting relationship
        contradicting_edge = create_temporal_relationship(
            db=db,
            edge_collection=edge_collection,
            from_id=f"{doc_collection}/{source_key}",
            to_id=f"{doc_collection}/{target_key}",
            relationship_type="TEST_RELATIONSHIP",
            attributes={"test": True, "updated": True}
        )
        
        if contradicting_edge is None:
            all_validation_failures.append("Test 6: Failed to create contradicting relationship")
        
        # Test 7: Verify contradiction resolution
        total_tests += 1
        logger.info("Test 7: Verifying contradiction resolution")
        
        # Find all relationships including invalidated ones
        all_query = f"""
        FOR e IN {edge_collection}
        FILTER e._from == @from_id AND e._to == @to_id
        RETURN e
        """
        all_cursor = db.aql.execute(
            all_query, 
            bind_vars={
                "from_id": f"{doc_collection}/{source_key}",
                "to_id": f"{doc_collection}/{target_key}"
            }
        )
        all_edges = list(all_cursor)
        
        # Count valid and invalid edges
        valid_edges = [e for e in all_edges if e.get("invalid_at") is None]
        invalid_edges = [e for e in all_edges if e.get("invalid_at") is not None]
        
        if len(valid_edges) != 1 or len(invalid_edges) != 1:
            all_validation_failures.append(f"Test 7: Contradiction resolution failed, found {len(valid_edges)} valid and {len(invalid_edges)} invalid edges")
        
        # Test 8: CLI compatibility
        total_tests += 1
        logger.info("Test 8: Testing CLI compatibility")
        
        # Create edge using CLI-compatible function
        cli_edge = create_edge_from_cli(
            db=db,
            from_key=source_key,
            to_key=target_key,
            collection=doc_collection,
            edge_collection=edge_collection,
            edge_type="CLI_TEST_RELATIONSHIP",
            rationale="Testing CLI compatibility"
        )
        
        if cli_edge is None or "created_at" not in cli_edge or "valid_at" not in cli_edge:
            all_validation_failures.append("Test 8: Failed to create edge using CLI-compatible function")
        
        # Final validation result
        if all_validation_failures:
            logger.error(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                logger.error(f"  - {failure}")
            sys.exit(1)  # Exit with error code
        else:
            logger.info(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            logger.info("Enhanced temporal relationship functionality is validated")
            sys.exit(0)  # Exit with success code
    
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        sys.exit(1)