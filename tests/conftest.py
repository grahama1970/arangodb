"""Pytest configuration file for ArangoDB tests."""

import os
import sys
import pytest
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Configure test environment variables
os.environ['ARANGODB_TEST_MODE'] = 'true'
os.environ['ARANGODB_DATABASE'] = 'pizza_test'
os.environ['ARANGO_DB_NAME'] = 'pizza_test'  # This is what the code actually uses

# Pytest configuration
pytest_plugins = []

@pytest.fixture(scope='session')
def arangodb_test_db():
    """Provide test database connection."""
    from arangodb.core.arango_setup import connect_arango, ensure_database
    
    # Connect to ArangoDB
    client = connect_arango()
    
    # Use test database
    test_db_name = 'test_arangodb'
    try:
        db = client.database(test_db_name)
    except:
        # Create test database if it doesn't exist
        sys_db = client.database('_system')
        sys_db.create_database(test_db_name)
        db = client.database(test_db_name)
    
    yield db
    
    # Cleanup is done manually if needed

@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / 'fixtures'