#!/usr/bin/env python
"""
Test script for context-enriched QA exports.

This script demonstrates how context generation and export works with ArangoDB's
relationship tracking for more comprehensive context in QA pairs.
"""

import sys
import asyncio
sys.path.append('.')

from src.arangodb.qa_generation.exporter import QAExporter
from src.arangodb.qa_generation.models import QAPair, QABatch, QuestionType
from src.arangodb.core.context_generator import ContextGenerator
from src.arangodb.core.db_operations import DatabaseOperations


async def main():
    """Run the context enrichment test."""
    print("Testing context-enriched QA export...")
    
    # Initialize database connection
    db = DatabaseOperations()
    
    # Initialize context generator and exporter
    context_generator = ContextGenerator(db)
    exporter = QAExporter(db=db)
    
    # Create a sample document in the database (if it doesn't exist)
    sample_doc_id = "marker_docs/arangodb_overview"
    document = db.get_document(sample_doc_id)
    
    if not document:
        print(f"Creating sample document '{sample_doc_id}'...")
        sample_doc = {
            "_id": sample_doc_id,
            "title": "ArangoDB Overview",
            "source": "Technical Documentation",
            "raw_corpus": {
                "full_text": "Introduction to ArangoDB\n\nArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models.\n\nKey Features\n\nArangoDB includes native graph capabilities, full-text search, and GeoJSON support."
            },
            "pages": [
                {
                    "page_num": 1,
                    "blocks": [
                        {
                            "block_id": "block_001",
                            "type": "section_header",
                            "level": 1,
                            "text": "Introduction to ArangoDB"
                        },
                        {
                            "block_id": "block_002",
                            "type": "text",
                            "text": "ArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models."
                        },
                        {
                            "block_id": "block_003",
                            "type": "section_header",
                            "level": 2,
                            "text": "Key Features"
                        },
                        {
                            "block_id": "block_004",
                            "type": "text",
                            "text": "ArangoDB includes native graph capabilities, full-text search, and GeoJSON support."
                        }
                    ]
                }
            ]
        }
        
        created = db.create_document(sample_doc, "marker_docs")
        if not created:
            print("Failed to create sample document.")
            sys.exit(1)
        
        document = sample_doc
    
    # Create test QA pairs
    qa_pair1 = QAPair(
        question="What is ArangoDB?",
        answer="ArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models.",
        thinking="The document describes ArangoDB as a database system that supports multiple data models.",
        question_type=QuestionType.FACTUAL,
        confidence=0.95,
        source_section="block_001",  # Reference the introduction section
        source_hash="abc123",
        citation_found=True,
        validation_score=0.98,
        temperature_used=0.1
    )
    
    qa_pair2 = QAPair(
        question="What are the key features of ArangoDB?",
        answer="ArangoDB includes native graph capabilities, full-text search, and GeoJSON support.",
        thinking="The document lists several key features in the 'Key Features' section.",
        question_type=QuestionType.FACTUAL,
        confidence=0.92,
        source_section="block_003",  # Reference the key features section
        source_hash="def456",
        citation_found=True,
        validation_score=0.96,
        temperature_used=0.1
    )
    
    # Create batch with document ID
    batch = QABatch(
        qa_pairs=[qa_pair1, qa_pair2],
        document_id=sample_doc_id.split("/")[-1]  # Use just the ID part
    )
    
    # Export with context enrichment
    print("Exporting QA pairs with context enrichment...")
    enriched_output_path = await exporter.export_to_unsloth(
        batch, 
        "context_enriched_export.jsonl", 
        format="jsonl",
        enrich_context=True  # Enable context enrichment
    )
    
    print(f"Exported to: {enriched_output_path}")
    
    # Compare with regular export (no context enrichment)
    print("\nExporting QA pairs without context enrichment for comparison...")
    regular_output_path = await exporter.export_to_unsloth(
        batch, 
        "regular_export.jsonl", 
        format="jsonl",
        enrich_context=False  # Disable context enrichment
    )
    
    print(f"Regular export to: {regular_output_path}")
    
    # Display the enriched output
    print("\nEnriched export content:")
    with open(enriched_output_path[0], 'r') as f:
        enriched_content = f.read()
        print(enriched_content)
    
    # Display the regular output
    print("\nRegular export content:")
    with open(regular_output_path[0], 'r') as f:
        regular_content = f.read()
        print(regular_content)
    
    print("\nTest complete!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())