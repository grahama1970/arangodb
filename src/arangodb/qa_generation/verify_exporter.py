"""
Verify the QA exporter functionality.
Module: verify_exporter.py
Description: Functions for verify exporter operations

This module tests the QA exporter with sample data to ensure it works
correctly for both JSONL and JSON formats with train/validation/test splits.
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

# Mock classes to avoid database dependencies
from .test_utils import MockContextGenerator

# Patch the context generator import in exporter.py
import importlib.util
import sys
# REMOVED: # REMOVED: 
# Create a mock module
mock_module = Magicobject()
mock_module.ContextGenerator = MockContextGenerator
sys.modules['src.arangodb.core.context_generator'] = mock_module

# Now import our models and exporter
from .models import QAPair, QABatch, QuestionType
from .exporter import QAExporter

# Replace the ContextGenerator with our mock
if hasattr(QAExporter, '__init__'):
    original_init = QAExporter.__init__
    
    def patched_init(self, output_dir="qa_output", db=None):
        original_init(self, output_dir, db)
        self.context_generator = MockContextGenerator(db)
    
    QAExporter.__init__ = patched_init


async def create_sample_qa_data() -> QABatch:
    """
    Create sample QA data for testing.
    
    Returns:
        QABatch with test data
    """
    # Create test QA pairs
    qa_pairs = []
    
    # Sample QA pairs of different types
    qa_factual = QAPair(
        question="What is ArangoDB?",
        thinking="ArangoDB is a multi-model database system. Let me extract the key details from the content.",
        answer="ArangoDB is a multi-model NoSQL database that combines document, graph, and key-value data models with a unified query language called AQL (ArangoDB Query Language).",
        question_type=QuestionType.FACTUAL,
        confidence=0.95,
        temperature_used=0.1,
        source_section="introduction",
        source_hash="abc123",
        validation_score=0.98,
        citation_found=True
    )
    qa_pairs.append(qa_factual)
    
    qa_comparative = QAPair(
        question="How does ArangoDB compare to MongoDB?",
        thinking="This is a comparative question about two database systems.",
        answer="ArangoDB differs from MongoDB in that it natively supports graphs and offers a unified query language (AQL) for all data models, while MongoDB is primarily document-oriented and uses a different query approach.",
        question_type=QuestionType.COMPARATIVE,
        confidence=0.90,
        temperature_used=0.2,
        source_section="comparison",
        source_hash="def456",
        validation_score=0.92,
        citation_found=True
    )
    qa_pairs.append(qa_comparative)
    
    qa_hierarchical = QAPair(
        question="What are the main components of ArangoDB's architecture?",
        thinking="Let me identify the key architectural components mentioned in the document.",
        answer="ArangoDB's architecture consists of the storage engine (RocksDB), the AQL query executor, the network layer for client communications, and the replication system for high availability.",
        question_type=QuestionType.HIERARCHICAL,
        confidence=0.88,
        temperature_used=0.1,
        source_section="architecture",
        source_hash="ghi789",
        validation_score=0.91,
        citation_found=True
    )
    qa_pairs.append(qa_hierarchical)
    
    # Create several more QA pairs to enable meaningful splits
    for i in range(7):
        qa = QAPair(
            question=f"Sample question {i+1}?",
            thinking=f"Analysis for question {i+1}",
            answer=f"Answer for question {i+1}, with detailed information about ArangoDB.",
            question_type=QuestionType.FACTUAL,
            confidence=0.85,
            temperature_used=0.1,
            source_section="section",
            source_hash="hash123",
            validation_score=0.9,
            citation_found=True
        )
        qa_pairs.append(qa)
    
    # Create batch
    batch = QABatch(
        qa_pairs=qa_pairs,
        document_id="arangodb_test_doc",
        generation_time=1.5,
        metadata={
            "file_summary": "Overview of ArangoDB database system",
            "document_type": "technical_manual",
            "parent_section": "databases"
        }
    )
    
    return batch


async def verify_unsloth_export(
    temp_dir: Path, 
    include_invalid: bool = False, 
    format: str = "jsonl", 
    split_ratio: Optional[Dict[str, float]] = None
) -> List[Path]:
    """
    Test the UnSloth export functionality.
    
    Args:
        temp_dir: Directory for test output
        include_invalid: Whether to include invalid QA pairs
        format: Export format ('json' or 'jsonl')
        split_ratio: Train/val/test split ratio
        
    Returns:
        List of created file paths
    """
    # Create test data
    batch = await create_sample_qa_data()
    
    # Initialize exporter
    exporter = QAExporter(output_dir=str(temp_dir))
    
    # Export with various options
    filename = f"test_export_{format}"
    if split_ratio:
        filename += "_split"
    
    # Create invalid QA pair for testing
    if include_invalid:
        invalid_qa = QAPair(
            question="Invalid question?",
            thinking="This answer cannot be validated.",
            answer="This is an invalid answer with no citation.",
            question_type=QuestionType.FACTUAL,
            confidence=0.6,
            temperature_used=0.3,
            source_section="unknown",
            source_hash="xyz",
            validation_score=0.5,
            citation_found=False
        )
        batch.qa_pairs.append(invalid_qa)
    
    # Export data
    output_paths = await exporter.export_to_unsloth(
        batch,
        filename=filename,
        include_invalid=include_invalid,
        format=format,
        split_ratio=split_ratio,
        enrich_context=False  # No DB connection in tests
    )
    
    return output_paths


async def validate_export_contents(
    file_paths: List[str], 
    format: str, 
    expected_pairs: int, 
    split: bool
) -> List[str]:
    """
    Validate export file contents.
    
    Args:
        file_paths: List of export file paths
        format: Expected format ('json' or 'jsonl')
        expected_pairs: Expected number of QA pairs
        split: Whether files should be split
        
    Returns:
        List of validation errors, empty if valid
    """
    errors = []
    
    # Check all files exist
    for path in file_paths:
        if not Path(path).exists():
            errors.append(f"File not found: {path}")
    
    # Count total QA pairs
    total_pairs = 0
    
    # Check file format
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if format == "jsonl":
                    # Each line should be valid JSON
                    lines = [line.strip() for line in f if line.strip()]
                    for i, line in enumerate(lines):
                        try:
                            data = json.loads(line)
                            if "messages" not in data:
                                errors.append(f"Missing 'messages' field in JSONL file {path}, line {i+1}")
                            total_pairs += 1
                        except json.JSONDecodeError:
                            errors.append(f"Invalid JSON in JSONL file {path}, line {i+1}")
                else:
                    # File should be a JSON array
                    data = json.load(f)
                    if not isinstance(data, list):
                        errors.append(f"JSON file {path} should contain an array")
                    total_pairs += len(data)
                    
                    # Check structure
                    for i, item in enumerate(data):
                        if "messages" not in item:
                            errors.append(f"Missing 'messages' field in JSON file {path}, item {i}")
                        
        except Exception as e:
            errors.append(f"Error reading file {path}: {e}")
    
    # Verify expected pairs
    if total_pairs != expected_pairs:
        errors.append(f"Expected {expected_pairs} total QA pairs, found {total_pairs}")
    
    # Verify split files
    if split and len(file_paths) < 2:
        errors.append(f"Expected multiple files for split, found {len(file_paths)}")
    
    return errors


async def test_unsloth_export() -> bool:
    """
    Test UnSloth export functionality with various options.
    
    Returns:
        True if all tests pass, False otherwise
    """
    # Create temp directory
    temp_dir = Path("./qa_output_test")
    temp_dir.mkdir(exist_ok=True)
    
    all_validation_failures = []
    total_tests = 0
    
    try:
        # Test 1: Basic JSONL export
        total_tests += 1
        try:
            output_paths = await verify_unsloth_export(temp_dir, format="jsonl")
            
            # Verify output
            errors = await validate_export_contents(
                output_paths, 
                format="jsonl", 
                expected_pairs=10,  # 10 valid pairs from sample data
                split=False
            )
            
            if errors:
                all_validation_failures.append(f"JSONL export validation errors: {errors}")
        except Exception as e:
            all_validation_failures.append(f"JSONL export test failed: {str(e)}")
        
        # Test 2: JSON export
        total_tests += 1
        try:
            output_paths = await verify_unsloth_export(temp_dir, format="json")
            
            # Verify output
            errors = await validate_export_contents(
                output_paths, 
                format="json", 
                expected_pairs=10,
                split=False
            )
            
            if errors:
                all_validation_failures.append(f"JSON export validation errors: {errors}")
        except Exception as e:
            all_validation_failures.append(f"JSON export test failed: {str(e)}")
        
        # Test 3: JSONL with train/val/test split
        total_tests += 1
        try:
            split_ratio = {"train": 0.6, "val": 0.2, "test": 0.2}
            output_paths = await verify_unsloth_export(
                temp_dir, 
                format="jsonl", 
                split_ratio=split_ratio
            )
            
            # Verify output - should create three files
            if len(output_paths) != 3:
                all_validation_failures.append(
                    f"Split export: Expected 3 output files, got {len(output_paths)}"
                )
            
            errors = await validate_export_contents(
                output_paths, 
                format="jsonl", 
                expected_pairs=10,
                split=True
            )
            
            if errors:
                all_validation_failures.append(f"Split export validation errors: {errors}")
        except Exception as e:
            all_validation_failures.append(f"Split export test failed: {str(e)}")
        
        # Test 4: Include invalid pairs
        total_tests += 1
        try:
            output_paths = await verify_unsloth_export(
                temp_dir, 
                format="jsonl", 
                include_invalid=True
            )
            
            # Verify output - should include the invalid pair (11 total)
            errors = await validate_export_contents(
                output_paths, 
                format="jsonl", 
                expected_pairs=11,
                split=False
            )
            
            if errors:
                all_validation_failures.append(f"Include invalid validation errors: {errors}")
        except Exception as e:
            all_validation_failures.append(f"Include invalid test failed: {str(e)}")
        
        # Test 5: Synchronous API
        total_tests += 1
        try:
            # Create test data and exporter
            batch = await create_sample_qa_data()
            exporter = QAExporter(output_dir=str(temp_dir))
            
            # Use sync version
            output_paths = exporter.export_to_unsloth_sync(
                batch,
                filename="test_export_sync",
                format="jsonl"
            )
            
            # Verify output
            errors = await validate_export_contents(
                output_paths, 
                format="jsonl", 
                expected_pairs=10,
                split=False
            )
            
            if errors:
                all_validation_failures.append(f"Sync API validation errors: {errors}")
        except Exception as e:
            all_validation_failures.append(f"Sync API test failed: {str(e)}")
        
        return all_validation_failures, total_tests
    
    finally:
        # Cleanup test files (optional)
        # import shutil
        # shutil.rmtree(temp_dir, ignore_errors=True)
        pass


if __name__ == "__main__":
    all_validation_failures, total_tests = asyncio.run(test_unsloth_export())
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("QA exporter is validated and ready for use")
        sys.exit(0)  # Exit with success code