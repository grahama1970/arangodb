"""
Q&A Edge Enrichment Module
Module: enrichment.py

Provides functionality to automatically enrich Q&A edges with search integration
and contradiction detection, making them fully integrated with the graph model.
"""

import json
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timezone
from loguru import logger

from arango.database import StandardDatabase

from arangodb.core.db_connection_wrapper import DatabaseOperations
from arangodb.core.view_config import ViewConfiguration, get_view_config
from arangodb.core.view_manager import ensure_arangosearch_view_optimized
from arangodb.core.graph.contradiction_detection import (
    detect_temporal_contradictions,
    resolve_all_contradictions
)
from arangodb.core.constants import CONFIG


class QAEdgeEnricher:
    """
    Enriches Q&A edges with search integration and contradiction detection.
    
    This class provides functionality to integrate Q&A edges with the existing
    search and graph infrastructure, ensuring they're available for querying'
    and resolving any contradictions with existing knowledge.
    """
    
    def __init__(self, db: DatabaseOperations):
        """
        Initialize the Q&A edge enricher.
        
        Args:
            db: Database operations wrapper
        """
        self.db = db
        self.edge_collection = CONFIG.get("qa", {}).get("edge_collection", "relationships")
        
        # Set up default search configuration
        self.search_fields = [
            "question", 
            "answer", 
            "thinking", 
            "rationale", 
            "context_rationale",
            "type", 
            "question_type"
        ]
        
        # QA-specific view name
        self.qa_view_name = "qa_view"
        
        # Default contradiction strategy
        self.contradiction_strategy = "newest_wins"
    
    def add_qa_edges_to_search_view(self, force_recreate: bool = False) -> bool:
        """
        Add Q&A edges to the search view for query functionality.
        
        Args:
            force_recreate: Force recreation of the view even if it exists
            
        Returns:
            Success status
        """
        try:
            # Create/update the Q&A-specific view
            ensure_arangosearch_view_optimized(
                db=self.db.db,
                view_name=self.qa_view_name,
                collection_name=self.edge_collection,
                search_fields=self.search_fields,
                force_recreate=force_recreate
            )
            
            # Get all the default views
            memory_view_config = get_view_config("memory_view")
            
            # Ensure Q&A fields are included in main memory view if needed
            # This makes Q&A edges searchable alongside other memory content
            ensure_arangosearch_view_optimized(
                db=self.db.db, 
                view_name=memory_view_config.name,
                collection_name=self.edge_collection,
                search_fields=self.search_fields,
                force_recreate=force_recreate
            )
            
            logger.info(f"Added Q&A edges to search views: {self.qa_view_name}, {memory_view_config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding Q&A edges to search view: {e}")
            return False
    
    def check_contradictions(
        self, 
        edge_doc: Dict[str, Any], 
        strategy: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Check for contradictions between a Q&A edge and existing edges.
        
        Args:
            edge_doc: The edge document to check
            strategy: Optional override for contradiction resolution strategy
            
        Returns:
            Tuple of (list of resolution results, overall success boolean)
        """
        resolution_strategy = strategy or self.contradiction_strategy
        
        try:
            # Check if the edge has required fields for contradiction detection
            if not all(k in edge_doc for k in ["_from", "_to", "type", "valid_at"]):
                logger.warning("Edge document missing fields required for contradiction detection")
                return [], False
            
            # Detect and resolve contradictions
            results, success = resolve_all_contradictions(
                db=self.db.db,
                edge_collection=self.edge_collection,
                edge_doc=edge_doc,
                strategy=resolution_strategy
            )
            
            return results, success
            
        except Exception as e:
            logger.error(f"Error checking contradictions: {e}")
            return [], False
    
    def enrich_edge_with_weight(self, edge_key: str, weight_factor: float = 1.0) -> bool:
        """
        Enrich an edge with weight based on confidence and question type.
        
        Args:
            edge_key: Key of the edge to enrich
            weight_factor: Optional weight scaling factor
            
        Returns:
            Success status
        """
        try:
            # Get the edge
            edge = self.db.db.collection(self.edge_collection).get(edge_key)
            if not edge:
                logger.warning(f"Edge {edge_key} not found")
                return False
            
            # Log the edge for debugging
            logger.debug(f"Edge to enrich: {edge}")
            
            # Calculate weight based on confidence and question type
            confidence = edge.get("confidence", 0.5)
            context_confidence = edge.get("context_confidence", 0.5)
            question_type = edge.get("question_type", "")
            
            logger.debug(f"Raw values - confidence: {confidence}, type: {type(confidence)}")
            logger.debug(f"Raw values - context_confidence: {context_confidence}, type: {type(context_confidence)}")
            logger.debug(f"Raw values - question_type: {question_type}, type: {type(question_type)}")
            
            # Handle case where confidence might be a string
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except ValueError:
                    confidence = 0.5
                    
            if isinstance(context_confidence, str):
                try:
                    context_confidence = float(context_confidence)
                except ValueError:
                    context_confidence = 0.5
            
            # Ensure we have numeric values
            confidence = float(confidence)
            context_confidence = float(context_confidence)
            
            # Weight factors by question type
            type_weights = {
                "FACTUAL": 0.9,
                "RELATIONSHIP": 0.8,
                "MULTI_HOP": 0.6,
                "HIERARCHICAL": 0.7,
                "COMPARATIVE": 0.7,
                "REVERSAL": 0.5,
                "CAUSAL": 0.8,
                "DEFINITIONAL": 0.85,
                "PROCEDURAL": 0.75
            }
            
            # Get base weight for question type or default to 0.5
            base_weight = type_weights.get(question_type, 0.5)
            logger.debug(f"Base weight for question type '{question_type}': {base_weight}")
            
            # Calculate combined weight using confidence and context_confidence
            # with question type base weight
            combined_weight = (
                base_weight * 
                ((confidence + context_confidence) / 2) * 
                weight_factor
            )
            
            logger.debug(f"Calculated combined weight: {combined_weight}")
            
            # Update edge with weight
            self.db.db.collection(self.edge_collection).update(
                edge_key,
                {"weight": combined_weight}
            )
            
            logger.debug(f"Updated edge {edge_key} with weight: {combined_weight}")
            return True
            
        except Exception as e:
            import traceback
            logger.error(f"Error enriching edge with weight: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def enrich_qa_edges(
        self, 
        edge_ids: List[str] = None,
        add_to_search: bool = True,
        check_contradictions: bool = True,
        update_weights: bool = True,
        weight_factor: float = 1.0,
        contradiction_strategy: str = None
    ) -> Dict[str, Any]:
        """
        Perform full enrichment on Q&A edges.
        
        Args:
            edge_ids: Optional list of edge IDs to enrich (if None, enrich all QA edges)
            add_to_search: Whether to add edges to search views
            check_contradictions: Whether to check for contradictions
            update_weights: Whether to update edge weights
            weight_factor: Weight scaling factor
            contradiction_strategy: Optional contradiction resolution strategy
            
        Returns:
            Dictionary with enrichment results
        """
        results = {
            "total_edges": 0,
            "search_added": False,
            "contradictions_checked": 0,
            "contradictions_found": 0,
            "contradictions_resolved": 0,
            "weights_updated": 0,
            "errors": []
        }
        
        try:
            # Add to search views if requested
            if add_to_search:
                search_added = self.add_qa_edges_to_search_view()
                results["search_added"] = search_added
            
            # If specific edge IDs provided, get those edges
            # Otherwise, get all Q&A edges
            if edge_ids:
                edges = []
                for edge_id in edge_ids:
                    # Handle both full ID (_id) and key formats
                    if "/" in edge_id:
                        # Full ID format: collection/key
                        collection, key = edge_id.split("/")
                        if collection != self.edge_collection:
                            logger.warning(f"Edge {edge_id} is not in collection {self.edge_collection}")
                            continue
                    else:
                        # Key only format
                        key = edge_id
                    
                    edge = self.db.db.collection(self.edge_collection).get(key)
                    if edge and edge.get("type") == "QA_DERIVED":
                        edges.append(edge)
            else:
                # Get all Q&A edges from the collection
                query = f"""
                FOR e IN {self.edge_collection}
                FILTER e.type == "QA_DERIVED" 
                LIMIT 1000
                RETURN e
                """
                cursor = self.db.db.aql.execute(query)
                edges = list(cursor)
            
            results["total_edges"] = len(edges)
            
            # Process each edge
            for edge in edges:
                edge_key = edge.get("_key")
                
                # Check for contradictions if requested
                if check_contradictions:
                    results["contradictions_checked"] += 1
                    contradiction_results, success = self.check_contradictions(
                        edge,
                        strategy=contradiction_strategy
                    )
                    
                    if contradiction_results:
                        results["contradictions_found"] += len(contradiction_results)
                        resolved = sum(1 for r in contradiction_results if r.get("success", False))
                        results["contradictions_resolved"] += resolved
                
                # Update weights if requested
                if update_weights:
                    weight_updated = self.enrich_edge_with_weight(
                        edge_key,
                        weight_factor=weight_factor
                    )
                    
                    if weight_updated:
                        results["weights_updated"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error in edge enrichment: {e}")
            results["errors"].append(str(e))
            return results


# Example usage
if __name__ == "__main__":
    # Initialize database operations
    db_ops = DatabaseOperations.get_instance()
    
    # Create enricher
    enricher = QAEdgeEnricher(db_ops)
    
    # Perform enrichment on all Q&A edges
    results = enricher.enrich_qa_edges()
    
    # Display results
    print(json.dumps(results, indent=2))