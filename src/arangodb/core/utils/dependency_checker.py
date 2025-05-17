"""
Dependency Checker Module

This module provides centralized dependency checking and mock type generation
for optional dependencies throughout the ArangoDB package.

It creates a consistent pattern for handling missing dependencies gracefully, 
providing helpful error messages, and creating mock types for type annotations.

Usage:
    from arangodb.core.utils.dependency_checker import check_dependency, HAS_ARANGO, ...

    # Check if a dependency is available
    if HAS_NUMPY:
        import numpy as np
        # Use numpy
    else:
        # Alternative implementation

    # Or use the check_dependency function
    np = check_dependency("numpy", "numpy", "1.20.0")
    if np:
        # Use numpy
    else:
        # Alternative implementation
"""

import importlib
import sys
from typing import Any, Dict, Optional, Tuple, Union, Type
from loguru import logger

# Initialize dependency status tracking dictionary
_DEPENDENCY_STATUS: Dict[str, bool] = {}

# Standard Database mock for type annotations
class MockStandardDatabase:
    """Mock ArangoDB StandardDatabase class for type annotations."""
    def __init__(self, *args, **kwargs):
        """Initialize with a warning message."""
        logger.warning("Using mock StandardDatabase - ArangoDB operations will fail")
        self.name = "mock_db"
    
    def collection(self, name: str) -> Any:
        """Mock collection method."""
        logger.warning(f"Attempted to access collection '{name}' in mock database")
        return None
    
    def aql(self, *args, **kwargs) -> Any:
        """Mock AQL execution method."""
        logger.warning("Attempted to execute AQL query in mock database")
        return None

# Define mock classes for dependencies
MOCK_CLASSES = {
    "arango.database.StandardDatabase": MockStandardDatabase,
}

def check_dependency(
    import_name: str, 
    package_name: Optional[str] = None, 
    min_version: Optional[str] = None
) -> Optional[Any]:
    """
    Check if a dependency is available and return the imported module if it is.
    
    Args:
        import_name: Name of the module to import
        package_name: Name of the package (for error messages)
        min_version: Minimum required version
    
    Returns:
        The imported module or None if not available
    """
    package_name = package_name or import_name
    
    # Check if we've already determined this dependency's status
    if import_name in _DEPENDENCY_STATUS:
        if not _DEPENDENCY_STATUS[import_name]:
            logger.debug(f"Dependency '{package_name}' previously found to be unavailable")
        return None if not _DEPENDENCY_STATUS[import_name] else importlib.import_module(import_name)
    
    try:
        # Attempt to import the module
        module = importlib.import_module(import_name)
        
        # Check version if specified
        if min_version and hasattr(module, "__version__"):
            current_version = module.__version__
            # Basic version comparison - can be enhanced with packaging.version
            if current_version < min_version:
                logger.warning(
                    f"Dependency '{package_name}' version {current_version} is older than "
                    f"required minimum version {min_version}"
                )
        
        # Store status for future checks
        _DEPENDENCY_STATUS[import_name] = True
        logger.debug(f"Dependency '{package_name}' is available")
        return module
    
    except ImportError:
        # Log the unavailable dependency
        _DEPENDENCY_STATUS[import_name] = False
        logger.warning(
            f"Optional dependency '{package_name}' is not available. "
            f"Install with: pip install {package_name}"
        )
        return None
    
    except Exception as e:
        # Log any other errors during import
        _DEPENDENCY_STATUS[import_name] = False
        logger.warning(f"Error importing '{package_name}': {e}")
        return None

def get_mock_class(full_class_path: str) -> Type:
    """
    Get a mock class for type annotations when the actual class isn't available.
    
    Args:
        full_class_path: Full import path of the class (e.g., 'arango.database.StandardDatabase')
    
    Returns:
        A mock class or a generic object
    """
    if full_class_path in MOCK_CLASSES:
        return MOCK_CLASSES[full_class_path]
    
    # Create a generic mock class if a specific one isn't defined
    class GenericMock:
        def __init__(self, *args, **kwargs):
            logger.warning(f"Using generic mock for {full_class_path}")
    
    return GenericMock

# Check for common dependencies
arango = check_dependency("arango", "python-arango", "7.5.0")
HAS_ARANGO = arango is not None

numpy = check_dependency("numpy", "numpy", "1.20.0")
HAS_NUMPY = numpy is not None

torch = check_dependency("torch", "torch", "2.0.0")
HAS_TORCH = torch is not None

transformers = check_dependency("transformers", "transformers", "4.0.0")
HAS_TRANSFORMERS = transformers is not None

sentence_transformers = check_dependency("sentence_transformers", "sentence-transformers", "2.0.0")
HAS_SENTENCE_TRANSFORMERS = sentence_transformers is not None

# Define mock ArangoDB types
if not HAS_ARANGO:
    StandardDatabase = MockStandardDatabase
else:
    from arango.database import StandardDatabase

# Define mock PyTorch types
if not HAS_TORCH:
    class Tensor:
        def __init__(self, *args, **kwargs):
            logger.warning("Using mock PyTorch Tensor")
    
    tensor = lambda x: None
else:
    from torch import Tensor, tensor


if __name__ == "__main__":
    """
    Test and validate the dependency checker module.
    """
    import sys
    
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List of validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Basic dependency checking
    total_tests += 1
    try:
        test_dep = check_dependency("this_module_definitely_does_not_exist")
        if test_dep is not None:
            all_validation_failures.append("check_dependency returned non-None for non-existent module")
        
        # Check that the status was cached
        if "this_module_definitely_does_not_exist" not in _DEPENDENCY_STATUS:
            all_validation_failures.append("Dependency status not cached")
        
        if _DEPENDENCY_STATUS.get("this_module_definitely_does_not_exist", True):
            all_validation_failures.append("Dependency status incorrectly recorded as available")
            
    except Exception as e:
        all_validation_failures.append(f"Error in basic dependency checking: {e}")
    
    # Test 2: Mock class retrieval
    total_tests += 1
    try:
        mock_class = get_mock_class("arango.database.StandardDatabase")
        mock_instance = mock_class()
        
        # Check that it's the correct type
        if not isinstance(mock_instance, MockStandardDatabase):
            all_validation_failures.append("get_mock_class returned incorrect class")
        
        # Test with unknown class
        generic_mock = get_mock_class("unknown.package.Class")
        if generic_mock.__name__ == "MockStandardDatabase":
            all_validation_failures.append("get_mock_class returned specific mock for unknown class")
        
    except Exception as e:
        all_validation_failures.append(f"Error in mock class retrieval: {e}")
    
    # Test 3: Global dependency flags
    total_tests += 1
    try:
        # These should be either True or False, but defined
        if "HAS_ARANGO" not in globals():
            all_validation_failures.append("HAS_ARANGO global flag not defined")
        
        if "HAS_TORCH" not in globals():
            all_validation_failures.append("HAS_TORCH global flag not defined")
        
        if "StandardDatabase" not in globals():
            all_validation_failures.append("StandardDatabase type not defined")
        
    except Exception as e:
        all_validation_failures.append(f"Error in global dependency flags: {e}")
    
    # Display validation results
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Module validated and ready for use")
        sys.exit(0)