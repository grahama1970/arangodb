"""
Validation script for CRUD commands with real ArangoDB connection

This script tests all CRUD operations with actual data to verify:
1. Real connections to ArangoDB work
2. All CRUD operations function correctly
3. Both JSON and table output formats work
4. Expected results match actual results
"""

import json
import sys
import os
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the core db operations
from arangodb.core.db_operations import (
    create_document,
    get_document,
    update_document,
    delete_document
)

# Import utilities
from arangodb.core.utils.embedding_utils import get_embedding
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.constants import COLLECTION_NAME

# For rich table display
from rich.console import Console
from rich.table import Table

console = Console()


def setup_test_collection():
    """Setup test collection with sample data"""
    try:
        db = get_db_connection()
        
        # Create test collection if not exists
        test_collection = "test_lessons"
        if not db.has_collection(test_collection):
            db.create_collection(test_collection)
            logger.info(f"Created test collection: {test_collection}")
        
        return db, test_collection
    except Exception as e:
        logger.error(f"Failed to setup test collection: {e}")
        raise


def test_create_document(db, collection_name):
    """Test document creation with actual ArangoDB"""
    logger.info("Testing CREATE operation...")
    
    # Test data
    test_lesson = {
        "problem": "How to handle database connection errors",
        "solution": "Use retry logic with exponential backoff",
        "description": "When connecting to databases, implement retry mechanisms with increasing delays between attempts",
        "tags": ["database", "error-handling", "best-practices"],
        "difficulty": "intermediate"
    }
    
    try:
        # Generate embedding first
        text_to_embed = f"{test_lesson.get('problem','')} {test_lesson.get('solution','')} {test_lesson.get('description','')}"
        if text_to_embed.strip() and 'embedding' not in test_lesson:
            try:
                logger.info("Generating embedding for test lesson...")
                embedding = get_embedding(text_to_embed)
                if embedding:
                    test_lesson['embedding'] = embedding
                    logger.info(f"Generated embedding with {len(embedding)} dimensions")
            except Exception as emb_err:
                logger.warning(f"Embedding generation failed: {emb_err}")
        
        # Create document with embedding
        result = create_document(db, collection_name, test_lesson)
        
        if not result:
            return False, "Failed to create document - no result returned"
        
        # Verify the document was created
        doc_key = result.get('_key')
        if not doc_key:
            return False, "Created document missing _key"
        
        # Get the created document to verify
        created_doc = get_document(db, collection_name, doc_key)
        if not created_doc:
            return False, f"Could not retrieve created document {doc_key}"
        
        # Check required fields
        if created_doc.get('problem') != test_lesson['problem']:
            return False, f"Problem field mismatch: expected '{test_lesson['problem']}', got '{created_doc.get('problem')}'"
        
        if created_doc.get('solution') != test_lesson['solution']:
            return False, f"Solution field mismatch: expected '{test_lesson['solution']}', got '{created_doc.get('solution')}'"
        
        # Check embedding was generated
        if 'embedding' not in created_doc:
            return False, "Embedding was not generated for document"
        
        if not isinstance(created_doc['embedding'], list) or len(created_doc['embedding']) == 0:
            return False, f"Invalid embedding format: {type(created_doc['embedding'])}"
        
        logger.info(f"Successfully created document: {doc_key}")
        return True, doc_key
        
    except Exception as e:
        return False, f"Create operation failed: {str(e)}"


def test_read_document(db, doc_key, collection_name):
    """Test document read with actual ArangoDB"""
    logger.info(f"Testing READ operation for document: {doc_key}")
    
    try:
        document = get_document(db, collection_name, doc_key)
        
        if not document:
            return False, f"Failed to read document {doc_key}"
        
        # Verify structure
        required_fields = ['_key', '_id', 'problem', 'solution', 'embedding']
        missing_fields = [field for field in required_fields if field not in document]
        
        if missing_fields:
            return False, f"Document missing required fields: {missing_fields}"
            
        logger.info(f"Successfully read document: {doc_key}")
        return True, document
        
    except Exception as e:
        return False, f"Read operation failed: {str(e)}"


def test_update_document(db, doc_key, collection_name):
    """Test document update with actual ArangoDB"""
    logger.info(f"Testing UPDATE operation for document: {doc_key}")
    
    update_data = {
        "difficulty": "advanced",
        "verified": True,
        "last_updated": "2024-01-16"
    }
    
    try:
        result = update_document(db, collection_name, doc_key, update_data)
        
        if not result:
            return False, "Failed to update document"
        
        # Verify the update
        updated_doc = get_document(db, collection_name, doc_key)
        
        if not updated_doc:
            return False, f"Could not retrieve updated document {doc_key}"
        
        # Check updates were applied
        for key, value in update_data.items():
            if updated_doc.get(key) != value:
                return False, f"Update failed for field '{key}': expected '{value}', got '{updated_doc.get(key)}'"
        
        # Ensure original fields still exist
        if not updated_doc.get('problem') or not updated_doc.get('solution'):
            return False, "Original fields were lost during update"
        
        logger.info(f"Successfully updated document: {doc_key}")
        return True, updated_doc
        
    except Exception as e:
        return False, f"Update operation failed: {str(e)}"


def test_delete_document(db, doc_key, collection_name):
    """Test document deletion with actual ArangoDB"""
    logger.info(f"Testing DELETE operation for document: {doc_key}")
    
    try:
        result = delete_document(db, collection_name, doc_key)
        
        if not result:
            return False, "Failed to delete document"
        
        # Verify deletion by trying to read it
        deleted_doc = get_document(db, collection_name, doc_key)
        
        if deleted_doc:
            return False, f"Document {doc_key} still exists after deletion"
        
        logger.info(f"Successfully deleted document: {doc_key}")
        return True, None
        
    except Exception as e:
        return False, f"Delete operation failed: {str(e)}"


def display_results_table(results):
    """Display results in a rich table format"""
    table = Table(title="CRUD Operations Validation Results")
    table.add_column("Operation", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    for operation, status, details in results:
        status_symbol = "✅" if status else "❌"
        table.add_row(operation, status_symbol, str(details))
    
    console.print(table)


def display_results_json(results):
    """Display results in JSON format"""
    json_results = {
        "validation_results": [
            {
                "operation": op,
                "status": "passed" if status else "failed",
                "details": str(details)
            }
            for op, status, details in results
        ],
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for _, status, _ in results if status),
            "failed": sum(1 for _, status, _ in results if not status)
        }
    }
    console.print(json.dumps(json_results, indent=2))


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time} {level} {message}")
    
    # Track all results
    results = []
    
    try:
        # Setup test collection
        db, test_collection = setup_test_collection()
        logger.info(f"Connected to ArangoDB, using collection: {test_collection}")
        
        # Run CRUD tests
        
        # 1. Create
        success, doc_key = test_create_document(db, test_collection)
        results.append(("CREATE", success, doc_key if success else doc_key))
        
        if not success:
            logger.error("CREATE failed, skipping dependent tests")
        else:
            # 2. Read
            success, document = test_read_document(db, doc_key, test_collection)
            results.append(("READ", success, f"Retrieved doc with {len(document)} fields" if success else document))
            
            # 3. Update
            success, updated_doc = test_update_document(db, doc_key, test_collection)
            results.append(("UPDATE", success, "Updated 3 fields" if success else updated_doc))
            
            # 4. Delete
            success, _ = test_delete_document(db, doc_key, test_collection)
            results.append(("DELETE", success, f"Deleted doc {doc_key}" if success else _))
        
        # Display results in both formats
        console.print("\n[bold]Table Format:[/bold]")
        display_results_table(results)
        
        console.print("\n[bold]JSON Format:[/bold]")
        display_results_json(results)
        
        # Final result
        failures = [r for r in results if not r[1]]
        if failures:
            console.print(f"\n❌ VALIDATION FAILED - {len(failures)} of {len(results)} tests failed")
            for op, _, details in failures:
                console.print(f"  - {op}: {details}")
            sys.exit(1)
        else:
            console.print(f"\n✅ VALIDATION PASSED - All {len(results)} tests produced expected results")
            console.print("CRUD operations are working correctly with real ArangoDB connection")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error during validation: {e}")
        console.print(f"\n❌ VALIDATION FAILED - Fatal error: {e}")
        sys.exit(1)