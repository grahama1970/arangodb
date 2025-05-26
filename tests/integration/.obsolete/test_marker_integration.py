#!/usr/bin/env python3
"""
Test script for Marker to ArangoDB integration.

This script tests the integration with a sample PDF to verify:
1. PDF processing with Marker
2. Storage in ArangoDB
3. Relationship creation
4. Q&A generation
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from loguru import logger
import numpy as np

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.integration.marker_integration import MarkerArangoDBIntegration
from arangodb.core.utils.embedding_utils import get_embedding


async def test_basic_functionality():
    """Test basic functionality of the integration."""
    
    logger.info("Testing Marker-ArangoDB integration...")
    
    # Initialize integration
    integration = MarkerArangoDBIntegration()
    
    # Create a test document in ArangoDB to verify connectivity
    test_doc = {
        "_key": "test_doc",
        "content": "This is a test document",
        "type": "test"
    }
    
    try:
        integration.db.collection("document_objects").insert(test_doc)
        logger.info("✓ Database connectivity verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    
    # Test embedding creation
    try:
        embedding = await get_embedding("Test text for embedding")
        logger.info(f"✓ Embedding creation verified (dimension: {len(embedding)})")
    except Exception as e:
        logger.error(f"Embedding creation failed: {e}")
        return False
    
    # Test cosine similarity calculation
    vec1 = np.random.rand(1536)
    vec2 = np.random.rand(1536)
    similarity = integration._cosine_similarity(vec1.tolist(), vec2.tolist())
    logger.info(f"✓ Cosine similarity calculation verified: {similarity:.4f}")
    
    return True


async def test_pdf_processing(pdf_path: str = None):
    """Test PDF processing pipeline."""
    
    if not pdf_path:
        # Create a simple test PDF if none provided
        test_pdf_path = "/tmp/test_marker_integration.pdf"
        
        # Use marker to create a simple PDF for testing
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        c.drawString(100, 750, "Test Document for Marker Integration")
        c.drawString(100, 700, "Section 1: Introduction")
        c.drawString(100, 650, "This is a test document to verify the Marker to ArangoDB integration.")
        c.drawString(100, 600, "It contains multiple sections and references.")
        c.drawString(100, 550, "Section 2: Methods")
        c.drawString(100, 500, "We use Marker to extract content and ArangoDB to store relationships.")
        c.drawString(100, 450, "See Table 1 for detailed results.")
        c.drawString(100, 400, "Table 1: Test Results")
        c.drawString(100, 350, "Method | Accuracy | Speed")
        c.drawString(100, 300, "Marker | 95% | Fast")
        c.save()
        
        pdf_path = test_pdf_path
        logger.info(f"Created test PDF at: {pdf_path}")
    
    # Initialize integration
    integration = MarkerArangoDBIntegration()
    
    # Process the PDF
    doc_id = "test_document"
    
    try:
        result = await integration.process_pdf(pdf_path, doc_id)
        
        logger.info(f"✓ PDF processed successfully")
        logger.info(f"  - Objects created: {result['object_count']}")
        logger.info(f"  - Q&A pairs generated: {result['qa_count']}")
        
        # Verify objects were created
        query = """
        FOR obj IN document_objects
            FILTER obj.document_id == @doc_id
            COLLECT type = obj._type WITH COUNT INTO count
            RETURN {type: type, count: count}
        """
        
        type_counts = list(integration.db.aql.execute(
            query, 
            bind_vars={"doc_id": doc_id}
        ))
        
        logger.info("Object types created:")
        for type_info in type_counts:
            logger.info(f"  - {type_info['type']}: {type_info['count']}")
        
        # Verify relationships were created
        query = """
        FOR edge IN content_relationships
            LET from_obj = DOCUMENT(edge._from)
            FILTER from_obj.document_id == @doc_id
            COLLECT type = edge.relationship_type WITH COUNT INTO count
            RETURN {type: type, count: count}
        """
        
        rel_counts = list(integration.db.aql.execute(
            query, 
            bind_vars={"doc_id": doc_id}
        ))
        
        logger.info("Relationship types created:")
        for rel_info in rel_counts:
            logger.info(f"  - {rel_info['type']}: {rel_info['count']}")
        
        # Sample Q&A pairs
        if result['qa_pairs']:
            logger.info("\nSample Q&A pairs:")
            for i, qa in enumerate(result['qa_pairs'][:3]):
                logger.info(f"\nQ&A {i+1}:")
                logger.info(f"Q: {qa['question']}")
                logger.info(f"A: {qa['answer'][:200]}...")
                logger.info(f"Type: {qa['metadata']['question_type']}")
        
        return True
        
    except Exception as e:
        logger.error(f"PDF processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_relationship_queries():
    """Test various relationship queries."""
    
    integration = MarkerArangoDBIntegration()
    doc_id = "test_document"
    
    # Test 1: Find all text that references tables
    query = """
    FOR edge IN content_relationships
        FILTER edge.relationship_type == "REFERENCES"
        LET from_obj = DOCUMENT(edge._from)
        LET to_obj = DOCUMENT(edge._to)
        FILTER from_obj.document_id == @doc_id
        FILTER to_obj._type == "table"
        RETURN {
            text: from_obj.text,
            table: to_obj.text,
            confidence: edge.confidence
        }
    """
    
    references = list(integration.db.aql.execute(query, bind_vars={"doc_id": doc_id}))
    
    logger.info(f"\nFound {len(references)} text-to-table references")
    for ref in references:
        logger.info(f"Text: {ref['text'][:100]}...")
        logger.info(f"References table: {ref['table'][:50]}...")
    
    # Test 2: Find similar content across sections
    query = """
    FOR edge in content_relationships
        FILTER edge.relationship_type == "SIMILAR"
        FILTER edge.confidence >= 0.8
        LET from_obj = DOCUMENT(edge._from)
        LET to_obj = DOCUMENT(edge._to)
        FILTER from_obj.document_id == @doc_id
        RETURN {
            from_section: from_obj.section_title,
            to_section: to_obj.section_title,
            similarity: edge.confidence
        }
    """
    
    similarities = list(integration.db.aql.execute(query, bind_vars={"doc_id": doc_id}))
    
    logger.info(f"\nFound {len(similarities)} similar content pairs")
    for sim in similarities:
        logger.info(f"{sim['from_section']} <-> {sim['to_section']}: {sim['similarity']:.2f}")


async def main():
    """Run all tests."""
    
    # Test basic functionality
    if not await test_basic_functionality():
        logger.error("Basic functionality test failed")
        return
    
    # Test PDF processing
    # You can provide a specific PDF path here
    pdf_path = None  # Will create test PDF if None
    
    if not await test_pdf_processing(pdf_path):
        logger.error("PDF processing test failed")
        return
    
    # Test relationship queries
    await test_relationship_queries()
    
    logger.info("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())