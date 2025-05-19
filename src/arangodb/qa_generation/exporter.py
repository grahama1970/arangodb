"""
Export Q&A pairs to various training formats.

This module handles exporting validated Q&A pairs to formats suitable
for fine-tuning with UnSloth and other training frameworks.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .models import QABatch


class QAExporter:
    """Exports Q&A pairs to various training formats."""
    
    def __init__(self, output_dir: str = "qa_output"):
        """
        Initialize exporter.
        
        Args:
            output_dir: Directory to save exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_unsloth(
        self, 
        batches: List[QABatch],
        filename: Optional[str] = None,
        include_invalid: bool = False
    ) -> str:
        """
        Export Q&A batches to UnSloth format.
        
        Args:
            batches: List of Q&A batches to export
            filename: Output filename (auto-generated if None)
            include_invalid: Whether to include unvalidated pairs
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"qa_unsloth_{timestamp}.jsonl"
        
        output_path = self.output_dir / filename
        
        # Collect all messages
        all_messages = []
        stats = {
            "total_pairs": 0,
            "valid_pairs": 0,
            "documents": set(),
            "question_types": {}
        }
        
        for batch in batches:
            stats["documents"].add(batch.document_id)
            
            # Convert to UnSloth format
            messages = batch.to_unsloth_format()
            
            if include_invalid:
                # Include all pairs, even unvalidated ones
                for qa in batch.qa_pairs:
                    if not qa.citation_found:
                        message = {
                            "messages": [
                                {"role": "user", "content": qa.question},
                                {"role": "assistant", "content": qa.answer, "thinking": qa.thinking}
                            ],
                            "metadata": {
                                "question_type": qa.question_type.value,
                                "confidence": qa.confidence,
                                "source_section": qa.source_section,
                                "validation_score": qa.validation_score,
                                "validated": False
                            }
                        }
                        messages.append(message)
            
            all_messages.extend(messages)
            
            # Update statistics
            stats["total_pairs"] += batch.total_pairs
            stats["valid_pairs"] += batch.valid_pairs
            
            for qa in batch.qa_pairs:
                q_type = qa.question_type.value
                stats["question_types"][q_type] = stats["question_types"].get(q_type, 0) + 1
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            for message in all_messages:
                f.write(json.dumps(message, ensure_ascii=False) + '\n')
        
        # Write statistics
        stats_path = output_path.with_suffix('.stats.json')
        stats["documents"] = list(stats["documents"])
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Exported {len(all_messages)} Q&A pairs to {output_path}")
        logger.info(f"Statistics saved to {stats_path}")
        
        return str(output_path)
    
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