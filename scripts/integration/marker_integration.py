"""
Module: marker_integration.py
Description: Document processing and marking functionality

External Dependencies:
- numpy: https://numpy.org/doc/
- loguru: https://loguru.readthedocs.io/
- arango: https://docs.python-arango.com/

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

#!/usr/bin/env python3
"""
Marker PDF to ArangoDB integration script.

This script demonstrates the complete pipeline for:
1. Converting a PDF with Marker
2. Storing document elements in ArangoDB
3. Creating relationships between elements
4. Generating Q&A pairs for model training
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import numpy as np
from loguru import logger

# Add ArangoDB project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arango import ArangoClient
from arangodb.core.arango_setup import ArangoSetup
from arangodb.core.utils.embedding_utils import get_embedding
from arangodb.core.graph.relationship_extraction import RelationshipExtractor, RelationshipType
from arangodb.core.llm_utils import llm

# Add Marker project to path
marker_path = "/home/graham/workspace/experiments/marker"
sys.path.insert(0, marker_path)

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.renderers.arangodb_json import ArangoDBRenderer


class MarkerArangoDBIntegration:
    """Integrates Marker PDF processing with ArangoDB storage and Q&A generation."""
    
    def __init__(self, db_config: Dict[str, str] = None):
        """Initialize with database configuration."""
        if db_config is None:
            db_config = {
                "host": os.getenv("ARANGO_HOST", "localhost"),
                "username": os.getenv("ARANGO_USERNAME", "root"),
                "password": os.getenv("ARANGO_PASSWORD", "openSesame")
            }
        
        # Setup ArangoDB
        self.setup = ArangoSetup(
            host=db_config["host"],
            username=db_config["username"],
            password=db_config["password"]
        )
        
        # Initialize database and collections
        self.db = self.setup.setup_database("marker_integration_test")
        self._setup_collections()
        
        # Initialize relationship extractor
        self.rel_extractor = RelationshipExtractor(
            db=self.db,
            edge_collection_name="content_relationships",
            entity_collection_name="document_objects"
        )
        
    def _setup_collections(self):
        """Setup required collections."""
        collections = [
            ("document_objects", False),    # Document content elements
            ("documents", False),           # Document metadata
            ("content_relationships", True) # Relationships between elements
        ]
        
        for name, is_edge in collections:
            if not self.db.has_collection(name):
                self.db.create_collection(name, edge=is_edge)
                logger.info(f"Created collection: {name}")
    
    async def process_pdf(self, pdf_path: str, doc_id: str = None) -> Dict[str, Any]:
        """Process a PDF through the complete pipeline."""
        
        if not doc_id:
            doc_id = Path(pdf_path).stem
        
        logger.info(f"Processing PDF: {pdf_path} with doc_id: {doc_id}")
        
        # 1. Convert PDF with Marker
        document = await self._convert_pdf(pdf_path)
        
        # 2. Render to ArangoDB format
        arangodb_output = self._render_to_arangodb(document)
        
        # 3. Store in ArangoDB
        await self._store_in_arangodb(arangodb_output, doc_id)
        
        # 4. Create embeddings
        await self._create_embeddings(doc_id)
        
        # 5. Build relationships
        await self._create_relationships(doc_id)
        
        # 6. Generate Q&A pairs
        qa_pairs = await self._generate_qa_pairs(doc_id)
        
        return {
            "doc_id": doc_id,
            "object_count": len(arangodb_output.objects),
            "qa_count": len(qa_pairs),
            "qa_pairs": qa_pairs
        }
    
    async def _convert_pdf(self, pdf_path: str):
        """Convert PDF using Marker."""
        logger.info("Converting PDF with Marker...")
        
        converter = PdfConverter(
            artifact_dict=create_model_dict()
        )
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        document = await loop.run_in_executor(None, converter, pdf_path)
        
        logger.info(f"Converted {len(document.pages)} pages")
        return document
    
    def _render_to_arangodb(self, document):
        """Render document to ArangoDB format."""
        logger.info("Rendering to ArangoDB format...")
        
        renderer = ArangoDBRenderer()
        output = renderer(document)
        
        logger.info(f"Rendered {len(output.objects)} objects")
        return output
    
    async def _store_in_arangodb(self, arangodb_output, doc_id: str):
        """Store document objects in ArangoDB."""
        logger.info("Storing in ArangoDB...")
        
        # Store document objects
        objects_to_insert = []
        for obj in arangodb_output.objects:
            obj_dict = obj.dict()
            obj_dict["document_id"] = doc_id
            objects_to_insert.append(obj_dict)
        
        # Batch insert
        self.db.collection("document_objects").insert_many(objects_to_insert)
        
        # Store document metadata
        metadata = arangodb_output.document_metadata
        metadata["_key"] = doc_id
        self.db.collection("documents").insert(metadata)
        
        logger.info(f"Stored {len(objects_to_insert)} objects")
    
    async def _create_embeddings(self, doc_id: str):
        """Create embeddings for document objects."""
        logger.info("Creating embeddings...")
        
        # Query text-based objects
        query = """
        FOR obj IN document_objects
            FILTER obj.document_id == @doc_id
            FILTER obj._type IN ["text", "table", "code", "section"]
            FILTER obj.text != null
            RETURN obj
        """
        
        objects = list(self.db.aql.execute(query, bind_vars={"doc_id": doc_id}))
        
        # Batch create embeddings
        tasks = []
        for obj in objects:
            tasks.append(self._embed_object(obj))
        
        await asyncio.gather(*tasks)
        logger.info(f"Created embeddings for {len(objects)} objects")
    
    async def _embed_object(self, obj: Dict):
        """Create embedding for a single object."""
        text = obj.get("text", "")
        if not text:
            return
        
        # Get embedding
        embedding = await get_embedding(text)
        
        # Update object with embedding
        self.db.collection("document_objects").update({
            "_key": obj["_key"],
            "embedding": embedding
        })
    
    async def _create_relationships(self, doc_id: str):
        """Create relationships between document elements."""
        logger.info("Creating relationships...")
        
        # 1. Sequential relationships within sections
        await self._create_sequential_relationships(doc_id)
        
        # 2. Hierarchical relationships
        await self._create_hierarchical_relationships(doc_id)
        
        # 3. Semantic similarity relationships
        await self._create_similarity_relationships(doc_id)
        
        # 4. Cross-reference relationships
        await self._create_reference_relationships(doc_id)
        
        logger.info("Completed relationship creation")
    
    async def _create_sequential_relationships(self, doc_id: str):
        """Create sequential relationships within sections."""
        query = """
        FOR obj IN document_objects
            FILTER obj.document_id == @doc_id
            FILTER obj._type IN ["text", "table", "code", "equation"]
            SORT obj.page_id, obj.position.top
            COLLECT section_hash = obj.section_hash INTO group
            FOR i IN 0..LENGTH(group)-2
                INSERT {
                    _from: CONCAT("document_objects/", group[i].obj._key),
                    _to: CONCAT("document_objects/", group[i+1].obj._key),
                    relationship_type: "NEXT_IN_SECTION",
                    confidence: 1.0,
                    metadata: {
                        section_hash: section_hash,
                        extraction_method: "sequential",
                        timestamp: DATE_ISO8601(DATE_NOW())
                    }
                } INTO content_relationships
        """
        
        self.db.aql.execute(query, bind_vars={"doc_id": doc_id})
    
    async def _create_hierarchical_relationships(self, doc_id: str):
        """Create parent-child relationships for sections."""
        query = """
        FOR section IN document_objects
            FILTER section.document_id == @doc_id
            FILTER section._type == "section"
            
            FOR obj IN document_objects
                FILTER obj.document_id == @doc_id
                FILTER obj.section_hash == section.section_hash
                FILTER obj._key != section._key
                
                INSERT {
                    _from: CONCAT("document_objects/", section._key),
                    _to: CONCAT("document_objects/", obj._key),
                    relationship_type: "PARENT_CHILD",
                    confidence: 1.0,
                    metadata: {
                        extraction_method: "hierarchical",
                        timestamp: DATE_ISO8601(DATE_NOW())
                    }
                } INTO content_relationships
        """
        
        self.db.aql.execute(query, bind_vars={"doc_id": doc_id})
    
    async def _create_similarity_relationships(self, doc_id: str, threshold: float = 0.85):
        """Create relationships based on semantic similarity."""
        
        # Get objects with embeddings
        query = """
        FOR obj IN document_objects
            FILTER obj.document_id == @doc_id
            FILTER obj._type IN ["text", "table", "code"]
            FILTER obj.embedding != null
            RETURN obj
        """
        
        elements = list(self.db.aql.execute(query, bind_vars={"doc_id": doc_id}))
        
        # Compare embeddings pairwise
        for i, elem1 in enumerate(elements):
            for elem2 in elements[i+1:]:
                # Skip if same section
                if elem1.get("section_hash") == elem2.get("section_hash"):
                    continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(
                    elem1["embedding"], 
                    elem2["embedding"]
                )
                
                if similarity >= threshold:
                    edge = {
                        "_from": f"document_objects/{elem1['_key']}",
                        "_to": f"document_objects/{elem2['_key']}",
                        "relationship_type": "SIMILAR",
                        "confidence": float(similarity),
                        "metadata": {
                            "extraction_method": "embedding_similarity",
                            "threshold": threshold,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    }
                    
                    self.db.collection("content_relationships").insert(edge)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    async def _create_reference_relationships(self, doc_id: str):
        """Create relationships for cross-references."""
        
        # Find text elements that reference tables/figures
        query = """
        FOR text_obj IN document_objects
            FILTER text_obj.document_id == @doc_id
            FILTER text_obj._type == "text"
            FILTER text_obj.text != null
            
            FOR ref_obj IN document_objects
                FILTER ref_obj.document_id == @doc_id
                FILTER ref_obj._type IN ["table", "image"]
                
                // Simple pattern matching for references
                LET ref_pattern = CONCAT("(Table|Figure|Fig\\.?)\\s*", 
                    REGEX_TEST(ref_obj._key, "[0-9]+") ? 
                    REGEX_EXTRACT(ref_obj._key, "[0-9]+")[0] : "")
                    
                FILTER REGEX_TEST(text_obj.text, ref_pattern, true)
                
                INSERT {
                    _from: CONCAT("document_objects/", text_obj._key),
                    _to: CONCAT("document_objects/", ref_obj._key),
                    relationship_type: "REFERENCES",
                    confidence: 0.9,
                    metadata: {
                        extraction_method: "pattern_matching",
                        pattern: ref_pattern,
                        timestamp: DATE_ISO8601(DATE_NOW())
                    }
                } INTO content_relationships
        """
        
        self.db.aql.execute(query, bind_vars={"doc_id": doc_id})
    
    async def _generate_qa_pairs(self, doc_id: str) -> List[Dict]:
        """Generate Q&A pairs from document relationships."""
        logger.info("Generating Q&A pairs...")
        
        qa_pairs = []
        
        # 1. Section-based Q&A
        qa_pairs.extend(await self._generate_section_qa(doc_id))
        
        # 2. Relationship-based Q&A
        qa_pairs.extend(await self._generate_relationship_qa(doc_id))
        
        # 3. Multi-hop Q&A
        qa_pairs.extend(await self._generate_multihop_qa(doc_id))
        
        # 4. Validate answers
        validated_pairs = await self._validate_qa_pairs(qa_pairs, doc_id)
        
        logger.info(f"Generated {len(validated_pairs)} Q&A pairs")
        return validated_pairs
    
    async def _generate_section_qa(self, doc_id: str) -> List[Dict]:
        """Generate Q&A pairs from sections."""
        qa_pairs = []
        
        # Query sections with their content
        query = """
        FOR section IN document_objects
            FILTER section.document_id == @doc_id
            FILTER section._type == "section"
            
            LET content = (
                FOR obj IN document_objects
                    FILTER obj.document_id == @doc_id
                    FILTER obj.section_hash == section.section_hash
                    FILTER obj._type IN ["text", "table"]
                    RETURN obj.text
            )
            
            RETURN {
                section: section,
                content: CONCAT_SEPARATOR(" ", content)
            }
        """
        
        sections = list(self.db.aql.execute(query, bind_vars={"doc_id": doc_id}))
        
        for section_data in sections:
            section = section_data["section"]
            content = section_data["content"]
            
            if not content:
                continue
            
            # Generate Q&A for section
            prompt = f"""
            Based on the following section content, generate a question-answer pair.
            Section: {section["text"]}
            Content: {content[:1000]}
            
            Generate:
            1. A factual question about the content
            2. A thinking process for answering
            3. A comprehensive answer
            
            Format as JSON:
            {{
                "question": "...",
                "thinking": "...",
                "answer": "..."
            }}
            """
            
            response = await llm(prompt)
            
            try:
                qa = json.loads(response)
                qa["metadata"] = {
                    "question_type": "section_based",
                    "section_title": section["text"],
                    "section_hash": section["section_hash"],
                    "confidence": 0.95
                }
                qa_pairs.append(qa)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Q&A response for section: {section['text']}")
        
        return qa_pairs
    
    async def _generate_relationship_qa(self, doc_id: str) -> List[Dict]:
        """Generate Q&A pairs from relationships."""
        qa_pairs = []
        
        # Query significant relationships
        query = """
        FOR edge IN content_relationships
            FILTER edge.confidence >= 0.8
            LET from_obj = DOCUMENT(edge._from)
            LET to_obj = DOCUMENT(edge._to)
            FILTER from_obj.document_id == @doc_id
            RETURN {
                edge: edge,
                from: from_obj,
                to: to_obj
            }
        """
        
        relationships = list(self.db.aql.execute(query, bind_vars={"doc_id": doc_id}))
        
        for rel in relationships[:10]:  # Limit to avoid too many Q&As
            edge = rel["edge"]
            from_obj = rel["from"]
            to_obj = rel["to"]
            
            # Generate question based on relationship type
            if edge["relationship_type"] == "REFERENCES":
                qa = await self._generate_reference_qa(from_obj, to_obj)
            elif edge["relationship_type"] == "SIMILAR":
                qa = await self._generate_similarity_qa(from_obj, to_obj)
            elif edge["relationship_type"] == "PARENT_CHILD":
                qa = await self._generate_hierarchy_qa(from_obj, to_obj)
            else:
                continue
            
            if qa:
                qa_pairs.append(qa)
        
        return qa_pairs
    
    async def _generate_reference_qa(self, from_obj: Dict, to_obj: Dict) -> Dict:
        """Generate Q&A for reference relationships."""
        prompt = f"""
        Generate a question-answer pair about a reference relationship.
        
        Text: {from_obj.get('text', '')[:500]}
        References: {to_obj.get('_type', '')} - {to_obj.get('text', '')[:200]}
        
        Create a question about what the text references and why.
        
        Format as JSON:
        {{
            "question": "...",
            "thinking": "...",
            "answer": "..."
        }}
        """
        
        response = await llm(prompt)
        
        try:
            qa = json.loads(response)
            qa["metadata"] = {
                "question_type": "reference",
                "relationship_type": "REFERENCES",
                "from_id": from_obj["_key"],
                "to_id": to_obj["_key"],
                "confidence": 0.9
            }
            return qa
        except json.JSONDecodeError:
            return None
    
    async def _generate_similarity_qa(self, obj1: Dict, obj2: Dict) -> Dict:
        """Generate Q&A for similar content."""
        prompt = f"""
        Generate a comparison question about two similar pieces of content.
        
        Content 1: {obj1.get('text', '')[:400]}
        Content 2: {obj2.get('text', '')[:400]}
        
        Create a question about how these contents are similar or different.
        
        Format as JSON:
        {{
            "question": "...",
            "thinking": "...",
            "answer": "..."
        }}
        """
        
        response = await llm(prompt)
        
        try:
            qa = json.loads(response)
            qa["metadata"] = {
                "question_type": "comparison",
                "relationship_type": "SIMILAR",
                "obj1_id": obj1["_key"],
                "obj2_id": obj2["_key"],
                "confidence": 0.85
            }
            return qa
        except json.JSONDecodeError:
            return None
    
    async def _generate_hierarchy_qa(self, parent: Dict, child: Dict) -> Dict:
        """Generate Q&A for hierarchical relationships."""
        prompt = f"""
        Generate a question about the relationship between a section and its content.
        
        Section: {parent.get('text', '')}
        Content: {child.get('text', '')[:500]}
        
        Create a question about what this section contains and why.
        
        Format as JSON:
        {{
            "question": "...",
            "thinking": "...",
            "answer": "..."
        }}
        """
        
        response = await llm(prompt)
        
        try:
            qa = json.loads(response)
            qa["metadata"] = {
                "question_type": "hierarchical",
                "relationship_type": "PARENT_CHILD",
                "parent_id": parent["_key"],
                "child_id": child["_key"],
                "confidence": 0.95
            }
            return qa
        except json.JSONDecodeError:
            return None
    
    async def _generate_multihop_qa(self, doc_id: str) -> List[Dict]:
        """Generate multi-hop Q&A requiring traversal of multiple relationships."""
        qa_pairs = []
        
        # Find paths between related content
        query = """
        FOR path IN 2..3 OUTBOUND
            (FOR start IN document_objects 
                FILTER start.document_id == @doc_id 
                FILTER start._type == "text"
                LIMIT 5
                RETURN start)
            content_relationships
            OPTIONS {uniqueVertices: "path"}
            FILTER IS_DOCUMENT(path.vertices[-1])
            LET last_vertex = DOCUMENT(path.vertices[-1]._id)
            FILTER last_vertex.document_id == @doc_id
            RETURN {
                start: path.vertices[0],
                end: path.vertices[-1],
                path_length: LENGTH(path.edges),
                edges: path.edges
            }
            LIMIT 10
        """
        
        paths = list(self.db.aql.execute(query, bind_vars={"doc_id": doc_id}))
        
        for path_data in paths:
            if path_data["path_length"] < 2:
                continue
            
            # Generate multi-hop question
            prompt = f"""
            Generate a multi-step reasoning question that connects these concepts:
            
            Start: {path_data['start'].get('text', '')[:300]}
            End: {path_data['end'].get('text', '')[:300]}
            Path length: {path_data['path_length']} steps
            
            Create a question that requires understanding multiple relationships.
            
            Format as JSON:
            {{
                "question": "...",
                "thinking": "...",
                "answer": "..."
            }}
            """
            
            response = await llm(prompt)
            
            try:
                qa = json.loads(response)
                qa["metadata"] = {
                    "question_type": "multi_hop",
                    "path_length": path_data["path_length"],
                    "start_id": path_data["start"]["_key"],
                    "end_id": path_data["end"]["_key"],
                    "confidence": 0.8
                }
                qa_pairs.append(qa)
            except json.JSONDecodeError:
                continue
        
        return qa_pairs
    
    async def _validate_qa_pairs(self, qa_pairs: List[Dict], doc_id: str) -> List[Dict]:
        """Validate Q&A pairs against source content."""
        validated = []
        
        for qa in qa_pairs:
            # Extract key information from answer
            answer_text = qa.get("answer", "")
            
            # Check if answer content exists in document
            query = """
            FOR obj IN document_objects
                FILTER obj.document_id == @doc_id
                FILTER obj.text != null
                FILTER CONTAINS(LOWER(obj.text), LOWER(@answer_snippet))
                LIMIT 1
                RETURN obj
            """
            
            # Use first 100 chars of answer for validation
            answer_snippet = answer_text[:100] if answer_text else ""
            
            results = list(self.db.aql.execute(
                query, 
                bind_vars={"doc_id": doc_id, "answer_snippet": answer_snippet}
            ))
            
            # Validate based on confidence or evidence
            if results or qa.get("metadata", {}).get("confidence", 0) >= 0.9:
                validated.append(qa)
        
        return validated
    
    def save_qa_pairs(self, qa_pairs: List[Dict], output_path: str):
        """Save Q&A pairs to JSON lines format for training."""
        with open(output_path, 'w') as f:
            for qa in qa_pairs:
                # Format for training
                training_item = {
                    "messages": [
                        {"role": "user", "content": qa["question"]},
                        {"role": "assistant", "content": qa["answer"], "thinking": qa["thinking"]}
                    ],
                    "metadata": qa.get("metadata", {})
                }
                f.write(json.dumps(training_item) + '\n')
        
        logger.info(f"Saved {len(qa_pairs)} Q&A pairs to {output_path}")


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Process PDF and generate Q&A pairs")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--doc-id", help="Document ID (defaults to filename)")
    parser.add_argument("--output", help="Output path for Q&A pairs", 
                       default="qa_pairs.jsonl")
    
    args = parser.parse_args()
    
    # Initialize integration
    integration = MarkerArangoDBIntegration()
    
    # Process PDF
    result = await integration.process_pdf(args.pdf_path, args.doc_id)
    
    # Save Q&A pairs
    if result["qa_pairs"]:
        integration.save_qa_pairs(result["qa_pairs"], args.output)
    
    # Print summary
    print(f"\nProcessing complete:")
    print(f"- Document ID: {result['doc_id']}")
    print(f"- Objects stored: {result['object_count']}")
    print(f"- Q&A pairs generated: {result['qa_count']}")
    print(f"- Output saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())