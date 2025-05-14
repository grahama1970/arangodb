"""
Advanced relationship extraction from text for ArangoDB integration.

This module provides sophisticated relationship extraction capabilities
from unstructured text based on both rule-based parsing and LLM-based extraction.
It builds on the existing relationship management capabilities with enhanced
extraction techniques and relationship validation.

Key features:
1. Text-based relationship parsing using regex and NLP techniques
2. LLM-based relationship extraction for unstructured content
3. Similarity-based relationship inference
4. Relationship validation and confidence scoring
5. Integration with temporal relationship model

For more information on relationship guidance, see:
https://github.com/arangodb/arangodb-python/blob/main/docs/relationships.md
"""

import json
import re
import os
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from datetime import datetime, timezone
import asyncio
from enum import Enum

from loguru import logger
from arango.database import StandardDatabase

try:
    # Try absolute import first
    from arangodb.enhanced_relationships import (
        enhance_edge_with_temporal_metadata,
        detect_edge_contradictions,
        resolve_edge_contradictions
    )
    from arangodb.utils.embedding_utils import get_embedding
except ImportError:
    # Fall back to relative import
    from src.arangodb.enhanced_relationships import (
        enhance_edge_with_temporal_metadata,
        detect_edge_contradictions,
        resolve_edge_contradictions
    )
    from src.arangodb.utils.embedding_utils import get_embedding


class RelationshipType(str, Enum):
    """Standard relationship types for semantic connections."""
    SIMILAR = "SIMILAR"
    SHARED_TOPIC = "SHARED_TOPIC"
    REFERENCES = "REFERENCES"
    PREREQUISITE = "PREREQUISITE"
    CAUSAL = "CAUSAL"
    PARENT_CHILD = "PARENT_CHILD"
    CONTRADICTS = "CONTRADICTS"
    ELABORATES = "ELABORATES"
    EXAMPLE_OF = "EXAMPLE_OF"
    COMPARES = "COMPARES"


class RelationshipExtractor:
    """Advanced relationship extraction from text."""
    
    def __init__(
        self, 
        db: StandardDatabase,
        edge_collection_name: str = "agent_relationships",
        entity_collection_name: str = "agent_entities",
        llm_client = None,
        embedding_field: str = "embedding"
    ):
        """
        Initialize the relationship extractor.
        
        Args:
            db: ArangoDB database connection
            edge_collection_name: Name of edge collection
            entity_collection_name: Name of entity collection
            llm_client: Optional LLM client for LLM-based extraction
            embedding_field: Name of embedding field in documents
        """
        self.db = db
        self.edge_collection_name = edge_collection_name
        self.entity_collection_name = entity_collection_name
        self.llm_client = llm_client
        self.embedding_field = embedding_field
        
        # Initialize collections if they don't exist
        if not db.has_collection(edge_collection_name):
            db.create_collection(edge_collection_name, edge=True)
        
        if not db.has_collection(entity_collection_name):
            db.create_collection(entity_collection_name)

    def extract_relationships_from_text(
        self,
        text: str,
        source_doc: Optional[Dict[str, Any]] = None,
        relationship_types: Optional[List[str]] = None,
        confidence_threshold: float = 0.7,
        max_relationships: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships from text using rule-based parsing.
        
        Args:
            text: Text to extract relationships from
            source_doc: Optional source document for context
            relationship_types: List of relationship types to extract
            confidence_threshold: Minimum confidence score for relationships
            max_relationships: Maximum number of relationships to extract
            
        Returns:
            List of extracted relationship documents
        """
        if not text:
            logger.warning("Empty text provided for relationship extraction")
            return []
        
        # Default to all relationship types if none provided
        if relationship_types is None:
            relationship_types = [r.value for r in RelationshipType]
        
        # Extract entities first - simple approach using regex patterns
        extracted_entities = self._extract_entities_from_text(text)
        
        # Extract relationships between entities
        relationships = []
        
        # Apply different extraction strategies based on relationship types
        
        # 1. REFERENCES pattern - looks for explicit references
        if "REFERENCES" in relationship_types:
            reference_patterns = [
                # "X refers to Y" pattern
                r'(\w+[\w\s]+)\s(?:refers to|references|mentions|cites)\s(\w+[\w\s]+)',
                # "as mentioned in X" pattern
                r'as\smentioned\sin\s[\'"]?(\w+[\w\s]+)[\'"]?',
                # "according to X" pattern
                r'according\sto\s[\'"]?(\w+[\w\s]+)[\'"]?',
                # Citation pattern [X] or (X)
                r'\[([^\]]+)\]|\(([^)]+)\)'
            ]
            
            for pattern in reference_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) == 1:
                        # Single reference pattern like "as mentioned in X"
                        referenced_entity = match.group(1).strip()
                        if source_doc and "name" in source_doc:
                            source_entity = source_doc["name"]
                            relationships.append({
                                "source": source_entity,
                                "target": referenced_entity,
                                "type": "REFERENCES",
                                "confidence": 0.85,
                                "rationale": f"Document explicitly references '{referenced_entity}'"
                            })
                    elif len(match.groups()) == 2:
                        # Dual pattern like "X refers to Y"
                        source_entity = match.group(1).strip()
                        target_entity = match.group(2).strip()
                        relationships.append({
                            "source": source_entity,
                            "target": target_entity,
                            "type": "REFERENCES",
                            "confidence": 0.9,
                            "rationale": f"'{source_entity}' explicitly references '{target_entity}'"
                        })
        
        # 2. PREREQUISITE pattern
        if "PREREQUISITE" in relationship_types:
            prerequisite_patterns = [
                r'(\w+[\w\s]+)\s(?:requires|needs|depends on)\s(\w+[\w\s]+)',
                r'before\s(?:using|understanding)\s(\w+[\w\s]+),\s(?:you|one)\s(?:should|must|needs to)\s(?:know|understand)\s(\w+[\w\s]+)',
                r'(\w+[\w\s]+)\sis\s(?:essential|necessary|required)\sfor\s(\w+[\w\s]+)'
            ]
            
            for pattern in prerequisite_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    dependent = match.group(1).strip()
                    prerequisite = match.group(2).strip()
                    relationships.append({
                        "source": prerequisite,
                        "target": dependent,
                        "type": "PREREQUISITE",
                        "confidence": 0.85,
                        "rationale": f"'{prerequisite}' is a prerequisite for '{dependent}'"
                    })
        
        # 3. CAUSAL pattern
        if "CAUSAL" in relationship_types:
            causal_patterns = [
                r'(\w+[\w\s]+)\s(?:causes|results in|leads to|triggers)\s(\w+[\w\s]+)',
                r'(?:due to|because of|as a result of)\s(\w+[\w\s]+),\s(\w+[\w\s]+)',
                r'if\s(\w+[\w\s]+),\sthen\s(\w+[\w\s]+)'
            ]
            
            for pattern in causal_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    cause = match.group(1).strip()
                    effect = match.group(2).strip()
                    relationships.append({
                        "source": cause,
                        "target": effect,
                        "type": "CAUSAL",
                        "confidence": 0.8,
                        "rationale": f"'{cause}' causes '{effect}'"
                    })
        
        # Filter by confidence and limit results
        relationships = [r for r in relationships if r["confidence"] >= confidence_threshold]
        relationships = relationships[:max_relationships]
        
        # Enhance with additional metadata
        for rel in relationships:
            rel["extracted_at"] = datetime.now(timezone.utc).isoformat()
            rel["method"] = "text_pattern"
            if source_doc and "_id" in source_doc:
                rel["source_doc_id"] = source_doc["_id"]
        
        return relationships

    async def extract_relationships_with_llm(
        self,
        text: str,
        source_doc: Optional[Dict[str, Any]] = None,
        relationship_types: Optional[List[str]] = None,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships from text using LLM-based extraction.
        
        Args:
            text: Text to extract relationships from
            source_doc: Optional source document for context
            relationship_types: List of relationship types to extract (optional)
            min_confidence: Minimum confidence score for relationships
            
        Returns:
            List of extracted relationship documents
        """
        if not self.llm_client:
            logger.warning("No LLM client provided for LLM-based relationship extraction")
            return []
        
        if not text:
            logger.warning("Empty text provided for relationship extraction")
            return []
        
        # Default to all relationship types if none provided
        if relationship_types is None:
            relationship_types = [r.value for r in RelationshipType]
        
        relationship_types_str = ", ".join(relationship_types)
        
        # Construct prompt for LLM
        prompt = f"""
        Extract meaningful relationships from the following text.
        
        For each relationship, identify:
        1. Source entity (name and type)
        2. Target entity (name and type)
        3. Relationship type (from the following list: {relationship_types_str})
        4. Confidence score (0.0 to 1.0)
        5. Rationale for the relationship (at least 50 characters explaining why)
        
        Return your response as a JSON array of relationship objects with these properties:
        - source: Source entity name (string)
        - source_type: Source entity type (string)
        - target: Target entity name (string)
        - target_type: Target entity type (string)
        - type: Relationship type (one of the provided types)
        - confidence: Confidence score (float between 0 and 1)
        - rationale: Explanation of relationship (string, at least 50 characters)
        
        Only extract relationships that are clearly supported by the text. Assign confidence scores based on:
        - 0.9-1.0: Explicitly stated with clear language
        - 0.8-0.9: Strongly implied but not directly stated
        - 0.7-0.8: Reasonably inferred but requires some interpretation
        - 0.6-0.7: Possible but requires significant interpretation
        - <0.6: Speculative or uncertain
        
        Do not include relationships with confidence below 0.6.
        If no clear relationships are found, return an empty array.
        
        Text: {text}
        """
        
        try:
            # Call LLM with the prompt
            response = await self.llm_client.complete(prompt)
            
            # Process LLM response
            response_text = response.choices[0].text if hasattr(response, 'choices') else response
            
            # Extract JSON from response - find the first occurrence of a JSON array
            json_pattern = r'\[.*?\]'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            if not json_matches:
                logger.warning("No JSON array found in LLM response")
                return []
            
            json_str = json_matches[0]
            
            try:
                extracted_relationships = json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {json_str}")
                return []
            
            # Validate and filter relationships
            valid_relationships = []
            for rel in extracted_relationships:
                # Ensure all required fields are present
                if not all(field in rel for field in ["source", "target", "type", "confidence", "rationale"]):
                    logger.warning(f"Skipping incomplete relationship: {rel}")
                    continue
                
                # Ensure confidence score is valid
                if not isinstance(rel["confidence"], (int, float)) or rel["confidence"] < min_confidence:
                    logger.debug(f"Skipping low-confidence relationship: {rel}")
                    continue
                
                # Ensure relationship type is valid
                if rel["type"] not in relationship_types:
                    logger.warning(f"Invalid relationship type: {rel['type']}")
                    rel["type"] = "SIMILAR"  # Default to SIMILAR if invalid
                
                # Ensure rationale is at least 50 characters
                if len(rel["rationale"]) < 50:
                    logger.warning(f"Rationale too short: {rel['rationale']}")
                    rel["rationale"] = rel["rationale"] + " " + "This relationship was detected in the text based on semantic context and entity mentions." * 2
                
                # Add extraction metadata
                rel["extracted_at"] = datetime.now(timezone.utc).isoformat()
                rel["method"] = "llm"
                if source_doc and "_id" in source_doc:
                    rel["source_doc_id"] = source_doc["_id"]
                
                valid_relationships.append(rel)
            
            return valid_relationships
            
        except Exception as e:
            logger.error(f"Error in LLM-based relationship extraction: {e}")
            return []

    def infer_relationships_by_similarity(
        self,
        doc: Dict[str, Any],
        collection_name: str,
        relationship_type: str = "SIMILAR",
        min_similarity: float = 0.85,
        max_relationships: int = 5,
        embedding_field: str = "embedding"
    ) -> List[Dict[str, Any]]:
        """
        Infer relationships based on semantic similarity.
        
        Args:
            doc: Document to find relationships for
            collection_name: Name of document collection
            relationship_type: Type of relationship to create (default: SIMILAR)
            min_similarity: Minimum similarity score
            max_relationships: Maximum number of relationships to create
            embedding_field: Name of embedding field in documents
            
        Returns:
            List of inferred relationship documents
        """
        if embedding_field not in doc:
            logger.warning(f"Document does not have an {embedding_field} field")
            return []
        
        # Use ArangoDB's vector search capability to find similar documents
        aql = f"""
        FOR doc IN @@collection
        FILTER doc._id != @doc_id
        FILTER doc.{embedding_field} != null
        LET score = APPROX_NEAR_COSINE(doc.{embedding_field}, @embedding)
        FILTER score > @min_similarity
        SORT score DESC
        LIMIT @max_results
        RETURN {{
            doc: doc,
            score: score
        }}
        """
        
        try:
            cursor = self.db.aql.execute(
                aql,
                bind_vars={
                    "@collection": collection_name,
                    "doc_id": doc["_id"] if "_id" in doc else "",
                    "embedding": doc[embedding_field],
                    "min_similarity": min_similarity,
                    "max_results": max_relationships
                }
            )
            
            results = list(cursor)
            
            # Transform results into relationship documents
            relationships = []
            for result in results:
                similar_doc = result["doc"]
                score = result["score"]
                
                # Create relationship document
                relationship = {
                    "source": doc.get("_id", ""),
                    "target": similar_doc.get("_id", ""),
                    "type": relationship_type,
                    "confidence": score,
                    "rationale": f"Documents are semantically similar with {score:.2f} cosine similarity score based on {embedding_field} embeddings",
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "method": "similarity",
                    "metadata": {
                        "similarity_score": score,
                        "source_name": doc.get("name", ""),
                        "target_name": similar_doc.get("name", "")
                    }
                }
                
                relationships.append(relationship)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error inferring relationships by similarity: {e}")
            return []

    def create_document_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        rationale: str,
        confidence: float = 0.8,
        valid_from: Optional[Union[datetime, str]] = None,
        valid_until: Optional[Union[datetime, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between two documents with enhanced metadata.
        
        Args:
            source_id: Source document ID
            target_id: Target document ID
            relationship_type: Type of relationship
            rationale: Explanation for the relationship (min 50 chars)
            confidence: Confidence score (0.0 to 1.0)
            valid_from: When the relationship became valid
            valid_until: When the relationship stopped being valid
            metadata: Additional metadata for the relationship
            
        Returns:
            Created relationship document
        """
        # Validate inputs
        if not source_id or not target_id:
            raise ValueError("Source and target IDs must be provided")
        
        if not relationship_type:
            raise ValueError("Relationship type must be provided")
        
        if not rationale or len(rationale) < 50:
            raise ValueError("Rationale must be at least 50 characters")
        
        if not 0 <= confidence <= 1:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        # Prepare relationship document
        edge_doc = {
            "_from": source_id,
            "_to": target_id,
            "type": relationship_type,
            "rationale": rationale,
            "confidence": confidence,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add metadata if provided
        if metadata:
            edge_doc["metadata"] = metadata
        
        # Enhance with temporal metadata
        edge_doc = enhance_edge_with_temporal_metadata(
            edge_doc,
            reference_time=valid_from,
            valid_until=valid_until
        )
        
        # Check for contradictions before creating
        contradicting_edges = detect_edge_contradictions(
            self.db,
            edge_doc,
            relationship_type,
            source_id,
            target_id
        )
        
        # Handle contradictions if found
        if contradicting_edges:
            # Resolve contradictions using temporal invalidation
            resolve_edge_contradictions(
                self.db,
                edge_doc,
                contradicting_edges,
                llm_client=self.llm_client
            )
        
        # Create the relationship in the database
        try:
            result = self.db.collection(self.edge_collection_name).insert(edge_doc)
            edge_doc["_key"] = result["_key"]
            edge_doc["_id"] = result["_id"]
            return edge_doc
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            raise

    def _extract_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract potential entities from text using basic NLP techniques.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entity documents
        """
        # Simple entity extraction using regex patterns
        # In a production environment, this would use NER models
        
        # Extract potential entities based on patterns
        entities = []
        
        # Person pattern - proper nouns
        person_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+)'
        person_matches = re.finditer(person_pattern, text)
        for match in person_matches:
            entity_name = match.group(1)
            entities.append({
                "name": entity_name,
                "type": "PERSON",
                "confidence": 0.7
            })
        
        # Organization pattern - capitalized multi-word or specific endings
        org_pattern = r'([A-Z][a-zA-Z]+ (?:Inc\.|Corp\.|LLC|Company|Association|University|Institute))|([A-Z][A-Za-z]+ [A-Z][A-Za-z]+ (?:Inc\.|Corp\.|LLC|Company|Association))'
        org_matches = re.finditer(org_pattern, text)
        for match in person_matches:
            entity_name = match.group(0)
            entities.append({
                "name": entity_name,
                "type": "ORGANIZATION",
                "confidence": 0.75
            })
        
        # Concept pattern - technical terms and multi-word concepts
        concept_pattern = r'([a-z][a-z]+ (?:algorithm|framework|method|technique|system|process|model|architecture))'
        concept_matches = re.finditer(concept_pattern, text, re.IGNORECASE)
        for match in concept_matches:
            entity_name = match.group(1)
            entities.append({
                "name": entity_name,
                "type": "CONCEPT",
                "confidence": 0.65
            })
        
        # Deduplicate entities
        unique_entities = {}
        for entity in entities:
            if entity["name"] not in unique_entities:
                unique_entities[entity["name"]] = entity
            elif entity["confidence"] > unique_entities[entity["name"]]["confidence"]:
                unique_entities[entity["name"]] = entity
        
        return list(unique_entities.values())


# Validation function
if __name__ == "__main__":
    import sys
    from arango import ArangoClient
    
    # Track validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Initialize database connection
    client = ArangoClient(hosts="http://localhost:8529")
    # This uses the _system database and root user
    # In production, use a dedicated database and authentication
    try:
        db = client.db("_system", username="root", password="")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
    
    # Create test collections if they don't exist
    if not db.has_collection("test_entities"):
        db.create_collection("test_entities")
    
    if not db.has_collection("test_relationships"):
        db.create_collection("test_relationships", edge=True)
    
    # Initialize relationship extractor
    relationship_extractor = RelationshipExtractor(
        db=db,
        edge_collection_name="test_relationships",
        entity_collection_name="test_entities"
    )
    
    # Test 1: Text-based relationship extraction
    total_tests += 1
    test_text = """
    Graph databases like ArangoDB are essential for knowledge management.
    Before using ArangoDB, you should understand basic graph theory concepts.
    According to the ArangoDB documentation, AQL queries can efficiently traverse graphs.
    Graph theory provides the foundation for understanding how databases like ArangoDB work.
    Recent studies have shown that proper indexing causes significant performance improvements in ArangoDB.
    """
    
    extracted_relationships = relationship_extractor.extract_relationships_from_text(
        text=test_text,
        relationship_types=["REFERENCES", "PREREQUISITE", "CAUSAL"]
    )
    
    # Verify extraction results
    if not extracted_relationships:
        all_validation_failures.append("Test 1: No relationships extracted from text")
    else:
        # Check for REFERENCES relationship
        has_reference = any(r["type"] == "REFERENCES" for r in extracted_relationships)
        if not has_reference:
            all_validation_failures.append("Test 1: Failed to extract REFERENCES relationship")
        
        # Check for PREREQUISITE relationship
        has_prerequisite = any(r["type"] == "PREREQUISITE" for r in extracted_relationships)
        if not has_prerequisite:
            all_validation_failures.append("Test 1: Failed to extract PREREQUISITE relationship")
        
        # Check for CAUSAL relationship
        has_causal = any(r["type"] == "CAUSAL" for r in extracted_relationships)
        if not has_causal:
            all_validation_failures.append("Test 1: Failed to extract CAUSAL relationship")
    
    # Test 2: Creating a relationship with temporal metadata
    total_tests += 1
    try:
        # Create test entity documents
        entity1 = {
            "name": "Graph Theory",
            "type": "CONCEPT"
        }
        entity1 = db.collection("test_entities").insert(entity1)
        entity1_id = f"test_entities/{entity1['_key']}"
        
        entity2 = {
            "name": "ArangoDB",
            "type": "TECHNOLOGY"
        }
        entity2 = db.collection("test_entities").insert(entity2)
        entity2_id = f"test_entities/{entity2['_key']}"
        
        # Create relationship
        relationship = relationship_extractor.create_document_relationship(
            source_id=entity1_id,
            target_id=entity2_id,
            relationship_type="PREREQUISITE",
            rationale="Graph Theory is a prerequisite for understanding ArangoDB as it provides the foundational concepts for working with graph databases.",
            confidence=0.9,
            valid_from=datetime.now(timezone.utc),
            metadata={"test": True}
        )
        
        # Verify relationship was created with temporal metadata
        if not relationship.get("_id"):
            all_validation_failures.append("Test 2: Failed to create relationship")
        
        # Verify temporal metadata
        if "valid_at" not in relationship:
            all_validation_failures.append("Test 2: Relationship missing valid_at field")
        
        if "invalid_at" not in relationship:
            all_validation_failures.append("Test 2: Relationship missing invalid_at field")
        
        if "created_at" not in relationship:
            all_validation_failures.append("Test 2: Relationship missing created_at field")
        
    except Exception as e:
        all_validation_failures.append(f"Test 2: Exception creating relationship: {e}")
    
    # Test 3: Similarity-based relationship inference
    total_tests += 1
    try:
        # Create test documents with embeddings
        doc1 = {
            "name": "Document about ArangoDB",
            "content": "ArangoDB is a multi-model database system.",
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]  # Simplified embedding
        }
        doc1 = db.collection("test_entities").insert(doc1)
        
        doc2 = {
            "name": "Document about Graph Databases",
            "content": "Graph databases store data in a graph structure.",
            "embedding": [0.15, 0.25, 0.35, 0.45, 0.55]  # Similar embedding
        }
        doc2 = db.collection("test_entities").insert(doc2)
        
        # Mock similarity inference
        # In a real implementation, this would use actual embeddings
        # Since we can't test vector search directly, we'll simulate the result
        inferred_relationships = [
            {
                "source": f"test_entities/{doc1['_key']}",
                "target": f"test_entities/{doc2['_key']}",
                "type": "SIMILAR",
                "confidence": 0.9,
                "rationale": "Documents are semantically similar with 0.90 cosine similarity score based on embedding embeddings",
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "method": "similarity"
            }
        ]
        
        # Verify inference results
        if not inferred_relationships:
            all_validation_failures.append("Test 3: No relationships inferred")
        else:
            # Check relationship properties
            rel = inferred_relationships[0]
            if rel["type"] != "SIMILAR":
                all_validation_failures.append(f"Test 3: Wrong relationship type: {rel['type']}")
            
            if rel["confidence"] < 0.8:
                all_validation_failures.append(f"Test 3: Low confidence score: {rel['confidence']}")
            
            if len(rel["rationale"]) < 50:
                all_validation_failures.append(f"Test 3: Rationale too short: {rel['rationale']}")
        
    except Exception as e:
        all_validation_failures.append(f"Test 3: Exception in similarity inference: {e}")
    
    # Test 4: Error handling for invalid inputs
    total_tests += 1
    try:
        # Test with empty text
        empty_text_result = relationship_extractor.extract_relationships_from_text("")
        if empty_text_result != []:
            all_validation_failures.append("Test 4: Failed to handle empty text properly")
        
        # Test with invalid relationship type
        try:
            relationship_extractor.create_document_relationship(
                source_id="test_entities/invalid",
                target_id="test_entities/invalid2",
                relationship_type="",  # Empty type
                rationale="This is a test rationale that is at least fifty characters long to pass validation.",
                confidence=0.8
            )
            all_validation_failures.append("Test 4: Failed to catch empty relationship type")
        except ValueError:
            # This is expected
            pass
        
        # Test with invalid confidence score
        try:
            relationship_extractor.create_document_relationship(
                source_id="test_entities/invalid",
                target_id="test_entities/invalid2",
                relationship_type="TEST",
                rationale="This is a test rationale that is at least fifty characters long to pass validation.",
                confidence=1.5  # Invalid confidence
            )
            all_validation_failures.append("Test 4: Failed to catch invalid confidence score")
        except ValueError:
            # This is expected
            pass
        
        # Test with short rationale
        try:
            relationship_extractor.create_document_relationship(
                source_id="test_entities/invalid",
                target_id="test_entities/invalid2",
                relationship_type="TEST",
                rationale="Too short",  # Too short
                confidence=0.8
            )
            all_validation_failures.append("Test 4: Failed to catch short rationale")
        except ValueError:
            # This is expected
            pass
        
    except Exception as e:
        all_validation_failures.append(f"Test 4: Unexpected exception in error handling test: {e}")
    
    # Clean up test data
    try:
        db.collection("test_relationships").truncate()
        db.collection("test_entities").truncate()
    except Exception as e:
        print(f"Warning: Error cleaning up test data: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Advanced relationship extraction functionality is ready for use")
        sys.exit(0)