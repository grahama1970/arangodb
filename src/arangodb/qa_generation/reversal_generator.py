"""
Enhanced reversal Q&A generation to mitigate the reversal curse.
Module: reversal_generator.py
Description: Implementation of reversal generator functionality

The reversal curse is when LLMs can answer "A is B" but fail at "B is A".
This module provides sophisticated reversal generation strategies.
"""

import re
from typing import Optional, List, Dict, Any
from loguru import logger

from .models import QAPair, QuestionType


class ReversalGenerator:
    """
    Generates reversal Q&A pairs to combat the reversal curse.
    
    Implements multiple strategies:
    1. Simple entity swapping
    2. Relationship inversion
    3. Property-to-entity reversal
    4. Cause-effect reversal
    """
    
    def __init__(self):
        self.reversal_patterns = {
            # Pattern: (question_pattern, answer_pattern, reversal_template)
            "definition": (
                r"(?:What is|Define|Explain)\s+(.+)\?",
                r"(.+)",
                "What term or concept is defined as: {answer}?"
            ),
            "property": (
                r"What (?:is the|are the)\s+(.+)\s+of\s+(.+)\?",
                r"(.+)",
                "What has {property} as its {answer}?"
            ),
            "relationship": (
                r"(?:What|Which)\s+(.+)\s+(?:is|are)\s+(.+)\s+(?:of|to|for)\s+(.+)\?",
                r"(.+)",
                "{answer} is the {relation} of what?"
            ),
            "location": (
                r"Where (?:is|are)\s+(.+)\s+(?:located|found)\?",
                r"(.+)",
                "What is located in/at {answer}?"
            ),
            "comparison": (
                r"How (?:does|do)\s+(.+)\s+compare (?:to|with)\s+(.+)\?",
                r"(.+)",
                "What is being compared to {entity2} in the following way: {answer}?"
            )
        }
    
    def generate_reversal(self, original_qa: QAPair) -> Optional[QAPair]:
        """
        Generate a reversal Q&A pair from an original pair.
        
        Args:
            original_qa: The original Q&A pair to reverse
            
        Returns:
            A new QAPair with reversed question-answer relationship
        """
        # Skip if already a reversal
        if original_qa.question_type == QuestionType.REVERSAL:
            return None
        
        # Try different reversal strategies
        reversal = None
        
        # Strategy 1: Pattern-based reversal
        reversal = self._pattern_based_reversal(original_qa)
        
        # Strategy 2: Entity extraction and swapping
        if not reversal:
            reversal = self._entity_swap_reversal(original_qa)
        
        # Strategy 3: Relationship inversion
        if not reversal:
            reversal = self._relationship_inversion(original_qa)
        
        # Strategy 4: Generic reversal
        if not reversal:
            reversal = self._generic_reversal(original_qa)
        
        return reversal
    
    def _pattern_based_reversal(self, original_qa: QAPair) -> Optional[QAPair]:
        """Use pattern matching for common Q&A structures."""
        question = original_qa.question
        answer = original_qa.answer
        
        for pattern_name, (q_pattern, a_pattern, reversal_template) in self.reversal_patterns.items():
            q_match = re.match(q_pattern, question, re.IGNORECASE)
            if q_match:
                # Extract components
                components = q_match.groups()
                
                # Build reversal
                if pattern_name == "definition":
                    reversal_q = reversal_template.format(answer=answer)
                    reversal_a = components[0] if components else question.split()[-1].strip("?")
                elif pattern_name == "property":
                    property_name = components[0]
                    entity = components[1]
                    reversal_q = f"What has {answer} as its {property_name}?"
                    reversal_a = entity
                elif pattern_name == "location":
                    entity = components[0]
                    reversal_q = reversal_template.format(answer=answer)
                    reversal_a = entity
                else:
                    continue
                
                return self._create_reversal_pair(
                    original_qa,
                    reversal_q,
                    reversal_a,
                    f"Pattern-based reversal using {pattern_name} pattern"
                )
        
        return None
    
    def _entity_swap_reversal(self, original_qa: QAPair) -> Optional[QAPair]:
        """Swap entities between question and answer."""
        # Extract entities using NER or simple heuristics
        question_entities = self._extract_entities(original_qa.question)
        answer_entities = self._extract_entities(original_qa.answer)
        
        if question_entities and answer_entities:
            # Swap the most prominent entities
            q_entity = question_entities[0]
            a_entity = answer_entities[0]
            
            # Create reversal by swapping
            reversal_q = original_qa.question.replace(q_entity, f"[{a_entity}]")
            reversal_q = reversal_q.replace(f"[{a_entity}]", a_entity)
            
            reversal_a = original_qa.answer.replace(a_entity, q_entity)
            
            return self._create_reversal_pair(
                original_qa,
                reversal_q,
                reversal_a,
                "Entity-swapping reversal"
            )
        
        return None
    
    def _relationship_inversion(self, original_qa: QAPair) -> Optional[QAPair]:
        """Invert relationship-based questions."""
        # Check if it's a relationship question
        if original_qa.question_type != QuestionType.RELATIONSHIP:
            return None
        
        # Common relationship inversions
        inversions = {
            "causes": "is caused by",
            "is caused by": "causes",
            "leads to": "results from",
            "results from": "leads to",
            "contains": "is contained in",
            "is contained in": "contains",
            "precedes": "follows",
            "follows": "precedes"
        }
        
        for original, inverted in inversions.items():
            if original in original_qa.question.lower():
                reversal_q = original_qa.question.lower().replace(original, inverted)
                reversal_q = reversal_q[0].upper() + reversal_q[1:]
                
                # The answer often becomes part of the question
                return self._create_reversal_pair(
                    original_qa,
                    reversal_q,
                    original_qa.answer,
                    "Relationship inversion reversal"
                )
        
        return None
    
    def _generic_reversal(self, original_qa: QAPair) -> Optional[QAPair]:
        """Fallback generic reversal strategy."""
        # Create a generic reversal
        reversal_q = f"What concept or entity is described by the following: {original_qa.answer}?"
        
        # Extract the main concept from the question
        question_words = original_qa.question.strip("?").split()
        if "What" in question_words:
            idx = question_words.index("What")
            if idx + 1 < len(question_words):
                reversal_a = " ".join(question_words[idx+1:idx+3])
            else:
                reversal_a = question_words[-1]
        else:
            # Take the last significant noun phrase
            reversal_a = " ".join(question_words[-3:])
        
        return self._create_reversal_pair(
            original_qa,
            reversal_q,
            reversal_a,
            "Generic reversal fallback"
        )
    
    def _extract_entities(self, text: str) -> List[str]:
        """Simple entity extraction using capitalization and patterns."""
        entities = []
        
        # Find capitalized words (proper nouns)
        words = text.split()
        for word in words:
            if word[0].isupper() and word not in ["What", "Where", "When", "How", "Why", "The"]:
                entities.append(word.strip(".,!?"))
        
        # Find quoted terms
        quoted = re.findall(r'"([^"]+)"', text)
        entities.extend(quoted)
        
        # Find terms after "is/are"
        is_pattern = re.findall(r'(?:is|are)\s+(?:a|an|the)?\s*([^.?!,]+)', text)
        if is_pattern:
            entities.extend([p.strip() for p in is_pattern])
        
        return list(set(entities))  # Remove duplicates
    
    def _create_reversal_pair(
        self,
        original_qa: QAPair,
        reversal_question: str,
        reversal_answer: str,
        thinking: str
    ) -> QAPair:
        """Create a new QAPair for the reversal."""
        reversal_qa = QAPair(
            question=reversal_question,
            answer=reversal_answer,
            thinking=f"{thinking}. Original: '{original_qa.question}' → '{original_qa.answer}'",
            question_type=QuestionType.REVERSAL,
            confidence=original_qa.confidence * 0.9,  # Slightly lower confidence
            temperature_used=original_qa.temperature_used,
            source_section=original_qa.source_section,
            source_hash=original_qa.source_hash,
            evidence_blocks=original_qa.evidence_blocks,
            relationship_types=original_qa.relationship_types,
            related_entities=original_qa.related_entities,
            validation_score=None,  # Will be validated separately
            citation_found=False,
            difficulty=original_qa.difficulty
        )
        
        # Add metadata to track the reversal
        reversal_qa.reversal_of = original_qa._key if hasattr(original_qa, '_key') else None
        
        return reversal_qa
    
    def generate_reversal_batch(self, qa_pairs: List[QAPair]) -> List[QAPair]:
        """Generate reversals for a batch of Q&A pairs."""
        reversals = []
        
        for qa in qa_pairs:
            if qa.question_type == QuestionType.REVERSAL:
                continue
                
            reversal = self.generate_reversal(qa)
            if reversal:
                reversals.append(reversal)
                logger.debug(f"Created reversal: {reversal.question[:50]}...")
            else:
                logger.warning(f"Failed to create reversal for: {qa.question[:50]}...")
        
        logger.info(f"Generated {len(reversals)} reversal pairs from {len(qa_pairs)} originals")
        return reversals


def enhance_with_reversals(qa_batch: List[QAPair], reversal_ratio: float = 0.2) -> List[QAPair]:
    """
    Enhance a Q&A batch with reversal pairs.
    
    Args:
        qa_batch: Original Q&A pairs
        reversal_ratio: Percentage of pairs to generate reversals for
        
    Returns:
        Combined list of original and reversal pairs
    """
    generator = ReversalGenerator()
    
    # Select pairs for reversal
    import random
    num_reversals = int(len(qa_batch) * reversal_ratio)
    pairs_to_reverse = random.sample(qa_batch, min(num_reversals, len(qa_batch)))
    
    # Generate reversals
    reversals = generator.generate_reversal_batch(pairs_to_reverse)
    
    # Combine and return
    return qa_batch + reversals