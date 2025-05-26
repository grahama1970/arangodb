#!/usr/bin/env python3
"""
Standalone verification script for Unsloth export functionality.

This script tests the QA exporter with sample data without database dependencies.
"""

import sys
import os
import json
import asyncio
import tempfile
import random
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

# Set up base path
BASE_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_PATH))

# Create simple model classes directly to avoid dependencies
class QuestionType(str, Enum):
    """Types of questions that can be generated."""
    FACTUAL = "FACTUAL"
    RELATIONSHIP = "RELATIONSHIP"
    MULTI_HOP = "MULTI_HOP"
    HIERARCHICAL = "HIERARCHICAL"
    COMPARATIVE = "COMPARATIVE"
    REVERSAL = "REVERSAL"

class QAPair(BaseModel):
    """Simplified Q&A pair for testing."""
    question: str
    thinking: str
    answer: str
    question_type: QuestionType
    confidence: float = 0.9
    temperature_used: float = 0.1
    source_section: str
    source_hash: str
    validation_score: Optional[float] = None
    citation_found: bool = True
    evidence_blocks: List[str] = Field(default_factory=list)
    section_summary: Optional[str] = None
    relationship_types: List[str] = Field(default_factory=list)
    related_entities: List[str] = Field(default_factory=list)

class QABatch(BaseModel):
    """Batch of Q&A pairs for training data export."""
    qa_pairs: List[QAPair]
    document_id: str
    generation_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.metadata:
            self.metadata = {
                "file_summary": "",
                "parent_section": "",
                "document_type": ""
            }


class SimpleContextGenerator:
    """Simple context generator for testing."""
    
    def __init__(self, db=None):
        """Initialize context generator."""
        self.db = db
    
    async def generate_document_context(self, document_id: str) -> Dict[str, Any]:
        """Generate document context."""
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


class QAExporter:
    """Simplified QA exporter for testing."""
    
    def __init__(self, output_dir: str = "qa_output", db=None):
        """Initialize exporter."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.context_generator = SimpleContextGenerator(db)
    
    async def enrich_with_context(self, batch: QABatch) -> QABatch:
        """Enrich QA batch with context information."""
        # Get document context
        document_context = await self.context_generator.generate_document_context(batch.document_id)
        
        # Update batch metadata
        batch.metadata.update({
            "file_summary": document_context.get("summary", ""),
            "document_type": document_context.get("source", "")
        })
        
        # Get section summaries
        section_summaries = document_context.get("section_summaries", {})
        
        # Add section summary to batch metadata
        for section_id, summary in section_summaries.items():
            batch.metadata[f"section_summary_{section_id}"] = summary
        
        # Enrich QA pairs with section summaries
        for qa in batch.qa_pairs:
            section_id = qa.source_section
            if section_id in section_summaries:
                qa.section_summary = section_summaries[section_id]
        
        return batch
    
    async def export_to_unsloth(
        self, 
        batches_or_pairs: Union[List[QABatch], List[QAPair], QABatch],
        filename: Optional[str] = None,
        include_invalid: bool = False,
        format: str = "jsonl",
        split_ratio: Optional[Dict[str, float]] = None,
        enrich_context: bool = True
    ) -> List[str]:
        """Export Q&A batches to UnSloth format."""
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            if format == "jsonl":
                filename = f"qa_unsloth_{timestamp}.jsonl"
            else:
                filename = f"qa_unsloth_{timestamp}.json"
        
        # Ensure correct extension
        base_filename = Path(filename).stem
        if format == "jsonl":
            filename = f"{base_filename}.jsonl"
        else:
            filename = f"{base_filename}.json"
        
        output_path = self.output_dir / filename
        
        # Collect all messages
        all_messages = []
        stats = {
            "total_pairs": 0,
            "valid_pairs": 0,
            "documents": set(),
            "question_types": {}
        }
        
        # Handle different input types
        batches = []
        pairs = []
        
        # Normalize input to have consistent processing
        if isinstance(batches_or_pairs, QABatch):
            # Single batch
            batches = [batches_or_pairs]
        elif isinstance(batches_or_pairs, list):
            if batches_or_pairs and isinstance(batches_or_pairs[0], QABatch):
                # List of batches
                batches = batches_or_pairs
            elif batches_or_pairs and isinstance(batches_or_pairs[0], QAPair):
                # List of QA pairs
                pairs = batches_or_pairs
        else:
            print(f"Unsupported input type: {type(batches_or_pairs)}")
            return []
            
        # Enrich batches with context if requested
        if enrich_context:
            enriched_batches = []
            for batch in batches:
                try:
                    enriched_batch = await self.enrich_with_context(batch)
                    enriched_batches.append(enriched_batch)
                except Exception as e:
                    print(f"Error enriching batch {batch.document_id}: {e}")
                    enriched_batches.append(batch)  # Use original batch if enrichment fails
            batches = enriched_batches
        
        # Process batches
        for batch in batches:
            stats["documents"].add(batch.document_id)
            
            # Convert to UnSloth format
            messages = []
            for qa in batch.qa_pairs:
                if qa.citation_found or include_invalid:
                    # Extract context information
                    file_summary = batch.metadata.get("file_summary", "")
                    parent_section = batch.metadata.get("parent_section", "")
                    current_section = qa.source_section
                    section_summary = qa.section_summary if hasattr(qa, "section_summary") and qa.section_summary else batch.metadata.get(f"section_summary_{current_section}", "")
                    
                    # Create a concise context field
                    context = f"Document: {batch.document_id}"
                    if file_summary:
                        context += f". Summary: {file_summary}"
                    if parent_section:
                        context += f". Section: {parent_section}"
                    if current_section and current_section != parent_section:
                        context += f" > {current_section}"
                    if section_summary:
                        context += f". Section summary: {section_summary}"
                    
                    if format == "jsonl":
                        # Chat format for JSONL (messages array)
                        message = {
                            "messages": [
                                {"role": "system", "content": context},
                                {"role": "user", "content": qa.question},
                                {"role": "assistant", "content": qa.answer}
                            ],
                            "metadata": {
                                "document_id": batch.document_id,
                                "question_type": qa.question_type.value,
                                "confidence": qa.confidence, 
                                "source_section": qa.source_section,
                                "validation_score": qa.validation_score,
                                "validated": qa.citation_found,
                                "thinking": qa.thinking,
                                "file_summary": file_summary,
                                "parent_section": parent_section,
                                "current_section": current_section,
                                "section_summary": section_summary,
                                "context": context
                            }
                        }
                    else:
                        # JSON format with thinking as part of content
                        message = {
                            "messages": [
                                {"role": "system", "content": context},
                                {"role": "user", "content": qa.question},
                                {"role": "assistant", "content": qa.answer, "thinking": qa.thinking}
                            ],
                            "metadata": {
                                "document_id": batch.document_id,
                                "question_type": qa.question_type.value,
                                "confidence": qa.confidence, 
                                "source_section": qa.source_section,
                                "validation_score": qa.validation_score,
                                "validated": qa.citation_found,
                                "file_summary": file_summary,
                                "parent_section": parent_section,
                                "current_section": current_section,
                                "section_summary": section_summary,
                                "context": context
                            }
                        }
                    messages.append(message)
            
            all_messages.extend(messages)
            
            # Update statistics
            stats["total_pairs"] += len(batch.qa_pairs)
            stats["valid_pairs"] += sum(1 for qa in batch.qa_pairs if qa.citation_found)
            
            for qa in batch.qa_pairs:
                q_type = qa.question_type.value
                stats["question_types"][q_type] = stats["question_types"].get(q_type, 0) + 1
        
        # Process individual QA pairs (if any)
        if pairs:
            doc_id = "unknown"
            all_pairs_messages = []
            
            for qa in pairs:
                if qa.citation_found or include_invalid:
                    # Create a concise context field
                    context = f"Document: {doc_id}"
                    if qa.source_section:
                        context += f". Section: {qa.source_section}"
                    if qa.section_summary:
                        context += f". Section summary: {qa.section_summary}"
                    
                    if format == "jsonl":
                        # Chat format for JSONL (messages array)
                        message = {
                            "messages": [
                                {"role": "system", "content": context},
                                {"role": "user", "content": qa.question},
                                {"role": "assistant", "content": qa.answer}
                            ],
                            "metadata": {
                                "document_id": doc_id,
                                "question_type": qa.question_type.value,
                                "confidence": qa.confidence,
                                "source_section": qa.source_section,
                                "validation_score": qa.validation_score,
                                "validated": qa.citation_found,
                                "thinking": qa.thinking,
                                "context": context
                            }
                        }
                    else:
                        # JSON format with thinking as part of content
                        message = {
                            "messages": [
                                {"role": "system", "content": context},
                                {"role": "user", "content": qa.question},
                                {"role": "assistant", "content": qa.answer, "thinking": qa.thinking}
                            ],
                            "metadata": {
                                "document_id": doc_id,
                                "question_type": qa.question_type.value,
                                "confidence": qa.confidence,
                                "source_section": qa.source_section,
                                "validation_score": qa.validation_score,
                                "validated": qa.citation_found,
                                "context": context
                            }
                        }
                    all_pairs_messages.append(message)
                
                # Update statistics
                q_type = qa.question_type.value
                stats["question_types"][q_type] = stats["question_types"].get(q_type, 0) + 1
            
            stats["documents"].add(doc_id)
            stats["total_pairs"] += len(pairs)
            stats["valid_pairs"] += sum(1 for qa in pairs if qa.citation_found)
            
            all_messages.extend(all_pairs_messages)
        
        # If no split is requested, just write a single file
        if not split_ratio:
            if format == "jsonl":
                # Write in JSONL format (one JSON object per line)
                with open(output_path, 'w', encoding='utf-8') as f:
                    for msg in all_messages:
                        f.write(json.dumps(msg, ensure_ascii=False) + '\n')
            else:
                # Write in JSON format (single JSON array)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(all_messages, f, indent=2, ensure_ascii=False)
            
            # Write statistics
            stats_path = output_path.with_suffix('.stats.json')
            stats["documents"] = list(stats["documents"])
            
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            print(f"Exported {len(all_messages)} Q&A pairs to {output_path}")
            print(f"Statistics saved to {stats_path}")
            
            return [str(output_path)]
        else:
            # Perform train/val/test split if requested
            output_files = self._split_and_save_data(all_messages, format, base_filename, split_ratio)
            
            # Write statistics
            stats_path = self.output_dir / f"{base_filename}.stats.json"
            stats["documents"] = list(stats["documents"])
            
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            print(f"Exported {len(all_messages)} Q&A pairs to multiple files with split: {split_ratio}")
            print(f"Statistics saved to {stats_path}")
            
            return output_files
    
    def _split_and_save_data(
        self, 
        messages: List[Dict[str, Any]], 
        format: str,
        base_filename: str,
        split_ratio: Dict[str, float]
    ) -> List[str]:
        """Split data and save to multiple files according to split ratio."""
        # Shuffle messages to ensure random distribution
        random.shuffle(messages)
        
        # Calculate number of examples for each split
        total = len(messages)
        splits = {}
        
        # Ensure split ratios are valid
        if abs(sum(split_ratio.values()) - 1.0) > 0.001:
            print(f"Split ratios don't sum to 1.0: {split_ratio}. Normalizing...")
            total_ratio = sum(split_ratio.values())
            split_ratio = {k: v / total_ratio for k, v in split_ratio.items()}
        
        # Calculate split indices
        cumulative = 0
        indices = {}
        for split_name, ratio in split_ratio.items():
            start_idx = cumulative
            end_idx = cumulative + int(total * ratio)
            splits[split_name] = messages[start_idx:end_idx]
            cumulative = end_idx
        
        # Handle any remaining examples due to rounding
        remaining = total - cumulative
        if remaining > 0:
            # Add remaining examples to the largest split
            largest_split = max(split_ratio.items(), key=lambda x: x[1])[0]
            splits[largest_split].extend(messages[cumulative:total])
        
        # Save each split to a separate file
        output_files = []
        for split_name, split_data in splits.items():
            if format == "jsonl":
                output_path = self.output_dir / f"{base_filename}_{split_name}.jsonl"
                with open(output_path, 'w', encoding='utf-8') as f:
                    for msg in split_data:
                        f.write(json.dumps(msg, ensure_ascii=False) + '\n')
            else:
                output_path = self.output_dir / f"{base_filename}_{split_name}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(split_data, f, indent=2, ensure_ascii=False)
            
            output_files.append(str(output_path))
            print(f"Saved {len(split_data)} examples to {output_path}")
        
        return output_files
    
    def export_to_unsloth_sync(
        self, 
        batches_or_pairs: Union[List[QABatch], List[QAPair], QABatch],
        filename: Optional[str] = None,
        include_invalid: bool = False,
        format: str = "jsonl",
        split_ratio: Optional[Dict[str, float]] = None,
        enrich_context: bool = False  # Default to False for sync version
    ) -> List[str]:
        """Synchronous version of export_to_unsloth."""
        # Use the async version with an event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async version
        return loop.run_until_complete(
            self.export_to_unsloth(
                batches_or_pairs,
                filename,
                include_invalid,
                format,
                split_ratio,
                enrich_context=False  # Don't enrich in sync version
            )
        )


async def create_sample_qa_data() -> QABatch:
    """Create sample QA data for testing."""
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
    """Test the UnSloth export functionality."""
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
    """Validate export file contents."""
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


async def test_unsloth_export() -> tuple:
    """Test UnSloth export functionality with various options."""
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
        # Don't clean up for now
        pass


if __name__ == "__main__":
    """Run verification tests."""
    loop = asyncio.get_event_loop()
    all_validation_failures, total_tests = loop.run_until_complete(test_unsloth_export())
    
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