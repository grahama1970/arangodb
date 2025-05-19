"""
QA Export Utilities

This module provides functions for exporting Q&A pairs to various formats
for model fine-tuning and data analysis.

Links:
- UnSloth: https://github.com/unslothai/unsloth
- OpenAI: https://platform.openai.com/docs/guides/fine-tuning

Sample Input/Output:
- Input: QA pairs from ArangoDB
- Output: Formatted files for fine-tuning
"""

import json
import csv
import os
import gzip
import shutil
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from loguru import logger

from arangodb.qa.schemas import (
    QAPair,
    QABatch,
    QAExportFormat
)


class QAExporter:
    """
    Exports Q&A pairs to various formats for training and analysis.
    
    Supports various export formats and data splitting for ML workflows.
    """
    
    def __init__(self, export_format: Optional[QAExportFormat] = None):
        """
        Initialize the exporter.
        
        Args:
            export_format: Configuration for export format
        """
        self.export_format = export_format or QAExportFormat()
    
    def export_to_file(
        self,
        qa_pairs: List[Union[QAPair, Dict[str, Any]]],
        output_path: Union[str, Path],
        format: Optional[str] = None
    ) -> Path:
        """
        Export Q&A pairs to a file.
        
        Args:
            qa_pairs: List of Q&A pairs (either QAPair objects or dicts)
            output_path: Path to output file
            format: Output format (jsonl, csv, json, parquet)
            
        Returns:
            Path to the exported file
        """
        # Determine format
        format = format or self.export_format.format
        
        # Convert to Path object
        output_path = Path(output_path)
        
        # Add appropriate extension if not present
        if not output_path.suffix or output_path.suffix != f".{format}":
            output_path = output_path.with_suffix(f".{format}")
        
        # Convert to JSONL format
        formatted_data = self.convert_to_training_format(qa_pairs)
        
        # Export based on format
        if format == "jsonl":
            self._export_jsonl(formatted_data, output_path)
        elif format == "json":
            self._export_json(formatted_data, output_path)
        elif format == "csv":
            self._export_csv(formatted_data, output_path)
        elif format == "parquet":
            self._export_parquet(formatted_data, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Compress if requested
        if self.export_format.compress:
            compressed_path = self._compress_file(output_path)
            return compressed_path
        
        return output_path
    
    def export_batch(
        self,
        qa_batch: QABatch,
        output_path: Union[str, Path],
        format: Optional[str] = None
    ) -> Path:
        """
        Export a QA batch to a file.
        
        Args:
            qa_batch: QA batch to export
            output_path: Path to output file
            format: Output format
            
        Returns:
            Path to the exported file
        """
        return self.export_to_file(qa_batch.qa_pairs, output_path, format)
    
    def export_with_split(
        self,
        qa_pairs: List[Union[QAPair, Dict[str, Any]]],
        output_dir: Union[str, Path],
        base_filename: str,
        format: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Export Q&A pairs with train/val/test split.
        
        Args:
            qa_pairs: List of Q&A pairs
            output_dir: Directory for output files
            base_filename: Base filename for split files
            format: Output format
            
        Returns:
            Dictionary of paths for each split
        """
        # Determine format
        format = format or self.export_format.format
        
        # Convert to Path object
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get split ratios
        split_ratio = self.export_format.split_ratio
        
        # Shuffle data
        shuffled_pairs = list(qa_pairs)
        random.shuffle(shuffled_pairs)
        
        # Calculate split indices
        train_idx = int(len(shuffled_pairs) * split_ratio["train"])
        val_idx = train_idx + int(len(shuffled_pairs) * split_ratio["val"])
        
        # Split data
        train_data = shuffled_pairs[:train_idx]
        val_data = shuffled_pairs[train_idx:val_idx]
        test_data = shuffled_pairs[val_idx:]
        
        # Create output paths
        train_path = output_dir / f"{base_filename}_train.{format}"
        val_path = output_dir / f"{base_filename}_val.{format}"
        test_path = output_dir / f"{base_filename}_test.{format}"
        
        # Export each split
        paths = {}
        if train_data:
            paths["train"] = self.export_to_file(train_data, train_path, format)
        if val_data:
            paths["val"] = self.export_to_file(val_data, val_path, format)
        if test_data:
            paths["test"] = self.export_to_file(test_data, test_path, format)
        
        # Create and export metadata about the split
        metadata = {
            "total_pairs": len(qa_pairs),
            "train_pairs": len(train_data),
            "val_pairs": len(val_data),
            "test_pairs": len(test_data),
            "split_ratio": dict(split_ratio),
            "format": format,
            "compressed": self.export_format.compress,
            "timestamp": datetime.now().isoformat(),
            "files": {k: str(v) for k, v in paths.items()}
        }
        
        # Export metadata
        meta_path = output_dir / f"{base_filename}_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        paths["metadata"] = meta_path
        
        return paths
    
    def convert_to_training_format(
        self,
        qa_pairs: List[Union[QAPair, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Convert Q&A pairs to training format.
        
        Args:
            qa_pairs: List of Q&A pairs
            
        Returns:
            List of formatted data for training
        """
        formatted_data = []
        
        for qa in qa_pairs:
            # Handle both QAPair objects and dicts
            if isinstance(qa, QAPair):
                # Get data from QAPair object
                question = qa.question
                thinking = qa.thinking
                answer = qa.answer
                question_type = qa.question_type
                confidence = qa.confidence
                validation_score = qa.validation_score
                citation_found = qa.citation_found
                document_id = qa.document_id
                source_sections = qa.source_sections
                created_at = qa.created_at
            else:
                # Get data from dict
                question = qa.get("question", "")
                thinking = qa.get("thinking", "")
                answer = qa.get("answer", "")
                question_type = qa.get("question_type", "FACTUAL")
                confidence = qa.get("confidence", 0.0)
                validation_score = qa.get("validation_score", 0.0)
                citation_found = qa.get("citation_found", False)
                document_id = qa.get("document_id", "")
                source_sections = qa.get("source_sections", [])
                created_at = qa.get("created_at", datetime.now().isoformat())
            
            # Skip if missing required fields
            if not all([question, answer]):
                continue
            
            # Format as UnSloth-compatible data
            formatted = {
                "messages": [
                    {"role": "user", "content": question},
                    {
                        "role": "assistant", 
                        "content": answer,
                        "thinking": thinking
                    }
                ],
                "metadata": {
                    "question_type": question_type,
                    "confidence": confidence,
                    "validation_score": validation_score,
                    "citation_found": citation_found,
                    "document_id": document_id,
                    "source_sections": source_sections,
                    "created_at": created_at
                }
            }
            
            formatted_data.append(formatted)
        
        return formatted_data
    
    def _export_jsonl(self, data: List[Dict[str, Any]], output_path: Path) -> None:
        """Export data to JSONL format."""
        with open(output_path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
    
    def _export_json(self, data: List[Dict[str, Any]], output_path: Path) -> None:
        """Export data to JSON format."""
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def _export_csv(self, data: List[Dict[str, Any]], output_path: Path) -> None:
        """Export data to CSV format."""
        if not data:
            # Create empty file
            with open(output_path, "w") as f:
                pass
            return
        
        with open(output_path, "w", newline="") as f:
            # Extract fields
            fieldnames = ["question", "answer", "thinking", "question_type", "confidence", "validation_score", "citation_found"]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                row = {
                    "question": item["messages"][0]["content"],
                    "answer": item["messages"][1]["content"],
                    "thinking": item["messages"][1].get("thinking", ""),
                    "question_type": item["metadata"]["question_type"],
                    "confidence": item["metadata"]["confidence"],
                    "validation_score": item["metadata"]["validation_score"],
                    "citation_found": item["metadata"]["citation_found"]
                }
                writer.writerow(row)
    
    def _export_parquet(self, data: List[Dict[str, Any]], output_path: Path) -> None:
        """Export data to Parquet format."""
        try:
            import pandas as pd
            
            # Convert to flat structure for pandas
            rows = []
            for item in data:
                row = {
                    "question": item["messages"][0]["content"],
                    "answer": item["messages"][1]["content"],
                    "thinking": item["messages"][1].get("thinking", ""),
                    "question_type": item["metadata"]["question_type"],
                    "confidence": item["metadata"]["confidence"],
                    "validation_score": item["metadata"]["validation_score"],
                    "citation_found": item["metadata"]["citation_found"],
                    "document_id": item["metadata"]["document_id"],
                    "created_at": item["metadata"]["created_at"]
                }
                rows.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(rows)
            
            # Write to Parquet
            df.to_parquet(output_path, index=False)
        
        except ImportError:
            logger.error("pandas is required for Parquet export")
            raise ImportError("pandas is required for Parquet export")
    
    def _compress_file(self, file_path: Path) -> Path:
        """
        Compress a file using gzip.
        
        Args:
            file_path: Path to the file to compress
            
        Returns:
            Path to the compressed file
        """
        compressed_path = file_path.with_suffix(f"{file_path.suffix}.gz")
        
        with open(file_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file
        os.remove(file_path)
        
        return compressed_path


def export_to_unsloth_format(
    qa_pairs: List[Union[QAPair, Dict[str, Any]]],
    output_path: Union[str, Path],
    compress: bool = False
) -> Path:
    """
    Export Q&A pairs to UnSloth format for fine-tuning.
    
    Args:
        qa_pairs: List of Q&A pairs
        output_path: Path to output file
        compress: Whether to compress the output file
        
    Returns:
        Path to the exported file
    """
    export_format = QAExportFormat(
        format="jsonl",
        compress=compress,
        include_metadata=True
    )
    
    exporter = QAExporter(export_format)
    return exporter.export_to_file(qa_pairs, output_path)


def export_to_openai_format(
    qa_pairs: List[Union[QAPair, Dict[str, Any]]],
    output_path: Union[str, Path],
    compress: bool = False
) -> Path:
    """
    Export Q&A pairs to OpenAI fine-tuning format.
    
    Args:
        qa_pairs: List of Q&A pairs
        output_path: Path to output file
        compress: Whether to compress the output file
        
    Returns:
        Path to the exported file
    """
    export_format = QAExportFormat(
        format="jsonl",
        compress=compress,
        include_metadata=False  # OpenAI doesn't need metadata
    )
    
    exporter = QAExporter(export_format)
    
    # Get formatted data
    formatted_data = exporter.convert_to_training_format(qa_pairs)
    
    # Convert to OpenAI format (remove thinking)
    for item in formatted_data:
        # Remove thinking from assistant message
        if "thinking" in item["messages"][1]:
            del item["messages"][1]["thinking"]
    
    # Export to file
    output_path = Path(output_path)
    
    # Add appropriate extension
    if not output_path.suffix or output_path.suffix != ".jsonl":
        output_path = output_path.with_suffix(".jsonl")
    
    # Export data
    with open(output_path, "w") as f:
        for item in formatted_data:
            f.write(json.dumps(item) + "\n")
    
    # Compress if requested
    if compress:
        compressed_path = output_path.with_suffix(".jsonl.gz")
        
        with open(output_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file
        os.remove(output_path)
        
        return compressed_path
    
    return output_path


def create_train_val_test_split(
    qa_pairs: List[Union[QAPair, Dict[str, Any]]],
    output_dir: Union[str, Path],
    base_filename: str,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    format: str = "jsonl",
    compress: bool = False
) -> Dict[str, Path]:
    """
    Create a train/val/test split for Q&A pairs.
    
    Args:
        qa_pairs: List of Q&A pairs
        output_dir: Directory for output files
        base_filename: Base filename for split files
        train_ratio: Ratio of data for training
        val_ratio: Ratio of data for validation
        format: Output format
        compress: Whether to compress the output files
        
    Returns:
        Dictionary of paths for each split
    """
    # Create export configuration
    export_format = QAExportFormat(
        format=format,
        compress=compress,
        split_ratio={
            "train": train_ratio,
            "val": val_ratio,
            "test": 1 - train_ratio - val_ratio
        }
    )
    
    # Create exporter
    exporter = QAExporter(export_format)
    
    # Export with split
    return exporter.export_with_split(qa_pairs, output_dir, base_filename, format)


if __name__ == "__main__":
    """
    Self-validation tests for the QA exporter.
    
    This validation tests the QA export functionality.
    """
    import sys
    import tempfile
    import shutil
    
    # Configure logger for validation output
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Create temp directory for outputs
    temp_dir = tempfile.mkdtemp()
    try:
        # Test 1: JSONL export
        total_tests += 1
        try:
            print("\nTest 1: JSONL export")
            
            # Create sample Q&A pairs
            qa_pairs = [
                QAPair(
                    question="What is the capital of France?",
                    thinking="I need to recall information about France and its capital city.",
                    answer="The capital of France is Paris.",
                    question_type="FACTUAL",
                    document_id="test_doc",
                    source_sections=["section_1"],
                    evidence_blocks=["text_123"],
                    confidence=0.95,
                    citation_found=True
                ),
                QAPair(
                    question="What is the largest planet in our solar system?",
                    thinking="I need to recall information about planets in our solar system.",
                    answer="Jupiter is the largest planet in our solar system.",
                    question_type="FACTUAL",
                    document_id="test_doc",
                    source_sections=["section_2"],
                    evidence_blocks=["text_456"],
                    confidence=0.9,
                    citation_found=True
                )
            ]
            
            # Create exporter
            exporter = QAExporter()
            
            # Export to JSONL
            output_path = Path(temp_dir) / "test_export.jsonl"
            exported_path = exporter.export_to_file(qa_pairs, output_path, "jsonl")
            
            # Verify export
            assert exported_path.exists(), f"Exported file {exported_path} does not exist"
            
            # Read back and verify contents
            with open(exported_path, "r") as f:
                lines = f.readlines()
                
                assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
                
                for line in lines:
                    data = json.loads(line)
                    assert "messages" in data, "Missing 'messages' key"
                    assert len(data["messages"]) == 2, f"Expected 2 messages, got {len(data['messages'])}"
                    assert data["messages"][0]["role"] == "user", f"Expected 'user' role, got {data['messages'][0]['role']}"
                    assert data["messages"][1]["role"] == "assistant", f"Expected 'assistant' role, got {data['messages'][1]['role']}"
            
            print(f"✅ Exported {len(qa_pairs)} Q&A pairs to {exported_path}")
            print("✅ JSONL export successful")
        except Exception as e:
            all_validation_failures.append(f"JSONL export test failed: {str(e)}")
        
        # Test 2: CSV export
        total_tests += 1
        try:
            print("\nTest 2: CSV export")
            
            # Create exporter
            exporter = QAExporter()
            
            # Export to CSV
            output_path = Path(temp_dir) / "test_export.csv"
            exported_path = exporter.export_to_file(qa_pairs, output_path, "csv")
            
            # Verify export
            assert exported_path.exists(), f"Exported file {exported_path} does not exist"
            
            # Read back and verify contents
            with open(exported_path, "r") as f:
                lines = f.readlines()
                
                assert len(lines) > 1, f"Expected header + data lines, got {len(lines)}"
                
                # Check header
                header = lines[0].strip().split(",")
                assert "question" in header, "Missing 'question' in header"
                assert "answer" in header, "Missing 'answer' in header"
                assert "thinking" in header, "Missing 'thinking' in header"
            
            print(f"✅ Exported {len(qa_pairs)} Q&A pairs to {exported_path}")
            print("✅ CSV export successful")
        except Exception as e:
            all_validation_failures.append(f"CSV export test failed: {str(e)}")
        
        # Test 3: Export with split
        total_tests += 1
        try:
            print("\nTest 3: Export with split")
            
            # Create more sample Q&A pairs
            more_qa_pairs = qa_pairs + [
                QAPair(
                    question="What is the closest star to Earth?",
                    thinking="I need to recall information about stars near Earth.",
                    answer="The closest star to Earth is the Sun. The next closest is Proxima Centauri.",
                    question_type="FACTUAL",
                    document_id="test_doc",
                    source_sections=["section_3"],
                    evidence_blocks=["text_789"],
                    confidence=0.85,
                    citation_found=True
                ),
                QAPair(
                    question="What is the deepest ocean on Earth?",
                    thinking="I need to recall information about ocean depths.",
                    answer="The Pacific Ocean is the deepest ocean on Earth, with the Mariana Trench being its deepest point.",
                    question_type="FACTUAL",
                    document_id="test_doc",
                    source_sections=["section_4"],
                    evidence_blocks=["text_012"],
                    confidence=0.8,
                    citation_found=True
                ),
                QAPair(
                    question="Who wrote 'Romeo and Juliet'?",
                    thinking="I need to recall information about famous plays and their authors.",
                    answer="William Shakespeare wrote 'Romeo and Juliet'.",
                    question_type="FACTUAL",
                    document_id="test_doc",
                    source_sections=["section_5"],
                    evidence_blocks=["text_345"],
                    confidence=0.95,
                    citation_found=True
                )
            ]
            
            # Create train/val/test split
            split_paths = create_train_val_test_split(
                more_qa_pairs,
                temp_dir,
                "split_test",
                train_ratio=0.6,
                val_ratio=0.2,
                format="jsonl"
            )
            
            # Verify split files
            assert "train" in split_paths, "Missing train split"
            assert "val" in split_paths, "Missing val split"
            assert "test" in split_paths, "Missing test split"
            assert "metadata" in split_paths, "Missing metadata file"
            
            # Check train file
            train_path = split_paths["train"]
            assert train_path.exists(), f"Train file {train_path} does not exist"
            
            # Read metadata
            with open(split_paths["metadata"], "r") as f:
                metadata = json.load(f)
                
                assert metadata["total_pairs"] == len(more_qa_pairs), f"Expected {len(more_qa_pairs)} total pairs, got {metadata['total_pairs']}"
                assert metadata["split_ratio"]["train"] == 0.6, f"Expected train ratio 0.6, got {metadata['split_ratio']['train']}"
                assert metadata["split_ratio"]["val"] == 0.2, f"Expected val ratio 0.2, got {metadata['split_ratio']['val']}"
                assert metadata["split_ratio"]["test"] == 0.2, f"Expected test ratio 0.2, got {metadata['split_ratio']['test']}"
            
            print(f"✅ Exported {len(more_qa_pairs)} Q&A pairs with split:")
            print(f"   - Train: {metadata['train_pairs']} pairs")
            print(f"   - Val: {metadata['val_pairs']} pairs")
            print(f"   - Test: {metadata['test_pairs']} pairs")
            print("✅ Split export successful")
        except Exception as e:
            all_validation_failures.append(f"Split export test failed: {str(e)}")
        
        # Test 4: UnSloth and OpenAI formats
        total_tests += 1
        try:
            print("\nTest 4: UnSloth and OpenAI formats")
            
            # Export to UnSloth format
            unsloth_path = export_to_unsloth_format(qa_pairs, Path(temp_dir) / "unsloth_export.jsonl")
            
            # Export to OpenAI format
            openai_path = export_to_openai_format(qa_pairs, Path(temp_dir) / "openai_export.jsonl")
            
            # Verify exports
            assert unsloth_path.exists(), f"UnSloth export file {unsloth_path} does not exist"
            assert openai_path.exists(), f"OpenAI export file {openai_path} does not exist"
            
            # Compare formats
            with open(unsloth_path, "r") as f:
                unsloth_data = [json.loads(line) for line in f]
                
                # Check that UnSloth format includes thinking
                for item in unsloth_data:
                    assert "thinking" in item["messages"][1], "UnSloth format missing 'thinking'"
            
            with open(openai_path, "r") as f:
                openai_data = [json.loads(line) for line in f]
                
                # Check that OpenAI format does not include thinking
                for item in openai_data:
                    assert "thinking" not in item["messages"][1], "OpenAI format should not have 'thinking'"
            
            print(f"✅ Exported to UnSloth format: {unsloth_path}")
            print(f"✅ Exported to OpenAI format: {openai_path}")
            print("✅ Format-specific export successful")
        except Exception as e:
            all_validation_failures.append(f"Format-specific export test failed: {str(e)}")
    
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)
    
    # Final validation result
    if all_validation_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("QA exporter module is validated and ready for use")
        sys.exit(0)  # Exit with success code