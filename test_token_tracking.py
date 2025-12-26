#!/usr/bin/env python3
"""
Test script for token tracking functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.token_tracker import token_tracker
import time

def test_token_logging():
    """Test basic token logging functionality."""
    print("🧪 Testing Token Tracking System")
    print("=" * 50)
    
    # Test logging a sample operation
    print("📝 Logging sample operations...")
    
    # Sample RAG operation
    token_tracker.log_usage(
        user_id=123,
        operation_type="rag_answer",
        query="What is the meaning of life?",
        model_name="gpt-4o-mini",
        prompt_tokens=1250,
        completion_tokens=150,
        response_time=2.34,
        success=True
    )
    
    # Sample embedding operation
    token_tracker.log_usage(
        user_id=123,
        operation_type="embedding",
        query="search query example",
        model_name="text-embedding-3-small",
        prompt_tokens=50,
        completion_tokens=0,
        response_time=0.45,
        success=True
    )
    
    # Sample failed operation
    token_tracker.log_usage(
        user_id=456,
        operation_type="rag_answer",
        query="another test query",
        model_name="gpt-4o-mini",
        prompt_tokens=0,
        completion_tokens=0,
        response_time=1.0,
        success=False,
        error_message="API rate limit exceeded"
    )
    
    print("✅ Sample operations logged successfully!")
    
    # Test statistics
    print("\n📊 Getting usage statistics...")
    stats = token_tracker.get_usage_stats(days=1)
    
    print(f"Total operations: {stats['operations_count']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Total cost: ${stats['total_cost']:.6f}")
    print(f"Success rate: {(stats['operations_count'] - len(stats.get('failed_operations', []))) / stats['operations_count'] * 100:.1f}%")
    
    # Test user-specific stats
    print("\n👤 User-specific statistics...")
    user_stats = token_tracker.get_usage_stats(user_id=123, days=1)
    print(f"User 123 operations: {user_stats['operations_count']}")
    print(f"User 123 tokens: {user_stats['total_tokens']}")
    print(f"User 123 cost: ${user_stats['total_cost']:.6f}")
    
    # Test recent operations
    print("\n🕒 Recent operations...")
    recent = token_tracker.get_recent_operations(limit=5)
    for i, op in enumerate(recent, 1):
        print(f"{i}. {op['timestamp']} | User {op['user_id']} | {op['operation_type']} | {op['total_tokens']} tokens")
    
    print("\n✅ Token tracking test completed successfully!")
    print(f"📁 Log file: {token_tracker.log_file}")

if __name__ == "__main__":
    test_token_logging()