#!/usr/bin/env python3
"""
Sync chunks from Pinecone to database for faster text retrieval.
This is a one-time migration script.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store import VectorStore
from app.models.chunk import Chunk
from app.db.database import SessionLocal
from sqlalchemy.orm import Session
import time

def sync_chunks_from_pinecone():
    """Extract chunks from Pinecone and store in database."""
    
    print("🔄 Starting Pinecone → Database sync...")
    
    # Initialize services
    vs = VectorStore()
    db: Session = SessionLocal()
    
    try:
        # Get index stats to see what namespaces exist
        info = vs.get_collection_info()
        print(f"📊 Index stats: {info}")
        
        namespaces = info.get("namespaces", {})
        total_synced = 0
        
        for namespace_name, namespace_info in namespaces.items():
            if not namespace_name.startswith("author_"):
                continue
                
            author_id = int(namespace_name.replace("author_", ""))
            vector_count = namespace_info.get("vector_count", 0)
            
            print(f"\n📚 Processing namespace {namespace_name} ({vector_count} vectors)...")
            
            # Query all vectors in this namespace
            # Note: Pinecone doesn't have a "list all" API, so we'll use a dummy query
            # with a very high top_k to get all vectors
            try:
                dummy_vector = [0.0] * 1536  # Zero vector
                
                search_results = vs.index.query(
                    vector=dummy_vector,
                    namespace=namespace_name,
                    top_k=10000,  # Get all vectors
                    include_metadata=True,
                    include_values=False
                )
                
                print(f"📥 Retrieved {len(search_results.matches)} vectors from {namespace_name}")
                
                # Process each vector
                for match in search_results.matches:
                    metadata = match.metadata
                    
                    # Check if chunk already exists
                    existing = db.query(Chunk).filter(Chunk.chunk_id == match.id).first()
                    if existing:
                        continue
                    
                    # Create new chunk record
                    chunk = Chunk(
                        chunk_id=match.id,
                        text=metadata.get("text", "Text not available in Pinecone metadata"),
                        section_title=metadata.get("section_title", "Unknown Section"),
                        chunk_index=metadata.get("chunk_index", 0),
                        chunk_type=metadata.get("chunk_type", "content"),
                        token_count=metadata.get("token_count", 0),
                        page_number=metadata.get("page_number", 1),
                        book_id=metadata.get("book_id"),
                        author_id=author_id
                    )
                    
                    db.add(chunk)
                    total_synced += 1
                
                # Commit this namespace
                db.commit()
                print(f"✅ Synced {len(search_results.matches)} chunks from {namespace_name}")
                
            except Exception as e:
                print(f"❌ Error processing namespace {namespace_name}: {e}")
                db.rollback()
        
        print(f"\n🎉 Sync complete! Total chunks synced: {total_synced}")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_chunks_from_pinecone()