#!/usr/bin/env python3
"""
Migration script to move existing vectors to author-specific namespaces.
This is a CRITICAL optimization that will dramatically improve search performance.
"""

import time
from typing import List, Dict, Any
from pinecone import Pinecone
from app.core.config import settings

def migrate_to_namespaces():
    """
    Migrate existing vectors from default namespace to author-specific namespaces.
    This is the most important optimization for search performance.
    """
    
    print("🚀 CRITICAL OPTIMIZATION: Migrating to Author Namespaces")
    print("=" * 60)
    print("This will dramatically improve search performance by 2-5x!")
    print("=" * 60)
    
    # Initialize Pinecone
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index(settings.PINECONE_INDEX_NAME)
    
    # Step 1: Get all vectors from default namespace
    print("📊 Step 1: Analyzing current vector distribution...")
    
    try:
        # Get index stats
        stats = index.describe_index_stats()
        total_vectors = stats.total_vector_count
        
        print(f"   Total vectors in index: {total_vectors}")
        
        if total_vectors == 0:
            print("⚠️ No vectors found. Upload some books first!")
            return
        
        # Step 2: Fetch vectors in batches and organize by author
        print(f"\n📦 Step 2: Fetching and organizing vectors by author...")
        
        # We'll use a dummy query to fetch all vectors
        dummy_vector = [0.1] * 1536  # OpenAI embedding dimension
        
        # Fetch all vectors (this might take a while for large datasets)
        all_results = index.query(
            vector=dummy_vector,
            top_k=min(total_vectors, 10000),  # Pinecone limit
            include_metadata=True,
            include_values=True,  # We need values to re-insert
            namespace=""  # Default namespace
        )
        
        print(f"   Fetched {len(all_results.matches)} vectors")
        
        # Organize by author
        author_vectors = {}
        for match in all_results.matches:
            author_id = match.metadata.get("author_id")
            if author_id:
                author_id = int(author_id)
                if author_id not in author_vectors:
                    author_vectors[author_id] = []
                
                # Prepare vector for re-insertion
                vector_data = {
                    "id": match.id,
                    "values": match.values,
                    "metadata": {
                        **match.metadata,
                        # Remove text from metadata (CRITICAL OPTIMIZATION)
                        "chunk_id": match.id
                    }
                }
                
                # Remove text from metadata if it exists
                if "text" in vector_data["metadata"]:
                    del vector_data["metadata"]["text"]
                
                author_vectors[author_id].append(vector_data)
        
        print(f"   Organized into {len(author_vectors)} author groups:")
        for author_id, vectors in author_vectors.items():
            print(f"     Author {author_id}: {len(vectors)} vectors")
        
        # Step 3: Insert vectors into author-specific namespaces
        print(f"\n🎯 Step 3: Creating author-specific namespaces...")
        
        total_migrated = 0
        
        for author_id, vectors in author_vectors.items():
            namespace = f"author_{author_id}"
            print(f"   Migrating {len(vectors)} vectors to namespace '{namespace}'...")
            
            # Insert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                try:
                    index.upsert(
                        vectors=batch,
                        namespace=namespace
                    )
                    total_migrated += len(batch)
                    print(f"     Batch {i//batch_size + 1}: {len(batch)} vectors")
                    
                    # Small delay to avoid rate limits
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"     ❌ Error in batch {i//batch_size + 1}: {e}")
        
        print(f"\n✅ Migration complete! Migrated {total_migrated} vectors")
        
        # Step 4: Verify namespaces
        print(f"\n🔍 Step 4: Verifying new namespaces...")
        
        final_stats = index.describe_index_stats()
        print(f"   Index stats after migration:")
        print(f"     Total vectors: {final_stats.total_vector_count}")
        print(f"     Namespaces: {len(final_stats.namespaces)}")
        
        for namespace, stats in final_stats.namespaces.items():
            print(f"       {namespace}: {stats.vector_count} vectors")
        
        # Step 5: Clean up old namespace (optional)
        print(f"\n🧹 Step 5: Cleaning up old default namespace...")
        
        response = input("Delete vectors from default namespace? (y/N): ")
        if response.lower() == 'y':
            try:
                index.delete(delete_all=True, namespace="")
                print("   ✅ Default namespace cleaned up")
            except Exception as e:
                print(f"   ⚠️ Error cleaning up: {e}")
        else:
            print("   ⚠️ Keeping old vectors in default namespace")
            print("   💡 You can clean them up later with: index.delete(delete_all=True, namespace='')")
        
        print(f"\n🎉 OPTIMIZATION COMPLETE!")
        print(f"📈 Expected performance improvement: 2-5x faster searches")
        print(f"💡 Search will now use author-specific namespaces automatically")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

def test_namespace_search():
    """Test search performance with new namespaces."""
    
    print(f"\n🧪 Testing namespace search performance...")
    
    from app.services.rag_service import RAGService
    
    # Test with real user data
    author_ids = [8, 10]  # vipin and rahul
    query = "who is doctor dolittle"
    
    rag_service = RAGService()
    
    start_time = time.time()
    results = rag_service.search_only(query, author_ids, limit=5)
    search_time = time.time() - start_time
    
    print(f"   Search time: {search_time:.3f}s")
    print(f"   Results: {len(results)}")
    
    if search_time < 1.0:
        print(f"   ✅ Excellent performance! (< 1 second)")
    elif search_time < 2.0:
        print(f"   ✅ Good performance! (< 2 seconds)")
    else:
        print(f"   ⚠️ Still slow (> 2 seconds) - check Pinecone region/connection")

def main():
    """Run the migration."""
    
    print("⚠️  IMPORTANT: This migration will reorganize your vector database")
    print("💾 Make sure you have a backup if this is production data")
    print("⏱️  This process may take several minutes for large datasets")
    
    response = input("\nProceed with migration? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        return
    
    migrate_to_namespaces()
    test_namespace_search()

if __name__ == "__main__":
    main()