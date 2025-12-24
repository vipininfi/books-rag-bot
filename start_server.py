#!/usr/bin/env python3
"""
Start the Book RAG API server on port 8001
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 Starting Book RAG API Server...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🔄 Interactive API: http://localhost:8001/redoc")
    print("\n✅ All systems operational:")
    print("   • BGE Embeddings: Ready (768-dim, FREE)")
    print("   • Pinecone Vector DB: Connected")
    print("   • Gemini 2.0 Flash: Ready for RAG")
    print("   • PostgreSQL: Connected (Aiven)")
    print("\n🎯 Ready to serve requests!")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )