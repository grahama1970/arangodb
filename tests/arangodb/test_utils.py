"""
Test utilities for ArangoDB memory bank tests.

Provides helper functions for setting up and tearing down test databases.
"""

import os
import uuid
from loguru import logger
from arango import ArangoClient

from arangodb.core.arango_setup import connect_arango


def setup_test_db(test_name: str = "test"):
    """
    Set up a test database with a unique name.
    
    Args:
        test_name: Base name for the test database
        
    Returns:
        An ArangoDB database instance for testing
    """
    # Create unique database name
    db_name = f"test_{test_name}_{uuid.uuid4().hex[:8]}"
    
    # Connect to ArangoDB
    client = ArangoClient(
        hosts=os.environ.get("ARANGO_HOST", "http://localhost:8529")
    )
    
    # Connect as root to create test database
    sys_db = client.db(
        name="_system",
        username=os.environ.get("ARANGO_USERNAME", "root"),
        password=os.environ.get("ARANGO_PASSWORD", "openSesame")
    )
    
    # Create test database
    try:
        sys_db.create_database(db_name)
        logger.info(f"Created test database: {db_name}")
    except Exception as e:
        logger.error(f"Failed to create test database: {e}")
        raise
    
    # Connect to test database
    db = client.db(
        name=db_name,
        username=os.environ.get("ARANGO_USERNAME", "root"),
        password=os.environ.get("ARANGO_PASSWORD", "openSesame")
    )
    
    return db


def teardown_test_db(db):
    """
    Tear down a test database.
    
    Args:
        db: The test database to tear down
    """
    db_name = db.name
    
    # Connect to system database
    client = ArangoClient(
        hosts=os.environ.get("ARANGO_HOST", "http://localhost:8529")
    )
    
    sys_db = client.db(
        name="_system",
        username=os.environ.get("ARANGO_USERNAME", "root"),
        password=os.environ.get("ARANGO_PASSWORD", "openSesame")
    )
    
    # Drop test database
    try:
        sys_db.delete_database(db_name)
        logger.info(f"Deleted test database: {db_name}")
    except Exception as e:
        logger.error(f"Failed to delete test database: {e}")
        # Don't raise - we want tests to continue even if cleanup fails