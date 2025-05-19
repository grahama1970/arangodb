"""
Q&A Edge Generator Module

Creates edge documents from Q&A pairs for integration with the ArangoDB graph.
Uses SpaCy for entity extraction and integrates with existing relationship patterns.
"""

import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from loguru import logger
import spacy
from rapidfuzz import fuzz

from .models import QAPair, QABatch
from ..core.db_connection_wrapper import DatabaseOperations
from ..core.constants import CONFIG
from ..core.field_constants import (
    FROM_FIELD, TO_FIELD, TYPE_FIELD, CONTENT_FIELD,
    CONFIDENCE_FIELD, TIMESTAMP_FIELD, EMBEDDING_FIELD
)
from ..core.utils.embedding_utils import get_embedding
from ..core.graph.entity_resolution import find_exact_entity_matches, resolve_entity
from ..core.graph.relationship_extraction import EntityExtractor
from ..core.search.bm25_search import bm25_search
from ..core.temporal_operations import create_temporal_entity


# Define the new relationship type constant
RELATIONSHIP_TYPE_QA_DERIVED = "qa_derived"


class QAEdgeGenerator:
    """
    Generates edge documents from Q&A pairs for graph integration.
    
    Combines SpaCy NER, existing pattern extraction, and BM25 keyword search
    to identify entities and create meaningful graph edges.
    """
    
    def __init__(self, db: DatabaseOperations):
        """
        Initialize the Q&A edge generator.
        
        Args:
            db: Database operations wrapper
        """
        self.db = db
        
        # Initialize NLP models and extractors
        self.spacy_available = False
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.spacy_available = True
        except OSError:
            logger.warning("SpaCy model not found. NER extraction with SpaCy will be disabled.")
            self.nlp = None
        except ImportError:
            logger.warning("SpaCy not installed. NER extraction with SpaCy will be disabled.")
            self.nlp = None
        
        # Initialize existing extractors
        self.pattern_extractor = EntityExtractor()
        
        # Edge collection name
        try:
            self.edge_collection = CONFIG["graph"]["edge_collections"][0]  # Use primary edge collection
        except (KeyError, IndexError):
            self.edge_collection = "test_relationships"  # Fallback for testing
            
        self.entity_collection = "entities"  # Default entity collection
        
    def extract_entities(self, qa_pair: QAPair) -> List[Dict[str, Any]]:
        """
        Extract entities from Q&A pair using multiple methods.
        
        Args:
            qa_pair: The Q&A pair to extract entities from
            
        Returns:
            List of entity dictionaries with name, type, and confidence
        """
        entities = []
        
        # 1. SpaCy NER extraction
        spacy_entities = self._extract_with_spacy(qa_pair)
        entities.extend(spacy_entities)
        
        # 2. Pattern-based extraction (existing method)
        pattern_entities = self._extract_with_patterns(qa_pair)
        entities.extend(pattern_entities)
        
        # 3. BM25 keyword extraction
        bm25_entities = self._extract_with_bm25(qa_pair)
        entities.extend(bm25_entities)
        
        # Deduplicate and resolve entities
        resolved_entities = self._resolve_entities(entities)
        
        return resolved_entities
    
    def _extract_with_spacy(self, qa_pair: QAPair) -> List[Dict[str, Any]]:
        """Extract entities using SpaCy NER."""
        entities = []
        
        # If SpaCy is not available, return empty list
        if not self.spacy_available or self.nlp is None:
            logger.debug("SpaCy not available for entity extraction")
            return entities
        
        # Process question and answer
        texts = [qa_pair.question, qa_pair.answer]
        if qa_pair.thinking:
            texts.append(qa_pair.thinking)
        
        for text in texts:
            doc = self.nlp(text)
            for ent in doc.ents:
                # Map SpaCy types to our types
                entity_type = self._map_spacy_type(ent.label_)
                if entity_type:
                    entities.append({
                        "name": ent.text,
                        "type": entity_type,
                        "confidence": 0.9,  # High confidence for SpaCy
                        "source": "spacy"
                    })
        
        return entities
    
    def _map_spacy_type(self, spacy_label: str) -> Optional[str]:
        """Map SpaCy entity labels to our entity types."""
        mapping = {
            "PERSON": "PERSON",
            "ORG": "ORGANIZATION",
            "GPE": "LOCATION",
            "LOC": "LOCATION",
            "PRODUCT": "CONCEPT",
            "WORK_OF_ART": "CONCEPT",
            "EVENT": "EVENT",
            "LAW": "CONCEPT",
            "LANGUAGE": "CONCEPT",
            "NORP": "GROUP",  # Nationalities, religious, political groups
        }
        return mapping.get(spacy_label)
    
    def _extract_with_patterns(self, qa_pair: QAPair) -> List[Dict[str, Any]]:
        """Extract entities using existing pattern matching."""
        entities = []
        
        # Use existing EntityExtractor
        texts = [qa_pair.question, qa_pair.answer]
        for text in texts:
            pattern_entities = self.pattern_extractor.extract_entities(text)
            for entity in pattern_entities:
                entity["source"] = "pattern"
                entities.append(entity)
        
        return entities
    
    def _extract_with_bm25(self, qa_pair: QAPair) -> List[Dict[str, Any]]:
        """Extract entities using BM25 keyword search."""
        entities = []
        
        # Search for relevant documents using question as query
        try:
            search_results = bm25_search(
                db=self.db.db,
                query_text=qa_pair.question,
                collections=[self.entity_collection],
                top_n=5
            )
        except Exception as e:
            logger.warning(f"BM25 search failed: {e}")
            return entities
        
        # Extract entities from search results
        for result in search_results.get("results", []):
            doc = result.get("doc", {})
            if doc.get("name"):
                entities.append({
                    "name": doc["name"],
                    "type": doc.get("type", "CONCEPT"),
                    "confidence": result.get("score", 0.7) / 10,  # Normalize BM25 score
                    "source": "bm25",
                    "_key": doc.get("_key")  # Preserve existing entity key
                })
        
        return entities
    
    def _resolve_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve and deduplicate entities using existing logic."""
        resolved = []
        seen = set()
        
        for entity in entities:
            # Use entity resolver function for deduplication
            entity_doc = {
                "name": entity["name"],
                "type": entity["type"],
                "confidence": entity["confidence"]
            }
            matches = find_exact_entity_matches(
                db=self.db.db,
                entity_doc=entity_doc,
                collection_name=self.entity_collection
            )
            
            if matches:
                # Use existing entity
                match = matches[0]
                key = match["_key"]
                if key not in seen:
                    resolved.append({
                        "name": match["name"],
                        "type": match["type"],
                        "confidence": max(entity["confidence"], match.get("confidence", 0.8)),
                        "_key": key,
                        "_id": match["_id"]
                    })
                    seen.add(key)
            else:
                # Create new entity
                name_key = f"{entity['name']}_{entity['type']}"
                if name_key not in seen:
                    resolved.append(entity)
                    seen.add(name_key)
        
        return resolved
    
    def create_qa_edges(
        self, 
        qa_pair: QAPair, 
        source_document: Dict[str, Any],
        batch_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create edge documents from Q&A pair.
        
        Args:
            qa_pair: The Q&A pair to create edges from
            source_document: The source document the Q&A was generated from
            batch_id: Optional batch identifier
            
        Returns:
            List of created edge documents
        """
        edges = []
        
        # Extract entities
        entities = self.extract_entities(qa_pair)
        
        if len(entities) < 2:
            logger.warning(f"Not enough entities ({len(entities)}) to create edges for Q&A pair")
            return edges
        
        # Sort entities by confidence to prioritize better matches
        entities.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        # Create edges between top entities
        # For now, create edge between two highest confidence entities
        from_entity = entities[0]
        to_entity = entities[1]
        
        # Ensure entities exist in database
        from_entity = self._ensure_entity_exists(from_entity)
        to_entity = self._ensure_entity_exists(to_entity)
        
        # Create edge document
        edge = self._create_edge_document(
            from_entity=from_entity,
            to_entity=to_entity,
            qa_pair=qa_pair,
            source_document=source_document,
            batch_id=batch_id
        )
        
        # Save edge to database
        try:
            result = self.db.db.collection(self.edge_collection).insert(edge)
            edge["_key"] = result["_key"]
            edge["_id"] = result["_id"]
            edges.append(edge)
            logger.info(f"Created Q&A edge: {edge['_id']}")
        except Exception as e:
            logger.error(f"Failed to create Q&A edge: {e}")
        
        return edges
    
    def _ensure_entity_exists(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure entity exists in database, create if necessary."""
        if "_key" in entity:
            # Entity already exists
            return entity
        
        # Create new entity
        entity_doc = {
            "name": entity["name"],
            "type": entity["type"],
            "confidence": entity.get("confidence", 0.8),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": entity.get("source", "qa_extraction")
        }
        
        # Add embedding
        entity_doc[EMBEDDING_FIELD] = get_embedding(entity["name"])
        
        # Create temporal entity
        result = create_temporal_entity(
            db=self.db.db,
            collection_name=self.entity_collection,
            entity_data=entity_doc
        )
        
        entity["_key"] = result["_key"]
        entity["_id"] = result["_id"]
        
        return entity
    
    def _create_edge_document(
        self,
        from_entity: Dict[str, Any],
        to_entity: Dict[str, Any],
        qa_pair: QAPair,
        source_document: Dict[str, Any],
        batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create edge document structure."""
        now = datetime.now(timezone.utc).isoformat()
        
        # Calculate edge confidence based on entity confidences and Q&A validation
        edge_confidence = (
            from_entity.get("confidence", 0.8) * 
            to_entity.get("confidence", 0.8) * 
            qa_pair.confidence
        )
        
        # Calculate context confidence based on source document and evidence
        context_confidence = self._calculate_context_confidence(qa_pair, source_document)
        
        # Generate context rationale
        context_rationale = self._generate_context_rationale(
            qa_pair=qa_pair, 
            source_document=source_document, 
            from_entity=from_entity, 
            to_entity=to_entity
        )
        
        # Create edge with all required fields
        edge = {
            FROM_FIELD: from_entity["_id"],
            TO_FIELD: to_entity["_id"],
            TYPE_FIELD: RELATIONSHIP_TYPE_QA_DERIVED,
            
            # Q&A content
            "question": qa_pair.question,
            "answer": qa_pair.answer,
            "thinking": qa_pair.thinking,
            "question_type": qa_pair.question_type.value,
            
            # Rationale and confidence
            "rationale": f"Q&A relationship between {from_entity['name']} and {to_entity['name']}: {qa_pair.question[:100]}...",
            CONFIDENCE_FIELD: edge_confidence,
            "weight": self._calculate_weight(qa_pair.question_type.value, edge_confidence),
            
            # Context confidence and rationale (new fields)
            "context_confidence": context_confidence,
            "context_rationale": context_rationale,
            "evidence_blocks": qa_pair.evidence_blocks,
            "hierarchical_context": self._extract_hierarchical_context(source_document),
            
            # Temporal metadata
            "created_at": now,
            "valid_at": source_document.get("valid_at", now),
            "invalid_at": None,
            
            # Context tracking
            "source_document_id": source_document.get("_id"),
            "source_section": qa_pair.source_section,
            "batch_id": batch_id,
            
            # Review metadata
            "review_status": "pending" if min(edge_confidence, context_confidence) < 0.7 else "auto_approved",
            "reviewed_by": None,
            "review_timestamp": None,
            
            # Standard fields
            TIMESTAMP_FIELD: now
        }
        
        # Add embeddings
        edge[EMBEDDING_FIELD] = get_embedding(qa_pair.answer)
        edge["question_embedding"] = get_embedding(qa_pair.question)
        
        return edge
    
    def _calculate_weight(self, question_type: str, confidence: float) -> float:
        """Calculate edge weight based on question type and confidence."""
        # Weight factors by question type
        type_weights = {
            "FACTUAL": 0.9,
            "RELATIONSHIP": 0.8,
            "MULTI_HOP": 0.6,
            "HIERARCHICAL": 0.7,
            "COMPARATIVE": 0.7,
            "REVERSAL": 0.5,
        }
        
        base_weight = type_weights.get(question_type, 0.5)
        return base_weight * confidence
        
    def _calculate_context_confidence(self, qa_pair: QAPair, source_document: Dict[str, Any]) -> float:
        """
        Calculate confidence in the contextual grounding of the Q&A pair.
        
        This evaluates how well the Q&A is grounded in the source document.
        
        Args:
            qa_pair: The Q&A pair
            source_document: The source document
            
        Returns:
            Confidence score (0-1)
        """
        # Start with validation score if available
        if qa_pair.validation_score:
            base_confidence = qa_pair.validation_score
        else:
            # Default base confidence
            base_confidence = 0.7
        
        # Adjust based on evidence blocks
        if qa_pair.evidence_blocks:
            # More evidence blocks increases confidence
            evidence_factor = min(len(qa_pair.evidence_blocks) / 3, 1.0) * 0.1
            base_confidence += evidence_factor
        
        # Adjust based on citation validation
        if qa_pair.citation_found:
            base_confidence += 0.15
        else:
            base_confidence -= 0.2
        
        # Adjust based on source section presence
        if qa_pair.source_section and source_document.get("_id", "").startswith(qa_pair.source_section):
            base_confidence += 0.05
        
        # Ensure within 0-1 range
        return max(0.0, min(1.0, base_confidence))
    
    def _generate_context_rationale(
        self, 
        qa_pair: QAPair, 
        source_document: Dict[str, Any],
        from_entity: Dict[str, Any],
        to_entity: Dict[str, Any]
    ) -> str:
        """
        Generate a detailed rationale for the context of this Q&A edge.
        
        Args:
            qa_pair: The Q&A pair
            source_document: The source document
            from_entity: From entity
            to_entity: To entity
            
        Returns:
            Context rationale string (min 50 chars)
        """
        # Start with base rationale
        rationale_parts = [
            f"Q&A extracted from document: {source_document.get('title', source_document.get('_id', 'Unknown'))}",
            f"Section: {qa_pair.source_section}"
        ]
        
        # Add evidence information
        if qa_pair.evidence_blocks:
            rationale_parts.append(
                f"Based on {len(qa_pair.evidence_blocks)} evidence blocks from source content"
            )
        
        # Add relationship context
        rationale_parts.append(
            f"Establishes {qa_pair.question_type.value.lower()} relationship between "
            f"{from_entity['name']} and {to_entity['name']}"
        )
        
        # Add validation context
        if qa_pair.validation_score:
            rationale_parts.append(f"Validated with confidence score of {qa_pair.validation_score:.2f}")
        
        if qa_pair.citation_found:
            rationale_parts.append("Source citations verified and found in document")
        
        # Combine and ensure minimum length
        rationale = ". ".join(rationale_parts)
        
        # Ensure minimum length of 50 characters
        if len(rationale) < 50:
            rationale += ". This Q&A pair provides contextual information derived from the document structure."
        
        return rationale
    
    def _extract_hierarchical_context(self, source_document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract hierarchical context from source document.
        
        This captures the document structure information to provide
        hierarchical context for the Q&A pair.
        
        Args:
            source_document: The source document
            
        Returns:
            Hierarchical context dictionary
        """
        hierarchy = {}
        
        # Extract document hierarchy info if available
        if "title" in source_document:
            hierarchy["document_title"] = source_document["title"]
        
        if "section_title" in source_document:
            hierarchy["section_title"] = source_document["section_title"]
        
        if "parent_id" in source_document:
            hierarchy["parent_id"] = source_document["parent_id"]
        
        if "parent_title" in source_document:
            hierarchy["parent_title"] = source_document["parent_title"]
        
        if "path" in source_document:
            hierarchy["path"] = source_document["path"]
        elif "section_path" in source_document:
            hierarchy["path"] = source_document["section_path"]
        
        # Add document level if available
        if "level" in source_document:
            hierarchy["level"] = source_document["level"]
        
        # Add heading info
        if "heading_level" in source_document:
            hierarchy["heading_level"] = source_document["heading_level"]
        
        # If no hierarchy info found, provide basic document reference
        if not hierarchy and "_id" in source_document:
            hierarchy["document_id"] = source_document["_id"]
        
        return hierarchy


# Example usage
if __name__ == "__main__":
    from arango import ArangoClient
    from ..core.db_connection_wrapper import DatabaseOperations
    
    # Initialize database
    client = ArangoClient(hosts="http://localhost:8529")
    db = client.db("agent_memory", username="root", password="openSesame")
    db_ops = DatabaseOperations(db)
    
    # Create edge generator
    edge_gen = QAEdgeGenerator(db_ops)
    
    # Test with sample Q&A pair
    test_qa = QAPair(
        question="How does Python handle memory management?",
        thinking="I need to explain Python's memory management approach...",
        answer="Python uses automatic garbage collection and reference counting.",
        question_type="FACTUAL",
        confidence=0.92,
        validation_score=0.95
    )
    
    test_doc = {
        "_id": "documents/python_guide_123",
        "title": "Python Programming Guide",
        "valid_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Extract entities
    entities = edge_gen.extract_entities(test_qa)
    print(f"Extracted entities: {entities}")
    
    # Create edges
    edges = edge_gen.create_qa_edges(test_qa, test_doc)
    print(f"Created edges: {len(edges)}")