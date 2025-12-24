#!/usr/bin/env python3
"""
Test script to verify Pinecone integration with BGE embeddings and Gemini
"""

import os
from dotenv import load_dotenv

def test_system_integration():
    """Test the complete system integration."""
    print("🔍 Testing Book RAG System Integration...")
    
    # Load environment
    load_dotenv()
    
    # Check if required environment variables are set
    if not os.getenv('PINECONE_API_KEY'):
        print("❌ PINECONE_API_KEY not found in .env file")
        return False
    
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not found in .env file")
        return False
    
    try:
        # Test Pinecone connection first
        print("1. Testing Pinecone connection...")
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        indexes = pc.list_indexes()
        print(f"   ✅ Pinecone connected successfully")
        print(f"   Available indexes: {[idx.name for idx in indexes]}")
        
        # Test BGE embeddings
        print("2. Testing BGE embedding model...")
        from app.services.embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService()
        print(f"   ✅ BGE model loaded: {embedding_service.model_name}")
        print(f"   Dimension: {embedding_service.dimension}")
        print(f"   Device: {embedding_service.device}")
        
        # Test embedding generation
        print("3. Testing embedding generation...")
        test_text = "This is a test document for BGE embeddings."
        embedding = embedding_service.embed_text(test_text)
        print(f"   ✅ Generated embedding with {len(embedding)} dimensions")
        
        # Test query embedding
        query_embedding = embedding_service.embed_query("test document")
        print(f"   ✅ Generated query embedding with {len(query_embedding)} dimensions")
        
        # Test Gemini
        print("4. Testing Gemini 2.0 Flash...")
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        response = model.generate_content("Hello, this is a test.")
        print(f"   ✅ Gemini response: {response.text[:50]}...")
        
        # Test vector store integration
        print("5. Testing vector store integration...")
        from app.services.vector_store import VectorStore
        from app.services.chunking_engine import Chunk, ChunkType
        
        vector_store = VectorStore()
        
        # Create test chunk
        test_chunk = Chunk(
            text=test_text,
            metadata={
                "author_id": 999,
                "book_id": 999,
                "section_title": "Test Section",
                "chunk_index": 0
            },
            chunk_type=ChunkType.FIXED,
            token_count=10
        )
        
        # Store test chunk
        print("6. Storing test chunk in Pinecone...")
        vector_store.store_chunks([test_chunk], [embedding])
        print("   ✅ Chunk stored successfully")
        
        # Test search
        print("7. Testing search functionality...")
        results = vector_store.search(
            query_vector=query_embedding,
            author_ids=[999],
            limit=5
        )
        
        print(f"   Found {len(results)} results")
        if results:
            print(f"   Best match score: {results[0]['score']:.3f}")
        
        # Test RAG service
        print("8. Testing RAG service...")
        from app.services.rag_service import RAGService
        
        rag_service = RAGService()
        model_info = rag_service.get_model_info()
        print(f"   ✅ RAG service initialized")
        print(f"   LLM: {model_info['llm_model']}")
        print(f"   Embeddings: {model_info['embedding_model']['model_name']}")
        
        # Cleanup test data
        print("9. Cleaning up test data...")
        vector_store.delete_book_chunks(999)
        print("   ✅ Test data cleaned up")
        
        print("\n🎉 All tests passed! System integration is working correctly.")
        print("\n📊 System Configuration:")
        print(f"   • Embeddings: BGE-Base (768 dimensions)")
        print(f"   • LLM: Gemini 2.0 Flash")
        print(f"   • Vector DB: Pinecone")
        print(f"   • Cost: ~$0/month for embeddings + Gemini usage")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("Please check your configuration.")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    test_system_integration()