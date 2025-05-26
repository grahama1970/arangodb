"""
Verification script for Q&A generation functionality.

This script verifies that the ArangoDB Q&A module correctly:
1. Generates questions with thinking process and answers
2. Validates answers against the corpus
3. Exports in the correct format

Expected output:
    Q&A pairs with question, thinking, and answer fields
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

from arangodb.qa_generation.generator_marker_aware import MarkerAwareQAGenerator
from arangodb.qa_generation.generator import QAGenerationConfig
from arangodb.qa_generation.models import QuestionType
from arangodb.qa_generation.exporter import QAExporter
from arangodb.core.db_connection_wrapper import DatabaseOperations


async def verify_qa_generation():
    """Verify Q&A generation with sample data."""
    logger.info("Starting Q&A generation verification")
    
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Create sample Marker output with corpus
    total_tests += 1
    sample_marker_output = {
        "document": {
            "id": "test_doc_001",
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
                            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn from data without being explicitly programmed."
                        },
                        {
                            "type": "text",
                            "text": "There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning."
                        }
                    ]
                }
            ]
        },
        "metadata": {
            "title": "ML Overview",
            "page_count": 1
        },
        "raw_corpus": {
            "full_text": """Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables systems to learn from data without being explicitly programmed.

There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning.""",
            "pages": [
                {
                    "page_num": 0,
                    "text": "Introduction to Machine Learning\n\nMachine learning is a subset of artificial intelligence that enables systems to learn from data without being explicitly programmed.\n\nThere are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning.",
                    "tables": []
                }
            ],
            "total_pages": 1
        }
    }
    
    # Test 2: Initialize Q&A generator
    total_tests += 1
    try:
        db = DatabaseOperations()
        config = QAGenerationConfig(
            max_questions_per_doc=5,
            validation_threshold=0.9,
            temperature_range=(0.0, 0.2),
            answer_temperature=0.0
        )
        
        generator = MarkerAwareQAGenerator(db, config)
        logger.info("Q&A generator initialized successfully")
        
    except Exception as e:
        all_validation_failures.append(f"Test 2 - Initialize generator: {e}")
    
    # Test 3: Generate Q&A pairs
    total_tests += 1
    try:
        logger.info("Generating Q&A pairs...")
        qa_batch = await generator.generate_from_marker_document(
            sample_marker_output,
            max_pairs=3
        )
        
        if not qa_batch.qa_pairs:
            all_validation_failures.append("Test 3 - Generate Q&A: No pairs generated")
        else:
            logger.info(f"Generated {len(qa_batch.qa_pairs)} Q&A pairs")
            
            # Verify each Q&A pair has required fields
            for i, qa_pair in enumerate(qa_batch.qa_pairs):
                if not qa_pair.question:
                    all_validation_failures.append(f"Test 3 - Q&A {i}: Missing question")
                if not qa_pair.thinking:
                    all_validation_failures.append(f"Test 3 - Q&A {i}: Missing thinking")
                if not qa_pair.answer:
                    all_validation_failures.append(f"Test 3 - Q&A {i}: Missing answer")
                
                # Log sample Q&A
                logger.info(f"\nQ&A Pair {i+1}:")
                logger.info(f"Question: {qa_pair.question}")
                logger.info(f"Thinking: {qa_pair.thinking[:100]}...")
                logger.info(f"Answer: {qa_pair.answer}")
                logger.info(f"Type: {qa_pair.question_type}")
                logger.info(f"Validated: {qa_pair.citation_found}")
                logger.info(f"Score: {qa_pair.validation_score}")
            
    except Exception as e:
        all_validation_failures.append(f"Test 3 - Generate Q&A pairs: {e}")
    
    # Test 4: Verify answer validation
    total_tests += 1
    try:
        valid_count = sum(1 for qa in qa_batch.qa_pairs if qa.citation_found)
        invalid_count = len(qa_batch.qa_pairs) - valid_count
        
        logger.info(f"\nValidation Results:")
        logger.info(f"Valid answers: {valid_count}")
        logger.info(f"Invalid answers: {invalid_count}")
        
        if valid_count == 0:
            all_validation_failures.append("Test 4 - Validation: No answers validated against corpus")
            
    except Exception as e:
        all_validation_failures.append(f"Test 4 - Verify validation: {e}")
    
    # Test 5: Export to UnSloth format
    total_tests += 1
    try:
        exporter = QAExporter()
        unsloth_data = exporter.export_to_unsloth(qa_batch.qa_pairs)
        
        if not unsloth_data:
            all_validation_failures.append("Test 5 - Export: No data exported")
        else:
            # Verify UnSloth format
            for i, item in enumerate(unsloth_data):
                if "messages" not in item:
                    all_validation_failures.append(f"Test 5 - Export item {i}: Missing messages")
                elif len(item["messages"]) != 2:
                    all_validation_failures.append(f"Test 5 - Export item {i}: Expected 2 messages, got {len(item['messages'])}")
                else:
                    user_msg = item["messages"][0]
                    assistant_msg = item["messages"][1]
                    
                    if user_msg.get("role") != "user":
                        all_validation_failures.append(f"Test 5 - Export item {i}: First message should be 'user'")
                    if assistant_msg.get("role") != "assistant":
                        all_validation_failures.append(f"Test 5 - Export item {i}: Second message should be 'assistant'")
                    if "thinking" not in assistant_msg:
                        all_validation_failures.append(f"Test 5 - Export item {i}: Missing thinking in assistant message")
                    
            logger.info(f"\nExported {len(unsloth_data)} Q&A pairs to UnSloth format")
            
            # Save sample output
            output_path = Path("./test_qa_output.json")
            with open(output_path, 'w') as f:
                json.dump(unsloth_data, f, indent=2)
            logger.info(f"Sample output saved to: {output_path}")
            
    except Exception as e:
        all_validation_failures.append(f"Test 5 - Export to UnSloth: {e}")
    
    # Test 6: Verify question types
    total_tests += 1
    try:
        question_types = {}
        for qa in qa_batch.qa_pairs:
            q_type = qa.question_type
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        logger.info(f"\nQuestion Type Distribution:")
        for q_type, count in question_types.items():
            logger.info(f"{q_type}: {count}")
            
        if len(question_types) == 0:
            all_validation_failures.append("Test 6 - Question types: No types found")
            
    except Exception as e:
        all_validation_failures.append(f"Test 6 - Question types: {e}")
    
    # Test 7: Check metadata
    total_tests += 1
    try:
        metadata = qa_batch.metadata
        logger.info(f"\nBatch Metadata:")
        logger.info(f"Source: {metadata.get('source')}")
        logger.info(f"Total generated: {metadata.get('total_generated')}")
        logger.info(f"Valid count: {metadata.get('valid_count')}")
        logger.info(f"Validation rate: {metadata.get('validation_rate', 0):.1%}")
        
        if metadata.get('corpus_validation') != True:
            all_validation_failures.append("Test 7 - Metadata: corpus_validation not set")
            
    except Exception as e:
        all_validation_failures.append(f"Test 7 - Check metadata: {e}")
    
    # Final results
    if all_validation_failures:
        logger.error(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            logger.error(f"  - {failure}")
        return False
    else:
        logger.info(f"✅ VALIDATION PASSED - All {total_tests} tests successful")
        logger.info("Q&A generation is working correctly with question/thinking/answer format")
        return True


async def verify_with_real_marker_file(marker_file_path: Path):
    """Verify Q&A generation with a real Marker output file."""
    logger.info(f"Verifying with real Marker file: {marker_file_path}")
    
    try:
        # Load Marker output
        with open(marker_file_path, 'r') as f:
            marker_output = json.load(f)
        
        # Check if it has raw corpus
        if "raw_corpus" not in marker_output:
            logger.warning("Marker output doesn't include raw_corpus")
        
        # Generate Q&A
        db = DatabaseOperations()
        config = QAGenerationConfig(
            max_questions_per_doc=10,
            validation_threshold=0.97
        )
        
        generator = MarkerAwareQAGenerator(db, config)
        qa_batch = await generator.generate_from_marker_document(marker_output)
        
        # Export
        exporter = QAExporter()
        unsloth_data = exporter.export_to_unsloth(qa_batch.qa_pairs)
        
        # Save output
        output_path = marker_file_path.parent / f"{marker_file_path.stem}_qa_verified.json"
        with open(output_path, 'w') as f:
            json.dump(unsloth_data, f, indent=2)
        
        logger.info(f"Generated {len(qa_batch.qa_pairs)} Q&A pairs")
        logger.info(f"Validation rate: {qa_batch.metadata.get('validation_rate', 0):.1%}")
        logger.info(f"Output saved to: {output_path}")
        
        # Show sample Q&A
        if qa_batch.qa_pairs:
            qa = qa_batch.qa_pairs[0]
            logger.info(f"\nSample Q&A:")
            logger.info(f"Q: {qa.question}")
            logger.info(f"T: {qa.thinking[:150]}...")
            logger.info(f"A: {qa.answer}")
        
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    # Run verification
    try:
        # Basic verification
        result = asyncio.run(verify_qa_generation())
        
        # If a Marker file is provided as argument, test with that
        if len(sys.argv) > 1:
            marker_file = Path(sys.argv[1])
            if marker_file.exists():
                logger.info("\n" + "="*50)
                result = asyncio.run(verify_with_real_marker_file(marker_file))
        
        sys.exit(0 if result else 1)
        
    except Exception as e:
        logger.error(f"Verification failed with error: {e}")
        sys.exit(1)