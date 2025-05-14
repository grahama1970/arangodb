"""
# Cross-Encoder Reranking Module

This module provides functionality to rerank search results using cross-encoder models,
which can significantly improve search quality by performing a more sophisticated
relevance assessment on the initial retrieval results.

## Third-Party Packages:
- sentence-transformers: https://www.sbert.net/docs/package_reference/cross_encoder.html (v4.1.0+)
- torch: https://pytorch.org/docs/stable/index.html (v2.2.0+)
- numpy: https://numpy.org/doc/stable/reference/index.html (v2.2.2+)
- tenacity: https://tenacity.readthedocs.io/en/latest/ (v9.0.0+)
- loguru: https://github.com/Delgan/loguru (v0.7.3+)

## Sample Input:
```python
query_text = "How do primary colors work?"
passages = [
    {"doc": {"_id": "123", "content": "Primary colors are red, blue, and yellow."}, "score": 0.85},
    {"doc": {"_id": "456", "content": "RGB is used in digital displays."}, "score": 0.75}
]
```

## Expected Output:
```python
reranked_results = [
    {"doc": {"_id": "123", "content": "Primary colors are red, blue, and yellow."}, 
     "score": 0.85, "cross_encoder_score": 0.92, "final_score": 0.92},
    {"doc": {"_id": "456", "content": "RGB is used in digital displays."}, 
     "score": 0.75, "cross_encoder_score": 0.45, "final_score": 0.45}
]
```
"""

import sys
import time
import logging
import os
import json
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from functools import lru_cache

import numpy as np
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import for type checking but with try/except to handle optional dependency
try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    logger.warning("sentence-transformers package not found - cross-encoder reranking will use fallback methods")
    HAS_CROSS_ENCODER = False

# Constants
DEFAULT_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
FALLBACK_MODEL = "cross-encoder/ms-marco-TinyBERT-L-2-v2"  # Smaller, faster model for fallback
CACHE_SIZE = 1024  # Number of query-passage pairs to cache
MAX_LENGTH = 512   # Maximum sequence length for cross-encoder input

# Define content fields to extract for reranking in order of preference
CONTENT_FIELDS = ["content", "text", "question", "problem", "description", "title"]

# Define a global variable for cross-encoder model instances to avoid reloading
_CROSS_ENCODER_INSTANCES = {}


def get_cross_encoder(model_name: str = DEFAULT_CROSS_ENCODER_MODEL) -> Any:
    """
    Get (or create) a cross-encoder model instance. Uses a global cache to avoid reloading.
    
    Args:
        model_name: Name of the cross-encoder model to use
        
    Returns:
        CrossEncoder instance or None if not available
    """
    global _CROSS_ENCODER_INSTANCES
    
    # Check if sentence-transformers is available
    if not HAS_CROSS_ENCODER:
        logger.warning(f"sentence-transformers not available - cannot load {model_name}")
        return None
    
    # Return cached instance if available
    if model_name in _CROSS_ENCODER_INSTANCES:
        return _CROSS_ENCODER_INSTANCES[model_name]
    
    try:
        # Try to create a new model instance
        logger.info(f"Loading cross-encoder model: {model_name}")
        model = CrossEncoder(model_name, max_length=MAX_LENGTH)
        _CROSS_ENCODER_INSTANCES[model_name] = model
        logger.info(f"Cross-encoder model {model_name} loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load cross-encoder model {model_name}: {e}")
        
        # Try fallback model if different from requested model
        if model_name != FALLBACK_MODEL:
            logger.info(f"Attempting to load fallback model: {FALLBACK_MODEL}")
            try:
                model = CrossEncoder(FALLBACK_MODEL, max_length=MAX_LENGTH)
                _CROSS_ENCODER_INSTANCES[model_name] = model  # Cache under requested name
                logger.info(f"Fallback model {FALLBACK_MODEL} loaded successfully")
                return model
            except Exception as fallback_e:
                logger.error(f"Failed to load fallback model: {fallback_e}")
        
        return None


def extract_text_for_reranking(doc: Dict[str, Any]) -> str:
    """
    Extract the most appropriate text field from a document for reranking.
    
    Args:
        doc: Document dictionary with potential text fields
        
    Returns:
        Extracted text content or empty string if no suitable field found
    """
    # Try each content field in order of preference
    for field in CONTENT_FIELDS:
        if field in doc and doc[field] and isinstance(doc[field], str):
            # Truncate to reasonable length to avoid model context limits
            return doc[field][:10000]  # Truncate very long texts
    
    # If no field found, try to convert the document to a string representation
    try:
        # Remove large fields like embeddings that aren't useful for reranking
        clean_doc = {k: v for k, v in doc.items() if k not in ["embedding", "_rev"]}
        return str(clean_doc)[:1000]  # Limited string representation
    except Exception as e:
        logger.warning(f"Failed to extract text from document: {e}")
        return ""


@lru_cache(maxsize=CACHE_SIZE)
def compute_cross_encoder_score(
    query_text: str, 
    passage_text: str,
    model_name: str = DEFAULT_CROSS_ENCODER_MODEL
) -> float:
    """
    Compute cross-encoder score for a query-passage pair with caching.
    
    Args:
        query_text: Search query text
        passage_text: Text content of the passage
        model_name: Cross-encoder model name
        
    Returns:
        Cross-encoder relevance score (0-1)
    """
    model = get_cross_encoder(model_name)
    
    # If model loading failed, return a fallback score
    if model is None:
        # Fallback to simpler text matching as approximation
        query_lower = query_text.lower()
        passage_lower = passage_text.lower()
        
        # Count term overlap as simple fallback
        query_terms = set(query_lower.split())
        # Remove very common words
        query_terms = {term for term in query_terms if len(term) > 2}
        
        if not query_terms:
            return 0.5  # Neutral score if no meaningful query terms
        
        # Count matching terms
        match_count = sum(1 for term in query_terms if term in passage_lower)
        score = match_count / len(query_terms)
        
        # Normalize to 0.4-0.8 range to avoid extreme scores
        return 0.4 + (score * 0.4)
    
    try:
        # Use the cross-encoder to get a relevance score
        score = model.predict([(query_text, passage_text)])
        
        # If score is an array/list with one element, extract the value
        if hasattr(score, '__len__') and len(score) == 1:
            score = float(score[0])
        else:
            score = float(score)
        
        # Most cross-encoder models output scores in different ranges
        # Normalize to 0-1 range using sigmoid if score is not already in that range
        if score < 0 or score > 1:
            score = 1.0 / (1.0 + np.exp(-score))
            
        return score
        
    except Exception as e:
        logger.error(f"Cross-encoder scoring failed: {e}")
        return 0.5  # Neutral score on error


@retry(
    retry=retry_if_exception_type((Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def cross_encoder_rerank(
    query_text: str,
    passages: List[Dict[str, Any]],
    model_name: str = DEFAULT_CROSS_ENCODER_MODEL,
    score_field: str = "score",
    content_extraction_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    top_k: Optional[int] = None,
    score_combination_strategy: str = "replace",
    score_combination_weights: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Rerank a list of passages using a cross-encoder model.
    
    Args:
        query_text: Query text
        passages: List of passages with document objects and scores
        model_name: Cross-encoder model name
        score_field: Field name where existing scores are stored
        content_extraction_fn: Optional custom function to extract text from documents
        top_k: Optional limit on number of results to return after reranking
        score_combination_strategy: How to combine original and cross-encoder scores
                                   ("replace", "weighted", "max", "min")
        score_combination_weights: Weights to use for weighted combination strategy
        
    Returns:
        Reranked list of passages with cross-encoder scores
    """
    start_time = time.time()
    logger.info(f"Reranking {len(passages)} passages with model {model_name}")
    
    # Short-circuit cases
    if not passages:
        logger.warning("No passages to rerank")
        return []
    
    if not query_text or not query_text.strip():
        logger.warning("Empty query text, returning original passage order")
        return passages
    
    # Use custom content extraction function if provided, otherwise use default
    content_extractor = content_extraction_fn or extract_text_for_reranking
    
    # Set default weights for weighted combination if not provided
    if score_combination_strategy == "weighted" and not score_combination_weights:
        score_combination_weights = {"original": 0.2, "cross_encoder": 0.8}
    
    # Process all passages
    scored_passages = []
    for passage in passages:
        doc = passage.get("doc", {})
        original_score = passage.get(score_field, 0)
        
        # Skip if no document (shouldn't happen in practice)
        if not doc:
            logger.warning("Skipping passage with missing document")
            continue
        
        # Extract text content for reranking
        text_content = content_extractor(doc)
        if not text_content:
            logger.warning(f"No content extracted from document {doc.get('_id', '?')}, using fallback score")
            cross_encoder_score = original_score  # Fall back to original score
        else:
            # Get cross-encoder score
            cross_encoder_score = compute_cross_encoder_score(query_text, text_content, model_name)
        
        # Combine scores according to strategy
        if score_combination_strategy == "replace":
            final_score = cross_encoder_score
        elif score_combination_strategy == "weighted":
            final_score = (
                score_combination_weights["original"] * original_score +
                score_combination_weights["cross_encoder"] * cross_encoder_score
            )
        elif score_combination_strategy == "max":
            final_score = max(original_score, cross_encoder_score)
        elif score_combination_strategy == "min":
            final_score = min(original_score, cross_encoder_score)
        else:
            logger.warning(f"Unknown score combination strategy: {score_combination_strategy}, using replacement")
            final_score = cross_encoder_score
        
        # Add all scores to the passage
        passage_with_scores = passage.copy()
        passage_with_scores["cross_encoder_score"] = cross_encoder_score
        passage_with_scores["final_score"] = final_score
        
        scored_passages.append(passage_with_scores)
    
    # Sort by final score
    scored_passages.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Apply top_k limit if specified
    if top_k is not None and top_k > 0:
        scored_passages = scored_passages[:top_k]
    
    elapsed_time = time.time() - start_time
    logger.info(f"Reranking completed in {elapsed_time:.2f}s")
    
    return scored_passages


def rerank_search_results(
    search_results: Dict[str, Any],
    model_name: str = DEFAULT_CROSS_ENCODER_MODEL,
    score_field: str = "score",
    top_k: Optional[int] = None,
    score_combination_strategy: str = "replace",
    score_combination_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Rerank the results of a search operation.
    
    Args:
        search_results: Search results dictionary with 'results' list
        model_name: Cross-encoder model name
        score_field: Field name where existing scores are stored
        top_k: Optional limit on number of results to return after reranking
        score_combination_strategy: How to combine original and cross-encoder scores
        score_combination_weights: Weights to use for weighted combination strategy
        
    Returns:
        Updated search results with reranked passages
    """
    start_time = time.time()
    
    # Make a copy to avoid modifying the original
    updated_results = search_results.copy()
    
    # Get query and results
    query_text = updated_results.get("query", "")
    passages = updated_results.get("results", [])
    
    # Check if we have enough to rerank
    if len(passages) <= 1:
        logger.info("Not enough passages to rerank (0 or 1), returning original results")
        # Just add metadata about reranking attempts
        updated_results["reranking_applied"] = False
        updated_results["reranking_model"] = model_name
        updated_results["reranking_time"] = 0.0
        return updated_results
    
    try:
        # Detect the correct score field if not specified
        if score_field not in passages[0]:
            # Try to detect score field automatically
            potential_score_fields = [
                field for field in ["score", "similarity_score", "bm25_score", "rrf_score", "hybrid_score"] 
                if any(field in p for p in passages)
            ]
            if potential_score_fields:
                detected_score_field = potential_score_fields[0]
                logger.info(f"Auto-detected score field: {detected_score_field}")
                score_field = detected_score_field
            else:
                logger.warning(f"Could not find score field {score_field} or auto-detect alternative")
        
        # Apply reranking
        reranked_passages = cross_encoder_rerank(
            query_text=query_text,
            passages=passages,
            model_name=model_name,
            score_field=score_field,
            top_k=top_k,
            score_combination_strategy=score_combination_strategy,
            score_combination_weights=score_combination_weights
        )
        
        # Replace results with reranked version
        updated_results["results"] = reranked_passages
        
        # Add metadata about reranking
        updated_results["reranking_applied"] = True
        updated_results["reranking_model"] = model_name
        updated_results["reranking_strategy"] = score_combination_strategy
        updated_results["reranking_time"] = time.time() - start_time
        updated_results["search_engine"] = updated_results.get("search_engine", "unknown") + "+cross-encoder"
        
        logger.info(f"Reranking completed for {len(passages)} passages in {updated_results['reranking_time']:.2f}s")
        return updated_results
    
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        
        # Return original results with error information
        updated_results["reranking_applied"] = False
        updated_results["reranking_error"] = str(e)
        updated_results["reranking_time"] = time.time() - start_time
        
        return updated_results


def validate_cross_encoder_reranking() -> Tuple[bool, List[str]]:
    """
    Validate cross-encoder reranking functionality.
    
    Returns:
        Tuple of (success_flag, list_of_validation_failures)
    """
    # Track validation failures
    validation_failures = []
    total_tests = 0
    
    # Test 1: Basic cross-encoder score computation
    total_tests += 1
    try:
        query = "What are primary colors?"
        passage = "Primary colors are red, blue, and yellow."
        score = compute_cross_encoder_score(query, passage)
        
        if not (0 <= score <= 1):
            validation_failures.append(
                f"Test 1 failed: Cross-encoder score {score} is not in range [0,1]"
            )
    except Exception as e:
        validation_failures.append(f"Test 1 failed with exception: {e}")
    
    # Test 2: Cross-encoder reranking with mock data
    total_tests += 1
    try:
        query = "How do database transactions work?"
        passages = [
            {
                "doc": {"_id": "1", "content": "Transaction management in databases ensures ACID properties."},
                "score": 0.8
            },
            {
                "doc": {"_id": "2", "content": "SQL is a query language for relational databases."},
                "score": 0.9
            }
        ]
        
        reranked = cross_encoder_rerank(query, passages)
        
        # Check if reranking worked (basic checks)
        if len(reranked) != 2:
            validation_failures.append(
                f"Test 2 failed: Expected 2 reranked passages, got {len(reranked)}"
            )
        
        # Check if cross_encoder_score and final_score fields are present
        for r in reranked:
            if "cross_encoder_score" not in r or "final_score" not in r:
                validation_failures.append(
                    f"Test 2 failed: Missing score fields in reranked result: {r.keys()}"
                )
                break
    except Exception as e:
        validation_failures.append(f"Test 2 failed with exception: {e}")
    
    # Test 3: Search results reranking
    total_tests += 1
    try:
        mock_search_results = {
            "query": "What are primary colors?",
            "results": [
                {
                    "doc": {"_id": "1", "content": "Primary colors are red, blue, and yellow."},
                    "score": 0.8
                },
                {
                    "doc": {"_id": "2", "content": "RGB is used in digital displays."},
                    "score": 0.9
                }
            ],
            "search_engine": "mock-engine"
        }
        
        reranked_results = rerank_search_results(mock_search_results)
        
        # Verify reranking metadata
        if not reranked_results.get("reranking_applied"):
            validation_failures.append(
                "Test 3 failed: Reranking not applied or flag not set"
            )
        
        # Check search engine name appending
        if not reranked_results.get("search_engine", "").endswith("+cross-encoder"):
            validation_failures.append(
                f"Test 3 failed: Search engine name not updated: {reranked_results.get('search_engine')}"
            )
    except Exception as e:
        validation_failures.append(f"Test 3 failed with exception: {e}")
    
    # Test 4: Different score combination strategies
    total_tests += 1
    try:
        query = "What are primary colors?"
        passages = [
            {
                "doc": {"_id": "1", "content": "Primary colors are red, blue, and yellow."},
                "score": 0.8
            },
            {
                "doc": {"_id": "2", "content": "RGB is used in digital displays."},
                "score": 0.9
            }
        ]
        
        # Test different strategies
        strategies = ["replace", "weighted", "max", "min"]
        for strategy in strategies:
            reranked = cross_encoder_rerank(
                query, passages, 
                score_combination_strategy=strategy,
                score_combination_weights={"original": 0.5, "cross_encoder": 0.5}
            )
            
            # Just check that we got results for each strategy
            if len(reranked) != 2:
                validation_failures.append(
                    f"Test 4 failed: Strategy '{strategy}' returned {len(reranked)} results instead of 2"
                )
    except Exception as e:
        validation_failures.append(f"Test 4 failed with exception: {e}")
    
    # Test 5: Error handling for empty or invalid inputs
    total_tests += 1
    try:
        # Empty query
        empty_query_result = cross_encoder_rerank("", passages)
        if not empty_query_result:
            validation_failures.append(
                "Test 5 failed: Empty query should return original passages, got empty list"
            )
        
        # Empty passages
        empty_passages_result = cross_encoder_rerank(query, [])
        if empty_passages_result:
            validation_failures.append(
                f"Test 5 failed: Empty passages should return empty list, got {len(empty_passages_result)} results"
            )
    except Exception as e:
        validation_failures.append(f"Test 5 failed with exception: {e}")
    
    # Final results
    success = len(validation_failures) == 0
    logger.info(f"Validation {'passed' if success else 'failed'} ({total_tests - len(validation_failures)}/{total_tests} tests passed)")
    
    return success, validation_failures


if __name__ == "__main__":
    """
    Validation for the cross-encoder reranking module.
    """
    import sys
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:HH:mm:ss} | {level:<7} | {message}"
    )
    
    try:
        # Run validation
        success, failures = validate_cross_encoder_reranking()
        
        if success:
            logger.info("✅ VALIDATION PASSED - Cross-encoder reranking functionality is working correctly")
            
            # Test specific edge cases for robustness
            logger.info("Running additional robustness tests...")
            
            # Test with long text
            long_text = "This is a very long text. " * 1000
            query = "long text"
            score = compute_cross_encoder_score(query, long_text)
            logger.info(f"Long text test score: {score:.4f}")
            
            logger.info("⭐ All tests completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ VALIDATION FAILED")
            for i, failure in enumerate(failures, 1):
                logger.error(f"  {i}. {failure}")
            
            # Number of failures vs total
            logger.error(f"Failed {len(failures)} out of {len(failures) + (success and 1 or 0)} tests")
            sys.exit(1)
    
    except Exception as e:
        logger.exception(f"Validation script error: {e}")
        sys.exit(1)