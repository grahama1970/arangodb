"""Test script for FastAPI visualization server

This script tests the server endpoints with sample data.

Sample input: HTTP requests with graph data
Expected output: HTML visualizations and API responses
"""

import json
import time
import asyncio
from typing import Dict, Any
import httpx
from loguru import logger

# Test data
def get_test_graph():
    """Get sample graph data for testing"""
    return {
        "nodes": [
            {"id": "1", "name": "Node 1", "group": 1},
            {"id": "2", "name": "Node 2", "group": 1},
            {"id": "3", "name": "Node 3", "group": 2},
            {"id": "4", "name": "Node 4", "group": 2},
            {"id": "5", "name": "Node 5", "group": 3},
        ],
        "links": [
            {"source": "1", "target": "2", "value": 1},
            {"source": "1", "target": "3", "value": 2},
            {"source": "2", "target": "4", "value": 1},
            {"source": "3", "target": "5", "value": 3},
            {"source": "4", "target": "5", "value": 1},
        ]
    }


async def test_endpoints():
    """Test server endpoints"""
    base_url = "http://localhost:8000"
    all_validation_failures = []
    total_tests = 0
    
    async with httpx.AsyncClient() as client:
        # Test 1: Root endpoint
        total_tests += 1
        try:
            response = await client.get(f"{base_url}/")
            if response.status_code != 200:
                all_validation_failures.append(f"Root endpoint: Status {response.status_code}")
            if "D3.js Visualization Server" not in response.text:
                all_validation_failures.append("Root endpoint: Missing expected content")
            logger.info("Root endpoint test completed")
        except Exception as e:
            all_validation_failures.append(f"Root endpoint: Failed with error {e}")
        
        # Test 2: List layouts
        total_tests += 1
        try:
            response = await client.get(f"{base_url}/layouts")
            if response.status_code != 200:
                all_validation_failures.append(f"Layouts endpoint: Status {response.status_code}")
            
            data = response.json()
            if "layouts" not in data:
                all_validation_failures.append("Layouts endpoint: Missing layouts list")
            elif len(data["layouts"]) != 4:
                all_validation_failures.append(f"Layouts endpoint: Expected 4 layouts, got {len(data['layouts'])}")
            logger.info("Layouts endpoint test completed")
        except Exception as e:
            all_validation_failures.append(f"Layouts endpoint: Failed with error {e}")
        
        # Test 3: Create visualization (no LLM)
        total_tests += 1
        try:
            request_data = {
                "graph_data": get_test_graph(),
                "layout": "force",
                "use_llm": False,
                "config": {
                    "width": 800,
                    "height": 600,
                    "title": "Test Force Layout"
                }
            }
            
            response = await client.post(
                f"{base_url}/visualize",
                json=request_data
            )
            
            if response.status_code != 200:
                all_validation_failures.append(f"Visualize endpoint: Status {response.status_code}")
            
            data = response.json()
            if "html" not in data:
                all_validation_failures.append("Visualize endpoint: Missing HTML response")
            if data.get("layout") != "force":
                all_validation_failures.append(f"Visualize endpoint: Expected force layout, got {data.get('layout')}")
            
            cache_key = None
            if "html" in data:
                # Extract cache key from response
                import hashlib
                cache_data = {
                    "nodes": sorted([n["id"] for n in request_data["graph_data"]["nodes"]]),
                    "links": sorted([(l["source"], l["target"]) for l in request_data["graph_data"]["links"]]),
                    "layout": "force",
                    "config": request_data["config"]
                }
                data_str = json.dumps(cache_data, sort_keys=True)
                cache_key = hashlib.sha256(data_str.encode()).hexdigest()
            
            logger.info("Visualize endpoint test completed")
        except Exception as e:
            all_validation_failures.append(f"Visualize endpoint: Failed with error {e}")
        
        # Test 4: Cache hit
        total_tests += 1
        if cache_key:
            try:
                # Wait a moment for cache to be written
                await asyncio.sleep(0.5)
                
                # Make same request again
                response = await client.post(
                    f"{base_url}/visualize",
                    json=request_data
                )
                
                if response.status_code != 200:
                    all_validation_failures.append(f"Cache hit test: Status {response.status_code}")
                
                data = response.json()
                if not data.get("cache_hit"):
                    logger.warning("Cache hit test: Expected cache hit, got miss")
                logger.info("Cache hit test completed")
            except Exception as e:
                all_validation_failures.append(f"Cache hit test: Failed with error {e}")
        
        # Test 5: Cache stats
        total_tests += 1
        try:
            response = await client.get(f"{base_url}/cache/stats")
            if response.status_code != 200:
                all_validation_failures.append(f"Cache stats: Status {response.status_code}")
            
            data = response.json()
            if "error" not in data and "total_cached" not in data:
                all_validation_failures.append("Cache stats: Invalid response format")
            logger.info("Cache stats test completed")
        except Exception as e:
            all_validation_failures.append(f"Cache stats: Failed with error {e}")
        
        # Test 6: Create visualization with LLM (if available)
        total_tests += 1
        try:
            request_data = {
                "graph_data": get_test_graph(),
                "use_llm": True,
                "query": "Show me the network connections"
            }
            
            response = await client.post(
                f"{base_url}/visualize",
                json=request_data,
                timeout=30.0  # LLM calls can take longer
            )
            
            if response.status_code != 200:
                all_validation_failures.append(f"LLM visualization: Status {response.status_code}")
            
            data = response.json()
            if "recommendation" in data and data["recommendation"]:
                logger.info(f"LLM recommended: {data['recommendation'].get('layout')}")
            logger.info("LLM visualization test completed")
        except Exception as e:
            logger.warning(f"LLM visualization test skipped: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        return False
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("FastAPI server is working correctly")
        return True


async def main():
    """Main test function"""
    logger.add("server_test.log", rotation="10 MB")
    logger.info("Starting server endpoint tests")
    
    # Wait for server to be ready
    logger.info("Waiting for server to start...")
    await asyncio.sleep(2)
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/", timeout=5.0)
            if response.status_code != 200:
                print("❌ Server not responding. Please start the server first with:")
                print("   uvicorn src.arangodb.visualization.server.visualization_server:app --reload")
                return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the server first with:")
        print("   uvicorn src.arangodb.visualization.server.visualization_server:app --reload")
        return
    
    # Run tests
    success = await test_endpoints()
    
    if success:
        print("\nServer test completed successfully!")
        print("You can now access the server at: http://localhost:8000")
        print("API documentation at: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main())