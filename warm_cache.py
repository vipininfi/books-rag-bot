#!/usr/bin/env python3
"""
Cache warming script to pre-populate embeddings for common queries.
This will make the first searches much faster.
"""

import asyncio
import time
from app.services.embedding_service import EmbeddingService
from app.core.cache import persistent_cache

# Common search queries to pre-cache
COMMON_QUERIES = [
    # Doctor Dolittle related
    "who is doctor dolittle",
    "doctor dolittle character",
    "dolittle story",
    "doctor dolittle animals",
    
    # General book queries
    "main character",
    "story summary",
    "book plot",
    "character description",
    "what happens in the story",
    
    # Common question patterns
    "who is",
    "what is",
    "how to",
    "why does",
    "when did",
    
    # Forgiveness book related (from the data we saw)
    "forgiveness",
    "how to forgive",
    "forgiveness steps",
    "self forgiveness",
    
    # General literature queries
    "protagonist",
    "antagonist",
    "theme",
    "moral",
    "lesson",
    "meaning"
]

async def warm_embedding_cache():
    """Pre-populate the embedding cache with common queries."""
    
    print("🔥 Warming Embedding Cache...")
    print("=" * 50)
    
    embedding_service = EmbeddingService()
    
    total_start = time.time()
    cached_count = 0
    new_count = 0
    
    for i, query in enumerate(COMMON_QUERIES, 1):
        print(f"[{i:2d}/{len(COMMON_QUERIES)}] Processing: '{query}'")
        
        query_start = time.time()
        
        try:
            # This will either use cache or generate new embedding
            embedding = embedding_service.embed_query(query)
            
            query_time = time.time() - query_start
            
            if query_time < 0.01:  # Very fast = cached
                cached_count += 1
                print(f"         ⚡ Cached: {query_time:.3f}s")
            else:  # Slower = new API call
                new_count += 1
                print(f"         🤖 New: {query_time:.3f}s")
                
                # Add small delay to respect rate limits
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"         ❌ Error: {e}")
    
    # Save all caches to disk
    persistent_cache.save_all()
    
    total_time = time.time() - total_start
    
    print(f"\n📊 Cache Warming Complete:")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Cached queries: {cached_count}")
    print(f"   New queries: {new_count}")
    print(f"   Average per query: {total_time/len(COMMON_QUERIES):.2f}s")
    
    # Show final cache stats
    stats = embedding_service.get_cache_stats()
    print(f"\n📈 Final Cache Stats:")
    print(f"   Session cache: {stats['session_cache_size']} entries")
    print(f"   Persistent cache: {stats['persistent_embeddings']} entries")
    print(f"   Hit rate: {stats['session_hit_rate_percent']}%")

def test_cache_effectiveness():
    """Test how much the cache improves performance."""
    
    print(f"\n🧪 Testing Cache Effectiveness...")
    
    embedding_service = EmbeddingService()
    
    test_queries = [
        "who is doctor dolittle",  # Should be cached
        "doctor dolittle character",  # Should be cached
        "brand new unique query that was never cached before"  # Should be new
    ]
    
    for query in test_queries:
        print(f"\nTesting: '{query}'")
        
        # Test 3 times to see caching effect
        times = []
        for i in range(3):
            start_time = time.time()
            embedding = embedding_service.embed_query(query)
            duration = time.time() - start_time
            times.append(duration)
            print(f"  Run {i+1}: {duration:.3f}s")
        
        print(f"  Average: {sum(times)/len(times):.3f}s")
        
        if times[1] < 0.01 and times[2] < 0.01:
            print(f"  ✅ Caching working! (runs 2-3 were instant)")
        elif times[0] > 0.5:
            print(f"  🤖 New query (first run was slow)")
        else:
            print(f"  ⚠️ Unexpected pattern")

async def main():
    """Run cache warming and testing."""
    
    print("🚀 Cache Warming and Testing Script")
    print("=" * 50)
    
    # Warm the cache
    await warm_embedding_cache()
    
    # Test effectiveness
    test_cache_effectiveness()
    
    print(f"\n✅ Cache warming complete!")
    print(f"💡 Now try searching - common queries should be much faster!")

if __name__ == "__main__":
    asyncio.run(main())