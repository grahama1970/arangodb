"""
ArangoDB Setup and Connection - Compatible Version

This module provides core functionality for setting up and interacting with ArangoDB,
with backward compatibility for older versions of python-arango.
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from loguru import logger

# Import dependency checker for graceful handling of missing dependencies
from arangodb.core.utils.dependency_checker import (
    HAS_ARANGO,
    StandardDatabase
)

# Import ArangoDB if available
if HAS_ARANGO:
    from arango import ArangoClient
    from arango.collection import StandardCollection
    from arango.exceptions import (
        ServerConnectionError,
        DatabaseCreateError,
        CollectionCreateError,
        ViewCreateError,
        GraphCreateError,
        IndexCreateError
    )

# Import core constants
from arangodb.core.constants import (
    ARANGO_HOST,
    ARANGO_USER,
    ARANGO_PASSWORD,
    ARANGO_DB_NAME,
    COLLECTION_NAME,
    EDGE_COLLECTION_NAME,
    GRAPH_NAME,
    MEMORY_COLLECTION,
    MEMORY_EDGE_COLLECTION,
    MEMORY_VIEW_NAME,
    MEMORY_GRAPH_NAME,
    MEMORY_MESSAGE_COLLECTION,
    SEARCH_FIELDS,
    DEFAULT_EMBEDDING_DIMENSIONS
)

def connect_arango() -> ArangoClient:
    """
    Connect to ArangoDB using environment variables.
    
    Returns:
        ArangoClient: Connected ArangoDB client
    """
    # Check for ArangoDB availability
    if not HAS_ARANGO:
        error_msg = "ArangoDB connection requires python-arango, but it is not installed"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    try:
        # Get connection details from environment or use defaults
        host = ARANGO_HOST
        username = ARANGO_USER
        password = ARANGO_PASSWORD
        
        logger.debug(f"Connecting to ArangoDB at {host}")
        client = ArangoClient(hosts=host)
        
        # Connect to the system database to check connection
        sys_db = client.db(
            name="_system",
            username=username,
            password=password,
            verify=True
        )
        
        # Test the connection - ping() might not be available in all versions
        # so we use a more reliable approach to test the connection
        sys_db.properties()
        logger.debug("Successfully connected to ArangoDB")
        
        return client
    
    except Exception as e:
        logger.exception(f"Error connecting to ArangoDB: {e}")
        raise

def ensure_database(client: ArangoClient) -> StandardDatabase:
    """
    Ensure that the database exists, creating it if necessary.
    
    Args:
        client: Connected ArangoDB client
        
    Returns:
        StandardDatabase: Database instance
    """
    try:
        # Get connection details from environment or use defaults
        username = ARANGO_USER
        password = ARANGO_PASSWORD
        db_name = ARANGO_DB_NAME
        
        sys_db = client.db(
            name="_system",
            username=username,
            password=password,
            verify=True
        )
        
        # Create database if it doesn't exist
        if not sys_db.has_database(db_name):
            logger.info(f"Creating database: {db_name}")
            sys_db.create_database(
                name=db_name,
                users=[{
                    "username": username,
                    "password": password,
                    "active": True
                }]
            )
            logger.info(f"Database created: {db_name}")
        
        # Connect to the database
        db = client.db(
            name=db_name,
            username=username,
            password=password,
            verify=True
        )
        
        logger.debug(f"Connected to database: {db_name}")
        return db
    
    except Exception as e:
        logger.exception(f"Error ensuring database: {e}")
        raise

def ensure_collection(
    db: StandardDatabase,
    collection_name: str,
    is_edge_collection: bool = False
) -> None:
    """
    Ensure that a collection exists, creating it if necessary.
    
    Args:
        db: Database instance
        collection_name: Name of the collection
        is_edge_collection: Whether it's an edge collection
    """
    try:
        # Check if collection exists
        if not db.has_collection(collection_name):
            logger.info(f"Creating {'edge ' if is_edge_collection else ''}collection: {collection_name}")
            
            # Create either an edge or document collection
            if is_edge_collection:
                db.create_collection(
                    name=collection_name,
                    edge=True
                )
            else:
                db.create_collection(
                    name=collection_name
                )
            
            logger.info(f"Collection created: {collection_name}")
        else:
            logger.debug(f"Collection already exists: {collection_name}")
    
    except Exception as e:
        logger.exception(f"Error ensuring collection {collection_name}: {e}")
        raise

def ensure_arangosearch_view_compatible(
    db: StandardDatabase,
    view_name: str,
    collection_name: str,
    search_fields: List[str]
) -> None:
    """
    Ensure that an ArangoSearch view exists for a collection, creating it if necessary.
    This version is compatible with older versions of python-arango.
    
    Args:
        db: Database instance
        view_name: Name of the view
        collection_name: Name of the collection to include in the view
        search_fields: List of fields to include in the view
    """
    try:
        # First try to delete the view if it exists
        try:
            # Use AQL to check for view existence
            cursor = db.aql.execute(
                "FOR v IN _views FILTER v.name == @name RETURN v", 
                bind_vars={"name": view_name}
            )
            view_exists = len(list(cursor)) > 0
            
            if view_exists:
                logger.info(f"Deleting existing view: {view_name}")
                db.aql.execute(
                    "FOR v IN _views FILTER v.name == @name REMOVE v IN _views",
                    bind_vars={"name": view_name}
                )
                # Wait for deletion to complete
                time.sleep(1)
        except Exception as e:
            logger.warning(f"Could not check/delete view: {e}")
        
        # Create the view - use the method directly first
        try:
            logger.info(f"Creating ArangoSearch view: {view_name}")
            view_properties = {
                "links": {
                    collection_name: {
                        "analyzers": ["text_en"],
                        "includeAllFields": False,
                        "fields": {field: {} for field in search_fields}
                    }
                }
            }
            db.create_arangosearch_view(view_name, view_properties)
            logger.info(f"ArangoSearch view created: {view_name}")
        except Exception as e:
            logger.warning(f"Could not create view using standard method: {e}")
            
            # Fall back to AQL approach for older versions
            logger.info(f"Attempting to create view using AQL: {view_name}")
            # Convert fields dict to AQL string
            fields_str = "{" + ", ".join([f'"{field}": {{}}' for field in search_fields]) + "}"
            
            aql = f"""
            LET fields = {fields_str}
            LET viewProps = {{
                "type": "arangosearch",
                "links": {{
                    "{collection_name}": {{
                        "analyzers": ["text_en"],
                        "includeAllFields": false,
                        "fields": fields
                    }}
                }}
            }}
            RETURN DOCUMENT("_views/{view_name}", viewProps)
            """
            db.aql.execute(aql)
            logger.info(f"ArangoSearch view created using AQL: {view_name}")
        
        # Wait for indexing to complete
        time.sleep(2)
    
    except Exception as e:
        logger.exception(f"Error ensuring ArangoSearch view: {e}")
        raise

# Backward compatibility alias
ensure_arangosearch_view = ensure_arangosearch_view_compatible

def delete_arangosearch_view(db: StandardDatabase, view_name: str) -> bool:
    """
    Delete an ArangoSearch view if it exists, with compatibility for older python-arango.
    
    Args:
        db: Database instance
        view_name: Name of the view to delete
        
    Returns:
        bool: True if view was deleted or didn't exist, False if deletion failed
    """
    try:
        # Try to use AQL which should work in all versions
        db.aql.execute(
            "FOR v IN _views FILTER v.name == @name REMOVE v IN _views",
            bind_vars={"name": view_name}
        )
        logger.info(f"ArangoSearch view deleted: {view_name}")
        return True
    except Exception as e:
        logger.warning(f"Error deleting ArangoSearch view via AQL: {e}")
        
        # Try the direct method if available
        try:
            if hasattr(db, 'delete_view'):
                db.delete_view(view_name)
                logger.info(f"ArangoSearch view deleted with direct method: {view_name}")
                return True
        except Exception as e2:
            logger.warning(f"Error deleting ArangoSearch view with direct method: {e2}")
        
        return False