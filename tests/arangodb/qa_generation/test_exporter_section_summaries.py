#!/usr/bin/env python
"""
Test script for enhanced QA exporter with section summaries.
"""

import sys
import asyncio
sys.path.append('.')

from arangodb.qa_generation.exporter import QAExporter
from arangodb.qa_generation.models import QAPair, QABatch, QuestionType, DifficultyLevel

async def main():
    # Create test data with section summaries
    qa_pair1 = QAPair(
        question='What is ArangoDB?',
        answer='ArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models.',
        thinking='The document describes ArangoDB as a database system that supports multiple data models.',
        question_type=QuestionType.FACTUAL,
        difficulty=DifficultyLevel.EASY,
        confidence=0.95,
        source_section='Introduction',
        source_hash='abc123',
        citation_found=True,
        validation_score=0.98,
        temperature_used=0.1,
        section_summary='This section introduces ArangoDB as a multi-model database system.'
    )
    
    qa_pair2 = QAPair(
        question='What are the key features of ArangoDB?',
        answer='Key features include native graph capabilities, AQL query language, and support for multiple data models.',
        thinking='The document lists several key features in the "Features" section.',
        question_type=QuestionType.FACTUAL,
        difficulty=DifficultyLevel.MEDIUM,
        confidence=0.92,
        source_section='Features',
        source_hash='def456',
        citation_found=True,
        validation_score=0.96,
        temperature_used=0.1,
        section_summary='This section outlines the key features and capabilities of ArangoDB.'
    )
    
    # Create batch with rich metadata including section summaries
    batch = QABatch(
        qa_pairs=[qa_pair1, qa_pair2],
        document_id='arangodb_overview',
        metadata={
            "file_summary": "Documentation about ArangoDB database system and its features",
            "parent_section": "Database Systems",
            "document_type": "Technical Documentation",
            "section_summary_Introduction": "Overview and introduction to ArangoDB database system",
            "section_summary_Features": "Detailed description of ArangoDB's capabilities and features"
        }
    )
    
    # Create exporter
    exporter = QAExporter()
    
    # Test JSONL export with section summaries
    jsonl_paths = await exporter.export_to_unsloth(batch, 'section_summaries_export.jsonl', format='jsonl')
    print(f'Exported to JSONL with section summaries: {jsonl_paths}')
    
    # Open the file to verify content
    print('\nVerifying JSONL content with section summaries:')
    if jsonl_paths and len(jsonl_paths) > 0:
        with open(jsonl_paths[0], 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                print(f"\nEntry {i+1}:")
                print(line)

if __name__ == '__main__':
    asyncio.run(main())