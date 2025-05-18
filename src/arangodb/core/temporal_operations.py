"""
Temporal Operations Module

Provides functions for bi-temporal data management including
point-in-time queries, temporal validation, and invalidation.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from loguru import logger
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError

def ensure_temporal_fields(document: Dict[str, Any], valid_at: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Ensure a document has proper temporal fields.
    
    Args:
        document: The document to enhance
        valid_at: The valid time (defaults to now if not provided)
    
    Returns:
        Document with temporal fields added
    """
    now = datetime.now(timezone.utc)
    
    # Add created_at if not present
    if 'created_at' not in document:
        document['created_at'] = now.isoformat()
    elif isinstance(document['created_at'], datetime):
        document['created_at'] = document['created_at'].isoformat()
    
    # Add valid_at if not present
    if 'valid_at' not in document:
        document['valid_at'] = (valid_at or now).isoformat()
    elif isinstance(document['valid_at'], datetime):
        document['valid_at'] = document['valid_at'].isoformat()
    
    # Ensure invalid_at is null for new documents
    if 'invalid_at' not in document:
        document['invalid_at'] = None
    elif document['invalid_at'] is not None and isinstance(document['invalid_at'], datetime):
        document['invalid_at'] = document['invalid_at'].isoformat()
    
    return document

def create_temporal_entity(
    db: StandardDatabase,
    collection_name: str,
    document: Dict[str, Any],
    valid_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create an entity with bi-temporal tracking.
    
    Args:
        db: ArangoDB database instance
        collection_name: Name of the collection
        document: The document to insert
        valid_at: When the fact became true (defaults to now)
    
    Returns:
        The created document with temporal fields
    """
    document = ensure_temporal_fields(document, valid_at)
    
    collection = db.collection(collection_name)
    result = collection.insert(document)
    
    # Return the complete document
    created_doc = collection.get(result['_key'])
    logger.debug(f"Created temporal entity in {collection_name}: {result['_key']}")
    
    return created_doc

def invalidate_entity(
    db: StandardDatabase,
    collection_name: str,
    entity_key: str,
    invalid_at: Optional[datetime] = None,
    reason: str = "Manual invalidation",
    invalidated_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mark an entity as invalid at a specific time.
    
    Args:
        db: ArangoDB database instance
        collection_name: Name of the collection
        entity_key: The entity key to invalidate
        invalid_at: When the entity becomes invalid (defaults to now)
        reason: Reason for invalidation
        invalidated_by: Entity that caused the invalidation
    
    Returns:
        The updated document
    """
    collection = db.collection(collection_name)
    
    # Get the current document
    current_doc = collection.get(entity_key)
    if not current_doc:
        raise ValueError(f"Entity {entity_key} not found in {collection_name}")
    
    # Already invalidated?
    if current_doc.get('invalid_at'):
        logger.warning(f"Entity {entity_key} is already invalidated")
        return current_doc
    
    # Update with invalidation info
    update_data = {
        'invalid_at': (invalid_at or datetime.now(timezone.utc)).isoformat(),
        'invalidation_reason': reason
    }
    
    if invalidated_by:
        update_data['invalidated_by'] = invalidated_by
    
    result = collection.update({'_key': entity_key}, update_data)
    updated_doc = collection.get(entity_key)
    
    logger.info(f"Invalidated entity {entity_key} in {collection_name} at {update_data['invalid_at']}")
    
    return updated_doc

def point_in_time_query(
    db: StandardDatabase,
    collection_name: str,
    timestamp: datetime,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Query entities valid at a specific point in time.
    
    Args:
        db: ArangoDB database instance
        collection_name: Name of the collection
        timestamp: The point in time to query
        filters: Additional filters to apply
        limit: Maximum number of results
    
    Returns:
        List of entities valid at the specified time
    """
    query = f"""
    FOR doc IN {collection_name}
        FILTER doc.valid_at <= @timestamp
        FILTER doc.invalid_at == null OR doc.invalid_at > @timestamp
    """
    
    bind_vars = {'timestamp': timestamp.isoformat()}
    
    # Add additional filters
    if filters:
        for key, value in filters.items():
            query += f" FILTER doc.{key} == @{key}"
            bind_vars[key] = value
    
    query += f" LIMIT {limit} RETURN doc"
    
    try:
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        logger.debug(f"Point-in-time query at {timestamp} returned {len(results)} results")
        return results
    except AQLQueryExecuteError as e:
        logger.error(f"Point-in-time query failed: {e}")
        return []

def temporal_range_query(
    db: StandardDatabase,
    collection_name: str,
    start_time: datetime,
    end_time: datetime,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Query entities within a temporal range.
    
    Args:
        db: ArangoDB database instance
        collection_name: Name of the collection
        start_time: Start of the time range
        end_time: End of the time range
        filters: Additional filters to apply
        limit: Maximum number of results
    
    Returns:
        List of entities valid during the specified time range
    """
    query = f"""
    FOR doc IN {collection_name}
        FILTER doc.valid_at >= @start_time
        FILTER doc.valid_at <= @end_time
        FILTER doc.invalid_at == null OR doc.invalid_at > @end_time
    """
    
    bind_vars = {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat()
    }
    
    # Add additional filters
    if filters:
        for key, value in filters.items():
            query += f" FILTER doc.{key} == @{key}"
            bind_vars[key] = value
    
    query += f" LIMIT {limit} RETURN doc"
    
    try:
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        logger.debug(f"Temporal range query from {start_time} to {end_time} returned {len(results)} results")
        return results
    except AQLQueryExecuteError as e:
        logger.error(f"Temporal range query failed: {e}")
        return []

def get_entity_history(
    db: StandardDatabase,
    collection_name: str,
    entity_key: str,
    include_invalidated: bool = True
) -> List[Dict[str, Any]]:
    """
    Get the complete temporal history of an entity.
    
    Args:
        db: ArangoDB database instance
        collection_name: Name of the collection
        entity_key: The entity key to get history for
        include_invalidated: Whether to include invalidated versions
    
    Returns:
        List of all versions of the entity
    """
    query = f"""
    FOR doc IN {collection_name}
        FILTER doc._key == @entity_key
    """
    
    if not include_invalidated:
        query += " FILTER doc.invalid_at == null"
    
    query += " SORT doc.valid_at DESC RETURN doc"
    
    bind_vars = {'entity_key': entity_key}
    
    try:
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        logger.debug(f"Entity history for {entity_key} has {len(results)} versions")
        return results
    except AQLQueryExecuteError as e:
        logger.error(f"Entity history query failed: {e}")
        return []

def create_temporal_indexes(db: StandardDatabase, collection_name: str):
    """
    Create indexes for efficient temporal queries.
    
    Args:
        db: ArangoDB database instance
        collection_name: Name of the collection
    """
    collection = db.collection(collection_name)
    
    # Index for valid_at queries
    collection.add_persistent_index(
        fields=['valid_at'],
        name=f'{collection_name}_valid_at_idx'
    )
    
    # Index for invalid_at queries
    collection.add_persistent_index(
        fields=['invalid_at'],
        name=f'{collection_name}_invalid_at_idx'
    )
    
    # Composite index for temporal range queries
    collection.add_persistent_index(
        fields=['valid_at', 'invalid_at'],
        name=f'{collection_name}_temporal_idx'
    )
    
    logger.info(f"Created temporal indexes for {collection_name}")

# Validation functions
def validate_temporal_consistency(
    db: StandardDatabase,
    collection_name: str,
    entity_key: str
) -> Dict[str, Any]:
    """
    Validate the temporal consistency of an entity.
    
    Args:
        db: ArangoDB database instance
        collection_name: Name of the collection
        entity_key: The entity key to validate
    
    Returns:
        Validation result with any issues found
    """
    collection = db.collection(collection_name)
    entity = collection.get(entity_key)
    
    if not entity:
        return {
            'is_valid': False,
            'errors': [f'Entity {entity_key} not found']
        }
    
    errors = []
    
    # Check temporal field presence
    if 'created_at' not in entity:
        errors.append('Missing created_at field')
    if 'valid_at' not in entity:
        errors.append('Missing valid_at field')
    
    # Check temporal ordering
    if 'created_at' in entity and 'valid_at' in entity:
        created_at = datetime.fromisoformat(entity['created_at'])
        valid_at = datetime.fromisoformat(entity['valid_at'])
        
        # Valid time should not be after created time (can't record future facts)
        if valid_at > created_at:
            errors.append(f'valid_at ({valid_at}) is after created_at ({created_at})')
    
    # Check invalidation
    if entity.get('invalid_at'):
        invalid_at = datetime.fromisoformat(entity['invalid_at'])
        if 'valid_at' in entity:
            valid_at = datetime.fromisoformat(entity['valid_at'])
            if invalid_at <= valid_at:
                errors.append(f'invalid_at ({invalid_at}) is not after valid_at ({valid_at})')
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'entity_key': entity_key,
        'validation_timestamp': datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    # Example usage
    from arangodb.core.db_operations import get_db_connection
    
    db = get_db_connection()
    
    # Create a temporal entity
    test_doc = {
        'name': 'Test Entity',
        'value': 42,
        'description': 'A test entity for temporal operations'
    }
    
    created = create_temporal_entity(
        db,
        'test_temporal',
        test_doc,
        valid_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )
    print(f"Created temporal entity: {created}")
    
    # Query at a specific time
    results = point_in_time_query(
        db,
        'test_temporal',
        datetime(2024, 6, 1, tzinfo=timezone.utc)
    )
    print(f"Point-in-time query results: {len(results)}")
    
    # Invalidate the entity
    invalidated = invalidate_entity(
        db,
        'test_temporal',
        created['_key'],
        invalid_at=datetime(2024, 12, 31, tzinfo=timezone.utc),
        reason='Test invalidation'
    )
    print(f"Invalidated entity: {invalidated}")