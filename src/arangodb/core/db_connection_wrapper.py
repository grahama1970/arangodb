"""
Database Operations Wrapper

Provides a class-based interface to ArangoDB operations for compatibility
with Q&A generation module.
"""

from arango.database import StandardDatabase
from .arango_setup import connect_arango


class DatabaseOperations:
    """Wrapper class for database operations."""
    
    def __init__(self, db: StandardDatabase = None):
        """Initialize with database connection."""
        self.db = db or connect_arango()
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        return self.db.collection(collection_name)
    
    def query(self, aql: str, bind_vars: dict = None):
        """Execute an AQL query."""
        return self.db.aql.execute(aql, bind_vars=bind_vars)
    
    def document_exists(self, collection: str, key: str) -> bool:
        """Check if a document exists."""
        try:
            col = self.get_collection(collection)
            col.get(key)
            return True
        except:
            return False