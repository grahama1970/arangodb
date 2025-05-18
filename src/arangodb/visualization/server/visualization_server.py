"""FastAPI server for D3.js visualizations with caching support

This module provides REST endpoints for generating and serving D3.js visualizations
with Redis caching for improved performance.

Links to third-party package documentation:
- FastAPI: https://fastapi.tiangolo.com/
- Redis: https://redis-py.readthedocs.io/

Sample input: POST request with graph data
Expected output: HTML visualization or JSON metadata
"""

import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis
from loguru import logger
import uvicorn

# Import visualization engine
from ..core.d3_engine import D3VisualizationEngine, VisualizationConfig, LayoutType


# Pydantic models for API
class GraphData(BaseModel):
    """Input graph data model"""
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


class VisualizationRequest(BaseModel):
    """Visualization request model"""
    graph_data: GraphData
    layout: Optional[LayoutType] = "force"
    config: Optional[Dict[str, Any]] = None
    query: Optional[str] = None
    use_llm: Optional[bool] = True
    cache_ttl: Optional[int] = 3600  # Cache TTL in seconds


class VisualizationResponse(BaseModel):
    """Visualization response model"""
    html: str
    layout: str
    title: str
    recommendation: Optional[Dict[str, Any]] = None
    cache_hit: bool = False
    generated_at: datetime = Field(default_factory=datetime.now)


class CachedVisualization(BaseModel):
    """Cached visualization data"""
    html: str
    layout: str
    title: str
    recommendation: Optional[Dict[str, Any]] = None
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime


# Initialize FastAPI app
app = FastAPI(
    title="D3.js Visualization Server",
    description="Generate and serve D3.js visualizations from ArangoDB data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
redis_client = None
try:
    redis_client = redis.Redis(
        host='localhost', 
        port=6379, 
        db=0, 
        decode_responses=True
    )
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_client = None

# Initialize visualization engine
engine = D3VisualizationEngine(use_llm=True)

# Static file serving
static_dir = Path("/home/graham/workspace/experiments/arangodb/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def generate_cache_key(data: Dict[str, Any], layout: str, config: Optional[Dict] = None) -> str:
    """Generate cache key from request data
    
    Args:
        data: Graph data
        layout: Layout type
        config: Optional configuration
        
    Returns:
        SHA256 hash as cache key
    """
    cache_data = {
        "nodes": sorted([n["id"] for n in data.get("nodes", [])]),
        "links": sorted([(l.get("source"), l.get("target")) for l in data.get("links", [])]),
        "layout": layout,
        "config": config or {}
    }
    
    data_str = json.dumps(cache_data, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()


async def get_cached_visualization(cache_key: str) -> Optional[CachedVisualization]:
    """Retrieve visualization from cache
    
    Args:
        cache_key: Cache key
        
    Returns:
        CachedVisualization or None
    """
    if not redis_client:
        return None
    
    try:
        cached_data = redis_client.get(f"viz:{cache_key}")
        if cached_data:
            data = json.loads(cached_data)
            # Update access metrics
            data["access_count"] += 1
            data["last_accessed"] = datetime.now().isoformat()
            redis_client.set(f"viz:{cache_key}", json.dumps(data))
            
            return CachedVisualization(**data)
    except Exception as e:
        logger.error(f"Cache retrieval error: {e}")
    
    return None


async def cache_visualization(
    cache_key: str, 
    html: str, 
    layout: str, 
    title: str,
    recommendation: Optional[Dict] = None,
    ttl: int = 3600
) -> None:
    """Cache visualization data
    
    Args:
        cache_key: Cache key
        html: HTML content
        layout: Layout type
        title: Visualization title
        recommendation: LLM recommendation data
        ttl: Time to live in seconds
    """
    if not redis_client:
        return
    
    try:
        cache_data = CachedVisualization(
            html=html,
            layout=layout,
            title=title,
            recommendation=recommendation,
            created_at=datetime.now(),
            access_count=1,
            last_accessed=datetime.now()
        )
        
        redis_client.setex(
            f"viz:{cache_key}",
            ttl,
            json.dumps(cache_data.dict(), default=str)
        )
    except Exception as e:
        logger.error(f"Cache storage error: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API documentation"""
    return """
    <html>
        <head>
            <title>D3.js Visualization Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .endpoint { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
                .method { color: #007ACC; font-weight: bold; }
                code { background: #e0e0e0; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>D3.js Visualization Server</h1>
            <p>Generate interactive D3.js visualizations from graph data.</p>
            
            <div class="endpoint">
                <span class="method">POST</span> <code>/visualize</code>
                <p>Generate a visualization from graph data</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <code>/visualize/{cache_key}</code>
                <p>Retrieve cached visualization</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <code>/layouts</code>
                <p>List available layout types</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <code>/cache/stats</code>
                <p>Get cache statistics</p>
            </div>
            
            <p>See <a href="/docs">/docs</a> for interactive API documentation.</p>
        </body>
    </html>
    """


@app.post("/visualize", response_model=VisualizationResponse)
async def create_visualization(request: VisualizationRequest):
    """Create a new visualization
    
    Args:
        request: Visualization request with graph data
        
    Returns:
        VisualizationResponse with HTML and metadata
    """
    try:
        # Convert graph data to dict
        graph_dict = request.graph_data.dict()
        
        # Generate cache key
        cache_key = generate_cache_key(
            graph_dict,
            request.layout,
            request.config
        )
        
        # Check cache first
        cached = await get_cached_visualization(cache_key)
        if cached:
            logger.info(f"Cache hit for key: {cache_key}")
            return VisualizationResponse(
                html=cached.html,
                layout=cached.layout,
                title=cached.title,
                recommendation=cached.recommendation,
                cache_hit=True
            )
        
        # Generate visualization
        if request.use_llm and engine.llm_recommender:
            # Use LLM recommendation
            recommendation = engine.recommend_visualization(graph_dict, request.query)
            
            if recommendation:
                # Apply recommendation to config
                config = VisualizationConfig(
                    layout=recommendation.layout_type,
                    title=recommendation.title,
                    **(request.config or {})
                )
                
                # Apply LLM config overrides
                for key, value in recommendation.config_overrides.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                
                layout = recommendation.layout_type
                title = recommendation.title
                rec_data = {
                    "layout": recommendation.layout_type,
                    "title": recommendation.title,
                    "reasoning": recommendation.reasoning,
                    "confidence": recommendation.confidence,
                    "alternatives": recommendation.alternative_layouts
                }
            else:
                config = VisualizationConfig(
                    layout=request.layout,
                    **(request.config or {})
                )
                layout = request.layout
                title = config.title or f"{layout.title()} Visualization"
                rec_data = None
        else:
            # Direct visualization without LLM
            config = VisualizationConfig(
                layout=request.layout,
                **(request.config or {})
            )
            layout = request.layout
            title = config.title or f"{layout.title()} Visualization"
            rec_data = None
        
        # Generate HTML
        html = engine.generate_visualization(
            graph_dict,
            layout=layout,
            config=config
        )
        
        # Cache the result
        await cache_visualization(
            cache_key,
            html,
            layout,
            title,
            rec_data,
            request.cache_ttl
        )
        
        return VisualizationResponse(
            html=html,
            layout=layout,
            title=title,
            recommendation=rec_data,
            cache_hit=False
        )
        
    except Exception as e:
        logger.error(f"Visualization generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualize/{cache_key}", response_class=HTMLResponse)
async def get_cached_visualization_by_key(cache_key: str):
    """Retrieve cached visualization by key
    
    Args:
        cache_key: Cache key
        
    Returns:
        HTML visualization or 404
    """
    cached = await get_cached_visualization(cache_key)
    
    if cached:
        return HTMLResponse(content=cached.html)
    else:
        raise HTTPException(status_code=404, detail="Visualization not found")


@app.get("/layouts")
async def list_layouts():
    """List available layout types
    
    Returns:
        List of layout types with descriptions
    """
    return {
        "layouts": [
            {
                "type": "force",
                "name": "Force-Directed",
                "description": "General purpose network layout with physics simulation",
                "best_for": ["networks", "clusters", "general graphs"]
            },
            {
                "type": "tree",
                "name": "Hierarchical Tree",
                "description": "Tree layout for hierarchical data",
                "best_for": ["hierarchies", "taxonomies", "org charts"]
            },
            {
                "type": "radial",
                "name": "Radial Tree",
                "description": "Circular tree layout",
                "best_for": ["centered hierarchies", "radial organization"]
            },
            {
                "type": "sankey",
                "name": "Sankey Diagram",
                "description": "Flow diagram for weighted paths",
                "best_for": ["flows", "processes", "resource allocation"]
            }
        ]
    }


@app.get("/cache/stats")
async def cache_statistics():
    """Get cache statistics
    
    Returns:
        Cache usage statistics
    """
    if not redis_client:
        return {"error": "Cache not available"}
    
    try:
        keys = redis_client.keys("viz:*")
        total_size = 0
        access_counts = []
        
        for key in keys:
            data = redis_client.get(key)
            if data:
                total_size += len(data)
                cached = json.loads(data)
                access_counts.append(cached.get("access_count", 0))
        
        return {
            "total_cached": len(keys),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_accesses": sum(access_counts),
            "average_accesses": round(sum(access_counts) / len(access_counts), 2) if access_counts else 0,
            "cache_available": True
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {"error": str(e)}


@app.delete("/cache/clear")
async def clear_cache():
    """Clear all cached visualizations
    
    Returns:
        Confirmation message
    """
    if not redis_client:
        return {"error": "Cache not available"}
    
    try:
        keys = redis_client.keys("viz:*")
        if keys:
            redis_client.delete(*keys)
        return {"message": f"Cleared {len(keys)} cached visualizations"}
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )