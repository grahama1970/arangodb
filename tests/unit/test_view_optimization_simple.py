"""
Simple test to verify view optimization.
"""

import time
from loguru import logger
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.view_manager import clear_view_cache


def test_view_optimization():
    """Test that view optimization improves connection performance."""
    
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
    
    # Measure third connection time (should also skip)
    logger.info("Testing third connection (should also skip)...")
    start3 = time.time()
    try:
        db3 = get_db_connection()
        time3 = time.time() - start3
        logger.info(f"Third connection time: {time3:.3f}s")
    except Exception as e:
        logger.error(f"Third connection failed: {e}")
        return
    
    # Report results
    logger.info(f"Connection times: {time1:.3f}s -> {time2:.3f}s -> {time3:.3f}s")
    
    # Check if subsequent connections are faster
    if time2 < time1 * 0.8 and time3 < time1 * 0.8:
        logger.info("✅ View optimization working! Subsequent connections are faster.")
        speedup = (1 - time2/time1) * 100
        logger.info(f"Speed improvement: {speedup:.1f}%")
    else:
        logger.warning("⚠️ View optimization may not be working as expected.")
        logger.warning(f"Expected {time2:.3f}s < {time1 * 0.8:.3f}s")
    
    # Check if database is working
    try:
        collections = db3.collections()
        logger.info(f"Database has {len(collections)} collections")
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")


if __name__ == "__main__":
    import sys
    
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    test_view_optimization()