"""
Module: migrate_to_bitemporal.py

External Dependencies:
- loguru: https://loguru.readthedocs.io/
- arango: https://docs.python-arango.com/

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

#!/usr/bin/env python3
"""
Migration script to add bi-temporal fields to existing documents.

This script updates all documents in specified collections to include
valid_at, created_at, and invalid_at fields for bi-temporal tracking.
"""

import sys
from datetime import datetime, timezone
from loguru import logger
from typing import List

from arangodb.core.db_operations import get_db_connection
from arangodb.core.temporal_operations import ensure_temporal_fields
from arangodb.core.constants import (
    MEMORY_MESSAGE_COLLECTION,
    MEMORY_COLLECTION,
    ENTITIES_COLLECTION,
    EDGES_COLLECTION
)

def migrate_collection(db, collection_name: str):
    """
    Migrate a single collection to bi-temporal format.
    
    Args:
        db: ArangoDB database instance
        collection_name: Name of the collection to migrate
    """
    logger.info(f"Starting migration for collection: {collection_name}")
    
    try:
        collection = db.collection(collection_name)
        count = 0
        updated = 0
        errors = 0
        
        # Process documents in batches
        batch_size = 100
        skip = 0
        
        while True:
            query = f"""
            FOR doc IN {collection_name}
                LIMIT {skip}, {batch_size}
                RETURN doc
            """
            
            cursor = db.aql.execute(query)
            documents = list(cursor)
            
            if not documents:
                break
                
            for doc in documents:
                count += 1
                
                # Check if document already has temporal fields
                if 'valid_at' in doc and 'created_at' in doc:
                    logger.debug(f"Document {doc['_key']} already has temporal fields")
                    continue
                
                try:
                    # Get timestamp from existing fields
                    timestamp = None
                    if 'timestamp' in doc:
                        timestamp = doc['timestamp']
                        if isinstance(timestamp, str):
                            timestamp = datetime.fromisoformat(timestamp)
                    elif 'created_at' in doc:
                        timestamp = doc['created_at']
                        if isinstance(timestamp, str):
                            timestamp = datetime.fromisoformat(timestamp)
                    else:
                        # Use current time as fallback
                        timestamp = datetime.now(timezone.utc)
                    
                    # Update document with temporal fields
                    update_data = {
                        'created_at': doc.get('created_at', timestamp.isoformat()),
                        'valid_at': doc.get('valid_at', timestamp.isoformat()),
                        'invalid_at': doc.get('invalid_at', None)
                    }
                    
                    collection.update({'_key': doc['_key']}, update_data)
                    updated += 1
                    
                except Exception as e:
                    logger.error(f"Error updating document {doc['_key']}: {e}")
                    errors += 1
            
            skip += batch_size
            
            # Progress update
            if count % 1000 == 0:
                logger.info(f"Processed {count} documents, updated {updated}, errors {errors}")
        
        logger.info(f"Migration complete for {collection_name}:")
        logger.info(f"  Total documents: {count}")
        logger.info(f"  Updated: {updated}")
        logger.info(f"  Errors: {errors}")
        
    except Exception as e:
        logger.error(f"Failed to migrate collection {collection_name}: {e}")
        raise

def create_indexes(db, collection_name: str):
    """
    Create temporal indexes for a collection.
    
    Args:
        db: ArangoDB database instance
        collection_name: Name of the collection
    """
    try:
        from arangodb.core.temporal_operations import create_temporal_indexes
        create_temporal_indexes(db, collection_name)
        logger.info(f"Created temporal indexes for {collection_name}")
    except Exception as e:
        logger.warning(f"Failed to create indexes for {collection_name}: {e}")

def main():
    """Main migration function."""
    # Collections to migrate
    collections = [
        MEMORY_MESSAGE_COLLECTION,
        # MEMORY_COLLECTION,
        # ENTITIES_COLLECTION,
        # EDGES_COLLECTION,
        # Add other collections as needed
    ]
    
    logger.info("Starting bi-temporal migration...")
    
    try:
        db = get_db_connection()
        
        # Migrate each collection
        for collection_name in collections:
            migrate_collection(db, collection_name)
            create_indexes(db, collection_name)
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("migration.log", level="DEBUG", rotation="10 MB")
    
    # Run migration
    main()