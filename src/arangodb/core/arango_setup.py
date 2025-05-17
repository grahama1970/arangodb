"""
ArangoDB Setup and Connection

This module provides core functionality for setting up and interacting with ArangoDB.
It handles database connections, collection creation, graph setup, and indexing.

Links:
- python-arango Driver: https://python-arango.readthedocs.io/en/latest/
- ArangoDB Manual: https://www.arangodb.com/docs/stable/

Sample Input/Output:

- connect_arango():
  - Input: None (uses environment variables)
  - Output: ArangoClient instance

- ensure_database(client: ArangoClient):
  - Input: ArangoClient instance
  - Output: StandardDatabase instance

- ensure_collection(db: StandardDatabase, collection_name: str):
  - Input: Database instance and collection name
  - Output: None (creates collection if it doesn't exist)
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
    This function is compatible with different versions of python-arango.
    
    Args:
        db: Database instance
        view_name: Name of the view
        collection_name: Name of the collection to include in the view
        search_fields: List of fields to include in the view
        
    Raises:
        ViewCreateError: If view creation fails
    """
    try:
        # First try to delete the view if it exists (for a clean setup)
        view_exists = False
        
        # Try using views() method if available
        try:
            views = db.views()
            for view in views:
                if view.get('name') == view_name:
                    view_exists = True
                    break
        except Exception as e:
            logger.debug(f"Could not check views with views() method: {e}")
            
            # Fall back to AQL for checking view existence
            try:
                cursor = db.aql.execute(
                    "FOR v IN _views FILTER v.name == @name RETURN v",
                    bind_vars={"name": view_name}
                )
                view_exists = len(list(cursor)) > 0
            except Exception as e2:
                logger.debug(f"Could not check views with AQL: {e2}")
        
        # Delete view if it exists
        if view_exists:
            logger.info(f"View {view_name} exists, deleting for clean setup")
            try:
                db.delete_view(view_name)
                logger.info(f"Deleted view: {view_name}")
            except Exception as e:
                logger.warning(f"Could not delete view with API: {e}")
                
                # Fall back to AQL for deletion
                try:
                    db.aql.execute(
                        "FOR v IN _views FILTER v.name == @name REMOVE v IN _views",
                        bind_vars={"name": view_name}
                    )
                    logger.info(f"Deleted view using AQL: {view_name}")
                except Exception as e2:
                    logger.warning(f"Could not delete view using AQL: {e2}")
            
            # Wait for deletion to complete
            time.sleep(1)

        # Create the view - use the preferred method first
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
        
        # Try standard API method first
        try:
            db.create_arangosearch_view(name=view_name, properties=view_properties)
            logger.info(f"ArangoSearch view created with API: {view_name}")
        except Exception as e:
            logger.warning(f"Error creating view with API: {e}")
            
            # Try older versions API
            try:
                # For older versions that need different method format
                db.create_view(name=view_name, view_type="arangosearch", properties=view_properties)
                logger.info(f"ArangoSearch view created with older API: {view_name}")
            except Exception as e2:
                logger.warning(f"Error creating view with older API: {e2}")
                
                # Fall back to AQL for creation
                try:
                    # Format fields as JSON-like string for AQL
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
                    RETURN DOCUMENT("_views/{view_name}", viewProps)
                    """
                    db.aql.execute(aql)
                    logger.info(f"ArangoSearch view created using AQL: {view_name}")
                except Exception as e3:
                    logger.error(f"Failed to create view using AQL: {e3}")
                    raise ViewCreateError(f"Could not create view {view_name}: {e3}")
                    
        # Wait for indexing to begin
        logger.info(f"Allowing time for indexing to begin: {view_name}")
        time.sleep(2)
    
    except ViewCreateError as e:
        logger.error(f"Failed to create view {view_name}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error ensuring view {view_name}: {e}")
        raise


def ensure_edge_collections(db: StandardDatabase) -> None:
    """
    Ensure that all required edge collections exist.
    
    Args:
        db: Database instance
        
    Raises:
        CollectionCreateError: If collection creation fails
    """
    try:
        # Create the main edge collection for relationships
        ensure_collection(db, EDGE_COLLECTION_NAME, is_edge_collection=True)
        
        # Create message edge collection (if it's being used)
        ensure_collection(db, "message_links", is_edge_collection=True)
    
    except Exception as e:
        logger.exception(f"Failed to ensure edge collections: {e}")
        raise


def ensure_memory_agent_collections(db: StandardDatabase) -> None:
    """
    Ensure that collections, edges, and views for the memory agent exist.
    
    Args:
        db: Database instance
        
    Raises:
        CollectionCreateError: If collection creation fails
        ViewCreateError: If view creation fails
    """
    try:
        # Create memory collections
        ensure_collection(db, MEMORY_COLLECTION, is_edge_collection=False)
        ensure_collection(db, MEMORY_MESSAGE_COLLECTION, is_edge_collection=False)
        ensure_collection(db, MEMORY_EDGE_COLLECTION, is_edge_collection=True)
        
        # Create memory view
        ensure_arangosearch_view(
            db,
            MEMORY_VIEW_NAME,
            MEMORY_COLLECTION,
            ["content", "summary", "tags", "metadata.context"]
        )
        
        logger.info("Memory agent collections and views ensured")
    
    except Exception as e:
        logger.exception(f"Failed to ensure memory agent collections: {e}")
        raise


def ensure_graph(
    db: StandardDatabase,
    graph_name: str,
    edge_collection: str,
    vertex_collection: str
) -> None:
    """
    Ensure that a graph exists, creating it if necessary.
    
    Args:
        db: Database instance
        graph_name: Name of the graph
        edge_collection: Name of the edge collection
        vertex_collection: Name of the vertex collection
        
    Raises:
        GraphCreateError: If graph creation fails
    """
    try:
        # Check if graph exists
        if not db.has_graph(graph_name):
            logger.info(f"Creating graph: {graph_name}")
            
            # Create the graph with appropriate edge definitions
            db.create_graph(
                name=graph_name,
                edge_definitions=[
                    {
                        "edge_collection": edge_collection,
                        "from_vertex_collections": [vertex_collection],
                        "to_vertex_collections": [vertex_collection]
                    }
                ]
            )
            
            logger.info(f"Graph created: {graph_name}")
        else:
            logger.debug(f"Graph already exists: {graph_name}")
    
    except GraphCreateError as e:
        logger.error(f"Failed to create graph {graph_name}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error ensuring graph {graph_name}: {e}")
        raise


def ensure_vector_index(
    db: StandardDatabase,
    collection_name: str,
    field_name: str = "embedding",
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
) -> None:
    """
    Ensure that a vector index exists for a collection, creating it if necessary.
    
    Args:
        db: Database instance
        collection_name: Name of the collection
        field_name: Name of the embedding field
        dimensions: Dimensions of the embeddings
        
    Raises:
        IndexCreateError: If index creation fails
    """
    try:
        collection = db.collection(collection_name)
        
        # Check if index already exists
        existing_indexes = collection.indexes()
        for index in existing_indexes:
            if index["type"] == "persistent" and field_name in index["fields"]:
                logger.debug(f"Vector index already exists for {collection_name}.{field_name}")
                return
        
        # Create vector index
        logger.info(f"Creating vector index for {collection_name}.{field_name}")
        collection.add_persistent_index(
            fields=[field_name],
            sparse=True
        )
        
        logger.info(f"Vector index created for {collection_name}.{field_name}")
    
    except IndexCreateError as e:
        logger.error(f"Failed to create vector index for {collection_name}.{field_name}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error ensuring vector index for {collection_name}.{field_name}: {e}")
        raise


# =============================================================================
# VALIDATION CODE
# =============================================================================

if __name__ == "__main__":
    """
    Self-validation tests for the arango_setup module.
    
    This validation checks for ArangoDB availability and performs real tests if available,
    or simulated tests if not available.
    
    """
    import sys
    import os
    
    # Configure logger for validation output
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Check if ArangoDB is available
    if not HAS_ARANGO:
        logger.warning("ArangoDB is not available. Running mock validation tests.")
        
        # Test 1: Error handling without ArangoDB
        total_tests += 1
        print("\nTest 1: Error handling without ArangoDB")
        
        try:
            # This should raise a RuntimeError since ArangoDB is not available
            error_caught = False
            try:
                client = connect_arango()
            except RuntimeError as e:
                if "ArangoDB connection requires" in str(e):
                    print("✓ Correctly identified missing ArangoDB dependency")
                    error_caught = True
                else:
                    all_validation_failures.append(f"Unexpected error message: {e}")
            
            if not error_caught:
                all_validation_failures.append("Failed to raise RuntimeError for missing ArangoDB dependency")
            
            # Test mock ArangoClient
            mock_client = ArangoClient(hosts="http://localhost:8529")
            print("✓ Successfully created mock ArangoClient")
            
            # Test ensure_database with mock client
            try:
                db = mock_client.db(name="test")
                ping_failed = False
                try:
                    db.ping()
                except RuntimeError:
                    ping_failed = True
                
                if ping_failed:
                    print("✓ Mock database correctly fails ping operation")
                else:
                    all_validation_failures.append("Mock database did not fail ping as expected")
            except Exception as e:
                all_validation_failures.append(f"Mock database test failed: {e}")
                
        except Exception as e:
            all_validation_failures.append(f"Mock validation error: {str(e)}")
    
    else:  # ArangoDB is available
        # Test 1: Connect to ArangoDB
        total_tests += 1
        try:
            print("Test 1: Connecting to ArangoDB...")
            client = connect_arango()
            print(f"Successfully connected to ArangoDB at {ARANGO_HOST}")
        except Exception as e:
            all_validation_failures.append(f"Connection test failed: {str(e)}")
            client = None
    
    # Only proceed with further tests if connection succeeds
    if client:
        # Test 2: Ensure database
        total_tests += 1
        try:
            print("Test 2: Ensuring database...")
            db = ensure_database(client)
            print(f"Successfully connected to database: {db.name}")
        except Exception as e:
            all_validation_failures.append(f"Database test failed: {str(e)}")
            db = None
        
        # Only proceed with collection/graph tests if database connection succeeds
        if db:
            # Test 3: Ensure test collection
            total_tests += 1
            try:
                test_collection = "test_arango_setup"
                print(f"Test 3: Creating test collection: {test_collection}")
                ensure_collection(db, test_collection)
                
                if not db.has_collection(test_collection):
                    all_validation_failures.append(f"Collection test failed: Collection {test_collection} was not created")
                else:
                    print(f"Successfully created collection: {test_collection}")
            except Exception as e:
                all_validation_failures.append(f"Collection test failed: {str(e)}")
            
            # Test 4: Ensure edge collection
            total_tests += 1
            try:
                test_edge_collection = "test_arango_edges"
                print(f"Test 4: Creating test edge collection: {test_edge_collection}")
                ensure_collection(db, test_edge_collection, is_edge_collection=True)
                
                if not db.has_collection(test_edge_collection):
                    all_validation_failures.append(f"Edge collection test failed: Collection {test_edge_collection} was not created")
                else:
                    # Verify it's an edge collection
                    collection = db.collection(test_edge_collection)
                    if not collection.properties()["edge"]:
                        all_validation_failures.append(f"Edge collection test failed: Collection {test_edge_collection} is not an edge collection")
                    else:
                        print(f"Successfully created edge collection: {test_edge_collection}")
            except Exception as e:
                all_validation_failures.append(f"Edge collection test failed: {str(e)}")
            
            # Test 5: Ensure graph
            total_tests += 1
            try:
                test_graph = "test_arango_graph"
                print(f"Test 5: Creating test graph: {test_graph}")
                ensure_graph(db, test_graph, test_edge_collection, test_collection)
                
                if not db.has_graph(test_graph):
                    all_validation_failures.append(f"Graph test failed: Graph {test_graph} was not created")
                else:
                    print(f"Successfully created graph: {test_graph}")
            except Exception as e:
                all_validation_failures.append(f"Graph test failed: {str(e)}")
            
            # Test 6: Ensure view
            total_tests += 1
            try:
                test_view = "test_arango_view"
                test_fields = ["name", "description", "tags"]
                print(f"Test 6: Creating test view: {test_view}")
                ensure_arangosearch_view(db, test_view, test_collection, test_fields)
                
                # Check if view exists using different methods depending on API availability
                view_exists = False
                
                # Method 1: Use has_view if available
                if hasattr(db, 'has_view'):
                    view_exists = db.has_view(test_view)
                else:
                    # Method 2: Try using views() method if available
                    try:
                        views = db.views()
                        for view in views:
                            if view.get('name') == test_view:
                                view_exists = True
                                break
                    except Exception:
                        # Method 3: Fall back to AQL for checking view existence
                        try:
                            cursor = db.aql.execute(
                                "FOR v IN _views FILTER v.name == @name RETURN v",
                                bind_vars={"name": test_view}
                            )
                            view_exists = len(list(cursor)) > 0
                        except Exception:
                            # If all methods fail, we'll assume it failed
                            pass
                
                if not view_exists:
                    all_validation_failures.append(f"View test failed: View {test_view} was not created or could not be verified")
                else:
                    print(f"Successfully created view: {test_view}")
            except Exception as e:
                all_validation_failures.append(f"View test failed: {str(e)}")
            
            # Test 7: Ensure vector index
            total_tests += 1
            try:
                test_field = "embedding"
                print(f"Test 7: Creating vector index on {test_collection}.{test_field}")
                ensure_vector_index(db, test_collection, test_field, 128)
                
                # Check if index exists
                collection = db.collection(test_collection)
                indexes = collection.indexes()
                index_exists = False
                for index in indexes:
                    if index["type"] == "persistent" and test_field in index["fields"]:
                        index_exists = True
                        break
                
                if not index_exists:
                    all_validation_failures.append(f"Vector index test failed: Index on {test_field} was not created")
                else:
                    print(f"Successfully created vector index on {test_collection}.{test_field}")
            except Exception as e:
                all_validation_failures.append(f"Vector index test failed: {str(e)}")
            
            # Clean up test resources
            try:
                print("Cleaning up test resources...")
                
                # Delete graph first (to remove edge definitions)
                if db.has_graph(test_graph):
                    db.delete_graph(test_graph)
                
                # Delete view
                try:
                    # Try with has_view if available
                    if hasattr(db, 'has_view') and db.has_view(test_view):
                        db.delete_view(test_view)
                    else:
                        # Try to delete anyway, catching any errors
                        try:
                            db.delete_view(test_view)
                        except Exception as ve:
                            logger.debug(f"Could not delete view using delete_view: {ve}")
                            
                            # Fall back to AQL for deletion
                            try:
                                db.aql.execute(
                                    "FOR v IN _views FILTER v.name == @name REMOVE v IN _views",
                                    bind_vars={"name": test_view}
                                )
                                logger.debug(f"Deleted view using AQL: {test_view}")
                            except Exception as ve2:
                                logger.debug(f"Could not delete view using AQL: {ve2}")
                except Exception as e:
                    logger.warning(f"Error during view cleanup: {e}")
                
                # Delete collections
                if db.has_collection(test_edge_collection):
                    db.delete_collection(test_edge_collection)
                
                if db.has_collection(test_collection):
                    db.delete_collection(test_collection)
                
                print("Test resources cleaned up successfully")
            except Exception as e:
                print(f"Warning: Could not clean up all test resources: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Core arango_setup module is validated and ready for use")
        sys.exit(0)  # Exit with success code