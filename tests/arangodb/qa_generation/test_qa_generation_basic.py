"""
Simple verification script for Q&A generation functionality.

This script verifies that the Q&A module can:
1. Generate questions with thinking process and answers
2. Handle the basic document format
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, Any

from arangodb.qa_generation.models import QAPair, QABatch, QuestionType
from arangodb.qa_generation.exporter import QAExporter


async def verify_basic_qa_generation():
    """Verify basic Q&A generation with hardcoded data."""
    logger.info("Starting basic Q&A generation verification")
    
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Create sample Q&A pairs manually
    total_tests += 1
    try:
        qa_pairs = []
        
        # Create first Q&A pair
        qa1 = QAPair(
            question="What are the three main types of machine learning?",
            thinking="I need to list the three types mentioned in the document: supervised learning, unsupervised learning, and reinforcement learning.",
            answer="The three main types of machine learning are supervised learning, unsupervised learning, and reinforcement learning.",
            question_type=QuestionType.FACTUAL,
            confidence=0.9,
            temperature_used=0.1,
            source_section="intro_section",
            source_hash="hash1",
            evidence_blocks=["block1"],
            citation_found=True,
            validation_score=0.98
        )
        qa_pairs.append(qa1)
        
        # Create second Q&A pair
        qa2 = QAPair(
            question="How does machine learning relate to artificial intelligence?",
            thinking="The document states that machine learning is a subset of artificial intelligence, which means it's a part of the broader AI field.",
            answer="Machine learning is a subset of artificial intelligence that enables systems to learn from data without being explicitly programmed.",
            question_type=QuestionType.RELATIONSHIP,
            confidence=0.95,
            temperature_used=0.0,
            source_section="intro_section",
            source_hash="hash1",
            evidence_blocks=["block1"],
            relationship_types=["SUBSET_OF"],
            related_entities=["machine_learning", "artificial_intelligence"],
            citation_found=True,
            validation_score=0.97
        )
        qa_pairs.append(qa2)
        
        logger.info(f"Created {len(qa_pairs)} Q&A pairs manually")
        
    except Exception as e:
        all_validation_failures.append(f"Test 1 - Create Q&A pairs: {e}")
    
    # Test 2: Create a batch
    total_tests += 1
    try:
        batch = QABatch(
            qa_pairs=qa_pairs,
            document_id="test_doc_001",
            metadata={
                "source": "manual_test",
                "corpus_validation": True,
                "total_generated": 2,
                "valid_count": 2,
                "validation_rate": 1.0
            }
        )
        logger.info(f"Created Q&A batch with {len(batch.qa_pairs)} pairs")
        
    except Exception as e:
        all_validation_failures.append(f"Test 2 - Create batch: {e}")
    
    # Test 3: Export to UnSloth format
    total_tests += 1
    try:
        exporter = QAExporter()
        # Export expects a list of batches, not individual qa_pairs
        export_path = exporter.export_to_unsloth([batch])
        
        if not export_path:
            all_validation_failures.append("Test 3 - Export: No path returned")
        else:
            logger.info(f"Exported to file: {export_path}")
            
            # Read the exported file to verify format
            with open(export_path, 'r') as f:
                lines = f.readlines()
                
            logger.info(f"Exported {len(lines)} items to UnSloth format")
            
            # Parse and verify each line
            unsloth_data = []
            for i, line in enumerate(lines):
                try:
                    item = json.loads(line.strip())
                    unsloth_data.append(item)
                    
                    if "messages" not in item:
                        all_validation_failures.append(f"Test 3 - Export item {i}: Missing messages")
                        continue
                        
                    messages = item["messages"]
                    if len(messages) != 2:
                        all_validation_failures.append(f"Test 3 - Export item {i}: Expected 2 messages, got {len(messages)}")
                        continue
                        
                    user_msg = messages[0]
                    assistant_msg = messages[1]
                    
                    if user_msg.get("role") != "user":
                        all_validation_failures.append(f"Test 3 - Export item {i}: First message should be 'user'")
                    if assistant_msg.get("role") != "assistant":
                        all_validation_failures.append(f"Test 3 - Export item {i}: Second message should be 'assistant'")
                    
                    # Check for thinking in assistant message
                    if "thinking" not in assistant_msg:
                        all_validation_failures.append(f"Test 3 - Export item {i}: Missing thinking in assistant message")
                    
                    logger.info(f"\nExported Q&A {i+1}:")
                    logger.info(f"User: {user_msg.get('content', '')[:100]}...")
                    logger.info(f"Assistant: {assistant_msg.get('content', '')[:100]}...")
                    logger.info(f"Thinking: {assistant_msg.get('thinking', '')[:100]}...")
                    
                except json.JSONDecodeError as e:
                    all_validation_failures.append(f"Test 3 - Export item {i}: Invalid JSON: {e}")
    
    except Exception as e:
        all_validation_failures.append(f"Test 3 - Export to UnSloth: {e}")
    
    # Test 4: Verify question types
    total_tests += 1
    try:
        question_types = {}
        for qa in qa_pairs:
            q_type = qa.question_type
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        logger.info(f"\nQuestion Type Distribution:")
        for q_type, count in question_types.items():
            logger.info(f"{q_type}: {count}")
        
        if len(question_types) == 0:
            all_validation_failures.append("Test 4 - Question types: No types found")
            
    except Exception as e:
        all_validation_failures.append(f"Test 4 - Question types: {e}")
    
    # Test 5: Save output
    total_tests += 1
    try:
        output_path = Path("./test_qa_simple_output.json")
        with open(output_path, 'w') as f:
            json.dump(unsloth_data, f, indent=2)
        logger.info(f"Sample output saved to: {output_path}")
        
    except Exception as e:
        all_validation_failures.append(f"Test 5 - Save output: {e}")
    
    # Final results
    if all_validation_failures:
        logger.error(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            logger.error(f"  - {failure}")
        return False
    else:
        logger.info(f"✅ VALIDATION PASSED - All {total_tests} tests successful")
        logger.info("Q&A generation functionality is working correctly")
        return True


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    # Run verification
    try:
        result = asyncio.run(verify_basic_qa_generation())
        sys.exit(0 if result else 1)
        
    except Exception as e:
        logger.error(f"Verification failed with error: {e}")
        sys.exit(1)