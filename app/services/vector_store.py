from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import uuid
import time

from app.core.config import settings
from app.services.chunking_engine import Chunk


class VectorStore:
    """Handles vector storage and retrieval using Pinecone."""
    
    def __init__(self):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.vector_size = 768  # BGE-Base dimension
        
        # Ensure index exists
        self._ensure_index()
        
        # Get index reference
        self.index = self.pc.Index(self.index_name)
    
    def _ensure_index(self):
        """Create index if it doesn't exist."""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                print(f"Creating Pinecone index: {self.index_name}")
                
                # Parse environment for region
                env_parts = settings.PINECONE_ENVIRONMENT.split('-')
                if len(env_parts) >= 3:
                    region = f"{env_parts[0]}-{env_parts[1]}-{env_parts[2]}"
                else:
                    region = "us-east-1"  # fallback
                
                # Create index with serverless spec
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.vector_size,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=region
                    )
                )
                
                # Wait for index to be ready
                print("Waiting for index to be ready...")
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
                
                print(f"Index {self.index_name} created successfully")
            else:
                print(f"Index {self.index_name} already exists")
                
        except Exception as e:
            print(f"Error ensuring index exists: {str(e)}")
            raise e
    
    def store_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]):
        """Store chunks with their embeddings in Pinecone."""
        vectors_to_upsert = []
        
        for chunk, embedding in zip(chunks, embeddings):
            vector_id = str(uuid.uuid4())
            
            # Prepare metadata (Pinecone has metadata size limits)
            metadata = {
                "author_id": chunk.metadata["author_id"],
                "book_id": chunk.metadata["book_id"],
                "section_title": chunk.metadata["section_title"][:100],  # Truncate long titles
                "chunk_index": chunk.metadata["chunk_index"],
                "chunk_type": chunk.chunk_type.value,
                "token_count": chunk.token_count,
                "page_number": chunk.metadata.get("page_number", 1),
                "text": chunk.text[:8000]  # Pinecone metadata limit, store first 8k chars
            }
            
            vectors_to_upsert.append({
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            })
        
        # Batch upsert (Pinecone handles batching automatically)
        batch_size = 100  # Pinecone recommended batch size
        
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                print(f"Upserted batch {i//batch_size + 1}/{(len(vectors_to_upsert) + batch_size - 1)//batch_size}")
            except Exception as e:
                print(f"Error upserting batch: {str(e)}")
                raise e
    
    def search(
        self, 
        query_vector: List[float], 
        author_ids: List[int], 
        limit: int = 20,
        score_threshold: float = 0.6  # Lowered from 0.7 to get more results
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks with author filtering."""
        
        # Pinecone filter format
        filter_dict = {
            "author_id": {"$in": author_ids}
        }
        
        try:
            # Perform search
            search_results = self.index.query(
                vector=query_vector,
                filter=filter_dict,
                top_k=limit,
                include_metadata=True,
                include_values=False
            )
            
            results = []
            for match in search_results.matches:
                # Only include results above threshold
                if match.score >= score_threshold:
                    results.append({
                        "id": match.id,
                        "score": match.score,
                        "text": match.metadata.get("text", ""),
                        "author_id": match.metadata.get("author_id"),
                        "book_id": match.metadata.get("book_id"),
                        "section_title": match.metadata.get("section_title", ""),
                        "chunk_type": match.metadata.get("chunk_type", ""),
                        "token_count": match.metadata.get("token_count", 0),
                        "page_number": match.metadata.get("page_number", 1)
                    })
            
            return results
            
        except Exception as e:
            print(f"Error searching Pinecone: {str(e)}")
            raise e
    
    def delete_book_chunks(self, book_id: int):
        """Delete all chunks for a specific book."""
        try:
            # Pinecone delete by metadata filter
            self.index.delete(
                filter={
                    "book_id": {"$eq": book_id}
                }
            )
            print(f"Deleted chunks for book_id: {book_id}")
            
        except Exception as e:
            print(f"Error deleting book chunks: {str(e)}")
            raise e
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            stats = self.index.describe_index_stats()
            index_description = self.pc.describe_index(self.index_name)
            
            return {
                "total_points": stats.total_vector_count,
                "vector_size": index_description.dimension,
                "distance": index_description.metric,
                "namespaces": stats.namespaces
            }
            
        except Exception as e:
            print(f"Error getting collection info: {str(e)}")
            return {
                "total_points": 0,
                "vector_size": self.vector_size,
                "distance": "cosine",
                "namespaces": {}
            }