"""
Module: models.py
Description: Fixed ArangoDB data models without nested class issues

External Dependencies:
- pydantic: https://docs.pydantic.dev/
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Message model with content and metadata"""
    id: Optional[str] = None
    content: str
    role: str = "user"
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BiTemporalMixin(BaseModel):
    """Mixin for bitemporal data tracking"""
    valid_from: datetime = Field(default_factory=datetime.now)
    valid_to: Optional[datetime] = None
    transaction_time: datetime = Field(default_factory=datetime.now)

class TemporalEntity(BiTemporalMixin):
    """Entity with temporal tracking"""
    id: str
    data: Dict[str, Any]
    entity_type: str

class LLMResponse(BaseModel):
    """LLM response model"""
    content: str
    model: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class QueryResult(BaseModel):
    """Query result model"""
    results: List[Dict[str, Any]]
    count: int = 0
    query: str
    timestamp: datetime = Field(default_factory=datetime.now)

class DocumentReference(BaseModel):
    """Reference to a document in ArangoDB"""
    id: str
    key: Optional[str] = None
    collection: str
    rev: Optional[str] = None

class SearchResult(BaseModel):
    """Search result with relevance scoring"""
    id: str
    score: float
    content: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

__all__ = ['Message', 'BiTemporalMixin', 'TemporalEntity', 'LLMResponse', 'QueryResult', 'DocumentReference', 'SearchResult']
