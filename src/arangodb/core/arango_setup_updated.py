"""
ArangoDB Setup and Connection - Updated for Compatibility

Modified version of arango_setup.py with backward compatibility for older python-arango versions.
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from loguru import logger

# Import dependency checker for graceful handling of missing dependencies
try:
    # Try absolute import first (for installed package)
    from arangodb.core.utils.dependency_checker import (
        HAS_ARANGO,
        StandardDatabase
    )
except ImportError:
    # Fall back to relative import (for development)
    from .utils.dependency_checker import (
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
else:
    # Create mock classes if ArangoDB is not available
    class ArangoClient:
        """Mock ArangoDB client."""
        def __init__(self, hosts=None):
            logger.warning("Using mock ArangoClient - operations will fail")
            self.hosts = hosts
            
        def db(self, name=None, username=None, password=None, verify=True):
            """Return a mock database."""
            return MockDatabase(name, username, password)
    
    class MockDatabase:
        """Mock ArangoDB database."""
        def __init__(self, name=None, username=None, password=None):
            self.name = name
            self.username = username
            
        def ping(self):
            """Mock ping method."""
            raise RuntimeError("ArangoDB is not available")
            
        def has_database(self, name):
            """Mock database check."""
            return False
            
    # Mock exception classes
    class ServerConnectionError(Exception):
        """Mock ArangoDB server connection error."""
        pass
        
    class DatabaseCreateError(Exception):
        """Mock ArangoDB database creation error."""
        pass
        
    class CollectionCreateError(Exception):
        """Mock ArangoDB collection creation error."""
        pass
        
    class ViewCreateError(Exception):
        """Mock ArangoDB view creation error."""
        pass
        
    class GraphCreateError(Exception):
        """Mock ArangoDB graph creation error."""
        pass
        
    class IndexCreateError(Exception):
        """Mock ArangoDB index creation error."""
        pass

# Import core constants - use relative imports for better portability
try:
    # Try absolute import first (for installed package)
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
except ImportError:
    # Fall back to relative import (for development)
    from ..constants import (
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
    
    Attempts to connect to the ArangoDB instance specified in environment variables.
    Falls back to localhost with default credentials if not specified.
    
    Returns:
        ArangoClient: Connected ArangoDB client
        
    Raises:
        RuntimeError: If ArangoDB is not available
        ServerConnectionError: If connection to ArangoDB fails
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
    
    except ServerConnectionError as e:
        logger.error(f"Failed to connect to ArangoDB: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error connecting to ArangoDB: {e}")
        raise


def ensure_database(client: ArangoClient) -> StandardDatabase:
    """
    Ensure that the database exists, creating it if necessary.
    
    Args:
        client: Connected ArangoDB client
        
    Returns:
        StandardDatabase: Database instance
        
    Raises:
        DatabaseCreateError: If database creation fails
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
    
    except DatabaseCreateError as e:
        logger.error(f"Failed to create database: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error ensuring database: {e}")
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
        
    Raises:
        CollectionCreateError: If collection creation fails
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
    
    except CollectionCreateError as e:
        logger.error(f"Failed to create collection {collection_name}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error ensuring collection {collection_name}: {e}")
        raise


def ensure_arangosearch_view(
    db: StandardDatabase,
    view_name: str,
    collection_name: str,
    search_fields: List[str]
) -> None:
    """
    Ensure that an ArangoSearch view exists for a collection, creating it if necessary.
    Updated for compatibility with older versions of python-arango.
    
    Args:
        db: Database instance
        view_name: Name of the view
        collection_name: Name of the collection to include in the view
        search_fields: List of fields to include in the view
        
    Raises:
        ViewCreateError: If view creation fails
    """
    try:
        # First try to check if view exists and delete it using AQL (works in all versions)
        try:
            # Check if view exists by querying _views collection
            logger.info(f"Checking if view exists: {view_name}")
            view_exists = False
            
            try:
                # Try to use AQL to check for view existence
                cursor = db.aql.execute(
                    "FOR v IN _views FILTER v.name == @name RETURN v",
                    bind_vars={"name": view_name}
                )
                view_exists = len(list(cursor)) > 0
                
                if view_exists:
                    logger.info(f"Found existing view: {view_name}, deleting...")
                    db.aql.execute(
                        "FOR v IN _views FILTER v.name == @name REMOVE v IN _views",
                        bind_vars={"name": view_name}
                    )
                    logger.info(f"Deleted existing view: {view_name}")
                    
                    # Wait for deletion to complete
                    time.sleep(1)
            except Exception as e:
                # If _views collection doesn't exist, this will fail
                logger.warning(f"Could not check/delete view using AQL: {e}")
                
                # Try using API method if available
                if hasattr(db, 'has_view') and hasattr(db, 'delete_view'):
                    try:
                        if db.has_view(view_name):
                            db.delete_view(view_name)
                            logger.info(f"Deleted existing view using API method: {view_name}")
                            # Wait for deletion to complete
                            time.sleep(1)
                    except Exception as e2:
                        logger.warning(f"Could not delete view using API method: {e2}")
                
        except Exception as e:
            logger.warning(f"Error checking/deleting view: {e}")
        
        # Now try to create the view
        logger.info(f"Creating ArangoSearch view: {view_name}")
        
        # Try using the built-in method first
        try:
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
            logger.info(f"Created ArangoSearch view using API: {view_name}")
        except Exception as e:
            logger.warning(f"Could not create view using API method: {e}")
            
            # Fall back to AQL for creation
            try:
                logger.info(f"Attempting to create view using AQL: {view_name}")
                # Format fields for AQL
                fields_str = "{" + ", ".join([f'"{field}": {{}}' for field in search_fields]) + "}"
                
                aql = f"""
                LET fields = {fields_str}
                LET viewProps = {{
                    "name": "{view_name}",
                    "type": "arangosearch",
                    "links": {{
                        "{collection_name}": {{
                            "analyzers": ["text_en"],
                            "includeAllFields": false,
                            "fields": fields
                        }}
                    }}
                }}
                LET doc = DOCUMENT("_views/{view_name}", viewProps)
                RETURN doc
                """
                
                db.aql.execute(aql)
                logger.info(f"Created ArangoSearch view using AQL: {view_name}")
            except Exception as e2:
                logger.error(f"Failed to create view using AQL: {e2}")
                raise ViewCreateError(f"Could not create view {view_name}: {e2}")
                
        # Wait for view to be created and indexing to start
        logger.info(f"Waiting for view indexing to complete: {view_name}")
        time.sleep(2)
    
    except ViewCreateError as e:
        logger.error(f"Failed to create view {view_name}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error ensuring view {view_name}: {e}")
        raise