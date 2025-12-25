#!/usr/bin/env python3
"""
Performance check script for the Book RAG system.
This script tests various components and provides optimization recommendations.
"""

import asyncio
import time
import statistics
from typing import List, Dict

from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.rag_service import RAGService
from app.core.performance import performance_metrics, log_performance_summary, get_optimization_suggestions

async def test_embedding_performance():
    """Test embedding service performance."""
    print("🤖 Testing Embedding Performance...")
    
    embedding_service = EmbeddingService()
    
    test_queries = [
        "How to be more productive?",
        "What is the meaning of life?",
        "Best practices for leadership",
        "How to manage stress effectively",
        "Building better relationships"
    ]
    
    times = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"  Test {i}/5: '{query[:30]}...'")
        start_time = time.time()
        
        try:
            embedding = embedding_service.embed_query(query)
            duration = time.time() - start_time
            times.append(duration)
            print(f"    ✅ {duration:.3f}s (dimension: {len(embedding)})")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    if times:
        avg_time = statistics.mean(times)
        print(f"\n📊 Embedding Results:")
        print(f"   Average: {avg_time:.3f}s")
        print(f"   Min: {min(times):.3f}s")
        print(f"   Max: {max(times):.3f}s")
        
        if avg_time > 1.0:
            print(f"   ⚠️ Slow embeddings detected (>{1.0}s average)")
            print(f"   💡 Consider caching or optimizing API calls")
        else:
            print(f"   ✅ Embedding performance is good")
    
    return times

def test_vector_search_performance():
    """Test vector search performance."""
    print("\n📊 Testing Vector Search Performance...")
    
    try:
        vector_store = VectorStore()
        
        # Get collection info
        stats = vector_store.get_collection_info()
        print(f"   Total vectors: {stats['total_points']}")
        print(f"   Vector dimension: {stats['vector_size']}")
        
        if stats['total_points'] == 0:
            print("   ⚠️ No vectors in database - upload some books first")
            return []
        
        # Test with dummy vector (same dimension as stored vectors)
        dummy_vector = [0.1] * stats['vector_size']
        
        search_times = []
        
        for i in range(3):
            print(f"  Search test {i+1}/3...")
            start_time = time.time()
            
            try:
                results = vector_store.search(
                    query_vector=dummy_vector,
                    author_ids=[1, 2, 3],  # Test with some author IDs
                    limit=10
                )
                duration = time.time() - start_time
                search_times.append(duration)
                print(f"    ✅ {duration:.3f}s ({len(results)} results)")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        if search_times:
            avg_time = statistics.mean(search_times)
            print(f"\n📊 Vector Search Results:")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Min: {min(search_times):.3f}s")
            print(f"   Max: {max(search_times):.3f}s")
            
            if avg_time > 0.5:
                print(f"   ⚠️ Slow vector search detected (>0.5s average)")
                print(f"   💡 Consider optimizing Pinecone queries or indexing")
            else:
                print(f"   ✅ Vector search performance is good")
        
        return search_times
        
    except Exception as e:
        print(f"   ❌ Vector store error: {e}")
        return []

async def test_end_to_end_search():
    """Test complete search pipeline."""
    print("\n🔍 Testing End-to-End Search Performance...")
    
    try:
        rag_service = RAGService()
        
        test_queries = [
            "productivity tips",
            "leadership advice",
            "stress management"
        ]
        
        search_times = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"  E2E Test {i}/{len(test_queries)}: '{query}'")
            start_time = time.time()
            
            try:
                results = rag_service.search_only(
                    query=query,
                    author_ids=[1, 2, 3],  # Test with some author IDs
                    limit=5
                )
                duration = time.time() - start_time
                search_times.append(duration)
                print(f"    ✅ {duration:.3f}s ({len(results)} results)")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        if search_times:
            avg_time = statistics.mean(search_times)
            print(f"\n📊 End-to-End Search Results:")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Min: {min(search_times):.3f}s")
            print(f"   Max: {max(search_times):.3f}s")
            
            if avg_time > 2.0:
                print(f"   ⚠️ Slow end-to-end search detected (>2.0s average)")
                print(f"   💡 Check individual components for bottlenecks")
            else:
                print(f"   ✅ End-to-end search performance is good")
        
        return search_times
        
    except Exception as e:
        print(f"   ❌ End-to-end search error: {e}")
        return []

def analyze_performance_bottlenecks(embedding_times, vector_times, e2e_times):
    """Analyze where the bottlenecks are."""
    print("\n🔍 Performance Bottleneck Analysis:")
    print("=" * 50)
    
    if not any([embedding_times, vector_times, e2e_times]):
        print("❌ No performance data available for analysis")
        return
    
    # Calculate averages
    avg_embedding = statistics.mean(embedding_times) if embedding_times else 0
    avg_vector = statistics.mean(vector_times) if vector_times else 0
    avg_e2e = statistics.mean(e2e_times) if e2e_times else 0
    
    print(f"Component Performance:")
    print(f"  Embeddings: {avg_embedding:.3f}s")
    print(f"  Vector Search: {avg_vector:.3f}s")
    print(f"  End-to-End: {avg_e2e:.3f}s")
    
    # Identify bottlenecks
    bottlenecks = []
    
    if avg_embedding > 1.0:
        bottlenecks.append("Embedding generation is slow")
    
    if avg_vector > 0.5:
        bottlenecks.append("Vector search is slow")
    
    if avg_e2e > 2.0:
        bottlenecks.append("Overall search is slow")
    
    if bottlenecks:
        print(f"\n⚠️ Identified Bottlenecks:")
        for bottleneck in bottlenecks:
            print(f"  - {bottleneck}")
    else:
        print(f"\n✅ No major bottlenecks detected")
    
    # Provide recommendations
    print(f"\n💡 Optimization Recommendations:")
    
    if avg_embedding > 1.0:
        print(f"  🔧 Embedding Optimization:")
        print(f"     - Implement embedding caching")
        print(f"     - Use connection pooling for OpenAI API")
        print(f"     - Consider batch processing for multiple queries")
    
    if avg_vector > 0.5:
        print(f"  🔧 Vector Search Optimization:")
        print(f"     - Optimize Pinecone index configuration")
        print(f"     - Reduce metadata size in vectors")
        print(f"     - Use appropriate top_k limits")
    
    if avg_e2e > 2.0:
        print(f"  🔧 Overall System Optimization:")
        print(f"     - Implement async processing")
        print(f"     - Add result caching")
        print(f"     - Optimize database queries")
        print(f"     - Use CDN for static assets")

async def main():
    """Run all performance tests."""
    print("🚀 Book RAG System Performance Check")
    print("=" * 50)
    
    # Test individual components
    embedding_times = await test_embedding_performance()
    vector_times = test_vector_search_performance()
    e2e_times = await test_end_to_end_search()
    
    # Analyze bottlenecks
    analyze_performance_bottlenecks(embedding_times, vector_times, e2e_times)
    
    # Show performance summary
    log_performance_summary()
    
    # Get optimization suggestions
    suggestions = get_optimization_suggestions()
    if suggestions:
        print(f"\n🎯 Additional Optimization Suggestions:")
        for suggestion in suggestions:
            print(f"  {suggestion}")
    
    print(f"\n✅ Performance check complete!")
    print(f"💡 Run this script regularly to monitor system performance")

if __name__ == "__main__":
    asyncio.run(main())