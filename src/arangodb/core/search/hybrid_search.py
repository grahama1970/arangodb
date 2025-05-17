"""
# Hybrid Search Module for PDF Extractor

This module provides a combined search approach that leverages BM25 text search,
semantic vector search, tag filtering, and optionally graph traversal capabilities,
delivering the best results from multiple search paradigms using Reciprocal Rank Fusion (RRF).

## Features:
- Combined BM25 and semantic search results with RRF re-ranking
- Tag filtering capabilities
- Optional graph traversal integration
- Optional Perplexity API enrichment with structured output
- Customizable weighting between search types
- Multiple output formats (JSON, table)
"""

import sys
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union

import litellm
from pydantic import BaseModel, Field
from typing import List, Optional
from loguru import logger
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, ArangoServerError
from colorama import init, Fore, Style
from tabulate import tabulate
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)

# Define litellm availability
HAS_LITELLM = True

# Import config variables
from arangodb.core.constants import (
    COLLECTION_NAME,
    SEARCH_FIELDS,
    ALL_DATA_FIELDS_PREVIEW,
    TEXT_ANALYZER,
    VIEW_NAME,
    GRAPH_NAME,
    EDGE_COLLECTION_NAME,
    DEFAULT_EMBEDDING_DIMENSIONS
)

# Define embedding field name
EMBEDDING_FIELD = "embedding"
from arangodb.core.utils.embedding_utils import get_embedding

# Import search modules
from arangodb.core.search.bm25_search import bm25_search
from arangodb.core.search.semantic_search import semantic_search
from arangodb.core.arango_setup import ensure_arangosearch_view
from arangodb.core.search.search_config import SearchConfig, SearchConfigManager, SearchMethod

# Optional imports with fallbacks
try:
    from arangodb.core.search.tag_search import tag_search
except ImportError:
    def tag_search(*args, **kwargs):
        """Fallback function when tag_search is not available"""
        logger.warning("Tag search called but module is not available")
        return {"results": [], "total": 0, "error": "Tag search module is not available"}
        
try:
    from arangodb.core.search.graph_traverse import graph_rag_search
except ImportError:
    def graph_rag_search(*args, **kwargs):
        """Fallback function when graph_rag_search is not available"""
        logger.warning("Graph search called but module is not available")
        return {"results": [], "total": 0, "error": "Graph search module is not available"}

# Helper functions
def truncate_large_value(value, max_length=1000, max_list_elements_shown=10, max_str_len=None):
    """Truncate large values for better log readability."""
    if isinstance(value, str) and max_str_len and len(value) > max_str_len:
        return value[:max_str_len] + "..."
    elif isinstance(value, str) and len(value) > max_length:
        return value[:max_length] + "..."
    elif isinstance(value, list) and len(value) > max_list_elements_shown:
        return value[:max_list_elements_shown] + [f"... ({len(value) - max_list_elements_shown} more items)"]
    elif isinstance(value, dict):
        return {k: truncate_large_value(v, max_length, max_list_elements_shown) 
                for k, v in list(value.items())[:max_list_elements_shown]}
    return value

def clean_json_string(json_str, return_dict=False):
    """
    Clean JSON string for safer parsing.
    
    Args:
        json_str: JSON string to clean
        return_dict: Whether to return a parsed dict or cleaned string
    
    Returns:
        Cleaned JSON string or parsed dict
    """
    if isinstance(json_str, dict):
        return json_str
        
    try:
        # Try direct parsing first
        import json
        parsed = json.loads(json_str)
        return parsed if return_dict else json_str
    except Exception:
        # Clean and try again
        cleaned = json_str
        # Remove potential markdown code block markers
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1]
        if "```" in cleaned:
            cleaned = cleaned.split("```", 1)[0]
            
        # Try parsing again
        try:
            parsed = json.loads(cleaned.strip())
            return parsed if return_dict else cleaned.strip()
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {} if return_dict else "{}"



# Define Pydantic models for structured output
class RelatedTopic(BaseModel):
    """A related topic extracted from Perplexity API"""
    title: str = Field(..., description="Title or brief description of the related topic")
    content: str = Field(..., description="Detailed information about the topic")
    confidence: int = Field(..., description="Confidence score from 1-5", ge=1, le=5)
    rationale: str = Field(..., description="Explanation of why this topic is relevant")
    source: Optional[str] = Field(None, description="Source of the information if available")

class PerplexityResponse(BaseModel):
    """Structured response from Perplexity API"""
    topics: List[RelatedTopic] = Field(..., description="List of related topics identified")
    summary: str = Field(..., description="Brief summary of the overall findings")


@retry(
    retry=retry_if_exception_type((Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_perplexity_structured(prompt: str, model: str = "sonar-small-online"):
    """Call Perplexity API with retry logic and get structured output."""
    system_prompt = """
    You are an expert research assistant. Based on the user's query, provide information in a structured JSON format.
    Extract 3-5 highly relevant topics related to the query.
    For each topic include:
    - A clear title
    - Detailed content (1-2 paragraphs)
    - A confidence score (1-5, where 5 is highest confidence)
    - A rationale explaining why this topic is relevant
    - Source information where available
    Also provide a brief summary of your overall findings.
    """
    
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=1024,
        response_format={"type": "json_object"},
        seed=42
    )
    
    # Extract the content from the response
    content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
    
    # Use clean_json_string to robustly parse JSON
    parsed_content = clean_json_string(content, return_dict=True)
    
    # Parse JSON into our Pydantic model
    try:
        structured_response = PerplexityResponse.model_validate(parsed_content)
        return structured_response
    except Exception as e:
        logger.error(f"Failed to parse Perplexity response: {e}")
        
        # Create a minimal valid response
        return PerplexityResponse(
            topics=[RelatedTopic(
                title="Error parsing response",
                content=f"Could not parse structured data: {str(e)}",
                confidence=1,
                rationale="Error occurred during parsing"
            )],
            summary="Error occurred while parsing the Perplexity response."
        )
    
def store_perplexity_results(
    db: StandardDatabase,
    query_text: str,
    search_results: Dict[str, Any],
    perplexity_response: PerplexityResponse,
    document_collection: str = "related_topics",
    edge_collection: str = "relationships"
) -> Dict[str, Any]:
    """
    Store Perplexity results in the graph database.
    
    Args:
        db: ArangoDB database connection
        query_text: Original query text
        search_results: Results from hybrid search
        perplexity_response: Structured response from Perplexity
        document_collection: Collection to store related topics
        edge_collection: Collection to store relationships
        
    Returns:
        Dictionary with IDs of created documents and edges
    """
    try:
        # Ensure collections exist
        if not db.has_collection(document_collection):
            logger.info(f"Creating collection: {document_collection}")
            db.create_collection(document_collection)
        
        if not db.has_collection(edge_collection):
            logger.info(f"Creating edge collection: {edge_collection}")
            db.create_collection(edge_collection, edge=True)
        
        doc_collection = db.collection(document_collection)
        edge_col = db.collection(edge_collection)
        
        # Create document for each topic
        created_docs = []
        created_edges = []
        
        for topic in perplexity_response.topics:
            # Create a unique key for the topic
            topic_key = f"perplexity_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Generate embedding for the topic content
            topic_text = f"{topic.title} {topic.content}"
            topic_embedding = get_embedding(topic_text)
            
            # Create the topic document
            topic_doc = {
                "_key": topic_key,
                "title": topic.title,
                "content": topic.content,
                "confidence": topic.confidence,
                "rationale": topic.rationale,
                "source": topic.source,
                "query": query_text,
                "type": "perplexity_result",
                "timestamp": int(time.time()),
                "embedding": topic_embedding
            }
            
            # Insert the document
            doc_result = doc_collection.insert(topic_doc)
            created_docs.append(doc_result)
            
            # Create edges from the top search results to this topic
            top_results = search_results.get("results", [])[:3]  # Connect to top 3 results
            
            for result in top_results:
                doc_id = result.get("doc", {}).get("_id")
                if not doc_id:
                    continue
                
                # Create the edge
                edge = {
                    "_from": doc_id,
                    "_to": f"{document_collection}/{topic_key}",
                    "type": "related_web_content",
                    "confidence": topic.confidence,
                    "rationale": topic.rationale,
                    "timestamp": int(time.time())
                }
                
                # Insert the edge
                edge_result = edge_col.insert(edge)
                created_edges.append(edge_result)
        
        logger.info(f"Stored {len(created_docs)} topics with {len(created_edges)} relationships")
        
        # Add the created document info to the search results
        search_results["stored_perplexity"] = {
            "documents": created_docs,
            "edges": created_edges,
            "topics": [topic.dict() for topic in perplexity_response.topics],
            "summary": perplexity_response.summary
        }
        
        return search_results
    
    except Exception as e:
        logger.exception(f"Error storing Perplexity results: {e}")
        search_results["perplexity_storage_error"] = str(e)
        return search_results


def enrich_with_perplexity(db, query_text, search_results, top_n=3):
    """Perplexity API enrichment with structured output and storage."""
    try:
        if not HAS_LITELLM:
            raise ImportError("litellm package is required for Perplexity API calls")
            
        # Build context from top results
        context = ""
        for i, result in enumerate(search_results.get("results", [])[:top_n]):
            doc = result.get("doc", {})
            content = next((doc.get(f) for f in ["problem", "question", "solution"] if f in doc), "")
            if content:
                context += f"{i+1}. {content}\n"
        
        # Create enriched query
        prompt = f"""
        Query: '{query_text}'
        
        Context from my database:
        {context}
        
        Please provide additional relevant information that complements or expands on what I already know.
        Focus on facts that aren't mentioned in my database information.
        """
        
        # Make API call for structured data
        structured_response = call_perplexity_structured(prompt)
        
        # Store the results in the database
        search_results = store_perplexity_results(
            db=db,
            query_text=query_text,
            search_results=search_results,
            perplexity_response=structured_response
        )
        
        # Add basic enrichment info to response for display purposes
        search_results["enrichment"] = {
            "perplexity_content": structured_response.summary,
            "topics": [
                {
                    "title": topic.title,
                    "confidence": topic.confidence,
                    "content": topic.content[:100] + "..." if len(topic.content) > 100 else topic.content
                }
                for topic in structured_response.topics
            ]
        }
        
        return search_results
        
    except Exception as e:
        logger.error(f"Perplexity API error: {e}")
        search_results["perplexity_error"] = str(e)
        return search_results


def hybrid_search(
    db: StandardDatabase,
    query_text: str,
    collections: Optional[List[str]] = None,
    filter_expr: Optional[str] = None,
    tag_list: Optional[List[str]] = None,
    min_score: Optional[Dict[str, float]] = None,
    weights: Optional[Dict[str, float]] = None,
    top_n: int = 10,
    initial_k: int = 20,
    rrf_k: int = 60,
    output_format: str = "table",
    fields_to_return: Optional[List[str]] = None,
    require_all_tags: bool = False,
    use_graph: bool = False,
    graph_min_depth: int = 1,
    graph_max_depth: int = 1,
    graph_direction: str = "ANY",
    relationship_types: Optional[List[str]] = None,
    edge_collection_name: Optional[str] = None,
    use_perplexity: bool = False,
    fields_to_search: Optional[List[str]] = None  # Add field flexibility
) -> Dict[str, Any]:
    """
    Performs hybrid search by combining BM25, Semantic search, and optionally
    graph traversal results using Reciprocal Rank Fusion (RRF) for re-ranking.

    Args:
        db: ArangoDB database connection
        query_text: The user's search query
        collections: Optional list of collections to search in
        filter_expr: Optional AQL filter expression
        tag_list: Optional list of tags to filter results
        min_score: Dictionary of minimum scores for each search type (bm25, semantic)
        weights: Dictionary of weights for each search type (bm25, semantic, graph)
        top_n: The final number of ranked results to return
        initial_k: Number of results to initially fetch from BM25 and Semantic searches
        rrf_k: Constant used in the RRF calculation (default 60)
        output_format: Output format ("table" or "json")
        fields_to_return: Fields to include in the result
        require_all_tags: Whether all tags must be present (for tag filtering)
        use_graph: Whether to include graph traversal in the hybrid search
        graph_min_depth: Minimum traversal depth for graph search
        graph_max_depth: Maximum traversal depth for graph search
        graph_direction: Direction of traversal (OUTBOUND, INBOUND, ANY)
        relationship_types: Optional list of relationship types to filter
        edge_collection_name: Custom edge collection name (uses default if None)
        use_perplexity: Whether to enrich results with Perplexity API
        fields_to_search: Optional list of fields to search in text searches (BM25/keyword)

    Returns:
        A dictionary containing the ranked 'results', 'total' unique documents found,
        the 'query' for reference, and other metadata.
    """
    start_time = time.time()
    logger.info(f"Hybrid search for query: '{query_text}'")
    
    # Input validation
    if not query_text or query_text.strip() == "":
        error_msg = "Query text cannot be empty"
        logger.error(error_msg)
        return {
            "results": [],
            "total": 0,
            "query": "",
            "time": time.time() - start_time,
            "format": output_format,
            "error": error_msg,
            "search_engine": "hybrid-failed"
        }
    
    # Use default collection if not specified
    if not collections:
        collections = [COLLECTION_NAME]
    
    # Default fields to return if not provided
    if not fields_to_return:
        fields_to_return = ["_key", "_id", "question", "problem", "solution", "context", "tags", "label", "validated"]
    
    # Default minimum scores if not provided
    if not min_score:
        min_score = {
            "bm25": 0.1,
            "semantic": 0.7,
            "graph": 0.5
        }
    elif isinstance(min_score, float):
        min_score = {
            "bm25": min_score,
            "semantic": min_score,
            "graph": min_score
        }
    
    # Default weights if not provided
    if not weights:
        if use_graph:
            weights = {
                "bm25": 0.3,
                "semantic": 0.5,
                "graph": 0.2
            }
        else:
            weights = {
                "bm25": 0.5,
                "semantic": 0.5
            }
    
    # Ensure weights sum to 1.0
    total_weight = sum(weights.values())
    if total_weight != 1.0:
        logger.warning(f"Weights do not sum to 1.0 ({total_weight}), normalizing...")
        for key in weights:
            weights[key] = weights[key] / total_weight
    
    try:
        # STEP 1: Run tag search first if tags are provided to pre-filter the dataset
        tag_filtered_ids = None
        if tag_list and len(tag_list) > 0:
            logger.info(f"Pre-filtering by tags: {tag_list} (require_all_tags={require_all_tags})")
            tag_search_results = tag_search(
                db=db,
                tags=tag_list,
                collections=collections,
                filter_expr=filter_expr,
                require_all_tags=require_all_tags,
                limit=initial_k * 5,  # Get extra results to ensure enough after filtering
                output_format="json",
                fields_to_return=["_id", "_key"]  # Minimal fields for efficiency
            )
            
            if tag_search_results.get("results", []):
                tag_filtered_ids = {r["doc"]["_id"] for r in tag_search_results.get("results", [])}
                logger.info(f"Tag pre-filtering found {len(tag_filtered_ids)} matching documents")
                
                # If no documents matched the tag criteria, return empty results
                if not tag_filtered_ids:
                    logger.warning(f"No documents matched the specified tags: {tag_list}")
                    return {
                        "results": [],
                        "total": 0,
                        "query": query_text,
                        "time": time.time() - start_time,
                        "search_engine": "hybrid-tag-filtered",
                        "weights": weights,
                        "format": output_format,
                        "tags": tag_list,
                        "require_all_tags": require_all_tags
                    }
            else:
                logger.warning(f"Tag search returned no results for tags: {tag_list}")
                return {
                    "results": [],
                    "total": 0,
                    "query": query_text,
                    "time": time.time() - start_time,
                    "search_engine": "hybrid-tag-filtered",
                    "weights": weights,
                    "format": output_format,
                    "tags": tag_list,
                    "require_all_tags": require_all_tags
                }
        
        # Create a tag-specific filter expression if we're using tag-filtered IDs
        tag_filtered_filter_expr = filter_expr
        if tag_filtered_ids:
            # Create a filter that only includes documents in our tag-filtered set
            id_list_str = ", ".join([f"'{doc_id}'" for doc_id in tag_filtered_ids])
            tag_filter = f"doc._id IN [{id_list_str}]"
            
            # Combine with existing filter expression if needed
            if filter_expr:
                tag_filtered_filter_expr = f"({filter_expr}) AND {tag_filter}"
            else:
                tag_filtered_filter_expr = tag_filter
                
            logger.info(f"Created tag-filtered expression for {len(tag_filtered_ids)} documents")
        
        # STEP 2: Run BM25 search without tag filtering (we're using tag_filtered_filter_expr instead)
        bm25_time_start = time.time()
        bm25_results = bm25_search(
            db=db,
            query_text=query_text,
            collections=collections,
            filter_expr=tag_filtered_filter_expr,  # Use our combined filter
            min_score=min_score.get("bm25", 0.1),
            top_n=initial_k,
            tag_list=None,  # No tag filtering here, we've already handled it
            output_format="json",
            fields_to_search=fields_to_search  # Pass through optional fields
        )
        bm25_time = time.time() - bm25_time_start
        
        # Extract BM25 candidates
        bm25_candidates = bm25_results.get("results", [])
        logger.info(f"BM25 search found {len(bm25_candidates)} candidates in {bm25_time:.3f}s")
        
        # STEP 3: Run semantic search (without duplicate tag filtering)
        semantic_time_start = time.time()
        
        # Get embedding for query
        query_embedding = get_embedding(query_text)
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return {
                "results": [],
                "total": 0,
                "query": query_text,
                "time": time.time() - start_time,
                "error": "Failed to generate embedding for semantic search",
                "search_engine": "hybrid-failed",
                "format": output_format
            }
        
        semantic_results = semantic_search(
            db=db,
            query=query_text,
            collections=collections,
            filter_expr=tag_filtered_filter_expr,  # Use our combined filter
            min_score=min_score.get("semantic", 0.7),
            top_n=initial_k,
            tag_list=None,  # No tag filtering here, we've already handled it
            output_format="json"
        )
        semantic_time = time.time() - semantic_time_start
        
        # Extract semantic candidates
        semantic_candidates = semantic_results.get("results", [])
        logger.info(f"Semantic search found {len(semantic_candidates)} candidates in {semantic_time:.3f}s")
        
        # STEP 4: Run graph traversal search if enabled
        graph_candidates = []
        graph_time = 0
        
        if use_graph:
            logger.info(f"Running graph traversal search (depth: {graph_min_depth}-{graph_max_depth}, direction: {graph_direction})")
            graph_time_start = time.time()
            
            # Use default or custom edge collection
            edge_col = edge_collection_name or EDGE_COLLECTION_NAME
            
            # Check if edge collection exists
            if not db.has_collection(edge_col):
                logger.warning(f"Edge collection '{edge_col}' does not exist, skipping graph search")
            else:
                # Run graph traversal search
                graph_results = graph_rag_search(
                    db=db,
                    query_text=query_text,
                    min_depth=graph_min_depth,
                    max_depth=graph_max_depth,
                    direction=graph_direction,
                    relationship_types=relationship_types,
                    min_score=min_score.get("graph", 0.5),
                    top_n=initial_k,
                    output_format="json",
                    fields_to_return=fields_to_return,
                    edge_collection_name=edge_col,
                    filter_expr=tag_filtered_filter_expr  # Use our combined filter
                )
                
                # Extract graph candidates
                graph_candidates = graph_results.get("results", [])
                
                # Process related documents to add them as candidates
                # Create a copy of the original candidates to avoid modifying during iteration
                original_graph_candidates = list(graph_candidates)
                
                for result in original_graph_candidates:
                    # Add related documents as candidates
                    related_docs = result.get("related", [])
                    for related in related_docs:
                        vertex = related.get("vertex", {})
                        if vertex:
                            # Add as a graph candidate with a reduced score from the original document
                            graph_candidates.append({
                                "doc": vertex,
                                "score": result.get("score", 0) * 0.8  # Slightly reduce score for related docs
                            })
                
                logger.info(f"Graph search found {len(graph_candidates)} candidates (including related docs)")
            
            graph_time = time.time() - graph_time_start
        
        # STEP 5: Combine results using weighted RRF
        combined_weights = weights
        logger.info(f"Combining results with weights: {combined_weights}")
        
        if use_graph and graph_candidates:
            combined_results = weighted_reciprocal_rank_fusion_with_graph(
                bm25_candidates=bm25_candidates,
                semantic_candidates=semantic_candidates,
                graph_candidates=graph_candidates,
                weights=combined_weights,
                rrf_k=rrf_k
            )
        else:
            combined_results = weighted_reciprocal_rank_fusion(
                bm25_candidates=bm25_candidates,
                semantic_candidates=semantic_candidates,
                weights=combined_weights,
                rrf_k=rrf_k
            )
        
        # Remove any potential duplicate entries that might slip through
        # (unlikely but possible with semantic + graph combined results)
        unique_results = {}
        for result in combined_results:
            doc_key = result.get("doc", {}).get("_key", "")
            if doc_key and doc_key not in unique_results:
                unique_results[doc_key] = result
        
        # Convert back to list and sort by hybrid score
        final_results = list(unique_results.values())
        final_results.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
        
        # STEP 6: Limit to top_n results
        final_results = final_results[:top_n]
        logger.info(f"Final results: {len(final_results)} documents")
        
        search_time = time.time() - start_time
        
        # Build the response
        response = {
            "results": final_results,
            "total": len(combined_results),
            "query": query_text,
            "time": search_time,
            "bm25_time": bm25_time,
            "semantic_time": semantic_time,
            "search_engine": "hybrid-bm25-semantic",
            "weights": weights,
            "format": output_format,
            "tags": tag_list,
            "require_all_tags": require_all_tags if tag_list else None
        }
        
        # Add graph search info if used
        if use_graph:
            response["graph_time"] = graph_time
            response["search_engine"] = "hybrid-bm25-semantic-graph"
            response["graph_params"] = {
                "min_depth": graph_min_depth,
                "max_depth": graph_max_depth,
                "direction": graph_direction,
                "relationship_types": relationship_types
            }
        
        # Add Perplexity enrichment if requested
        if use_perplexity and HAS_LITELLM and final_results:
            logger.info(f"Enriching search results with Perplexity API")
            response = enrich_with_perplexity(db, query_text, response)
        
        return response
    
    except Exception as e:
        logger.exception(f"Hybrid search error: {e}")
        return {
            "results": [],
            "total": 0,
            "query": query_text,
            "time": time.time() - start_time,
            "error": str(e),
            "search_engine": "hybrid-failed",
            "format": output_format
        }


def weighted_reciprocal_rank_fusion(
    bm25_candidates: List[Dict[str, Any]],
    semantic_candidates: List[Dict[str, Any]],
    weights: Dict[str, float] = None,
    rrf_k: int = 60
) -> List[Dict[str, Any]]:
    """
    Combines multiple result lists using Weighted Reciprocal Rank Fusion.

    Args:
        bm25_candidates: Results from BM25 search
        semantic_candidates: Results from semantic search
        weights: Dictionary of weights for each search type
        rrf_k: Constant for the RRF formula (default: 60)

    Returns:
        A combined list of results, sorted by hybrid score
    """
    if weights is None:
        weights = {
            "bm25": 0.5,
            "semantic": 0.5
        }
    
    # Create a dictionary to track document keys and their rankings
    doc_scores = {}

    # Process BM25 results
    bm25_weight = weights.get("bm25", 0.5)
    for rank, result in enumerate(bm25_candidates, 1):
        doc_key = result.get("doc", {}).get("_key", "")
        if not doc_key:
            continue

        # Initialize if not seen before
        if doc_key not in doc_scores:
            doc_scores[doc_key] = {
                "doc": result.get("doc", {}),
                "bm25_rank": rank,
                "bm25_score": result.get("score", 0),
                "semantic_rank": len(semantic_candidates) + 1,  # Default to worst possible rank
                "semantic_score": 0,
                "hybrid_score": 0
            }
        else:
            # Update BM25 rank info
            doc_scores[doc_key]["bm25_rank"] = rank
            doc_scores[doc_key]["bm25_score"] = result.get("score", 0)

    # Process semantic results
    semantic_weight = weights.get("semantic", 0.5)
    for rank, result in enumerate(semantic_candidates, 1):
        doc_key = result.get("doc", {}).get("_key", "")
        if not doc_key:
            continue

        # Initialize if not seen before
        if doc_key not in doc_scores:
            doc_scores[doc_key] = {
                "doc": result.get("doc", {}),
                "bm25_rank": len(bm25_candidates) + 1,  # Default to worst possible rank
                "bm25_score": 0,
                "semantic_rank": rank,
                "semantic_score": result.get("similarity_score", 0),
                "hybrid_score": 0
            }
        else:
            # Update semantic rank info
            doc_scores[doc_key]["semantic_rank"] = rank
            doc_scores[doc_key]["semantic_score"] = result.get("similarity_score", 0)

    # Calculate weighted RRF scores
    for doc_key, scores in doc_scores.items():
        # Calculate individual RRF scores
        bm25_rrf = 1 / (rrf_k + scores["bm25_rank"])
        semantic_rrf = 1 / (rrf_k + scores["semantic_rank"])
        
        # Apply weights
        weighted_bm25 = bm25_rrf * bm25_weight
        weighted_semantic = semantic_rrf * semantic_weight
        
        # Calculate hybrid score
        scores["hybrid_score"] = weighted_bm25 + weighted_semantic

    # Convert to list and sort by hybrid score (descending)
    result_list = [v for k, v in doc_scores.items()]
    result_list.sort(key=lambda x: x["hybrid_score"], reverse=True)

    return result_list


def weighted_reciprocal_rank_fusion_with_graph(
    bm25_candidates: List[Dict[str, Any]],
    semantic_candidates: List[Dict[str, Any]],
    graph_candidates: List[Dict[str, Any]],
    weights: Dict[str, float] = None,
    rrf_k: int = 60
) -> List[Dict[str, Any]]:
    """
    Combines multiple result lists including graph traversal using Weighted RRF.

    Args:
        bm25_candidates: Results from BM25 search
        semantic_candidates: Results from semantic search
        graph_candidates: Results from graph traversal search
        weights: Dictionary of weights for each search type
        rrf_k: Constant for the RRF formula (default: 60)

    Returns:
        A combined list of results, sorted by hybrid score
    """
    if weights is None:
        weights = {
            "bm25": 0.4,
            "semantic": 0.4,
            "graph": 0.2
        }
    
    # Create a dictionary to track document keys and their rankings
    doc_scores = {}

    # Process BM25 results
    bm25_weight = weights.get("bm25", 0.4)
    for rank, result in enumerate(bm25_candidates, 1):
        doc_key = result.get("doc", {}).get("_key", "")
        if not doc_key:
            continue

        # Initialize if not seen before
        if doc_key not in doc_scores:
            doc_scores[doc_key] = {
                "doc": result.get("doc", {}),
                "bm25_rank": rank,
                "bm25_score": result.get("score", 0),
                "semantic_rank": len(semantic_candidates) + 1,  # Default to worst possible rank
                "semantic_score": 0,
                "graph_rank": len(graph_candidates) + 1,  # Default to worst possible rank
                "graph_score": 0,
                "hybrid_score": 0
            }
        else:
            # Update BM25 rank info
            doc_scores[doc_key]["bm25_rank"] = rank
            doc_scores[doc_key]["bm25_score"] = result.get("score", 0)

    # Process semantic results
    semantic_weight = weights.get("semantic", 0.4)
    for rank, result in enumerate(semantic_candidates, 1):
        doc_key = result.get("doc", {}).get("_key", "")
        if not doc_key:
            continue

        # Initialize if not seen before
        if doc_key not in doc_scores:
            doc_scores[doc_key] = {
                "doc": result.get("doc", {}),
                "bm25_rank": len(bm25_candidates) + 1,  # Default to worst possible rank
                "bm25_score": 0,
                "semantic_rank": rank,
                "semantic_score": result.get("similarity_score", 0),
                "graph_rank": len(graph_candidates) + 1,  # Default to worst possible rank
                "graph_score": 0,
                "hybrid_score": 0
            }
        else:
            # Update semantic rank info
            doc_scores[doc_key]["semantic_rank"] = rank
            doc_scores[doc_key]["semantic_score"] = result.get("similarity_score", 0)
    
    # Process graph results
    graph_weight = weights.get("graph", 0.2)
    for rank, result in enumerate(graph_candidates, 1):
        doc_key = result.get("doc", {}).get("_key", "")
        if not doc_key:
            continue

        # Initialize if not seen before
        if doc_key not in doc_scores:
            doc_scores[doc_key] = {
                "doc": result.get("doc", {}),
                "bm25_rank": len(bm25_candidates) + 1,  # Default to worst possible rank
                "bm25_score": 0,
                "semantic_rank": len(semantic_candidates) + 1,  # Default to worst possible rank
                "semantic_score": 0,
                "graph_rank": rank,
                "graph_score": result.get("score", 0),
                "hybrid_score": 0
            }
        else:
            # Update graph rank info
            doc_scores[doc_key]["graph_rank"] = rank
            doc_scores[doc_key]["graph_score"] = result.get("score", 0)

    # Calculate weighted RRF scores
    for doc_key, scores in doc_scores.items():
        # Calculate individual RRF scores
        bm25_rrf = 1 / (rrf_k + scores["bm25_rank"])
        semantic_rrf = 1 / (rrf_k + scores["semantic_rank"])
        graph_rrf = 1 / (rrf_k + scores["graph_rank"])
        
        # Apply weights
        weighted_bm25 = bm25_rrf * bm25_weight
        weighted_semantic = semantic_rrf * semantic_weight
        weighted_graph = graph_rrf * graph_weight
        
        # Calculate hybrid score
        scores["hybrid_score"] = weighted_bm25 + weighted_semantic + weighted_graph

    # Convert to list and sort by hybrid score (descending)
    result_list = [v for k, v in doc_scores.items()]
    result_list.sort(key=lambda x: x["hybrid_score"], reverse=True)

    return result_list


def print_hybrid_search_results(search_results: Dict[str, Any], max_width: int = 120) -> None:
    """
    Simple helper to print search result counts.
    
    Args:
        search_results: The search results to display
        max_width: Maximum width for text fields in characters (unused)
    """
    result_count = len(search_results.get("results", []))
    query = search_results.get("query", "")
    search_engine = search_results.get("search_engine", "hybrid")
    search_time = search_results.get("time", 0)
    
    print(f"Found {result_count} results for query '{query}'")
    print(f"Search engine: {search_engine}, Time: {search_time:.3f}s")


def search_with_config(
    db: StandardDatabase,
    query_text: str,
    config: Optional[SearchConfig] = None,
    collections: Optional[List[str]] = None,
    output_format: str = "json"
) -> Dict[str, Any]:
    """
    Performs search using configuration to determine strategy.
    
    Args:
        db: ArangoDB database connection
        query_text: The user's search query
        config: SearchConfig object (uses default if None)
        collections: Optional list of collections to search in
        output_format: Output format ("table" or "json")
        
    Returns:
        Search results dictionary
    """
    # Use default config if none provided
    if config is None:
        manager = SearchConfigManager()
        config = manager.get_config_for_query(query_text)
    
    # Route to appropriate search method based on config
    if config.preferred_method == SearchMethod.BM25:
        # BM25 search only
        return bm25_search(
            db=db,
            query_text=query_text,
            collections=collections,
            filter_expr=config.metadata_filters.get("filter_expr"),
            tag_list=config.tags,
            min_score=config.min_score or 0.1,
            top_n=config.result_limit,
            output_format=output_format,
            fields_to_search=config.metadata_filters.get("fields_to_search")
        )
    
    elif config.preferred_method == SearchMethod.SEMANTIC:
        # Semantic search only
        return semantic_search(
            db=db,
            query=query_text,
            collections=collections,
            filter_expr=config.metadata_filters.get("filter_expr"),
            min_score=config.min_score or 0.7,
            top_n=config.result_limit,
            tag_list=config.tags,
            output_format=output_format
        )
    
    elif config.preferred_method == SearchMethod.TAG:
        # Tag search only
        return tag_search(
            db=db,
            tags=config.tags or [],
            collections=collections,
            filter_expr=config.metadata_filters.get("filter_expr"),
            require_all_tags=config.metadata_filters.get("require_all_tags", False),
            limit=config.result_limit,
            output_format=output_format,
            fields_to_return=config.metadata_filters.get("fields_to_return")
        )
    
    elif config.preferred_method == SearchMethod.GRAPH:
        # Graph traversal search
        return graph_rag_search(
            db=db,
            query_text=query_text,
            min_depth=1,
            max_depth=config.graph_depth,
            top_n=config.result_limit,
            output_format=output_format,
            fields_to_return=config.metadata_filters.get("fields_to_return")
        )
    
    elif config.preferred_method == SearchMethod.HYBRID:
        # Hybrid search with configuration
        min_score = {}
        if config.min_score:
            min_score = {
                "bm25": config.min_score,
                "semantic": config.min_score,
                "graph": config.min_score
            }
        
        weights = {
            "bm25": config.bm25_weight,
            "semantic": config.semantic_weight
        }
        
        if config.include_graph_context:
            weights["graph"] = 1.0 - config.bm25_weight - config.semantic_weight
        
        return hybrid_search(
            db=db,
            query_text=query_text,
            collections=collections,
            filter_expr=config.metadata_filters.get("filter_expr"),
            tag_list=config.tags,
            min_score=min_score,
            weights=weights,
            top_n=config.result_limit,
            initial_k=config.rerank_top_k,
            output_format=output_format,
            fields_to_return=config.metadata_filters.get("fields_to_return"),
            use_graph=config.include_graph_context,
            graph_max_depth=config.graph_depth,
            fields_to_search=config.metadata_filters.get("fields_to_search")
        )
    
    else:
        # Default to hybrid if method not recognized
        return hybrid_search(
            db=db,
            query_text=query_text,
            collections=collections,
            top_n=config.result_limit,
            output_format=output_format
        )


def validate_hybrid_search(search_results: Dict[str, Any]) -> bool:
    """
    Validate basic hybrid search results structure.
    
    Args:
        search_results: Search results to validate
        
    Returns:
        True if validation passes, False otherwise
    """
    # Check for required fields
    if "results" not in search_results:
        logger.error("No 'results' field in search results")
        return False
        
    if "total" not in search_results:
        logger.error("No 'total' field in search results")
        return False
        
    if "search_engine" not in search_results:
        logger.warning("No 'search_engine' field in search results")
        
    # Check if there was an error
    if "error" in search_results:
        logger.error(f"Search error: {search_results['error']}")
        return False
    
    # Verify at least one search score exists in the first result (if results exist)
    results = search_results.get("results", [])
    if results:
        first_result = results[0]
        if not any(key in first_result for key in ["hybrid_score", "bm25_score", "semantic_score", "graph_score"]):
            logger.error("No score fields found in results")
            return False
        
    return True


if __name__ == "__main__":
    """
    Simple usage function to verify the module works with real data.
    """
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:HH:mm:ss} | {level:<7} | {message}"
    )
    
    # Set up database connection
    from arango import ArangoClient
    from arangodb.core.constants import ARANGO_HOST, ARANGO_DB_NAME, ARANGO_USER, ARANGO_PASSWORD, COLLECTION_NAME, SEARCH_FIELDS
    from arangodb.core.arango_setup import ensure_arangosearch_view
    
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    # Ensure test collection exists
    if not db.has_collection(COLLECTION_NAME):
        db.create_collection(COLLECTION_NAME)
    
    # Add test document if collection is empty
    collection = db.collection(COLLECTION_NAME)
    if collection.count() == 0:
        # Create document with text content
        doc = {
            "content": "This is a test document for hybrid search with BM25 and vector embeddings",
            "tags": ["test", "search", "hybrid", "bm25", "vector"]
        }
        
        # Get embedding for content
        doc_embedding = get_embedding(doc["content"])
        if doc_embedding:
            doc[EMBEDDING_FIELD] = doc_embedding
            collection.insert(doc)
            print(f"Created test document in {COLLECTION_NAME}")
        else:
            print("Failed to generate embedding for test document")
            sys.exit(1)
    
    # Ensure search view exists
    ensure_arangosearch_view(db, VIEW_NAME, COLLECTION_NAME, SEARCH_FIELDS)
    
    # Prepare weights for hybrid search
    weights = {"bm25": 0.6, "semantic": 0.4}
    
    # Perform a simple search
    query_text = "hybrid search test"
    print(f"Testing hybrid search functionality with query: '{query_text}'")
    result = hybrid_search(
        db=db,
        query_text=query_text,
        collections=[COLLECTION_NAME],
        weights=weights,
        min_score={"bm25": 0.1, "semantic": 0.5},
        top_n=5
    )
    
    # Verify we got results
    if result["total"] > 0 and len(result["results"]) > 0:
        print(f"✅ VALIDATION PASSED: Hybrid search returned {result['total']} results")
        print(f"First result hybrid score: {result['results'][0].get('hybrid_score', 0):.2f}")
        
        # Show component scores if available
        first_result = result["results"][0]
        if "bm25_score" in first_result:
            print(f"BM25 component score: {first_result['bm25_score']:.2f}")
        if "semantic_score" in first_result:
            print(f"Semantic component score: {first_result['semantic_score']:.2f}")
    else:
        print(f"❌ VALIDATION FAILED: No results returned for test query")
        sys.exit(1)
    
    # Verify search metadata
    if "search_engine" in result and "hybrid" in result["search_engine"]:
        print("✅ Search metadata correctly populated")
    else:
        print("❌ Search metadata validation failed")
        sys.exit(1)
    
    print(f"Hybrid search completed in {result.get('time', 0):.3f}s")
    sys.exit(0)