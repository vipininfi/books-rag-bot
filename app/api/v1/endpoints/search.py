from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

from app.db.database import get_db
from app.models.subscription import Subscription
from app.services.rag_service import RAGService
from app.schemas.search import SearchRequest, SearchResponse, RAGRequest, RAGResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

# Create a thread pool for CPU-bound operations
executor = ThreadPoolExecutor(max_workers=4)


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform semantic search across subscribed authors' books."""
    
    # Start timing
    start_time = time.time()
    print(f"🔍 SEARCH START: Query='{request.query}' User={current_user.id}")
    
    # Step 1: Get user's subscribed authors (optimized query)
    step1_start = time.time()
    author_ids = db.query(Subscription.author_id).filter(
        Subscription.user_id == current_user.id
    ).all()
    author_ids = [aid[0] for aid in author_ids]  # Extract IDs from tuples
    
    step1_time = time.time() - step1_start
    print(f"📊 STEP 1 (Get Subscriptions): {step1_time:.3f}s - Found {len(author_ids)} authors: {author_ids}")
    
    if not author_ids:
        total_time = time.time() - start_time
        print(f"⚠️  SEARCH END (No Subscriptions): {total_time:.3f}s")
        return SearchResponse(
            query=request.query,
            results=[],
            total_results=0,
            subscribed_authors=[]
        )
    
    # Step 2: Perform vector search (run in thread pool to avoid blocking)
    step2_start = time.time()
    
    def run_search():
        rag_service = RAGService()
        return rag_service.search_only(
            query=request.query,
            author_ids=author_ids,
            limit=request.limit
        )
    
    # Run search in thread pool
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(executor, run_search)
    
    step2_time = time.time() - step2_start
    print(f"🎯 STEP 2 (Vector Search): {step2_time:.3f}s - Found {len(results)} results")
    
    # Step 3: Enrich results with book and author information (super optimized)
    step3_start = time.time()
    
    enriched_results = []
    if results:
        from app.models.book import Book
        from app.models.author import Author
        
        # Get all unique book and author IDs
        book_ids = list(set(result["book_id"] for result in results))
        author_ids_for_lookup = list(set(result["author_id"] for result in results))
        
        # Batch fetch with optimized queries (select only needed fields)
        books_query = db.query(Book.id, Book.title).filter(Book.id.in_(book_ids))
        authors_query = db.query(Author.id, Author.name).filter(Author.id.in_(author_ids_for_lookup))
        
        books = {book.id: book.title for book in books_query.all()}
        authors = {author.id: author.name for author in authors_query.all()}
        
        # Enrich results quickly
        for result in results:
            book_title = books.get(result["book_id"], "Unknown Book")
            author_name = authors.get(result["author_id"], "Unknown Author")
            
            enriched_result = {
                **result,
                "book_title": book_title,
                "author_name": author_name
            }
            enriched_results.append(enriched_result)
    
    step3_time = time.time() - step3_start
    print(f"📚 STEP 3 (Enrich Results): {step3_time:.3f}s - Enriched {len(enriched_results)} results")
    
    # Calculate total time
    total_time = time.time() - start_time
    print(f"✅ SEARCH COMPLETE: {total_time:.3f}s total")
    print(f"   - Subscriptions: {step1_time:.3f}s ({(step1_time/total_time)*100:.1f}%)")
    print(f"   - Vector Search: {step2_time:.3f}s ({(step2_time/total_time)*100:.1f}%)")
    print(f"   - Enrich Results: {step3_time:.3f}s ({(step3_time/total_time)*100:.1f}%)")
    
    # Performance warning
    if total_time > 2.0:
        print(f"⚠️ SLOW SEARCH WARNING: {total_time:.3f}s exceeds 2.0s target")
    
    return SearchResponse(
        query=request.query,
        results=enriched_results,
        total_results=len(enriched_results),
        subscribed_authors=author_ids
    )


@router.post("/rag-stream")
async def rag_query_stream(
    request: RAGRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate RAG answer with streaming response - sources first, then AI answer."""
    
    def event_generator():
        start_time = time.time()
        print(f"🚀 RAG STREAM START: Query='{request.query}' User={current_user.id}")
        
        try:
            # Step 1: Get subscriptions quickly
            author_ids = db.query(Subscription.author_id).filter(
                Subscription.user_id == current_user.id
            ).all()
            author_ids = [aid[0] for aid in author_ids]
            print(f"📊 Found {len(author_ids)} authors")
            
            if not author_ids:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No subscribed authors found'})}\n\n"
                return
            
            # Step 2: Get search results
            rag_service = RAGService()
            search_results = rag_service.search_only(
                query=request.query,
                author_ids=author_ids,
                limit=max(request.max_chunks * 2, 16)
            )
            
            # Step 3: Send sources immediately
            if search_results:
                reranked_results = rag_service.rerank_results(request.query, search_results, request.max_chunks)
                
                sources = []
                for result in reranked_results:
                    source_data = {
                        "book_id": int(result["book_id"]),
                        "section_title": result["section_title"],
                        "score": result["score"],
                        "chunk_type": result["chunk_type"],
                        "page_number": int(result.get("page_number", 1)),
                        "text": result["text"]
                    }
                    sources.append(source_data)
                
                # Send sources first
                print(f"🚀 Sending {len(sources)} sources")
                yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
                
                # Step 4: Stream AI response
                context_chunks = []
                for result in reranked_results:
                    section_header = f"--- Section: {result['section_title']} ---"
                    context_chunks.append(f"{section_header}\n{result['text']}")
                
                context = "\n\n".join(context_chunks)
                messages = rag_service._build_rag_messages(request.query, context)
                
                print(f"🚀 Starting OpenAI streaming...")
                stream = rag_service.client.chat.completions.create(
                    model=rag_service.model_name,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1500,
                    stream=True
                )
                
                chunk_count = 0
                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        chunk_count += 1
                        print(f"🚀 Chunk {chunk_count}: '{content[:10]}...'")
                        yield f"data: {json.dumps({'type': 'answer_chunk', 'content': content})}\n\n"
                
                print(f"🚀 Streaming complete: {chunk_count} chunks")
                total_time = time.time() - start_time
                yield f"data: {json.dumps({'type': 'complete', 'total_time': total_time})}\n\n"
                
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No relevant content found'})}\n\n"
                
        except Exception as e:
            print(f"❌ Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/rag", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate RAG answer from subscribed authors' books."""
    
    # Start timing
    start_time = time.time()
    print(f"🤖 RAG START: Query='{request.query}' User={current_user.id}")
    
    # Step 1: Get user's subscribed authors
    step1_start = time.time()
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).all()
    
    author_ids = [sub.author_id for sub in subscriptions]
    step1_time = time.time() - step1_start
    print(f"📊 RAG STEP 1 (Get Subscriptions): {step1_time:.3f}s - Found {len(author_ids)} authors")
    
    # Step 2: Generate RAG answer (run in thread pool)
    step2_start = time.time()
    
    def run_rag():
        rag_service = RAGService()
        return rag_service.generate_answer(
            query=request.query,
            author_ids=author_ids,
            max_chunks=request.max_chunks
        )
    
    # Run RAG in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_rag)
    
    step2_time = time.time() - step2_start
    print(f"🎯 RAG STEP 2 (Generate Answer): {step2_time:.3f}s")
    
    # Calculate total time
    total_time = time.time() - start_time
    print(f"✅ RAG COMPLETE: {total_time:.3f}s total")
    print(f"   - Subscriptions: {step1_time:.3f}s ({(step1_time/total_time)*100:.1f}%)")
    print(f"   - RAG Generation: {step2_time:.3f}s ({(step2_time/total_time)*100:.1f}%)")
    
    return RAGResponse(**result)


@router.get("/stats")
async def get_search_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get search statistics for the current user."""
    
    from app.services.token_tracker import token_tracker
    
    # Get user-specific stats from token tracker
    user_stats = token_tracker.get_usage_stats(user_id=current_user.id, days=30)
    
    # Get subscription count
    subscription_count = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).count()
    
    # Get vector store stats (optional, but keep for system info)
    rag_service = RAGService()
    try:
        vector_stats = rag_service.vector_store.get_collection_info()
        total_chunks = vector_stats.get("total_points", 0)
    except Exception:
        total_chunks = 0
    
    return {
        "total_searches": user_stats.get("by_operation", {}).get("search", {}).get("count", 0),
        "total_rag_queries": user_stats.get("by_operation", {}).get("rag_answer", {}).get("count", 0),
        "total_tokens": user_stats.get("total_tokens", 0),
        "total_cost": user_stats.get("total_cost", 0.0),
        "user_subscriptions": subscription_count,
        "total_chunks_in_system": total_chunks,
        "by_day": user_stats.get("by_day", {})
    }