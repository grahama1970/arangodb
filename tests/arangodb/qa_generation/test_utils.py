"""
Test utilities for QA generation module.

This module provides stubs and mock objects for testing the QA generation
module without database dependencies.
"""

import asyncio

class MockDatabaseOperations:
    """Mock implementation of DatabaseOperations for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock database operations."""
        self.aql = MockAQL()
    
    def get_document_by_id(self, doc_id):
        """Mock method to get a document by ID."""
        return {"_id": doc_id, "text": f"Sample document {doc_id}"}
    
    def run_query(self, query, bind_vars=None):
        """Mock method to run a query."""
        return []


class MockAQL:
    """Mock AQL executor."""
    
    def execute(self, query, bind_vars=None):
        """Mock execute method."""
        return []


class MockContextGenerator:
    """Mock context generator for testing."""
    
    def __init__(self, db=None):
        """Initialize mock context generator."""
        self.db = db or MockDatabaseOperations()
    
    async def generate_document_context(self, document_id):
        """Generate mock document context."""
        await asyncio.sleep(0.1)  # Simulate async operation
        return {
            "summary": f"Summary of document {document_id}",
            "source": "test_document",
            "section_summaries": {
                "intro": "Introduction to the document",
                "main": "Main content of the document",
                "conclusion": "Conclusion of the document"
            }
        }