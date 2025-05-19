"""
Validation module for Q&A pairs using RapidFuzz.

This module validates generated Q&A pairs against the document corpus
to ensure answers are grounded in actual content.
"""

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from rapidfuzz import fuzz, process

from .models import QAPair, ValidationResult
from ..core.db_connection_wrapper import DatabaseOperations


class QAValidator:
    """Validates Q&A pairs against document corpus using RapidFuzz."""
    
    def __init__(self, db: DatabaseOperations, threshold: float = 0.97):
        """
        Initialize the validator.
        
        Args:
            db: Database operations instance
            threshold: RapidFuzz similarity threshold (default: 97%)
        """
        self.db = db
        self.threshold = threshold * 100  # RapidFuzz uses 0-100 scale
        self._corpus_cache = {}
    
    async def validate_qa_pair(self, qa_pair: QAPair, document_id: str) -> ValidationResult:
        """
        Validate a single Q&A pair against document corpus.
        
        Args:
            qa_pair: The Q&A pair to validate
            document_id: The source document ID
            
        Returns:
            ValidationResult with score and matched content
        """
        try:
            # Get document corpus if not cached
            if document_id not in self._corpus_cache:
                await self._load_document_corpus(document_id)
            
            corpus = self._corpus_cache[document_id]
            
            # Extract key answer segments for validation
            answer_segments = self._extract_answer_segments(qa_pair.answer)
            
            # Find best match in corpus
            best_match = None
            best_score = 0.0
            best_block_id = None
            
            for segment in answer_segments:
                for block_id, text in corpus.items():
                    # Use partial ratio for substring matching
                    score = fuzz.partial_ratio(segment, text)
                    
                    if score > best_score:
                        best_score = score
                        best_match = text[:500]  # Store first 500 chars
                        best_block_id = block_id
            
            # Create validation result
            is_valid = best_score >= self.threshold
            
            return ValidationResult(
                valid=is_valid,
                score=best_score / 100,  # Convert to 0-1 scale
                matched_content=best_match if is_valid else None,
                matched_block_id=best_block_id if is_valid else None,
                error_message=None if is_valid else f"Score {best_score}% below threshold {self.threshold}%"
            )
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                valid=False,
                score=0.0,
                matched_content=None,
                matched_block_id=None,
                error_message=str(e)
            )
    
    async def validate_batch(self, qa_pairs: List[QAPair], document_id: str) -> List[ValidationResult]:
        """
        Validate a batch of Q&A pairs concurrently.
        
        Args:
            qa_pairs: List of Q&A pairs to validate
            document_id: The source document ID
            
        Returns:
            List of ValidationResults
        """
        # Load corpus once for the batch
        if document_id not in self._corpus_cache:
            await self._load_document_corpus(document_id)
        
        # Validate concurrently
        tasks = [self.validate_qa_pair(qa, document_id) for qa in qa_pairs]
        results = await asyncio.gather(*tasks)
        
        # Log statistics
        valid_count = sum(1 for r in results if r.valid)
        logger.info(f"Validated {len(qa_pairs)} Q&A pairs: {valid_count} valid, {len(qa_pairs) - valid_count} invalid")
        
        return results
    
    async def _load_document_corpus(self, document_id: str):
        """Load document content into corpus cache."""
        try:
            # Query all text content from document
            query = """
            FOR obj IN document_objects
                FILTER obj.document_id == @doc_id
                FILTER obj._type IN ["text", "table", "code", "section"]
                FILTER obj.text != null
                RETURN {
                    id: obj._key,
                    text: obj.text,
                    type: obj._type
                }
            """
            
            cursor = self.db.aql.execute(query, bind_vars={"doc_id": document_id})
            
            # Build corpus dict
            corpus = {}
            for obj in cursor:
                corpus[obj['id']] = obj['text']
            
            self._corpus_cache[document_id] = corpus
            logger.info(f"Loaded corpus for document {document_id}: {len(corpus)} blocks")
            
        except Exception as e:
            logger.error(f"Error loading corpus: {e}")
            self._corpus_cache[document_id] = {}
    
    def _extract_answer_segments(self, answer: str, segment_length: int = 50) -> List[str]:
        """
        Extract key segments from answer for validation.
        
        Args:
            answer: The answer text
            segment_length: Length of segments to extract
            
        Returns:
            List of answer segments
        """
        # Split answer into sentences
        sentences = answer.replace('\n', ' ').split('. ')
        
        segments = []
        
        # Extract key segments from each sentence
        for sentence in sentences:
            # Skip very short sentences
            if len(sentence) < 20:
                continue
            
            # Take the first significant portion
            segment = sentence.strip()[:segment_length]
            if segment:
                segments.append(segment)
        
        # Also include the full first sentence if reasonable length
        if sentences and len(sentences[0]) <= 100:
            segments.append(sentences[0])
        
        return segments
    
    def clear_cache(self, document_id: Optional[str] = None):
        """
        Clear the corpus cache.
        
        Args:
            document_id: Specific document to clear, or None for all
        """
        if document_id:
            self._corpus_cache.pop(document_id, None)
        else:
            self._corpus_cache.clear()
        
        logger.info(f"Cleared corpus cache for: {document_id or 'all documents'}")