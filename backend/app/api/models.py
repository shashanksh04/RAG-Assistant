from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[Dict[str, Any]] = []

class AskRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    enable_query_expansion: bool = False
    enable_hyde: bool = False

class Source(BaseModel):
    source: str
    page: int
    snippet: str
    relevance_score: float = 0.0
    citation: str

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: float
    is_grounded: bool
    conversation_id: Optional[str] = None

class DocumentInfo(BaseModel):
    filename: str
    chunk_count: int = 0
    total_pages: int = 0
    title: Optional[str] = "Unknown"
    author: Optional[str] = "Unknown"