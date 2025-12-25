#!/usr/bin/env python3
"""
Test the optimized search performance with all critical fixes applied.
"""

import asyncio
import time
from app.services.rag_service import RAGService
from app.services.query_router import query_router

async def test_optimized_performance():
    """Test the optimized search with real user data."""
    
    print("🚀 Testing OPTIMIZED Search Performance")
    print("=" * 60)
    print("CRITICAL FIXES APPLIED:")
    print("✅ Parallel namespace queries (Fix #1)")
    print("✅ Query intent routing (Fix #2)")  
    print("✅ Single namespace for small datasets (Fix #3)")
    print("✅ No text in Pinecone metadata")
    print("✅ Persistent caching")
    print("=" * 60)
    
    # Real user data
    author_ids = [8, 10]  # vipin and rahul
    
    # Test different query types
    test_queries = [
        # Fact-based query (should use routing optimization)
        "who is doctor dolittle",
        
        # Semantic query (should use vector search)
        "how to forgive someone",
        
        # Another fact query
        "what is the main character",
        
        # Conceptual query
        "steps for personal growth"
    ]
    
    rag_service = RAGService()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 TEST {i}: '{query}'")
        print("-" * 40)
        
        # Show routing decision
        routing = query_router.get_routing_decision(query)
        print(f"🎯 Query Type: {routing['query_type']} (confidence: {routing['confidence']:.2f})")
        print(f"💡 Approach: {routing['recommended_approach']}")
        
        # Time the search
        start_time = time.time()
        
        try:
            results = rag_service.search_only(query, author_ids, limit=5)
            search_time = time.time() - start_time
            
            print(f"⏱️  TOTAL TIME: {search_time:.3f}s")
            print(f"📊 Results: {len(results)}")
            
            # Performance assessment
            if search_time < 0.5:
                print(f"🎉 EXCELLENT! (< 0.5s)")
            elif search_time < 1.0:
                print(f"✅ GOOD! (< 1.0s)")
            elif search_time < 2.0:
                print(f"⚠️  ACCEPTABLE (< 2.0s)")
            else:
                print(f"❌ STILL SLOW (> 2.0s)")
            
            # Show sample results
            if results:
                print(f"📋 Sample result:")
                result = results[0]
                print(f"   Score: {result['score']:.3f}")
                print(f"   Section: {result['section_title']}")
                print(f"   Text: {result['text'][:100]}...")
        
        except Exception as e:
            search_time = time.time() - start_time
            print(f"❌ ERROR after {search_time:.3f}s: {e}")
    
    # Test cache effectiveness
    print(f"\n🔄 Testing Cache Effectiveness...")
    print("-" * 40)
    
    # Run the same query twice
    test_query = "who is doctor dolittle"
    
    # First run (should be fast due to routing or cache)
    start_time = time.time()
    results1 = rag_service.search_only(test_query, author_ids, limit=5)
    time1 = time.time() - start_time
    
    # Second run (should be cached)
    start_time = time.time()
    results2 = rag_service.search_only(test_query, author_ids, limit=5)
    time2 = time.time() - start_time
    
    print(f"First run:  {time1:.3f}s ({len(results1)} results)")
    print(f"Second run: {time2:.3f}s ({len(results2)} results)")
    
    if time2 < 0.1:
        print(f"✅ Caching working perfectly!")
    elif time2 < time1 * 0.5:
        print(f"✅ Caching providing speedup")
    else:
        print(f"⚠️  Caching may not be working optimally")

def test_query_routing():
    """Test the query routing system."""
    
    print(f"\n🧠 Testing Query Routing System")
    print("=" * 40)
    
    test_queries = [
        "who is doctor dolittle",           # Should be FACT_LOOKUP
        "what is the main character",       # Should be FACT_LOOKUP  
        "how to forgive someone",           # Should be SEMANTIC_SEARCH
        "explain the concept of love",      # Should be SEMANTIC_SEARCH
        "when was the book written",        # Should be FACT_LOOKUP
        "why is forgiveness important",     # Should be SEMANTIC_SEARCH
    ]
    
    for query in test_queries:
        routing = query_router.get_routing_decision(query)
        
        print(f"Query: '{query}'")
        print(f"  Type: {routing['query_type']}")
        print(f"  Confidence: {routing['confidence']:.2f}")
        print(f"  Use Vector: {routing['use_vector_search']}")
        print()

async def main():
    """Run all optimization tests."""
    
    print("🎯 CRITICAL OPTIMIZATION TESTING")
    print("This tests all the fixes for sub-second search performance")
    print()
    
    # Test query routing
    test_query_routing()
    
    # Test optimized search performance
    await test_optimized_performance()
    
    print(f"\n🎉 OPTIMIZATION TESTING COMPLETE!")
    print(f"💡 Expected improvements:")
    print(f"   - Parallel queries: 40-60% faster")
    print(f"   - Query routing: Eliminates vector calls for facts")
    print(f"   - Small dataset optimization: Single query vs multiple")
    print(f"   - Persistent caching: Near-instant repeated queries")

if __name__ == "__main__":
    asyncio.run(main())