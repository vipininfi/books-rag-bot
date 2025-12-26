#!/usr/bin/env python3
"""
Test script to verify token tracking for search operations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import RAGService
from app.services.token_tracker import token_tracker
import time

def test_search_token_tracking():
    """Test if search operations are properly tracked."""
    print("🔍 Testing Search Token Tracking")
    print("=" * 50)
    
    # Clear any existing logs for clean test
    print("📊 Getting initial token stats...")
    initial_stats = token_tracker.get_usage_stats(user_id=999, days=1)
    print(f"Initial operations for user 999: {initial_stats['operations_count']}")
    
    # Create RAG service
    rag_service = RAGService()
    
    # Test search operation
    print("\n🔍 Performing test search...")
    try:
        # This should trigger an embedding API call
        results = rag_service.search_only(
            query="test search query for token tracking",
            author_ids=[1, 2],  # Dummy author IDs
            limit=5,
            user_id=999  # Test user ID
        )
        
        print(f"✅ Search completed. Found {len(results)} results")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        print("This might be expected if you don't have vector store configured")
    
    # Check token stats after search
    print("\n📊 Checking token usage after search...")
    time.sleep(1)  # Give time for logging
    
    final_stats = token_tracker.get_usage_stats(user_id=999, days=1)
    print(f"Final operations for user 999: {final_stats['operations_count']}")
    
    new_operations = final_stats['operations_count'] - initial_stats['operations_count']
    print(f"New operations logged: {new_operations}")
    
    if new_operations > 0:
        print("✅ Token tracking is working for search!")
        
        # Show recent operations
        recent = token_tracker.get_recent_operations(user_id=999, limit=5)
        for op in recent:
            print(f"  - {op['operation_type']}: {op['total_tokens']} tokens, ${op['cost_estimate']:.6f}")
    else:
        print("⚠️  No new token usage logged. Possible reasons:")
        print("  1. Embedding was cached (no API call needed)")
        print("  2. Vector store not configured")
        print("  3. Token tracking not working properly")
        
        # Let's test embedding directly
        print("\n🧪 Testing embedding service directly...")
        try:
            embedding = rag_service.embedding_service.embed_query(
                "direct embedding test query", 
                user_id=999
            )
            print(f"✅ Direct embedding generated: {len(embedding)} dimensions")
            
            # Check again
            time.sleep(1)
            final_stats2 = token_tracker.get_usage_stats(user_id=999, days=1)
            new_ops2 = final_stats2['operations_count'] - final_stats['operations_count']
            print(f"New operations after direct embedding: {new_ops2}")
            
        except Exception as e:
            print(f"❌ Direct embedding failed: {e}")

if __name__ == "__main__":
    test_search_token_tracking()