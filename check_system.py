#!/usr/bin/env python3
"""
System status checker for Book RAG System
"""

import os
from dotenv import load_dotenv

def check_system_status():
    """Check the status of all system components."""
    print("🔍 Book RAG System Status Check")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    status = {
        "pinecone": False,
        "gemini": False,
        "embeddings": False,
        "database": False,
        "overall": False
    }
    
    # Check Pinecone
    print("\n📊 Pinecone Vector Database")
    try:
        if not os.getenv('PINECONE_API_KEY'):
            print("❌ PINECONE_API_KEY not found")
        else:
            from pinecone import Pinecone
            pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            indexes = pc.list_indexes()
            print(f"✅ Connected successfully")
            print(f"   API Key: {os.getenv('PINECONE_API_KEY')[:20]}...")
            print(f"   Indexes: {[idx.name for idx in indexes]}")
            status["pinecone"] = True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
    
    # Check Gemini
    print("\n🤖 Gemini AI")
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        print("❌ GEMINI_API_KEY not configured")
        print("   Add your Gemini API key to .env file")
    else:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content("Hello")
            print("✅ API key valid")
            print(f"   Key: {gemini_key[:20]}...")
            print(f"   Model: gemini-2.5-flash")
            status["gemini"] = True
        except Exception as e:
            print(f"❌ API key invalid: {str(e)}")
    
    # Check BGE Embeddings
    print("\n🔤 BGE Embeddings")
    try:
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        model_info = embedding_service.get_model_info()
        print("✅ BGE model loaded successfully")
        print(f"   Model: {model_info['model_name']}")
        print(f"   Dimension: {model_info['dimension']}")
        print(f"   Device: {model_info['device']}")
        status["embeddings"] = True
    except Exception as e:
        print(f"❌ BGE model loading failed: {str(e)}")
        print("   Run: pip install sentence-transformers torch")
    
    # Check Database
    print("\n🗄️  PostgreSQL Database")
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not configured")
    else:
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✅ Database connection successful")
                print(f"   URL: {db_url.split('@')[0]}@***")
                status["database"] = True
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            print("   Make sure PostgreSQL is running and database exists")
    
    # Overall status
    print("\n" + "=" * 50)
    ready_components = sum(status.values())
    total_components = len(status) - 1  # Exclude 'overall'
    
    if ready_components == total_components:
        print("🎉 System Ready! All components operational")
        status["overall"] = True
        print("\nNext steps:")
        print("1. Start API: python start_server.py")
        print("2. Visit: http://localhost:8001/docs")
    else:
        print(f"⚠️  System Partially Ready ({ready_components}/{total_components} components)")
        print("\nRequired actions:")
        if not status["pinecone"]:
            print("- Fix Pinecone configuration")
        if not status["gemini"]:
            print("- Add Gemini API key to .env")
        if not status["embeddings"]:
            print("- Install BGE embedding dependencies")
        if not status["database"]:
            print("- Setup PostgreSQL database")
    
    return status

if __name__ == "__main__":
    check_system_status()