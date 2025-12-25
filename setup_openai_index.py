#!/usr/bin/env python3
"""
Setup script for creating a new Pinecone index with OpenAI embedding dimensions.
This script will create a new index specifically for OpenAI text-embedding-3-small (1536 dimensions).
"""

import os
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_openai_pinecone_index():
    """Create a new Pinecone index for OpenAI embeddings."""
    
    # Get configuration from environment
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
    index_name = os.getenv("PINECONE_INDEX_NAME", "book-chunks-openai")
    
    if not api_key:
        print("❌ Error: PINECONE_API_KEY not found in environment variables")
        return False
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        
        print(f"🔧 Setting up Pinecone index: {index_name}")
        print(f"📊 Dimensions: 1536 (OpenAI text-embedding-3-small)")
        print(f"🌍 Environment: {environment}")
        
        # Check if index already exists
        existing_indexes = [index.name for index in pc.list_indexes()]
        
        if index_name in existing_indexes:
            print(f"⚠️  Index '{index_name}' already exists!")
            
            # Get index info
            index_info = pc.describe_index(index_name)
            print(f"📋 Current index dimensions: {index_info.dimension}")
            
            if index_info.dimension != 1536:
                print(f"❌ Existing index has wrong dimensions ({index_info.dimension} instead of 1536)")
                print(f"💡 You may need to delete the old index and create a new one")
                
                response = input("Do you want to delete the existing index and create a new one? (y/N): ")
                if response.lower() == 'y':
                    print(f"🗑️  Deleting existing index: {index_name}")
                    pc.delete_index(index_name)
                    
                    # Wait for deletion to complete
                    print("⏳ Waiting for index deletion...")
                    time.sleep(10)
                else:
                    print("❌ Keeping existing index. Please update your configuration.")
                    return False
            else:
                print("✅ Existing index has correct dimensions (1536)")
                return True
        
        # Parse environment for region
        env_parts = environment.split('-')
        if len(env_parts) >= 3:
            region = f"{env_parts[0]}-{env_parts[1]}-{env_parts[2]}"
        else:
            region = "us-east-1"  # fallback
        
        print(f"🚀 Creating new index with region: {region}")
        
        # Create index with OpenAI dimensions
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI text-embedding-3-small dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=region
            )
        )
        
        # Wait for index to be ready
        print("⏳ Waiting for index to be ready...")
        while True:
            try:
                index_status = pc.describe_index(index_name)
                if index_status.status['ready']:
                    break
                print("   Still initializing...")
                time.sleep(2)
            except Exception as e:
                print(f"   Checking status: {e}")
                time.sleep(2)
        
        print(f"✅ Index '{index_name}' created successfully!")
        print(f"📊 Dimensions: 1536")
        print(f"📏 Metric: cosine")
        print(f"☁️  Spec: Serverless AWS ({region})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Pinecone index: {str(e)}")
        return False

def verify_openai_setup():
    """Verify that OpenAI API key is configured."""
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("💡 Please add your OpenAI API key to the .env file:")
        print("   OPENAI_API_KEY=your_openai_api_key_here")
        return False
    
    if openai_key == "your_openai_api_key_here":
        print("❌ Please replace the placeholder OpenAI API key with your actual key")
        return False
    
    print("✅ OpenAI API key found")
    return True

def main():
    """Main setup function."""
    print("🤖 OpenAI + Pinecone Setup Script")
    print("=" * 50)
    
    # Verify OpenAI setup
    if not verify_openai_setup():
        return
    
    # Setup Pinecone index
    if setup_openai_pinecone_index():
        print("\n🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Install new dependencies: pip install -r requirements.txt")
        print("2. Add your OpenAI API key to .env file")
        print("3. Clear old vector data if needed: python clear_vector_db.py")
        print("4. Upload books to populate the new index")
        print("\n💰 Cost Information:")
        print("- OpenAI text-embedding-3-small: $0.00002 per 1K tokens")
        print("- OpenAI GPT-4o mini: $0.00015 per 1K input tokens, $0.0006 per 1K output tokens")
        print("- Significantly cheaper than previous setup!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()