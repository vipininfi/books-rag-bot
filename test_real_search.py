#!/usr/bin/env python3
"""
Test script to debug the real search performance with actual user data.
"""

import asyncio
import time
from app.services.rag_service import RAGService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

async def test_real_search():
    """Test search with real user data."""
    
    print("🔍 Testing Real Search Performance")
    print("=" * 50)
    
    # Real user data from vipin@gmail.com
    author_ids = [8, 10]  # vipin and rahul
    query = "who is doctor dolittle"
    
    print(f"Query: '{query}'")
    print(f"Author IDs: {author_ids}")
    
    # Test 1: Embedding service only
    print(f"\n1️⃣ Testing Embedding Service...")
    embedding_service = EmbeddingService()
    
    embed_start = time.time()
    embedding = embedding_service.embed_query(query)
    embed_time = time.time() - embed_start
    
    print(f"   Embedding: {embed_time:.3f}s (dimension: {len(embedding)})")
    
    # Test 2: Vector search only
    print(f"\n2️⃣ Testing Vector Search...")
    vector_store = VectorStore()
    
    vector_start = time.time()
    vector_results = vector_store.search(
        query_vector=embedding,
        author_ids=author_ids,
        limit=10
    )
    vector_time = time.time() - vector_start
    
    print(f"   Vector Search: {vector_time:.3f}s ({len(vector_results)} results)")
    
    # Show some results for debugging
    if vector_results:
        print(f"   Sample results:")
        for i, result in enumerate(vector_results[:3]):
            print(f"     {i+1}. Score: {result['score']:.3f} | Author: {result['author_id']} | Book: {result['book_id']}")
            print(f"        Text: {result['text'][:100]}...")
    else:
        print(f"   ⚠️ No results found!")
    
    # Test 3: Full RAG search
    print(f"\n3️⃣ Testing Full RAG Search...")
    rag_service = RAGService()
    
    rag_start = time.time()
    rag_results = rag_service.search_only(
        query=query,
        author_ids=author_ids,
        limit=10
    )
    rag_time = time.time() - rag_start
    
    print(f"   RAG Search: {rag_time:.3f}s ({len(rag_results)} results)")
    
    # Test 4: Cache effectiveness
    print(f"\n4️⃣ Testing Cache Effectiveness...")
    
    # Run the same query again to test caching
    cache_start = time.time()
    cached_embedding = embedding_service.embed_query(query)
    cache_time = time.time() - cache_start
    
    print(f"   Cached Query: {cache_time:.3f}s")
    
    # Show cache stats
    cache_stats = embedding_service.get_cache_stats()
    print(f"   Cache Stats: {cache_stats}")
    
    # Test 5: Different queries to populate cache
    print(f"\n5️⃣ Testing Multiple Queries...")
    
    test_queries = [
        "doctor dolittle character",
        "who is doctor dolittle",  # Same as before (should be cached)
        "dolittle story",
        "doctor character"
    ]
    
    for i, test_query in enumerate(test_queries, 1):
        query_start = time.time()
        test_embedding = embedding_service.embed_query(test_query)
        query_time = time.time() - query_start
        print(f"   Query {i}: '{test_query}' -> {query_time:.3f}s")
    
    # Final cache stats
    final_stats = embedding_service.get_cache_stats()
    print(f"\n📊 Final Cache Stats: {final_stats}")
    
    # Performance summary
    print(f"\n📊 Performance Summary:")
    print(f"   Embedding (first): {embed_time:.3f}s")
    print(f"   Vector Search: {vector_time:.3f}s")
    print(f"   RAG Search: {rag_time:.3f}s")
    print(f"   Cached Query: {cache_time:.3f}s")
    
    total_estimated = embed_time + vector_time + 0.1  # Add small overhead
    print(f"   Estimated Total: {total_estimated:.3f}s")
    
    if total_estimated > 2.0:
        print(f"   ⚠️ Still too slow! Need more optimization.")
        
        if embed_time > 1.0:
            print(f"   🔧 Embedding is the bottleneck ({embed_time:.3f}s)")
        if vector_time > 0.5:
            print(f"   🔧 Vector search is slow ({vector_time:.3f}s)")
    else:
        print(f"   ✅ Performance looks good!")

def check_vector_data():
    """Check what data is actually in the vector database."""
    print(f"\n🔍 Checking Vector Database Content...")
    
    try:
        vector_store = VectorStore()
        stats = vector_store.get_collection_info()
        
        print(f"   Total vectors: {stats['total_points']}")
        print(f"   Vector dimension: {stats['vector_size']}")
        
        # Try to get some sample data
        dummy_vector = [0.1] * stats['vector_size']
        
        # Search without author filter to see all data
        all_results = vector_store.search(
            query_vector=dummy_vector,
            author_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],  # Try many author IDs
            limit=20,
            score_threshold=0.0  # Very low threshold
        )
        
        print(f"   Sample results (no filter): {len(all_results)}")
        
        if all_results:
            author_ids_found = set(r['author_id'] for r in all_results)
            book_ids_found = set(r['book_id'] for r in all_results)
            
            print(f"   Authors in DB: {sorted(author_ids_found)}")
            print(f"   Books in DB: {sorted(book_ids_found)}")
            
            # Show sample content
            print(f"   Sample content:")
            for i, result in enumerate(all_results[:3]):
                print(f"     {i+1}. Author {result['author_id']}, Book {result['book_id']}")
                print(f"        Section: {result['section_title']}")
                print(f"        Text: {result['text'][:100]}...")
        else:
            print(f"   ⚠️ No vectors found at all!")
            
    except Exception as e:
        print(f"   ❌ Error checking vector data: {e}")

async def main():
    """Run all tests."""
    check_vector_data()
    await test_real_search()

if __name__ == "__main__":
    asyncio.run(main())