#!/usr/bin/env python
"""
Test script for QA exporter.
"""

import sys
sys.path.append('.')

from arangodb.qa_generation.exporter import QAExporter
from arangodb.qa_generation.models import QAPair, QABatch, QuestionType

if __name__ == '__main__':
    # Create test data
    qa_pair = QAPair(
        question='What is ArangoDB?',
        answer='ArangoDB is a multi-model NoSQL database.',
        thinking='ArangoDB is a database system that supports multiple data models.',
        question_type=QuestionType.FACTUAL,
        confidence=0.95,
        source_section='introduction',
        source_hash='abc123',
        citation_found=True,
        validation_score=0.98,
        temperature_used=0.1
    )
    
    batch = QABatch(
        qa_pairs=[qa_pair],
        document_id='test_doc'
    )
    
    # Create exporter
    exporter = QAExporter()
    
    # Test export formats
    jsonl_path = exporter.export_to_unsloth(batch, 'test_export.jsonl', format='jsonl')
    print(f'Exported to JSONL: {jsonl_path}')
    
    json_path = exporter.export_to_unsloth(batch, 'test_export.json', format='json')
    print(f'Exported to JSON: {json_path}')
    
    # Test with split
    split_paths = exporter.export_to_unsloth(
        batch, 
        'test_export_split', 
        format='jsonl',
        split_ratio={"train": 0.8, "val": 0.1, "test": 0.1}
    )
    print(f'Exported with split: {split_paths}')
    
    # Open the files to verify content
    print('\nVerifying JSONL content:')
    with open(jsonl_path[0], 'r') as f:
        print(f.read())
        
    print('\nVerifying JSON content:')
    with open(json_path[0], 'r') as f:
        print(f.read())