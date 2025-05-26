#!/usr/bin/env python
"""
Test script for enhanced QA exporter with context information.
"""

import sys
sys.path.append('.')

from arangodb.qa_generation.exporter import QAExporter
from arangodb.qa_generation.models import QAPair, QABatch, QuestionType

if __name__ == '__main__':
    # Create test data
    qa_pair1 = QAPair(
        question='What is ArangoDB?',
        answer='ArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models.',
        thinking='The document describes ArangoDB as a database system that supports multiple data models.',
        question_type=QuestionType.FACTUAL,
        confidence=0.95,
        source_section='Introduction',
        source_hash='abc123',
        citation_found=True,
        validation_score=0.98,
        temperature_used=0.1
    )
    
    qa_pair2 = QAPair(
        question='What are the key features of ArangoDB?',
        answer='Key features include native graph capabilities, AQL query language, and support for multiple data models.',
        thinking='The document lists several key features in the "Features" section.',
        question_type=QuestionType.FACTUAL,
        confidence=0.92,
        source_section='Features',
        source_hash='def456',
        citation_found=True,
        validation_score=0.96,
        temperature_used=0.1
    )
    
    # Create batch with rich metadata
    batch = QABatch(
        qa_pairs=[qa_pair1, qa_pair2],
        document_id='arangodb_overview',
        metadata={
            "file_summary": "Documentation about ArangoDB database system and its features",
            "parent_section": "Database Systems",
            "document_type": "Technical Documentation"
        }
    )
    
    # Create exporter
    exporter = QAExporter()
    
    # Test JSONL export with enhanced context
    jsonl_path = exporter.export_to_unsloth(batch, 'enhanced_export.jsonl', format='jsonl')
    print(f'Exported to JSONL with enhanced context: {jsonl_path}')
    
    # Open the file to verify content
    print('\nVerifying JSONL content with enhanced context:')
    with open(jsonl_path[0], 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            print(f"\nEntry {i+1}:")
            print(line)