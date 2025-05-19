"""
Integration test for the complete Q&A generation flow.

This test verifies:
1. Marker outputs are properly structured
2. Q&A generator produces question/thinking/answer
3. Validation works correctly
4. Export format is correct
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime

from arangodb.qa_generation import (
    MarkerAwareQAGenerator,
    QAGenerationConfig,
    QAExporter,
    QuestionType
)
from arangodb.core.db_operations import DatabaseOperations


class TestQAGenerationFlow:
    """Test the complete Q&A generation flow."""
    
    @pytest.fixture
    def sample_marker_output(self):
        """Create a sample Marker output with Q&A-optimized format."""
        return {
            "document": {
                "id": "test_document",
                "pages": [
                    {
                        "blocks": [
                            {
                                "type": "section_header",
                                "text": "Introduction to Machine Learning",
                                "level": 1
                            },
                            {
                                "type": "text",
                                "text": "Machine learning is a subset of artificial intelligence."
                            },
                            {
                                "type": "section_header",
                                "text": "Types of Learning",
                                "level": 2
                            },
                            {
                                "type": "text",
                                "text": "There are three main types: supervised, unsupervised, and reinforcement learning."
                            }
                        ]
                    }
                ]
            },
            "metadata": {
                "title": "ML Basics",
                "processing_time": 1.5
            },
            "validation": {
                "corpus_validation": {
                    "performed": True,
                    "threshold": 97,
                    "raw_corpus_length": 500
                }
            },
            "raw_corpus": {
                "full_text": """Introduction to Machine Learning

Machine learning is a subset of artificial intelligence.

Types of Learning

There are three main types: supervised, unsupervised, and reinforcement learning.""",
                "pages": [
                    {
                        "page_num": 0,
                        "text": "Introduction to Machine Learning\n\nMachine learning is a subset of artificial intelligence.\n\nTypes of Learning\n\nThere are three main types: supervised, unsupervised, and reinforcement learning.",
                        "tables": []
                    }
                ],
                "total_pages": 1
            }
        }
    
    @pytest.fixture
    def qa_config(self):
        """Create Q&A generation configuration."""
        return QAGenerationConfig(
            max_questions_per_doc=5,
            validation_threshold=0.9,
            temperature_range=(0.0, 0.2),
            answer_temperature=0.0,
            max_retries=3
        )
    
    @pytest.mark.asyncio
    async def test_qa_generation_from_marker(self, sample_marker_output, qa_config):
        """Test Q&A generation from Marker output."""
        # Initialize generator
        db = DatabaseOperations()
        generator = MarkerAwareQAGenerator(db, qa_config)
        
        # Generate Q&A pairs
        qa_batch = await generator.generate_from_marker_document(
            sample_marker_output,
            max_pairs=3
        )
        
        # Verify batch structure
        assert qa_batch is not None
        assert len(qa_batch.qa_pairs) > 0
        assert qa_batch.document_id == "test_document"
        
        # Verify metadata
        assert qa_batch.metadata["source"] == "marker"
        assert qa_batch.metadata["corpus_validation"] == True
        assert "validation_rate" in qa_batch.metadata
        
        # Verify each Q&A pair
        for qa_pair in qa_batch.qa_pairs:
            # Check required fields
            assert qa_pair.question is not None
            assert qa_pair.thinking is not None
            assert qa_pair.answer is not None
            
            # Check field content
            assert len(qa_pair.question) > 10
            assert len(qa_pair.thinking) > 20
            assert len(qa_pair.answer) > 10
            
            # Check metadata
            assert qa_pair.question_type in QuestionType
            assert 0 <= qa_pair.confidence <= 1
            assert qa_pair.validation_score is not None
            
            # Log for inspection
            print(f"\nQ: {qa_pair.question}")
            print(f"T: {qa_pair.thinking[:100]}...")
            print(f"A: {qa_pair.answer}")
            print(f"Valid: {qa_pair.citation_found}")
    
    @pytest.mark.asyncio
    async def test_answer_validation(self, sample_marker_output, qa_config):
        """Test that answers are validated against the corpus."""
        db = DatabaseOperations()
        generator = MarkerAwareQAGenerator(db, qa_config)
        
        # Generate Q&A pairs
        qa_batch = await generator.generate_from_marker_document(
            sample_marker_output,
            max_pairs=5
        )
        
        # Check validation results
        valid_count = sum(1 for qa in qa_batch.qa_pairs if qa.citation_found)
        invalid_count = len(qa_batch.qa_pairs) - valid_count
        
        print(f"\nValidation Results:")
        print(f"Valid: {valid_count}")
        print(f"Invalid: {invalid_count}")
        print(f"Rate: {qa_batch.metadata['validation_rate']:.1%}")
        
        # At least some should be valid
        assert valid_count > 0
        
        # Check that validation scores are set
        for qa_pair in qa_batch.qa_pairs:
            assert qa_pair.validation_score is not None
            assert 0 <= qa_pair.validation_score <= 1
            
            if qa_pair.citation_found:
                # Valid answers should have high scores
                assert qa_pair.validation_score >= 0.9
    
    def test_unsloth_export_format(self, sample_marker_output, qa_config):
        """Test export to UnSloth training format."""
        # Create some Q&A pairs (mock for testing)
        from arangodb.qa_generation.models import QAPair
        
        qa_pairs = [
            QAPair(
                question="What is machine learning?",
                thinking="The user is asking for a definition of machine learning.",
                answer="Machine learning is a subset of artificial intelligence.",
                question_type=QuestionType.FACTUAL,
                confidence=0.95,
                validation_score=0.98,
                citation_found=True
            ),
            QAPair(
                question="What are the types of machine learning?",
                thinking="The user wants to know about different types of ML.",
                answer="There are three main types: supervised, unsupervised, and reinforcement learning.",
                question_type=QuestionType.FACTUAL,
                confidence=0.92,
                validation_score=0.96,
                citation_found=True
            )
        ]
        
        # Export to UnSloth format
        exporter = QAExporter()
        unsloth_data = exporter.export_to_unsloth(qa_pairs)
        
        # Verify format
        assert isinstance(unsloth_data, list)
        assert len(unsloth_data) == 2
        
        for item in unsloth_data:
            # Check structure
            assert "messages" in item
            assert len(item["messages"]) == 2
            
            # Check user message
            user_msg = item["messages"][0]
            assert user_msg["role"] == "user"
            assert "content" in user_msg
            
            # Check assistant message
            assistant_msg = item["messages"][1]
            assert assistant_msg["role"] == "assistant"
            assert "content" in assistant_msg
            assert "thinking" in assistant_msg
            
            # Check metadata
            assert "metadata" in item
            assert "question_type" in item["metadata"]
            assert "confidence" in item["metadata"]
            assert "validation_score" in item["metadata"]
        
        print(f"\nExported {len(unsloth_data)} Q&A pairs to UnSloth format")
        print(json.dumps(unsloth_data[0], indent=2))
    
    @pytest.mark.asyncio
    async def test_marker_corpus_detection(self, qa_config):
        """Test handling of Marker outputs with and without corpus."""
        db = DatabaseOperations()
        generator = MarkerAwareQAGenerator(db, qa_config)
        
        # Test with corpus
        marker_with_corpus = {
            "document": {"id": "doc1"},
            "raw_corpus": {"full_text": "Test content"}
        }
        
        # This should work fine
        qa_batch = await generator.generate_from_marker_document(
            marker_with_corpus,
            max_pairs=1
        )
        assert qa_batch is not None
        
        # Test without corpus (should fall back)
        marker_without_corpus = {
            "document": {
                "id": "doc2",
                "pages": [{
                    "blocks": [{
                        "type": "text",
                        "text": "Fallback content"
                    }]
                }]
            }
        }
        
        # This should still work with fallback
        qa_batch = await generator.generate_from_marker_document(
            marker_without_corpus,
            max_pairs=1
        )
        assert qa_batch is not None
        
        print("✓ Corpus detection and fallback working correctly")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])