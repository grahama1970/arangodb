"""ArangoDB Visualization Package
Module: __init__.py
Description: Package initialization and exports

This package provides D3.js-based visualization capabilities for ArangoDB graph data.
Supports multiple layout types including force-directed, hierarchical tree, radial,
and Sankey diagrams with LLM-driven recommendations.
"""

__version__ = "0.1.0"

# Import core components
from .core.d3_engine import D3VisualizationEngine
from .core.data_transformer import DataTransformer
# from .core.llm_recommender import LLMVisualizationRecommender  # To be implemented in Task 6

__all__ = [
    "D3VisualizationEngine",
    "DataTransformer", 
    # "LLMVisualizationRecommender"  # To be implemented in Task 6
]