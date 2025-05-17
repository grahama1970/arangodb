"""
Core Utilities Module

This module provides shared utility functions for all core modules, including:
- Embedding generation
- Logging utilities
- JSON handling
- Error handling
- Validation utilities
- Display formatting

These utilities are used across the core layer modules.
"""

# Note: These imports will be activated during incremental refactoring
# For now, we'll keep them commented out until the modules are created
"""
# Import and expose utility functions
from arangodb.core.utils.embedding import (
    get_embedding,
    get_embedding_with_fallback,
    normalize_embedding,
)
from arangodb.core.utils.log_utils import (
    truncate_large_value,
    log_safe_results,
    setup_logger,
)
from arangodb.core.utils.json_utils import (
    safe_json_loads,
    safe_json_dumps,
    sanitize_json,
)
from arangodb.core.utils.validation import (
    validate_inputs,
    validate_outputs,
    track_validation_failures,
)
from arangodb.core.utils.display_utils import (
    format_search_results,
    format_graph_results,
    truncate_text,
)

# Export named packages
__all__ = [
    # Embedding utilities
    "get_embedding",
    "get_embedding_with_fallback",
    "normalize_embedding",
    
    # Logging utilities
    "truncate_large_value",
    "log_safe_results",
    "setup_logger",
    
    # JSON utilities
    "safe_json_loads",
    "safe_json_dumps",
    "sanitize_json",
    
    # Validation utilities
    "validate_inputs",
    "validate_outputs",
    "track_validation_failures",
    
    # Display utilities
    "format_search_results",
    "format_graph_results",
    "truncate_text",
]
"""