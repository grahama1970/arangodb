"""
Search API Core Module

This module provides core search functionality for ArangoDB, including:
- BM25 (keyword-based) search
- Semantic (vector similarity) search
- Hybrid search (combined approach)
- Cross-encoder reranking
- Tag-based search
- Graph traversal search
- Keyword search
- Glossary search

All search functions are independent of user interfaces and focus purely on 
search algorithm implementation.
"""

# Import all search functions
from .bm25_search import bm25_search
from .semantic_search import semantic_search, safe_semantic_search
from .hybrid_search import hybrid_search, weighted_reciprocal_rank_fusion
from .cross_encoder_reranking import (
    cross_encoder_rerank,
    rerank_search_results,
    get_cross_encoder,
    extract_text_for_reranking
)
from .tag_search import tag_search, validate_tag_search
from .graph_traverse import graph_traverse, graph_rag_search  
from .keyword_search import search_keyword
from .glossary_search import glossary_search, validate_glossary_search

# Simple imports to avoid circular references

# Export named packages
__all__ = [
    # BM25 search
    "bm25_search",
    
    # Semantic search
    "semantic_search",
    "safe_semantic_search",
    
    # Hybrid search
    "hybrid_search",
    "weighted_reciprocal_rank_fusion",
    
    # Cross-encoder reranking
    "cross_encoder_rerank",
    "rerank_search_results",
    "get_cross_encoder",
    "extract_text_for_reranking",
    
    # Tag search
    "tag_search",
    "validate_tag_search",
    
    # Graph traversal
    "graph_traverse",
    "graph_rag_search",
    
    # Keyword search
    "search_keyword",
    
    # Glossary search
    "glossary_search",
    "validate_glossary_search",
]