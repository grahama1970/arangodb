"""
Q&A Generation module that leverages ArangoDB's graph relationships.'
Module: generator.py

This module generates high-quality question-answer pairs from documents
using graph traversal and multi-hop reasoning.
"""

import asyncio
import json
import random
import time
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from loguru import logger
from tqdm.asyncio import tqdm

from litellm import acompletion
import litellm

from .models import (
    QAPair,
    QAGenerationConfig,
    QuestionType,
    ValidationResult,
    QABatch
)
from .validator import QAValidator
from .validation_models import QAValidationError, QARetryContext
from .reversal_generator import ReversalGenerator, enhance_with_reversals
from ..core.db_connection_wrapper import DatabaseOperations


# Enable structured output validation
litellm.enable_json_schema_validation = True


class QAGenerator:
    """
    Generates Q&A pairs from ArangoDB document graph.
    
    Uses LiteLLM with structured output for consistent formatting
    and RapidFuzz validation for factual accuracy.
    """
    
    def __init__(
        self, 
        db: DatabaseOperations,
        config: Optional[QAGenerationConfig] = None
    ):
        """
        Initialize the generator.
        
        Args:
            db: Database operations instance  
            config: Generation configuration
        """
        self.db = db
        self.config = config or QAGenerationConfig()
        self.validator = QAValidator(db, self.config.validation_threshold)
        self.reversal_generator = ReversalGenerator()
        self._semaphore = asyncio.Semaphore(self.config.semaphore_limit)
    
    async def generate_for_document(
        self, 
        document_id: str,
        max_pairs: Optional[int] = None
    ) -> QABatch:
        """
        Generate Q&A pairs for an entire document.
        
        Args:
            document_id: The document ID to process
            max_pairs: Maximum number of pairs to generate
            
        Returns:
            QABatch containing all generated pairs
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting Q&A generation for document: {document_id}")
        
        # Get document structure
        sections = await self._get_document_sections(document_id)
        relationships = await self._get_document_relationships(document_id)
        
        # Generate Q&A pairs by type
        qa_pairs = []
        
        # Calculate how many of each type to generate
        type_counts = self._calculate_type_distribution(max_pairs or 100)
        
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
            elif question_type == QuestionType.COMPARATIVE:
                pairs = await self._generate_comparative_qa(sections, relationships, count)
            elif question_type == QuestionType.REVERSAL:
                # Skip during main generation, reversals will be added at the end
                pairs = []
            else:
                pairs = []
            
            qa_pairs.extend(pairs)
        
        # Add reversal pairs after generating all other types
        if any(qt == QuestionType.REVERSAL for qt in self.config.question_type_weights.keys()):
            # Generate reversals from existing pairs
            reversal_ratio = self.config.question_type_weights.get(QuestionType.REVERSAL, 0.1)
            qa_pairs = enhance_with_reversals(qa_pairs, reversal_ratio)
            logger.info(f"Enhanced with {int(len(qa_pairs) * reversal_ratio)} reversal pairs")
        
        # Validate all pairs
        logger.info(f"Validating {len(qa_pairs)} Q&A pairs...")
        validation_results = await self.validator.validate_batch(qa_pairs, document_id)
        
        # Update pairs with validation results
        for qa_pair, result in zip(qa_pairs, validation_results):
            qa_pair.validation_score = result.score
            qa_pair.citation_found = result.valid
        
        # Create batch
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        batch = QABatch(
            qa_pairs=qa_pairs,
            document_id=document_id,
            generation_time=generation_time
        )
        
        logger.info(f"Generated {batch.total_pairs} pairs ({batch.valid_pairs} valid) in {generation_time:.2f}s")
        
        return batch
    
    async def _generate_factual_qa(self, sections: List[Dict], count: int) -> List[QAPair]:
        """Generate factual Q&A pairs from sections."""
        qa_pairs = []
        
        # Select random sections for factual questions
        selected_sections = random.sample(sections, min(count, len(sections)))
        
        # Process in batches
        batch_size = self.config.batch_size
        for i in range(0, len(selected_sections), batch_size):
            batch = selected_sections[i:i + batch_size]
            tasks = [self._generate_single_factual_qa(section) for section in batch]
            results = await asyncio.gather(*tasks)
            qa_pairs.extend([r for r in results if r])
        
        return qa_pairs[:count]  # Limit to requested count
    
    async def _generate_single_factual_qa(self, section: Dict) -> Optional[QAPair]:
        """Generate a single factual Q&A pair with retry logic."""
        async with self._semaphore:
            # Create initial prompt
            initial_prompt = f"""
            Based on the following section, generate a factual question and answer.
            
            Section: {section['title']}
            Content: {section['content'][:1000]}
            
            Requirements:
            1. The question should ask about specific facts in the content
            2. The answer must be directly stated in the content
            3. Include your reasoning process
            4. Be precise and factual
            
            Generate the Q&A pair:
            """
            
            # Define metadata updater
            def update_metadata(qa_pair):
                qa_pair.source_section = section['hash']
                qa_pair.source_hash = section['content_hash']
                qa_pair.evidence_blocks = section['content_blocks']
            
            return await self._generate_with_retry(
                initial_prompt=initial_prompt,
                system_prompt="You are an expert at creating factual Q&A pairs from technical documents.",
                question_type=QuestionType.FACTUAL,
                content=section['content'],
                metadata_updater=update_metadata
            )
    
    async def _generate_relationship_qa(self, relationships: List[Dict], count: int) -> List[QAPair]:
        """Generate relationship-based Q&A pairs."""
        qa_pairs = []
        
        # Filter for meaningful relationships
        meaningful_rels = [
            r for r in relationships 
            if r['relationship_type'] in ['REFERENCES', 'ELABORATES', 'COMPARES']
        ]
        
        # Select relationships
        selected_rels = random.sample(meaningful_rels, min(count, len(meaningful_rels)))
        
        # Generate Q&A for each relationship
        for rel in selected_rels:
            qa = await self._generate_single_relationship_qa(rel)
            if qa:
                qa_pairs.append(qa)
        
        return qa_pairs[:count]
    
    async def _generate_with_retry(
        self,
        initial_prompt: str,
        system_prompt: str,
        question_type: QuestionType,
        content: str,
        metadata_updater: callable
    ) -> Optional[QAPair]:
        """Helper method for generating Q&A with retry logic."""
        # Select temperature from range
        temperature = random.choice(self.config.question_temperature_range)
        
        # Initialize retry context
        retry_context = QARetryContext(
            attempt_number=0,
            previous_errors=[],
            original_prompt=initial_prompt,
            section_content=content,
            temperature=temperature
        )
        
        # Retry loop
        for attempt in range(self.config.max_retries):
            try:
                retry_context.attempt_number = attempt + 1
                
                # Build prompt and messages
                if attempt == 0:
                    prompt = initial_prompt
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                else:
                    prompt = retry_context.build_retry_prompt()
                    messages = [
                        {"role": "system", "content": f"{system_prompt} Fix the previous errors."},
                        {"role": "user", "content": prompt}
                    ]
                
                # Generate with structured output
                response = await acompletion(
                    model=self.config.model,
                    messages=messages,
                    response_format=QAPair,
                    temperature=self.config.answer_temperature if attempt > 0 else temperature,
                    max_tokens=self.config.max_tokens
                )
                
                # Parse response - when using response_format, the parsed object is in the message
                if hasattr(response.choices[0].message, 'parsed'):
                    qa_pair = response.choices[0].message.parsed
                else:
                    # Fallback to content parsing
                    response_content = response.choices[0].message.content
                    if isinstance(response_content, str):
                        import json
                        qa_pair = QAPair(**json.loads(response_content))
                    else:
                        qa_pair = response_content
                
                # Validate response
                validation_error = self._validate_qa_response(qa_pair, content)
                if validation_error:
                    retry_context.previous_errors.append(validation_error)
                    
                    if attempt < self.config.max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {validation_error.error_message}")
                        await asyncio.sleep(self.config.retry_delay)
                        continue
                    else:
                        logger.error(f"All {self.config.max_retries} attempts failed for {question_type} Q&A")
                        return None
                
                # Update metadata
                qa_pair.question_type = question_type
                qa_pair.temperature_used = temperature
                metadata_updater(qa_pair)
                
                return qa_pair
                
            except Exception as e:
                error = QAValidationError(
                    error_type="GENERATION_ERROR",
                    error_message=str(e),
                    fix_suggestion="Ensure response follows the exact Q&A format requested"
                )
                retry_context.previous_errors.append(error)
                
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} exception: {e}")
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                else:
                    logger.error(f"All attempts failed with exception: {e}")
                    return None
        
        return None
    
    async def _generate_single_relationship_qa(self, relationship: Dict) -> Optional[QAPair]:
        """Generate Q&A for a single relationship with retry logic."""
        async with self._semaphore:
            # Prepare content for validation
            content = f"{relationship['from_text']} {relationship['to_text']}"
            
            # Create initial prompt
            initial_prompt = f"""
            Generate a question about the relationship between two elements.
            
            Element 1: {relationship['from_text'][:500]}
            Element 2: {relationship['to_text'][:500]}
            Relationship: {relationship['relationship_type']}
            
            Create a question that explores how these elements are related,
            and provide a comprehensive answer based on the content.
            """
            
            # Define metadata updater
            def update_metadata(qa_pair):
                qa_pair.relationship_types = [relationship['relationship_type']]
                qa_pair.related_entities = [relationship['from_id'], relationship['to_id']]
                qa_pair.evidence_blocks = [relationship['from_id'], relationship['to_id']]
            
            return await self._generate_with_retry(
                initial_prompt=initial_prompt,
                system_prompt="You are an expert at understanding document relationships.",
                question_type=QuestionType.RELATIONSHIP,
                content=content,
                metadata_updater=update_metadata
            )
    
    async def _generate_multihop_qa(self, relationships: List[Dict], count: int) -> List[QAPair]:
        """Generate multi-hop reasoning Q&A pairs."""
        qa_pairs = []
        
        # Find multi-hop paths in the graph
        paths = await self._find_multihop_paths(relationships, count)
        
        for path in paths:
            qa = await self._generate_single_multihop_qa(path)
            if qa:
                qa_pairs.append(qa)
        
        return qa_pairs[:count]
    
    async def _find_multihop_paths(self, relationships: List[Dict], count: int) -> List[List[Dict]]:
        """Find paths through the relationship graph for multi-hop reasoning."""
        # Build adjacency list
        graph = {}
        for rel in relationships:
            from_id = rel['from_id']
            to_id = rel['to_id']
            
            if from_id not in graph:
                graph[from_id] = []
            graph[from_id].append(rel)
        
        # Find paths of length 2-3
        paths = []
        nodes = list(graph.keys())
        
        for _ in range(count * 2):  # Generate more than needed
            if not nodes:
                break
                
            start_node = random.choice(nodes)
            path = self._random_walk(graph, start_node, max_length=3)
            
            if len(path) >= 2:  # At least 2 hops
                paths.append(path)
        
        # Take unique paths
        unique_paths = []
        seen = set()
        
        for path in paths:
            path_key = tuple(rel['_id'] for rel in path)
            if path_key not in seen:
                seen.add(path_key)
                unique_paths.append(path)
        
        return unique_paths[:count]
    
    def _random_walk(self, graph: Dict, start: str, max_length: int = 3) -> List[Dict]:
        """Perform random walk through graph."""
        path = []
        current = start
        visited = {start}
        
        for _ in range(max_length):
            if current not in graph or not graph[current]:
                break
            
            # Filter out already visited nodes
            candidates = [
                rel for rel in graph[current] 
                if rel['to_id'] not in visited
            ]
            
            if not candidates:
                break
            
            # Choose random edge
            edge = random.choice(candidates)
            path.append(edge)
            
            current = edge['to_id']
            visited.add(current)
        
        return path
    
    async def _generate_single_multihop_qa(self, path: List[Dict]) -> Optional[QAPair]:
        """Generate Q&A requiring multi-hop reasoning with retry logic."""
        async with self._semaphore:
            # Build path description
            path_desc = []
            content_parts = []
            
            for i, edge in enumerate(path):
                path_desc.append(f"Step {i+1}: {edge['from_text'][:200]} → {edge['to_text'][:200]}")
                content_parts.extend([edge['from_text'], edge['to_text']])
            
            content = " ".join(content_parts)
            
            # Create initial prompt
            initial_prompt = f"""
            Generate a question that requires following this reasoning path:
            
            {chr(10).join(path_desc)}
            
            Create a question that requires understanding all steps,
            and provide a comprehensive answer that explains the connections.
            """
            
            # Define metadata updater
            def update_metadata(qa_pair):
                qa_pair.relationship_types = [edge['relationship_type'] for edge in path]
                qa_pair.related_entities = [edge['from_id'] for edge in path] + [path[-1]['to_id']]
                qa_pair.evidence_blocks = qa_pair.related_entities
            
            return await self._generate_with_retry(
                initial_prompt=initial_prompt,
                system_prompt="You are an expert at creating multi-hop reasoning questions.",
                question_type=QuestionType.MULTI_HOP,
                content=content,
                metadata_updater=update_metadata
            )
    
    # Reversal generation is now handled by ReversalGenerator class
    # See reversal_generator.py for implementation
    
    async def _generate_hierarchical_qa(self, sections: List[Dict], count: int) -> List[QAPair]:
        """Generate questions about document structure."""
        qa_pairs = []
        
        # Group sections by level
        sections_by_level = {}
        for section in sections:
            level = section.get('level', 1)
            if level not in sections_by_level:
                sections_by_level[level] = []
            sections_by_level[level].append(section)
        
        # Generate questions about hierarchy
        for _ in range(count):
            qa = await self._generate_single_hierarchical_qa(sections_by_level)
            if qa:
                qa_pairs.append(qa)
        
        return qa_pairs[:count]
    
    async def _generate_single_hierarchical_qa(self, sections_by_level: Dict) -> Optional[QAPair]:
        """Generate Q&A about document hierarchy."""
        async with self._semaphore:
            try:
                temperature = random.choice(self.config.question_temperature_range)
                
                # Build hierarchy description
                hierarchy_desc = []
                for level, sections in sorted(sections_by_level.items()):
                    level_titles = [s['title'] for s in sections[:5]]  # Limit to 5
                    hierarchy_desc.append(f"Level {level}: {', '.join(level_titles)}")
                
                prompt = f"""
                Generate a question about the document structure:
                
                {chr(10).join(hierarchy_desc)}
                
                Create a question about the organization, hierarchy, or relationships
                between sections, and provide an answer based on the structure.
                """
                
                response = await acompletion(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at understanding document organization."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=QAPair,
                    temperature=temperature,
                    max_tokens=self.config.max_tokens
                )
                
                qa_pair = response.choices[0].message.content
                
                # Update metadata
                qa_pair.question_type = QuestionType.HIERARCHICAL
                qa_pair.temperature_used = temperature
                
                return qa_pair
                
            except Exception as e:
                logger.error(f"Error generating hierarchical Q&A: {e}")
                return None
    
    async def _generate_comparative_qa(self, sections: List[Dict], relationships: List[Dict], count: int) -> List[QAPair]:
        """Generate comparative Q&A pairs."""
        qa_pairs = []
        
        # Find comparable elements
        comparable_pairs = []
        
        # Find similar sections
        for i, section1 in enumerate(sections):
            for section2 in sections[i+1:]:
                if section1.get('level') == section2.get('level'):
                    comparable_pairs.append((section1, section2))
        
        # Sample and generate
        selected_pairs = random.sample(comparable_pairs, min(count, len(comparable_pairs)))
        
        for pair in selected_pairs:
            qa = await self._generate_single_comparative_qa(pair[0], pair[1])
            if qa:
                qa_pairs.append(qa)
        
        return qa_pairs[:count]
    
    async def _generate_single_comparative_qa(self, item1: Dict, item2: Dict) -> Optional[QAPair]:
        """Generate comparative Q&A between two items."""
        async with self._semaphore:
            try:
                temperature = random.choice(self.config.question_temperature_range)
                
                prompt = f"""
                Generate a comparison question between these two elements:
                
                Element 1: {item1['title']}
                Content 1: {item1.get('content', '')[:500]}
                
                Element 2: {item2['title']}
                Content 2: {item2.get('content', '')[:500]}
                
                Create a question that compares or contrasts these elements,
                and provide an answer that explains the similarities or differences.
                """
                
                response = await acompletion(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at comparative analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=QAPair,
                    temperature=temperature,
                    max_tokens=self.config.max_tokens
                )
                
                qa_pair = response.choices[0].message.content
                
                # Update metadata
                qa_pair.question_type = QuestionType.COMPARATIVE
                qa_pair.temperature_used = temperature
                qa_pair.related_entities = [item1.get('_id'), item2.get('_id')]
                qa_pair.evidence_blocks = qa_pair.related_entities
                
                return qa_pair
                
            except Exception as e:
                logger.error(f"Error generating comparative Q&A: {e}")
                return None
    
    def _calculate_type_distribution(self, total_count: int) -> Dict[QuestionType, int]:
        """Calculate how many questions of each type to generate."""
        distribution = {}
        
        # Calculate counts based on weights
        remaining = total_count
        weights = self.config.question_type_weights.copy()
        
        for q_type, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            count = int(total_count * weight)
            distribution[q_type] = min(count, remaining)
            remaining -= distribution[q_type]
        
        # Distribute any remaining
        if remaining > 0:
            for q_type in distribution:
                if remaining == 0:
                    break
                distribution[q_type] += 1
                remaining -= 1
        
        return distribution
    
    def _validate_qa_response(self, qa_pair: QAPair, content: str) -> Optional[QAValidationError]:
        """
        Validate that Q&A response has required fields and answer is in content.
        
        Args:
            qa_pair: The generated Q&A pair
            content: The source content to validate against
            
        Returns:
            QAValidationError if validation fails, None if valid
        """
        errors = QAValidationError(
            error_type="VALIDATION_ERROR",
            error_message="",
            fix_suggestion=""
        )
        
        # Check required fields
        missing_fields = []
        if not qa_pair.question:
            missing_fields.append("question")
        if not qa_pair.thinking:
            missing_fields.append("thinking")
        if not qa_pair.answer:
            missing_fields.append("answer")
        
        if missing_fields:
            errors.missing_fields = missing_fields
            errors.error_message = f"Missing required fields: {', '.join(missing_fields)}"
            errors.fix_suggestion = "Ensure all required fields (question, thinking, answer) are provided"
            return errors
        
        # Check answer length
        invalid_fields = {}
        if len(qa_pair.answer) < self.config.min_answer_length:
            invalid_fields["answer"] = f"Too short (min {self.config.min_answer_length} chars)"
        elif len(qa_pair.answer) > self.config.max_answer_length:
            invalid_fields["answer"] = f"Too long (max {self.config.max_answer_length} chars)"
        
        # Check if answer is in content (quick check, full validation comes later)
        answer_segments = qa_pair.answer.split('. ')
        found_in_content = False
        
        for segment in answer_segments:
            if len(segment) > 20:  # Only check meaningful segments
                # Use simple string matching for quick validation
                if segment.lower() in content.lower():
                    found_in_content = True
                    break
        
        if not found_in_content:
            invalid_fields["answer"] = "Answer not found in provided content"
        
        if invalid_fields:
            errors.invalid_fields = invalid_fields
            errors.error_message = "Invalid field values detected"
            errors.fix_suggestion = "Ensure answer is extracted directly from the provided content and meets length requirements"
            return errors
        
        return None
    
    async def _get_document_sections(self, document_id: str) -> List[Dict]:
        """Get all sections from document."""
        query = """
        FOR obj IN document_objects
            FILTER obj.document_id == @doc_id
            FILTER obj._type == "section"
            
            LET content_blocks = (
                FOR content IN document_objects
                    FILTER content.document_id == @doc_id
                    FILTER content.section_hash == obj.section_hash
                    FILTER content._type IN ["text", "table", "code"]
                    RETURN content
            )
            
            RETURN {
                _id: obj._id,
                title: obj.text,
                level: obj.section_level,
                hash: obj.section_hash,
                content: CONCAT_SEPARATOR(" ", content_blocks[*].text),
                content_blocks: content_blocks[*]._key,
                content_hash: MD5(CONCAT_SEPARATOR(" ", content_blocks[*].text))
            }
        """
        
        cursor = self.db.aql.execute(query, bind_vars={"doc_id": document_id})
        return list(cursor)
    
    async def _get_document_relationships(self, document_id: str) -> List[Dict]:
        """Get all relationships from document."""
        query = """
        FOR edge IN content_relationships
            LET from_obj = DOCUMENT(edge._from)
            LET to_obj = DOCUMENT(edge._to)
            
            FILTER from_obj.document_id == @doc_id
            FILTER edge.confidence >= 0.8
            
            RETURN {
                _id: edge._key,
                relationship_type: edge.relationship_type,
                confidence: edge.confidence,
                from_id: from_obj._key,
                from_text: from_obj.text,
                to_id: to_obj._key,
                to_text: to_obj.text
            }
        """
        
        cursor = self.db.aql.execute(query, bind_vars={"doc_id": document_id})
        return list(cursor)