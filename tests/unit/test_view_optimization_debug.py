"""
Debug test for view optimization.
"""

import time
from loguru import logger
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.view_manager import clear_view_cache


def test_view_optimization_debug():
    """Test view optimization with debug logging."""
    
    # Enable debug logging
    logger.remove()
    import sys
    logger.add(sys.stderr, level="DEBUG")
    
    # Clear cache to start fresh
    clear_view_cache()
    
    # Measure first connection time (will create views)
    logger.info("Testing first connection (will create views)...")
    start1 = time.time()
    try:
        db1 = get_db_connection()
        time1 = time.time() - start1
        logger.info(f"First connection time: {time1:.3f}s")
    except Exception as e:
        logger.error(f"First connection failed: {e}")
        return
    
    # Wait a bit to ensure any async operations complete
    time.sleep(1)
    
    # Measure second connection time (should skip view recreation)
    logger.info("Testing second connection (should skip view recreation)...")
    start2 = time.time()
    try:
        db2 = get_db_connection()
        time2 = time.time() - start2
        logger.info(f"Second connection time: {time2:.3f}s")
    except Exception as e:
        logger.error(f"Second connection failed: {e}")
        return
    
    # Report results
    logger.info(f"Connection times: {time1:.3f}s -> {time2:.3f}s")
    
    # Check if subsequent connections are faster
    if time2 < time1 * 0.8:
        logger.info("✅ View optimization working! Second connection is faster.")
        speedup = (1 - time2/time1) * 100
        logger.info(f"Speed improvement: {speedup:.1f}%")
    else:
        logger.warning("⚠️ View optimization may not be working as expected.")
        logger.warning(f"Expected {time2:.3f}s < {time1 * 0.8:.3f}s")


if __name__ == "__main__":
    test_view_optimization_debug()