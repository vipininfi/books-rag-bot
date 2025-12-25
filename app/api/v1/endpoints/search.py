from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.subscription import Subscription
from app.services.rag_service import RAGService
from app.schemas.search import SearchRequest, SearchResponse, RAGRequest, RAGResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform semantic search across subscribed authors' books."""
    
    # Get user's subscribed authors
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).all()
    
    author_ids = [sub.author_id for sub in subscriptions]
    
    if not author_ids:
        # Return empty results with helpful message
        return SearchResponse(
            query=request.query,
            results=[],
            total_results=0,
            subscribed_authors=[]
        )
    
    # Perform search
    rag_service = RAGService()
    results = rag_service.search_only(
        query=request.query,
        author_ids=author_ids,
        limit=request.limit
    )
    
    # Enrich results with book and author information
    from app.models.book import Book
    from app.models.author import Author
    
    enriched_results = []
    for result in results:
        # Get book info
        book = db.query(Book).filter(Book.id == result["book_id"]).first()
        author = db.query(Author).filter(Author.id == result["author_id"]).first()
        
        if book and author:
            enriched_result = {
                **result,
                "book_title": book.title,
                "author_name": author.name
            }
            enriched_results.append(enriched_result)
    
    return SearchResponse(
        query=request.query,
        results=enriched_results,
        total_results=len(enriched_results),
        subscribed_authors=author_ids
    )


@router.post("/rag", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate RAG answer from subscribed authors' books."""
    
    # Get user's subscribed authors
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).all()
    
    author_ids = [sub.author_id for sub in subscriptions]
    
    # Generate RAG answer (let the service handle empty author_ids)
    rag_service = RAGService()
    result = rag_service.generate_answer(
        query=request.query,
        author_ids=author_ids,
        max_chunks=request.max_chunks
    )
    
    return RAGResponse(**result)


@router.get("/stats")
async def get_search_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get search statistics for the current user."""
    
    # Get subscription count
    subscription_count = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).count()
    
    # Get vector store stats
    rag_service = RAGService()
    vector_stats = rag_service.vector_store.get_collection_info()
    
    return {
        "user_subscriptions": subscription_count,
        "total_chunks_in_system": vector_stats["total_points"],
        "vector_dimension": vector_stats["vector_size"]
    }