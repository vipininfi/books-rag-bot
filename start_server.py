#!/usr/bin/env python3
"""
Start the Book RAG API server on port 8001
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    import os
    
    # Render provides PORT env var
    port = int(os.environ.get("PORT", 8001))
    
    # Check if running on Render
    is_render = os.environ.get("RENDER") == "true"
    
    print(f"🚀 Starting Book RAG API Server...")
    print(f"📍 Server will be available at: http://0.0.0.0:{port}")
    
    if is_render:
        print("🌐 Running in PRODUCTION mode (Render)")
    else:
        print("🔧 Running in DEVELOPMENT mode")
        print(f"📚 API Documentation: http://localhost:{port}/docs")
        print(f"🔄 Interactive API: http://localhost:{port}/redoc")
    
    print("\n✅ All systems operational:")
    print("   • BGE Embeddings: Ready (768-dim, FREE)")
    print("   • Pinecone Vector DB: Connected")
    print("   • Gemini 2.0 Flash: Ready for RAG")
    print("   • PostgreSQL: Connected (Aiven)")
    print("\n🎯 Ready to serve requests!")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_render,  # Disable reload in production
        log_level="info"
    )