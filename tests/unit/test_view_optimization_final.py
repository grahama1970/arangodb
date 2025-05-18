"""
Final test for view optimization.
"""

import time
from loguru import logger
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.view_manager import clear_view_cache


def test_view_optimization():
    """Test that view optimization dramatically improves performance."""
    
    # Clear cache to start fresh
    clear_view_cache()
    
    # Test multiple connection cycles
    connection_times = []
    
    for i in range(5):
        start = time.time()
        db = get_db_connection()
        duration = time.time() - start
        connection_times.append(duration)
        logger.info(f"Connection {i+1}: {duration:.3f}s")
        
        # Small delay between connections
        time.sleep(0.1)
    
    # First connection should be slowest (creating views)
    # Subsequent connections should be much faster (using cache)
    
    logger.info(f"Connection times: {[f'{t:.3f}s' for t in connection_times]}")
    
    # Calculate average of subsequent connections
    first_time = connection_times[0]
    avg_subsequent = sum(connection_times[1:]) / (len(connection_times) - 1)
    
    speedup = (1 - avg_subsequent/first_time) * 100
    logger.info(f"Speed improvement: {speedup:.1f}%")
    
    # Assert significant improvement
    assert avg_subsequent < first_time * 0.5, f"Expected {avg_subsequent:.3f}s < {first_time * 0.5:.3f}s"
    
    logger.info("✅ View optimization successful!")
    return connection_times, speedup


if __name__ == "__main__":
    import sys
    
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    times, speedup = test_view_optimization()
    print(f"\nSummary:")
    print(f"Initial connection: {times[0]:.3f}s")
    print(f"Average subsequent: {sum(times[1:])/len(times[1:]):.3f}s")
    print(f"Speed improvement: {speedup:.1f}%")
    print(f"\n✅ View optimization is working correctly!")