#!/usr/bin/env python3
"""
Validation script for constants.py
This script validates that the core constants module loads correctly and contains the required values.
"""

import sys
import os
from loguru import logger

# Set up logger
logger.remove()
logger.add(sys.stderr, level="INFO")

def validate_constants():
    """
    Validate that constants module loads correctly and contains necessary values.
    """
    try:
        # Add the src directory to the path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

        # Import the constants module directly using absolute imports
        from arangodb.core.constants import CONFIG
        
        # Track validation failures
        all_validation_failures = []
        total_tests = 0
        
        # Test 1: Check if CONFIG is defined
        total_tests += 1
        if not isinstance(CONFIG, dict):
            all_validation_failures.append("CONFIG is not a dictionary")
        else:
            logger.info("CONFIG is properly defined as a dictionary")
        
        # Test 2: Check if essential keys are in CONFIG
        total_tests += 1
        required_keys = ["arango", "embedding", "search", "graph", "llm"]
        missing_keys = [key for key in required_keys if key not in CONFIG]
        if missing_keys:
            all_validation_failures.append(f"Missing required keys in CONFIG: {', '.join(missing_keys)}")
        else:
            logger.info(f"All required keys are present in CONFIG: {', '.join(required_keys)}")
        
        # Test 3: Check if arango section contains connection details
        total_tests += 1
        if "arango" in CONFIG:
            arango_keys = ["host", "user", "password", "db_name"]
            missing_arango_keys = [key for key in arango_keys if key not in CONFIG["arango"]]
            if missing_arango_keys:
                all_validation_failures.append(f"Missing required keys in CONFIG['arango']: {', '.join(missing_arango_keys)}")
            else:
                logger.info(f"All required keys are present in CONFIG['arango']: {', '.join(arango_keys)}")
                logger.info(f"ArangoDB connection details: host={CONFIG['arango']['host']}, user={CONFIG['arango']['user']}, db_name={CONFIG['arango']['db_name']}")
        
        # Final validation report
        if all_validation_failures:
            logger.error(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                logger.error(f"  - {failure}")
            return False
        else:
            logger.info(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            logger.info("Constants module is validated and ready for use")
            return True
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Running constants validation...")
    is_valid = validate_constants()
    sys.exit(0 if is_valid else 1)