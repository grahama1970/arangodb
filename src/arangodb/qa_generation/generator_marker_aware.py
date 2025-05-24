"""
Q&A Generator that uses complete corpus from Marker.

This generator is aware of Marker's validated corpus and uses it
for answer validation instead of re-extracting from PDFs.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from .generator import QAGenerator
from .models import (
    QAPair,
    QAGenerationConfig,
    QuestionType,
    ValidationResult,
    QABatch
)
from .validator import QAValidator
from ..core.db_connection_wrapper import DatabaseOperations


class MarkerAwareQAGenerator(QAGenerator):
    """
    Q&A generator that uses Marker's validated corpus.
    
    This generator expects documents to have the raw corpus
    included from Marker's Q&A-optimized conversion.
    """
    
    def __init__(
        self,
        db: DatabaseOperations,
        config: Optional[QAGenerationConfig] = None
    ):
        """Initialize with Marker corpus awareness."""
        super().__init__(db, config)
        self._marker_corpus_cache = {}
        
    async def generate_from_marker_document(
        self,
        marker_output: Dict[str, Any],
        max_pairs: Optional[int] = None
    ) -> QABatch:
        """
        Generate Q&A pairs from Marker output with validated corpus.
        
        Args:
            marker_output: Complete Marker output including raw_corpus
            max_pairs: Maximum number of pairs to generate
            
        Returns:
            QABatch with validated Q&A pairs
        """
        # Extract document info
        document = marker_output.get("document", {})
        document_id = document.get("id", f"marker_{datetime.utcnow().timestamp()}")
        
        # Get the validated corpus from Marker
        raw_corpus = marker_output.get("raw_corpus")
        if not raw_corpus:
            logger.warning("No raw corpus found in Marker output, falling back to document content")
            raw_corpus = self._extract_corpus_from_document(document)
        
        # Store corpus for validation
        self._marker_corpus_cache[document_id] = raw_corpus
        
        # Generate Q&A pairs using the document structure
        logger.info(f"Generating Q&A pairs using Marker corpus")
        qa_pairs = await self._generate_qa_from_structure(
            document,
            raw_corpus,
            max_pairs or self.config.max_questions_per_doc
        )
        
        # Validate against Marker's corpus
        validated_pairs = await self._validate_with_marker_corpus(
            qa_pairs,
            document_id,
            raw_corpus
        )
        
        # Create batch with metadata
        batch = QABatch(
            qa_pairs=validated_pairs,
            document_id=document_id,
            metadata={
                "source": "marker",
                "corpus_validation": True,
                "marker_validation": marker_output.get("validation", {}),
                "total_generated": len(qa_pairs),
                "valid_count": len(validated_pairs),
                "validation_rate": len(validated_pairs) / len(qa_pairs) if qa_pairs else 0
            }
        )
        
        # Ensure batch has required fields even if it's empty
        if not hasattr(batch, 'document_id') or not batch.document_id:
            batch.document_id = document_id
        
        return batch
    
    async def _generate_qa_from_structure(
        self,
        document: Dict[str, Any],
        raw_corpus: Dict[str, Any],
        max_pairs: int
    ) -> List[QAPair]:
        """Generate Q&A pairs from Marker document structure."""
        qa_pairs = []
        
        # Extract sections and content
        sections = self._extract_sections(document)
        relationships = self._extract_relationships(document)
        
        # Calculate distribution
        type_counts = self._calculate_type_distribution(max_pairs)
        
        # Generate each type
        for question_type, count in type_counts.items():
            if count == 0:
                continue
                
            logger.info(f"Generating {count} {question_type.value} questions...")
            
            if question_type == QuestionType.FACTUAL:
                pairs = await self._generate_factual_qa(sections, count)
            elif question_type == QuestionType.RELATIONSHIP:
                pairs = await self._generate_relationship_qa(relationships, count)
            elif question_type == QuestionType.MULTI_HOP:
                pairs = await self._generate_multihop_qa(relationships, count)
            elif question_type == QuestionType.HIERARCHICAL:
                pairs = await self._generate_hierarchical_qa(sections, count)
            elif question_type == QuestionType.REVERSAL:
                pairs = await self._generate_reversal_qa(sections, count)
            else:
                continue
            
            qa_pairs.extend(pairs)
        
        return qa_pairs
    
    async def _validate_with_marker_corpus(
        self,
        qa_pairs: List[QAPair],
        document_id: str,
        raw_corpus: Dict[str, Any]
    ) -> List[QAPair]:
        """Validate Q&A pairs against Marker's validated corpus."""
        from rapidfuzz import fuzz
        
        validated_pairs = []
        full_text = raw_corpus.get("full_text", "")
        
        for qa_pair in qa_pairs:
            # Check answer against raw corpus
            answer_segments = self._extract_answer_segments(qa_pair.answer)
            best_score = 0.0
            
            for segment in answer_segments:
                # Check against full text
                score = fuzz.partial_ratio(segment, full_text)
                best_score = max(best_score, score)
                
                # Also check against individual pages if available
                if "pages" in raw_corpus:
                    for page_data in raw_corpus["pages"]:
                        page_text = page_data.get("text", "")
                        score = fuzz.partial_ratio(segment, page_text)
                        best_score = max(best_score, score)
                        
                        # Check tables specifically
                        for table_text in page_data.get("tables", []):
                            score = fuzz.partial_ratio(segment, table_text)
                            best_score = max(best_score, score)
                
                if best_score >= self.config.validation_threshold * 100:
                    break
            
            # Set validation results
            qa_pair.validation_score = best_score / 100
            qa_pair.citation_found = best_score >= self.config.validation_threshold * 100
            
            if qa_pair.citation_found:
                validated_pairs.append(qa_pair)
            else:
                logger.warning(
                    f"Rejected Q&A - Score: {best_score:.1f}%\n"
                    f"Q: {qa_pair.question[:50]}...\n"
                    f"A: {qa_pair.answer[:50]}..."
                )
        
        return validated_pairs
    
    def _extract_sections(self, document: Dict[str, Any]) -> List[Dict]:
        """Extract sections from Marker document structure."""
        sections = []
        
        # Handle different Marker output formats
        if "pages" in document:
            # Page-based format
            for page_num, page in enumerate(document["pages"]):
                for block in page.get("blocks", []):
                    if block.get("type") == "section_header":
                        sections.append({
                            "title": block.get("text", ""),
                            "level": block.get("level", 1),
                            "page": page_num,
                            "content": self._get_section_content(page, block)
                        })
        elif "children" in document:
            # Hierarchical format
            self._extract_sections_recursive(document["children"], sections)
        
        return sections
    
    def _extract_sections_recursive(self, blocks: List[Dict], sections: List[Dict], level: int = 0):
        """Recursively extract sections from hierarchical structure."""
        for block in blocks:
            if block.get("block_type") == "SectionHeader":
                sections.append({
                    "title": block.get("text", ""),
                    "level": level,
                    "content": block.get("content", ""),
                    "children": block.get("children", [])
                })
            
            if "children" in block:
                self._extract_sections_recursive(block["children"], sections, level + 1)
    
    def _extract_relationships(self, document: Dict[str, Any]) -> List[Dict]:
        """Extract relationships from document structure."""
        relationships = []
        
        # Extract relationships between sections, entities, etc.
        # This would be customized based on Marker's output structure
        
        return relationships
    
    def _extract_corpus_from_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: Extract corpus from document if not provided."""
        text_parts = []
        
        if "pages" in document:
            for page in document["pages"]:
                for block in page.get("blocks", []):
                    if "text" in block:
                        text_parts.append(block["text"])
        elif "children" in document:
            self._extract_text_recursive(document["children"], text_parts)
        
        return {
            "full_text": "\n".join(text_parts),
            "pages": [],
            "total_pages": len(document.get("pages", []))
        }
    
    def _extract_text_recursive(self, blocks: List[Dict], text_parts: List[str]):
        """Recursively extract text from blocks."""
        for block in blocks:
            if "text" in block:
                text_parts.append(block["text"])
            if "children" in block:
                self._extract_text_recursive(block["children"], text_parts)
    
    def _extract_answer_segments(self, answer: str) -> List[str]:
        """Extract key segments from answer for validation."""
        segments = []
        
        # Split by sentences
        sentences = answer.split('. ')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                segments.append(sentence[:100] if len(sentence) > 100 else sentence)
        
        # Also include first portion
        if len(answer) > 50:
            segments.append(answer[:100])
        
        return segments
    
    def _get_section_content(self, page: Dict, section_block: Dict) -> str:
        """Get content following a section header."""
        content_parts = []
        found_section = False
        
        for block in page.get("blocks", []):
            if block == section_block:
                found_section = True
                continue
            
            if found_section:
                # Stop at next section header
                if block.get("type") == "section_header":
                    break
                    
                if "text" in block:
                    content_parts.append(block["text"])
        
        return " ".join(content_parts)


async def generate_qa_from_marker_file(
    marker_file: Path,
    db: DatabaseOperations,
    config: Optional[QAGenerationConfig] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Generate Q&A pairs from a Marker output file.
    
    Args:
        marker_file: Path to Marker JSON output
        db: Database operations instance
        config: Generation configuration
        output_dir: Output directory
        
    Returns:
        Path to generated Q&A file
    """
    # Load Marker output
    with open(marker_file, 'r') as f:
        marker_output = json.load(f)
    
    # Check if it's Q&A-optimized output
    if "raw_corpus" not in marker_output:
        logger.warning(
            "Marker output doesn't include raw_corpus. "
            "Consider using marker-qa convert for better validation."
        )
    
    # Create generator
    generator = MarkerAwareQAGenerator(db, config)
    
    # Generate Q&A pairs
    qa_batch = await generator.generate_from_marker_document(marker_output)
    
    # Export to UnSloth format
    from .exporter import QAExporter
    exporter = QAExporter()
    
    output_dir = output_dir or Path("./qa_output")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Export to file
    output_path = output_dir / f"{marker_file.stem}_qa.json"
    export_paths = await exporter.export_to_unsloth(qa_batch, filename=output_path.name)
    
    logger.info(f"Generated {len(qa_batch.qa_pairs)} validated Q&A pairs")
    logger.info(f"Validation rate: {qa_batch.metadata.get('validation_rate', 0):.1%}")
    logger.info(f"Output: {export_paths[0] if export_paths else output_path}")
    
    return Path(export_paths[0]) if export_paths else output_path


# Example usage
async def main():
    """Example of using Marker-aware generator."""
    from ..core.db_connection_wrapper import DatabaseOperations
    
    # Initialize
    db = DatabaseOperations()
    
    # Generate from Marker output
    output_path = await generate_qa_from_marker_file(
        marker_file=Path("./marker_output/document.json"),
        db=db,
        config=QAGenerationConfig(
            max_questions_per_doc=30,
            validation_threshold=0.97
        )
    )
    
    print(f"Q&A generation complete: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())