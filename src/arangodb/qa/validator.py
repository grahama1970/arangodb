"""
QA Validation Module

This module provides validation functionality for QA pairs, including
checking answers against source content and verifying that questions
are answerable from the provided context.

Links:
- RapidFuzz: https://rapidfuzz.github.io/RapidFuzz/
- ArangoDB: https://www.arangodb.com/docs/stable/

Sample Input/Output:
- Input: QA pair and source content
- Output: Validation result with confidence score
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set
from loguru import logger
import asyncio
from rapidfuzz import fuzz
import re
import time
from pydantic import BaseModel, Field

from arangodb.qa.schemas import (
    QAPair,
    QAValidationResult,
    ValidationStatus
)


def extract_answer_segments(answer: str, min_length: int = 5) -> List[str]:
    """
    Extract key segments from an answer for validation.
    
    Args:
        answer: The answer text
        min_length: Minimum segment length
        
    Returns:
        List of answer segments
    """
    # Clean the answer
    clean_answer = answer.strip()
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', clean_answer)
    
    # Further split long sentences by commas, semicolons, etc.
    segments = []
    for sentence in sentences:
        if len(sentence) > 100:  # Only split long sentences
            sub_segments = re.split(r'(?<=[:;,])\s+', sentence)
            segments.extend(sub_segments)
        else:
            segments.append(sentence)
    
    # Filter out short segments and duplicates
    return [seg for seg in segments if len(seg) >= min_length]


class QAValidator:
    """
    Validates QA pairs against source content.
    
    Uses fuzzy matching to determine if answers are supported by the source content.
    """
    
    def __init__(
        self,
        threshold: float = 97.0,
        min_segment_length: int = 15
    ):
        """
        Initialize the validator.
        
        Args:
            threshold: Minimum validation score (0-100)
            min_segment_length: Minimum text segment length for validation
        """
        self.threshold = threshold
        self.min_segment_length = min_segment_length
        self.corpus_cache = {}  # Cache for document corpus
    
    def validate_qa_pair(
        self,
        qa_pair: QAPair,
        corpus: Union[str, Dict[str, str]]
    ) -> QAValidationResult:
        """
        Validate a QA pair against source content.
        
        Args:
            qa_pair: The QA pair to validate
            corpus: Source content as string or dict of section IDs to content
            
        Returns:
            Validation result
        """
        # Extract key segments from the answer
        segments = extract_answer_segments(qa_pair.answer, self.min_segment_length)
        
        if not segments:
            return QAValidationResult(
                qa_id=qa_pair._key or "unknown",
                validation_score=0.0,
                status=ValidationStatus.FAILED,
                matched_segments=[],
                metadata={
                    "error": "No valid segments found in answer"
                }
            )
        
        # Validate each segment against the corpus
        best_score = 0.0
        best_match = ""
        matches = []
        
        # Handle different corpus formats
        corpus_text = ""
        if isinstance(corpus, str):
            corpus_text = corpus
        elif isinstance(corpus, dict):
            # Combine all sections into a single text for validation
            corpus_text = "\n".join(corpus.values())
        
        # Validate each segment
        for segment in segments:
            # Skip very short segments
            if len(segment) < self.min_segment_length:
                continue
                
            # Calculate fuzzy match score
            score = fuzz.partial_ratio(segment, corpus_text)
            
            # Track matches
            if score >= 50:  # Track any reasonable match
                matches.append({
                    "segment": segment,
                    "score": score
                })
            
            # Track best score
            if score > best_score:
                best_score = score
                best_match = segment
        
        # Determine validation status
        if best_score >= self.threshold:
            status = ValidationStatus.VALIDATED
        elif best_score >= 85:
            status = ValidationStatus.PARTIAL
        else:
            status = ValidationStatus.FAILED
        
        # Create result
        result = QAValidationResult(
            qa_id=qa_pair._key or "unknown",
            validation_score=best_score / 100.0,  # Convert to 0-1 range
            status=status,
            matched_segments=matches,
            metadata={
                "best_match": best_match,
                "segments_checked": len(segments),
                "original_threshold": self.threshold
            }
        )
        
        return result
    
    async def validate_batch(
        self,
        qa_pairs: List[QAPair],
        corpus: Union[str, Dict[str, str]]
    ) -> List[QAValidationResult]:
        """
        Validate a batch of QA pairs.
        
        Args:
            qa_pairs: List of QA pairs to validate
            corpus: Source content
            
        Returns:
            List of validation results
        """
        # Create validation tasks
        tasks = []
        for qa_pair in qa_pairs:
            # Run validation in a separate task
            task = asyncio.create_task(self._validate_async(qa_pair, corpus))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def _validate_async(
        self,
        qa_pair: QAPair,
        corpus: Union[str, Dict[str, str]]
    ) -> QAValidationResult:
        """
        Validate a QA pair asynchronously.
        
        Args:
            qa_pair: The QA pair to validate
            corpus: Source content
            
        Returns:
            Validation result
        """
        # Run validation in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.validate_qa_pair,
            qa_pair,
            corpus
        )
    
    def validate_against_document(
        self,
        qa_pair: QAPair,
        document_id: str,
        db
    ) -> QAValidationResult:
        """
        Validate a QA pair against a document in ArangoDB.
        
        Args:
            qa_pair: The QA pair to validate
            document_id: The document ID
            db: ArangoDB database instance
            
        Returns:
            Validation result
        """
        # Check cache first
        if document_id in self.corpus_cache:
            corpus = self.corpus_cache[document_id]
        else:
            # Get document content
            query = """
            FOR obj IN document_objects
                FILTER obj.document_id == @document_id
                FILTER obj._type IN ["text", "table", "code"]
                RETURN {
                    id: obj._key,
                    section: obj.section_hash,
                    text: obj.text
                }
            """
            
            cursor = db.aql.execute(query, bind_vars={"document_id": document_id})
            results = list(cursor)
            
            # Create corpus dict
            corpus = {
                result["id"]: result["text"]
                for result in results
                if result["text"]
            }
            
            # Cache for future use
            self.corpus_cache[document_id] = corpus
        
        # Validate against corpus
        return self.validate_qa_pair(qa_pair, corpus)
    
    async def validate_batch_against_document(
        self,
        qa_pairs: List[QAPair],
        document_id: str,
        db
    ) -> List[QAValidationResult]:
        """
        Validate a batch of QA pairs against a document.
        
        Args:
            qa_pairs: List of QA pairs to validate
            document_id: The document ID
            db: ArangoDB database instance
            
        Returns:
            List of validation results
        """
        # Get document content (only once for all QA pairs)
        if document_id not in self.corpus_cache:
            query = """
            FOR obj IN document_objects
                FILTER obj.document_id == @document_id
                FILTER obj._type IN ["text", "table", "code"]
                RETURN {
                    id: obj._key,
                    section: obj.section_hash,
                    text: obj.text
                }
            """
            
            cursor = db.aql.execute(query, bind_vars={"document_id": document_id})
            results = list(cursor)
            
            # Create corpus dict
            corpus = {
                result["id"]: result["text"]
                for result in results
                if result["text"]
            }
            
            # Cache for future use
            self.corpus_cache[document_id] = corpus
        else:
            corpus = self.corpus_cache[document_id]
        
        # Validate batch against corpus
        return await self.validate_batch(qa_pairs, corpus)
    
    def validate_against_text(
        self,
        qa_pair: QAPair,
        text: str
    ) -> QAValidationResult:
        """
        Validate a QA pair against raw text.
        
        Args:
            qa_pair: The QA pair to validate
            text: Raw text to validate against
            
        Returns:
            Validation result
        """
        return self.validate_qa_pair(qa_pair, text)


def validate_qa_batch_with_corpus(
    qa_pairs: List[QAPair],
    corpus: Union[str, Dict[str, str]],
    threshold: float = 97.0
) -> Tuple[List[QAPair], Dict[str, Any]]:
    """
    Validate a batch of QA pairs against a corpus.
    
    Args:
        qa_pairs: List of QA pairs to validate
        corpus: Source content
        threshold: Validation threshold (0-100)
        
    Returns:
        Tuple of (validated_qa_pairs, validation_stats)
    """
    validator = QAValidator(threshold=threshold)
    validated_pairs = []
    
    # Track validation statistics
    stats = {
        "total": len(qa_pairs),
        "validated": 0,
        "partial": 0,
        "failed": 0,
        "avg_score": 0.0
    }
    
    # Validate each pair
    for qa_pair in qa_pairs:
        result = validator.validate_qa_pair(qa_pair, corpus)
        
        # Update QA pair with validation result
        qa_pair.validation_score = result.validation_score
        qa_pair.citation_found = result.status == ValidationStatus.VALIDATED
        qa_pair.validation_status = result.status
        
        # Only include validated pairs
        if result.status == ValidationStatus.VALIDATED:
            validated_pairs.append(qa_pair)
            stats["validated"] += 1
        elif result.status == ValidationStatus.PARTIAL:
            stats["partial"] += 1
        else:
            stats["failed"] += 1
        
        # Track scores
        stats["avg_score"] += result.validation_score
    
    # Calculate average score
    if qa_pairs:
        stats["avg_score"] /= len(qa_pairs)
    
    # Calculate validation rate
    stats["validation_rate"] = stats["validated"] / stats["total"] if stats["total"] > 0 else 0.0
    
    return validated_pairs, stats


async def validate_qa_batch_async(
    qa_pairs: List[QAPair],
    corpus: Union[str, Dict[str, str]],
    threshold: float = 97.0
) -> Tuple[List[QAPair], Dict[str, Any]]:
    """
    Validate a batch of QA pairs asynchronously.
    
    Args:
        qa_pairs: List of QA pairs to validate
        corpus: Source content
        threshold: Validation threshold (0-100)
        
    Returns:
        Tuple of (validated_qa_pairs, validation_stats)
    """
    validator = QAValidator(threshold=threshold)
    
    # Get validation results asynchronously
    results = await validator.validate_batch(qa_pairs, corpus)
    
    # Track validation statistics
    stats = {
        "total": len(qa_pairs),
        "validated": 0,
        "partial": 0,
        "failed": 0,
        "avg_score": 0.0
    }
    
    # Process results
    validated_pairs = []
    for i, result in enumerate(results):
        # Update QA pair with validation result
        qa_pairs[i].validation_score = result.validation_score
        qa_pairs[i].citation_found = result.status == ValidationStatus.VALIDATED
        qa_pairs[i].validation_status = result.status
        
        # Only include validated pairs
        if result.status == ValidationStatus.VALIDATED:
            validated_pairs.append(qa_pairs[i])
            stats["validated"] += 1
        elif result.status == ValidationStatus.PARTIAL:
            stats["partial"] += 1
        else:
            stats["failed"] += 1
        
        # Track scores
        stats["avg_score"] += result.validation_score
    
    # Calculate average score
    if qa_pairs:
        stats["avg_score"] /= len(qa_pairs)
    
    # Calculate validation rate
    stats["validation_rate"] = stats["validated"] / stats["total"] if stats["total"] > 0 else 0.0
    
    return validated_pairs, stats


if __name__ == "__main__":
    """
    Self-validation tests for the QA validator.
    
    This validation tests the QA validation functionality.
    """
    import sys
    import json
    
    # Configure logger for validation output
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Basic validation
    total_tests += 1
    try:
        print("\nTest 1: Basic validation")
        
        # Create a QA pair
        qa_pair = QAPair(
            question="What is the capital of France?",
            thinking="I need to recall information about France and its capital city.",
            answer="The capital of France is Paris.",
            question_type="FACTUAL",
            document_id="test_doc",
            source_sections=["section_1"],
            evidence_blocks=["text_123"],
            confidence=0.95,
            citation_found=False
        )
        
        # Create validator
        validator = QAValidator(threshold=90.0)
        
        # Create test corpus
        corpus = """
        France is a country in Western Europe. The capital of France is Paris.
        Paris is known for its art, culture, and architecture.
        """
        
        # Validate
        result = validator.validate_qa_pair(qa_pair, corpus)
        
        # Verify result
        assert result.validation_score >= 0.9, f"Expected score >= 0.9, got {result.validation_score}"
        assert result.status == ValidationStatus.VALIDATED, f"Expected VALIDATED, got {result.status}"
        
        print(f"Validation score: {result.validation_score:.2f}")
        print(f"Validation status: {result.status}")
        print("✅ Basic validation successful")
    except Exception as e:
        all_validation_failures.append(f"Basic validation test failed: {str(e)}")
    
    # Test 2: Failed validation
    total_tests += 1
    try:
        print("\nTest 2: Failed validation")
        
        # Create a QA pair with incorrect answer
        qa_pair = QAPair(
            question="What is the capital of Germany?",
            thinking="I need to recall information about Germany and its capital city.",
            answer="The capital of Germany is Hamburg.",  # Incorrect
            question_type="FACTUAL",
            document_id="test_doc",
            source_sections=["section_1"],
            evidence_blocks=["text_123"],
            confidence=0.95,
            citation_found=False
        )
        
        # Create validator
        validator = QAValidator(threshold=90.0)
        
        # Create test corpus
        corpus = """
        Germany is a country in Western Europe. The capital of Germany is Berlin.
        Berlin is known for its history and vibrant culture.
        """
        
        # Validate
        result = validator.validate_qa_pair(qa_pair, corpus)
        
        # Verify result
        assert result.validation_score < 0.9, f"Expected score < 0.9, got {result.validation_score}"
        assert result.status != ValidationStatus.VALIDATED, f"Expected non-VALIDATED, got {result.status}"
        
        print(f"Validation score: {result.validation_score:.2f}")
        print(f"Validation status: {result.status}")
        print("✅ Failed validation test successful")
    except Exception as e:
        all_validation_failures.append(f"Failed validation test failed: {str(e)}")
    
    # Test 3: Batch validation
    total_tests += 1
    try:
        print("\nTest 3: Batch validation")
        
        # Create multiple QA pairs
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
                citation_found=False
            ),
            QAPair(
                question="What is the capital of Germany?",
                thinking="I need to recall information about Germany and its capital city.",
                answer="The capital of Germany is Hamburg.",  # Incorrect
                question_type="FACTUAL",
                document_id="test_doc",
                source_sections=["section_1"],
                evidence_blocks=["text_123"],
                confidence=0.95,
                citation_found=False
            ),
            QAPair(
                question="What is the capital of Italy?",
                thinking="I need to recall information about Italy and its capital city.",
                answer="The capital of Italy is Rome.",
                question_type="FACTUAL",
                document_id="test_doc",
                source_sections=["section_1"],
                evidence_blocks=["text_123"],
                confidence=0.95,
                citation_found=False
            )
        ]
        
        # Create test corpus
        corpus = """
        France is a country in Western Europe. The capital of France is Paris.
        Paris is known for its art, culture, and architecture.
        
        Germany is a country in Western Europe. The capital of Germany is Berlin.
        Berlin is known for its history and vibrant culture.
        
        Italy is a country in Southern Europe. The capital of Italy is Rome.
        Rome is known for its ancient history and architecture.
        """
        
        # Run batch validation
        validated_pairs, stats = validate_qa_batch_with_corpus(qa_pairs, corpus, threshold=90.0)
        
        # Verify results
        assert len(validated_pairs) == 2, f"Expected 2 validated pairs, got {len(validated_pairs)}"
        assert stats["validated"] == 2, f"Expected 2 validated pairs, got {stats['validated']}"
        assert stats["failed"] == 1, f"Expected 1 failed pair, got {stats['failed']}"
        
        print(f"Validation stats: {json.dumps(stats, indent=2)}")
        print("✅ Batch validation successful")
    except Exception as e:
        all_validation_failures.append(f"Batch validation test failed: {str(e)}")
    
    # Test 4: Asynchronous validation
    total_tests += 1
    try:
        print("\nTest 4: Asynchronous validation")
        
        # Create multiple QA pairs (same as Test 3)
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
                citation_found=False
            ),
            QAPair(
                question="What is the capital of Germany?",
                thinking="I need to recall information about Germany and its capital city.",
                answer="The capital of Germany is Hamburg.",  # Incorrect
                question_type="FACTUAL",
                document_id="test_doc",
                source_sections=["section_1"],
                evidence_blocks=["text_123"],
                confidence=0.95,
                citation_found=False
            ),
            QAPair(
                question="What is the capital of Italy?",
                thinking="I need to recall information about Italy and its capital city.",
                answer="The capital of Italy is Rome.",
                question_type="FACTUAL",
                document_id="test_doc",
                source_sections=["section_1"],
                evidence_blocks=["text_123"],
                confidence=0.95,
                citation_found=False
            )
        ]
        
        # Create test corpus (same as Test 3)
        corpus = """
        France is a country in Western Europe. The capital of France is Paris.
        Paris is known for its art, culture, and architecture.
        
        Germany is a country in Western Europe. The capital of Germany is Berlin.
        Berlin is known for its history and vibrant culture.
        
        Italy is a country in Southern Europe. The capital of Italy is Rome.
        Rome is known for its ancient history and architecture.
        """
        
        # Define async test function
        async def async_test():
            # Run async batch validation
            validator = QAValidator(threshold=90.0)
            results = await validator.validate_batch(qa_pairs, corpus)
            
            # Count validated pairs
            validated = sum(1 for r in results if r.status == ValidationStatus.VALIDATED)
            
            # Verify results
            assert validated == 2, f"Expected 2 validated pairs, got {validated}"
            assert len(results) == 3, f"Expected 3 results, got {len(results)}"
            
            # Also test the helper function
            validated_pairs, stats = await validate_qa_batch_async(qa_pairs, corpus, threshold=90.0)
            assert len(validated_pairs) == 2, f"Expected 2 validated pairs, got {len(validated_pairs)}"
            assert stats["validated"] == 2, f"Expected 2 validated pairs, got {stats['validated']}"
            
            print(f"Async validation stats: {json.dumps(stats, indent=2)}")
            return "✅ Async validation successful"
        
        # Run async test
        import asyncio
        result = asyncio.run(async_test())
        print(result)
    except Exception as e:
        all_validation_failures.append(f"Async validation test failed: {str(e)}")
    
    # Final validation result
    if all_validation_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("QA validator module is validated and ready for use")
        sys.exit(0)  # Exit with success code