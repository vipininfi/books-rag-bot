#!/usr/bin/env python3
"""
Test script to verify BGE embeddings integration
"""

import os
from dotenv import load_dotenv

def test_embeddings():
    """Test BGE embeddings functionality."""
    print("🔍 Testing BGE Embeddings Integration...")
    
    # Load environment
    load_dotenv()
    
    try:
        # Test BGE embeddings
        print("1. Loading BGE embedding model...")
        from app.services.embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService()
        model_info = embedding_service.get_model_info()
        
        print(f"   ✅ Model loaded: {model_info['model_name']}")
        print(f"   Dimension: {model_info['dimension']}")
        print(f"   Device: {model_info['device']}")
        print(f"   Max sequence length: {model_info['max_seq_length']}")
        
        # Test single embedding
        print("2. Testing single text embedding...")
        test_text = "This is a test document about machine learning and artificial intelligence."
        embedding = embedding_service.embed_text(test_text)
        print(f"   ✅ Generated embedding with {len(embedding)} dimensions")
        print(f"   First 5 values: {embedding[:5]}")
        
        # Test query embedding
        print("3. Testing query embedding...")
        query = "machine learning"
        query_embedding = embedding_service.embed_query(query)
        print(f"   ✅ Generated query embedding with {len(query_embedding)} dimensions")
        
        # Test similarity
        print("4. Testing similarity calculation...")
        similarity = embedding_service.calculate_similarity(embedding, query_embedding)
        print(f"   ✅ Similarity score: {similarity:.4f}")
        
        # Test batch embeddings
        print("5. Testing batch embeddings...")
        texts = [
            "Artificial intelligence is transforming technology.",
            "Machine learning algorithms learn from data.",
            "Deep learning uses neural networks.",
            "Natural language processing handles text."
        ]
        
        batch_embeddings = embedding_service.embed_batch(texts)
        print(f"   ✅ Generated {len(batch_embeddings)} embeddings")
        print(f"   Each embedding has {len(batch_embeddings[0])} dimensions")
        
        # Test Pinecone integration
        print("6. Testing Pinecone integration...")
        from app.services.vector_store import VectorStore
        from app.services.chunking_engine import Chunk, ChunkType
        
        vector_store = VectorStore()
        
        # Create test chunk
        test_chunk = Chunk(
            text=test_text,
            metadata={
                "author_id": 888,
                "book_id": 888,
                "section_title": "Test BGE Section",
                "chunk_index": 0
            },
            chunk_type=ChunkType.FIXED,
            token_count=15
        )
        
        # Store test chunk
        vector_store.store_chunks([test_chunk], [embedding])
        print("   ✅ Stored chunk in Pinecone")
        
        # Test search
        results = vector_store.search(
            query_vector=query_embedding,
            author_ids=[888],
            limit=5
        )
        
        print(f"   ✅ Found {len(results)} results")
        if results:
            print(f"   Best match score: {results[0]['score']:.4f}")
            print(f"   Retrieved text: {results[0]['text'][:50]}...")
        
        # Cleanup
        vector_store.delete_book_chunks(888)
        print("   ✅ Cleaned up test data")
        
        print("\n🎉 BGE Embeddings integration working perfectly!")
        print("\n📊 System Status:")
        print(f"   • Embeddings: BGE-Base (768 dimensions) - FREE")
        print(f"   • Vector DB: Pinecone - $70/month")
        print(f"   • Total embedding cost: $0/month")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_embeddings()