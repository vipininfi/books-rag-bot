#!/usr/bin/env python3
"""
Setup Pinecone index for BGE embeddings (768 dimensions)
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import time

def setup_pinecone_index():
    """Setup Pinecone index with correct dimensions for BGE."""
    print("🔧 Setting up Pinecone index for BGE embeddings...")
    
    # Load environment
    load_dotenv()
    
    if not os.getenv('PINECONE_API_KEY'):
        print("❌ PINECONE_API_KEY not found in .env file")
        return False
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index_name = os.getenv('PINECONE_INDEX_NAME', 'book-chunks')
        
        # Check existing indexes
        existing_indexes = [index.name for index in pc.list_indexes()]
        print(f"Existing indexes: {existing_indexes}")
        
        if index_name in existing_indexes:
            # Get index info
            index_info = pc.describe_index(index_name)
            current_dimension = index_info.dimension
            
            print(f"Found existing index '{index_name}' with {current_dimension} dimensions")
            
            if current_dimension == 768:
                print("✅ Index already has correct dimensions for BGE (768)")
                return True
            else:
                print(f"❌ Index has {current_dimension} dimensions, but BGE needs 768")
                
                # Ask user what to do
                response = input("Do you want to delete and recreate the index? (y/N): ").lower()
                if response != 'y':
                    print("Keeping existing index. You'll need to create a new index with a different name.")
                    return False
                
                # Delete existing index
                print(f"Deleting existing index '{index_name}'...")
                pc.delete_index(index_name)
                
                # Wait for deletion
                print("Waiting for index deletion...")
                while index_name in [idx.name for idx in pc.list_indexes()]:
                    time.sleep(2)
                print("✅ Index deleted")
        
        # Create new index with BGE dimensions
        print(f"Creating new index '{index_name}' with 768 dimensions...")
        
        # Parse environment for region
        env_parts = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1-aws').split('-')
        if len(env_parts) >= 3:
            region = f"{env_parts[0]}-{env_parts[1]}-{env_parts[2]}"
        else:
            region = "us-east-1"
        
        pc.create_index(
            name=index_name,
            dimension=768,  # BGE-Base dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=region
            )
        )
        
        # Wait for index to be ready
        print("Waiting for index to be ready...")
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(2)
        
        print(f"✅ Index '{index_name}' created successfully!")
        
        # Verify index
        index_info = pc.describe_index(index_name)
        print(f"   Dimension: {index_info.dimension}")
        print(f"   Metric: {index_info.metric}")
        print(f"   Status: {index_info.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up index: {str(e)}")
        return False

if __name__ == "__main__":
    success = setup_pinecone_index()
    if success:
        print("\n🎉 Pinecone index setup complete!")
        print("You can now run: python test_embeddings.py")
    else:
        print("\n❌ Index setup failed")