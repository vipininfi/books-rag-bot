from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")


class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    author_id: int
    book_id: int
    book_title: str
    author_name: str
    section_title: str
    chunk_type: str
    token_count: int
    page_number: int


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    subscribed_authors: List[int]


class RAGRequest(BaseModel):
    query: str = Field(..., description="Question to ask")
    max_chunks: int = Field(default=8, ge=1, le=20, description="Maximum chunks to use for context")


class RAGSource(BaseModel):
    book_id: int
    section_title: str
    score: float
    chunk_type: str
    page_number: Optional[int] = None
    text: Optional[str] = None


class RAGResponse(BaseModel):
    answer: str
    sources: List[RAGSource]
    total_chunks: int
    query: str