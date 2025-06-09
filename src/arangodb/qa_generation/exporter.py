"""
Export Q&A pairs to various training formats.
Module: exporter.py
Description: Implementation of exporter functionality

This module handles exporting validated Q&A pairs to formats suitable
for fine-tuning with UnSloth and other training frameworks.
"""

import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from loguru import logger
import random

from .models import QABatch, QAPair, QAExportFormat
from ..core.context_generator import ContextGenerator


class QAExporter:
    """Exports Q&A pairs to various training formats."""
    
    def __init__(self, output_dir: str = "qa_output", db=None):
        """
        Initialize exporter.
        
        Args:
            output_dir: Directory to save exported files
            db: Optional database connection
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.context_generator = ContextGenerator(db)
        
    async def enrich_with_context(self, batch: QABatch) -> QABatch:
        """
        Enrich QA batch with context information.
        
        Args:
            batch: QA batch to enrich
            
        Returns:
            Enriched QA batch
        """
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
        """
        Export Q&A batches to UnSloth format.
        
        Args:
            batches_or_pairs: List of Q&A batches or pairs to export
            filename: Output filename (auto-generated if None)
            include_invalid: Whether to include unvalidated pairs
            format: Output format ('json' or 'jsonl')
            split_ratio: Train/val/test split ratio (e.g. {"train": 0.8, "val": 0.1, "test": 0.1})
                If None, no split is performed
            
        Returns:
            List of paths to exported files
        """
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
            logger.error(f"Unsupported input type: {type(batches_or_pairs)}")
            return []
            
        # Enrich batches with context if requested
        if enrich_context:
            enriched_batches = []
            for batch in batches:
                try:
                    enriched_batch = await self.enrich_with_context(batch)
                    enriched_batches.append(enriched_batch)
                except Exception as e:
                    logger.error(f"Error enriching batch {batch.document_id}: {e}")
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
                    # Extract context information
                    file_summary = ""
                    parent_section = ""
                    current_section = qa.source_section
                    section_summary = qa.section_summary if hasattr(qa, "section_summary") and qa.section_summary else ""
                    
                    # Create a concise context field
                    context = f"Document: {doc_id}"
                    if current_section:
                        context += f". Section: {current_section}"
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
                                "document_id": doc_id,
                                "question_type": qa.question_type.value,
                                "confidence": qa.confidence,
                                "source_section": qa.source_section,
                                "validation_score": qa.validation_score,
                                "validated": qa.citation_found,
                                "thinking": qa.thinking,
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
                                "document_id": doc_id,
                                "question_type": qa.question_type.value,
                                "confidence": qa.confidence,
                                "source_section": qa.source_section,
                                "validation_score": qa.validation_score,
                                "validated": qa.citation_found,
                                "current_section": current_section,
                                "section_summary": section_summary,
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
            
            logger.info(f"Exported {len(all_messages)} Q&A pairs to {output_path}")
            logger.info(f"Statistics saved to {stats_path}")
            
            return [str(output_path)]
        else:
            # Perform train/val/test split if requested
            output_files = self._split_and_save_data(all_messages, format, base_filename, split_ratio)
            
            # Write statistics
            stats_path = self.output_dir / f"{base_filename}.stats.json"
            stats["documents"] = list(stats["documents"])
            
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"Exported {len(all_messages)} Q&A pairs to multiple files with split: {split_ratio}")
            logger.info(f"Statistics saved to {stats_path}")
            
            return output_files
    
    def _split_and_save_data(
        self, 
        messages: List[Dict[str, Any]], 
        format: str,
        base_filename: str,
        split_ratio: Dict[str, float]
    ) -> List[str]:
        """
        Split data and save to multiple files according to split ratio.
        
        Args:
            messages: List of messages to split
            format: Output format ('json' or 'jsonl')
            base_filename: Base filename to use
            split_ratio: Train/val/test split ratio
            
        Returns:
            List of paths to exported files
        """
        # Shuffle messages to ensure random distribution
        random.shuffle(messages)
        
        # Calculate number of examples for each split
        total = len(messages)
        splits = {}
        
        # Ensure split ratios are valid
        if abs(sum(split_ratio.values()) - 1.0) > 0.001:
            logger.warning(f"Split ratios don't sum to 1.0: {split_ratio}. Normalizing...")
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
            logger.info(f"Saved {len(split_data)} examples to {output_path}")
        
        return output_files
    
    def export_to_openai(
        self,
        batches: List[QABatch],
        filename: Optional[str] = None
    ) -> str:
        """
        Export to OpenAI fine-tuning format.
        
        Args:
            batches: List of Q&A batches
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"qa_openai_{timestamp}.jsonl"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for batch in batches:
                for qa in batch.qa_pairs:
                    if not qa.citation_found:
                        continue
                    
                    # OpenAI format
                    conversation = {
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant that answers questions based on technical documents."},
                            {"role": "user", "content": qa.question},
                            {"role": "assistant", "content": qa.answer}
                        ]
                    }
                    
                    f.write(json.dumps(conversation, ensure_ascii=False) + '\n')
        
        logger.info(f"Exported to OpenAI format: {output_path}")
        return str(output_path)
    
    def export_to_alpaca(
        self,
        batches: List[QABatch],
        filename: Optional[str] = None
    ) -> str:
        """
        Export to Alpaca format.
        
        Args:
            batches: List of Q&A batches
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"qa_alpaca_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        alpaca_data = []
        
        for batch in batches:
            for qa in batch.qa_pairs:
                if not qa.citation_found:
                    continue
                
                # Alpaca format
                entry = {
                    "instruction": qa.question,
                    "input": "",  # No additional input
                    "output": qa.answer
                }
                
                alpaca_data.append(entry)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(alpaca_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported to Alpaca format: {output_path}")
        return str(output_path)
    
    def export_summary_report(
        self,
        batches: List[QABatch],
        filename: Optional[str] = None
    ) -> str:
        """
        Export a summary report of Q&A generation.
        
        Args:
            batches: List of Q&A batches
            filename: Report filename
            
        Returns:
            Path to report file
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"qa_report_{timestamp}.md"
        
        output_path = self.output_dir / filename
        
        # Collect statistics
        total_pairs = sum(b.total_pairs for b in batches)
        valid_pairs = sum(b.valid_pairs for b in batches)
        total_time = sum(b.generation_time for b in batches)
        
        question_types = {}
        confidence_scores = []
        validation_scores = []
        
        for batch in batches:
            for qa in batch.qa_pairs:
                # Question types
                q_type = qa.question_type.value
                question_types[q_type] = question_types.get(q_type, 0) + 1
                
                # Scores
                confidence_scores.append(qa.confidence)
                if qa.validation_score is not None:
                    validation_scores.append(qa.validation_score)
        
        # Generate report
        report = f"""# Q&A Generation Report

Generated on: {datetime.utcnow().isoformat()}

## Summary Statistics

- **Total Q&A Pairs**: {total_pairs}
- **Valid Pairs**: {valid_pairs} ({valid_pairs/total_pairs*100:.1f}%)
- **Documents Processed**: {len(batches)}
- **Total Generation Time**: {total_time:.2f} seconds
- **Average Time per Document**: {total_time/len(batches):.2f} seconds

## Question Type Distribution

| Type | Count | Percentage |
|------|-------|------------|
"""
        
        for q_type, count in sorted(question_types.items()):
            percentage = count / total_pairs * 100
            report += f"| {q_type} | {count} | {percentage:.1f}% |\n"
        
        report += f"""
## Score Statistics

- **Average Confidence**: {sum(confidence_scores)/len(confidence_scores):.3f}
- **Average Validation Score**: {sum(validation_scores)/len(validation_scores):.3f}

## Sample Q&A Pairs

"""
        
        # Add samples of each type
        for q_type in question_types:
            report += f"### {q_type} Example\n\n"
            
            # Find a sample
            for batch in batches:
                for qa in batch.qa_pairs:
                    if qa.question_type.value == q_type and qa.citation_found:
                        report += f"**Question**: {qa.question}\n\n"
                        report += f"**Thinking**: {qa.thinking}\n\n"
                        report += f"**Answer**: {qa.answer}\n\n"
                        report += f"**Validation Score**: {qa.validation_score:.3f}\n\n"
                        report += "---\n\n"
                        break
                else:
                    continue
                break
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Generated report: {output_path}")
        return str(output_path)


    def export_to_unsloth_sync(
        self, 
        batches_or_pairs: Union[List[QABatch], List[QAPair], QABatch],
        filename: Optional[str] = None,
        include_invalid: bool = False,
        format: str = "jsonl",
        split_ratio: Optional[Dict[str, float]] = None,
        enrich_context: bool = False  # Default to False for sync version
    ) -> List[str]:
        """
        Synchronous version of export_to_unsloth.
        
        Args:
            batches_or_pairs: List of QA batches or pairs to export
            filename: Output filename (auto-generated if None)
            include_invalid: Whether to include unvalidated pairs
            format: Output format ('json' or 'jsonl')
            split_ratio: Train/val/test split ratio (e.g. {"train": 0.8, "val": 0.1, "test": 0.1})
                If None, no split is performed
            enrich_context: Whether to enrich with context (False for sync version)
            
        Returns:
            List of paths to exported files
        """
        # Warn user that context enrichment is not available in sync version
        if enrich_context:
            logger.warning("Context enrichment is only available in async version. Use export_to_unsloth_async for context enrichment.")
        
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


if __name__ == "__main__":
    """
    Test the exporter with a simple example.
    """
    import sys
    from .models import QABatch, QAPair, QuestionType, ValidationStatus
    
    # Create test data
    qa_pair1 = QAPair(
        question="What is ArangoDB?",
        thinking="ArangoDB is a multi-model database system. Let me provide an overview of its features.",
        answer="ArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models. It provides a unified query language called AQL (ArangoDB Query Language) and allows for complex data relationships to be modeled and queried efficiently.",
        question_type=QuestionType.FACTUAL,
        confidence=0.95,
        temperature_used=0.0,
        source_section="introduction",
        source_hash="abc123",
        validation_score=0.98,
        citation_found=True
    )
    
    qa_pair2 = QAPair(
        question="How does ArangoDB compare to MongoDB?",
        thinking="This is a comparative question. I'll analyze the key differences between the two database systems.",
        answer="ArangoDB differs from MongoDB in several key aspects: 1) ArangoDB supports graph data model natively, while MongoDB is primarily document-oriented; 2) ArangoDB uses AQL as its query language, whereas MongoDB uses MQL; 3) ArangoDB offers built-in graph traversal functions that aren't available in MongoDB without additional components.",
        question_type=QuestionType.COMPARATIVE,
        confidence=0.87,
        temperature_used=0.2,
        source_section="comparisons",
        source_hash="def456",
        validation_score=0.92,
        citation_found=True
    )
    
    # Create a batch
    batch = QABatch(
        qa_pairs=[qa_pair1, qa_pair2],
        document_id="arangodb_overview",
        generation_time=1.5
    )
    
    # Create exporter
    exporter = QAExporter()
    
    async def run_tests():
        # Test all export formats
        all_validation_failures = []
        total_tests = 0
        
        # Test 1: JSONL format with no split
        total_tests += 1
        try:
            output_path = await exporter.export_to_unsloth(batch, "test_export_jsonl", format="jsonl", enrich_context=False)
            
            # Verify output exists
            if not Path(output_path[0]).exists():
                all_validation_failures.append(f"JSONL export: File {output_path[0]} was not created")
            
            # Verify content format
            with open(output_path[0], 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line.startswith('{') or not first_line.endswith('}'):
                    all_validation_failures.append(f"JSONL export: Invalid JSONL format in {output_path[0]}")
        except Exception as e:
            all_validation_failures.append(f"JSONL export failed: {str(e)}")
        
        # Test 2: JSON format with no split
        total_tests += 1
        try:
            output_path = await exporter.export_to_unsloth(batch, "test_export_json", format="json", enrich_context=False)
            
            # Verify output exists
            if not Path(output_path[0]).exists():
                all_validation_failures.append(f"JSON export: File {output_path[0]} was not created")
            
            # Verify content format
            with open(output_path[0], 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content.startswith('[') or not content.endswith(']'):
                    all_validation_failures.append(f"JSON export: Invalid JSON format in {output_path[0]}")
        except Exception as e:
            all_validation_failures.append(f"JSON export failed: {str(e)}")
        
        # Test 3: JSONL format with split
        total_tests += 1
        try:
            split_ratio = {"train": 0.8, "val": 0.1, "test": 0.1}
            output_paths = await exporter.export_to_unsloth(
                batch, "test_export_split", format="jsonl", split_ratio=split_ratio, enrich_context=False
            )
            
            # With only 2 examples, we should get at least 2 files
            if len(output_paths) < 2:
                all_validation_failures.append(f"Split export: Expected at least 2 output files, got {len(output_paths)}")
        except Exception as e:
            all_validation_failures.append(f"Split export failed: {str(e)}")
        
        # Test 4: Alpaca format
        total_tests += 1
        try:
            output_path = exporter.export_to_alpaca([batch], "test_export_alpaca")
            
            # Verify output exists
            if not Path(output_path).exists():
                all_validation_failures.append(f"Alpaca export: File {output_path} was not created")
        except Exception as e:
            all_validation_failures.append(f"Alpaca export failed: {str(e)}")
        
        # Test 5: OpenAI format
        total_tests += 1
        try:
            output_path = exporter.export_to_openai([batch], "test_export_openai")
            
            # Verify output exists
            if not Path(output_path).exists():
                all_validation_failures.append(f"OpenAI export: File {output_path} was not created")
        except Exception as e:
            all_validation_failures.append(f"OpenAI export failed: {str(e)}")
        
        # Test 6: Report format
        total_tests += 1
        try:
            output_path = exporter.export_summary_report([batch], "test_export_report.md")
            
            # Verify output exists
            if not Path(output_path).exists():
                all_validation_failures.append(f"Report export: File {output_path} was not created")
        except Exception as e:
            all_validation_failures.append(f"Report export failed: {str(e)}")
        
        # Test 7: Context enrichment (synchronous version)
        total_tests += 1
        try:
            output_path = exporter.export_to_unsloth_sync(batch, "test_export_sync", format="jsonl")
            
            # Verify output exists
            if not Path(output_path[0]).exists():
                all_validation_failures.append(f"Sync export: File {output_path[0]} was not created")
        except Exception as e:
            all_validation_failures.append(f"Sync export failed: {str(e)}")
        
        # Final validation result
        if all_validation_failures:
            print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                print(f"  - {failure}")
            return 1  # Exit with error code
        else:
            print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("QA exporter is validated and ready for use")
            return 0  # Exit with success code
    
    # Run the tests asynchronously
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)