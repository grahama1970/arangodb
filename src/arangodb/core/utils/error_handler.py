"""
Error Handling Module for ArangoDB Knowledge Graph System
Module: error_handler.py
Description: API handlers and endpoints for error handler

This module provides centralized error handling for the ArangoDB Knowledge Graph System,
with categorized errors, retry logic, and human-friendly error messages.

Features:
- Categorized exception types
- Retry logic for transient errors
- Human-friendly error messages
- Error logging and tracking
"""

import sys
import time
from typing import Optional, Callable, Any, Dict, Type, List, Union
from functools import wraps
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

# Base exception class for all ArangoDB Knowledge Graph errors
class ArangoKGError(Exception):
    """Base exception class for all ArangoDB Knowledge Graph errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize with message, optional error code and details."""
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        """Convert to string with error code if available."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

# Configuration errors
class ConfigurationError(ArangoKGError):
    """Raised when there's an issue with configuration settings."""
    pass

# Database errors
class DatabaseError(ArangoKGError):
    """Raised when there's a database-related error."""
    pass

class ConnectionError(DatabaseError):
    """Raised when there's an issue connecting to the database."""
    pass

class QueryError(DatabaseError):
    """Raised when there's an issue with a database query."""
    pass

class DocumentError(DatabaseError):
    """Raised when there's an issue with a document operation."""
    pass

# Search errors
class SearchError(ArangoKGError):
    """Raised when there's a search-related error."""
    pass

class EmbeddingError(SearchError):
    """Raised when there's an issue generating embeddings."""
    pass

class SearchConfigError(SearchError):
    """Raised when there's an issue with search configuration."""
    pass

# Memory errors
class MemoryError(ArangoKGError):
    """Raised when there's a memory-related error."""
    pass

class ConversationError(MemoryError):
    """Raised when there's an issue with conversation operations."""
    pass

class EpisodeError(MemoryError):
    """Raised when there's an issue with episode operations."""
    pass

# Graph errors
class GraphError(ArangoKGError):
    """Raised when there's a graph-related error."""
    pass

class RelationshipError(GraphError):
    """Raised when there's an issue with relationship operations."""
    pass

class TraversalError(GraphError):
    """Raised when there's an issue with graph traversal."""
    pass

# LLM errors
class LLMError(ArangoKGError):
    """Raised when there's an LLM-related error."""
    pass

class TokenLimitError(LLMError):
    """Raised when token limits are exceeded."""
    pass

class ModelUnavailableError(LLMError):
    """Raised when an LLM model is unavailable."""
    pass

# Utility functions for error handling
def with_error_handling(
    error_map: Dict[Type[Exception], Type[ArangoKGError]] = None,
    default_error: Type[ArangoKGError] = ArangoKGError,
    retry_exceptions: List[Type[Exception]] = None,
    max_retries: int = 3,
    message_template: Optional[str] = None,
):
    """
    Decorator for functions to provide standardized error handling.
    
    Args:
        error_map: Mapping from caught exception types to custom exception types
        default_error: Default error type to use if not in error_map
        retry_exceptions: List of exception types to retry
        max_retries: Maximum number of retry attempts
        message_template: Template string for error message
        
    Returns:
        Decorated function with error handling
    """
    error_map = error_map or {}
    retry_exceptions = retry_exceptions or []
    
    def decorator(func):
        # If any retry exceptions are specified, use tenacity to retry
        if retry_exceptions:
            # Apply retry decorator
            @retry(
                retry=retry_if_exception_type(tuple(retry_exceptions)),
                stop=stop_after_attempt(max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                reraise=True,
            )
            def retry_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
                
            func_to_wrap = retry_wrapper
        else:
            func_to_wrap = func
        
        @wraps(func_to_wrap)
        def wrapper(*args, **kwargs):
            try:
                return func_to_wrap(*args, **kwargs)
            except tuple(error_map.keys()) as e:
                # Map to custom exception type
                error_type = error_map[type(e)]
                error_msg = message_template.format(func=func.__name__, error=str(e)) if message_template else str(e)
                
                # Log the error
                logger.error(f"{error_type.__name__} in {func.__name__}: {error_msg}")
                
                # Raise mapped exception
                raise error_type(error_msg, details={"original_error": str(e), "original_type": type(e).__name__})
            except RetryError as e:
                # Handle case where retries were exhausted
                if hasattr(e, "last_attempt") and hasattr(e.last_attempt, "exception"):
                    original_error = e.last_attempt.exception()
                    error_type = error_map.get(type(original_error), default_error)
                    error_msg = f"Max retries ({max_retries}) exceeded in {func.__name__}: {str(original_error)}"
                else:
                    error_type = default_error
                    error_msg = f"Max retries ({max_retries}) exceeded in {func.__name__}"
                
                # Log the error
                logger.error(f"{error_type.__name__} in {func.__name__} after {max_retries} retries")
                
                # Raise mapped exception
                raise error_type(error_msg, details={"retries": max_retries})
            except Exception as e:
                # Handle unexpected exceptions
                error_msg = message_template.format(func=func.__name__, error=str(e)) if message_template else str(e)
                
                # Log the error
                logger.error(f"Unexpected {type(e).__name__} in {func.__name__}: {error_msg}")
                
                # Raise as default error type
                raise default_error(error_msg, details={"original_error": str(e), "original_type": type(e).__name__})
        
        return wrapper
    
    return decorator

def handle_db_errors(func):
    """
    Decorator specifically for database operations.
    
    Maps common ArangoDB errors to custom exception types.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with database error handling
    """
    # Import here to avoid circular imports
    from arango.exceptions import (
        ArangoServerError,
        DocumentInsertError,
        DocumentGetError,
        DocumentUpdateError,
        DocumentDeleteError,
        AQLQueryExecuteError,
        ConnectionError as ArangoConnectionError,
    )
    
    # Map ArangoDB exceptions to custom exceptions
    error_map = {
        ArangoConnectionError: ConnectionError,
        ArangoServerError: DatabaseError,
        DocumentInsertError: DocumentError,
        DocumentGetError: DocumentError,
        DocumentUpdateError: DocumentError,
        DocumentDeleteError: DocumentError,
        AQLQueryExecuteError: QueryError,
    }
    
    # List of exceptions to retry
    retry_exceptions = [
        ArangoConnectionError,
        AQLQueryExecuteError,
    ]
    
    # Apply general error handling with specific mappings
    return with_error_handling(
        error_map=error_map,
        default_error=DatabaseError,
        retry_exceptions=retry_exceptions,
        max_retries=3,
        message_template="Database operation failed in {func}: {error}"
    )(func)

def handle_search_errors(func):
    """
    Decorator specifically for search operations.
    
    Maps common search errors to custom exception types.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with search error handling
    """
    # Import here to avoid circular imports
    import torch
    from arango.exceptions import AQLQueryExecuteError
    
    # Map search exceptions to custom exceptions
    error_map = {
        torch.cuda.OutOfMemoryError: EmbeddingError,
        torch.cuda.CudaError: EmbeddingError,
        ValueError: SearchError,
        AQLQueryExecuteError: QueryError,
    }
    
    # Apply general error handling with specific mappings
    return with_error_handling(
        error_map=error_map,
        default_error=SearchError,
        message_template="Search operation failed in {func}: {error}"
    )(func)

def handle_llm_errors(func):
    """
    Decorator specifically for LLM operations.
    
    Maps common LLM errors to custom exception types.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with LLM error handling
    """
    # Map LLM exceptions to custom exceptions
    error_map = {
        ValueError: LLMError,
        ConnectionError: LLMError,
        TimeoutError: LLMError,
    }
    
    # List of exceptions to retry
    retry_exceptions = [
        ConnectionError,
        TimeoutError,
    ]
    
    # Apply general error handling with specific mappings
    return with_error_handling(
        error_map=error_map,
        default_error=LLMError,
        retry_exceptions=retry_exceptions,
        max_retries=3,
        message_template="LLM operation failed in {func}: {error}"
    )(func)

def get_friendly_error_message(error: Exception) -> str:
    """
    Convert an exception to a human-friendly error message.
    
    Args:
        error: The exception to convert
        
    Returns:
        Human-friendly error message
    """
    if isinstance(error, ArangoKGError):
        # Use custom error message
        return str(error)
    
    # Map common exceptions to friendly messages
    error_type = type(error).__name__
    
    friendly_messages = {
        "ConnectionError": "Could not connect to the database. Please check your network connection and try again.",
        "DocumentGetError": "The requested document could not be found.",
        "DocumentInsertError": "Could not create the document. It might already exist or contain invalid data.",
        "DocumentUpdateError": "Could not update the document. It might not exist or contain invalid data.",
        "DocumentDeleteError": "Could not delete the document. It might not exist or be referenced by other documents.",
        "AQLQueryExecuteError": "The database query failed. Please check your input and try again.",
        "ValueError": "Invalid input provided. Please check your input and try again.",
        "KeyError": "A required key was not found. Please check your input and try again.",
        "TypeError": "An operation was performed on an incompatible type. Please check your input and try again.",
        "IndexError": "An index was out of range. Please check your input and try again.",
        "AttributeError": "An object did not have the requested attribute. Please check your input and try again.",
        "ImportError": "A required module could not be imported. Please check your installation.",
        "ModuleNotFoundError": "A required module could not be found. Please check your installation.",
        "PermissionError": "You do not have permission to perform this operation. Please check your credentials.",
        "FileNotFoundError": "The requested file could not be found. Please check the file path.",
        "IOError": "An I/O operation failed. Please check your file paths and permissions.",
        "OSError": "An operating system error occurred. Please check your file paths and permissions.",
        "TimeoutError": "The operation timed out. Please try again later.",
        "MemoryError": "The operation ran out of memory. Please try a smaller input or free up memory.",
    }
    
    # Get friendly message or use the error message
    message = friendly_messages.get(error_type, str(error))
    
    # For unknown errors, add the error type
    if error_type not in friendly_messages:
        message = f"{error_type}: {message}"
    
    return message

# Self-validation when run directly
if __name__ == "__main__":
    # Configure logging for standalone testing
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    print("=== Testing Error Handling Module ===")
    
    # Test custom exceptions
    try:
        raise DatabaseError("Test database error", "DB001", {"table": "test_table"})
    except ArangoKGError as e:
        print(f"Caught expected exception: {e}")
        print(f"Error code: {e.error_code}")
        print(f"Details: {e.details}")
    
    # Test error handling decorator
    @with_error_handling(
        error_map={ValueError: SearchError},
        default_error=ArangoKGError,
        message_template="Test function failed: {error}"
    )
    def test_function(raise_error=False, error_type=None):
        """Test function for error handling decorator."""
        if raise_error:
            if error_type == "value":
                raise ValueError("Test value error")
            elif error_type == "key":
                raise KeyError("Test key error")
            else:
                raise Exception("Test generic error")
        return "Success"
    
    # Test successful case
    result = test_function()
    print(f"Test function result: {result}")
    
    # Test mapped error
    try:
        test_function(raise_error=True, error_type="value")
    except SearchError as e:
        print(f"Caught expected SearchError: {e}")
    
    # Test default error
    try:
        test_function(raise_error=True, error_type="key")
    except ArangoKGError as e:
        print(f"Caught expected ArangoKGError: {e}")
    
    # Test friendly error messages
    errors = [
        DatabaseError("Test database error"),
        ValueError("Test value error"),
        ConnectionError("Test connection error"),
    ]
    
    for error in errors:
        friendly_message = get_friendly_error_message(error)
        print(f"Friendly message for {type(error).__name__}: {friendly_message}")
    
    print("\n=== Error Handling Module Tests Passed ===")
