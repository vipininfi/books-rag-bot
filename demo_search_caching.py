#!/usr/bin/env python3
"""
Demo script to show the difference between cached and uncached search token usage.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import RAGService
from app.services.token_tracker import token_tracker
import time
import uuid

def demo_search_caching():
    """Demonstrate search caching and token usage."""
    print("🔍 Search Caching & Token Usage Demo")
    print("=" * 60)
    
    # Create RAG service
    rag_service = RAGService()
    test_user_id = 888
    
    print("📊 Initial token stats...")
    initial_stats = token_tracker.get_usage_stats(user_id=test_user_id, days=1)
    print(f"Starting operations: {initial_stats['operations_count']}")
    print(f"Starting tokens: {initial_stats['total_tokens']}")
    
    # Test 1: First search (should use tokens)
    print("\n🔍 Test 1: First search with unique query")
    unique_query = f"unique search query {uuid.uuid4().hex[:8]}"
    print(f"Query: '{unique_query}'")
    
    try:
        start_time = time.time()
        results1 = rag_service.search_only(
            query=unique_query,
            author_ids=[1, 2],
            limit=5,
            user_id=test_user_id
        )
        search_time1 = time.time() - start_time
        print(f"✅ First search completed in {search_time1:.3f}s")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    # Check tokens after first search
    time.sleep(0.5)
    stats_after_1 = token_tracker.get_usage_stats(user_id=test_user_id, days=1)
    tokens_used_1 = stats_after_1['total_tokens'] - initial_stats['total_tokens']
    print(f"Tokens used in first search: {tokens_used_1}")
    
    # Test 2: Repeat same search (should be cached)
    print(f"\n🔍 Test 2: Repeat same search (should be cached)")
    print(f"Query: '{unique_query}' (same as before)")
    
    try:
        start_time = time.time()
        results2 = rag_service.search_only(
            query=unique_query,
            author_ids=[1, 2],
            limit=5,
            user_id=test_user_id
        )
        search_time2 = time.time() - start_time
        print(f"✅ Cached search completed in {search_time2:.3f}s")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    # Check tokens after second search
    time.sleep(0.5)
    stats_after_2 = token_tracker.get_usage_stats(user_id=test_user_id, days=1)
    tokens_used_2 = stats_after_2['total_tokens'] - stats_after_1['total_tokens']
    print(f"Tokens used in cached search: {tokens_used_2}")
    
    # Test 3: Another unique search
    print(f"\n🔍 Test 3: Another unique search")
    unique_query2 = f"another unique query {uuid.uuid4().hex[:8]}"
    print(f"Query: '{unique_query2}'")
    
    try:
        start_time = time.time()
        results3 = rag_service.search_only(
            query=unique_query2,
            author_ids=[1, 2],
            limit=5,
            user_id=test_user_id
        )
        search_time3 = time.time() - start_time
        print(f"✅ Third search completed in {search_time3:.3f}s")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    # Final token check
    time.sleep(0.5)
    final_stats = token_tracker.get_usage_stats(user_id=test_user_id, days=1)
    tokens_used_3 = final_stats['total_tokens'] - stats_after_2['total_tokens']
    print(f"Tokens used in third search: {tokens_used_3}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Search 1 (unique):  {search_time1:.3f}s, {tokens_used_1} tokens")
    print(f"Search 2 (cached):  {search_time2:.3f}s, {tokens_used_2} tokens")
    print(f"Search 3 (unique):  {search_time3:.3f}s, {tokens_used_3} tokens")
    
    total_new_ops = final_stats['operations_count'] - initial_stats['operations_count']
    total_new_tokens = final_stats['total_tokens'] - initial_stats['total_tokens']
    total_new_cost = final_stats['total_cost'] - initial_stats['total_cost']
    
    print(f"\nTotal new operations: {total_new_ops}")
    print(f"Total new tokens: {total_new_tokens}")
    print(f"Total new cost: ${total_new_cost:.6f}")
    
    print("\n💡 Key Insights:")
    print("- Unique queries use tokens for embedding generation")
    print("- Cached queries use 0 tokens (much faster)")
    print("- Embedding tokens are small (5-50) compared to RAG answers (1000+)")
    print("- The system aggressively caches to minimize costs")

if __name__ == "__main__":
    demo_search_caching()