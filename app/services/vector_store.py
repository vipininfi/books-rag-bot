from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import uuid
import time
import threading

from app.core.config import settings
from app.services.chunking_engine import Chunk

# Global Pinecone client for connection reuse
_pinecone_client = None
_pinecone_index = None
_client_lock = threading.Lock()

def get_pinecone_client():
    """Get shared Pinecone client and index for connection reuse."""
    global _pinecone_client, _pinecone_index
    
    if _pinecone_client is None or _pinecone_index is None:
        with _client_lock:
            if _pinecone_client is None:
                _pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
                _pinecone_index = _pinecone_client.Index(settings.PINECONE_INDEX_NAME)
                print(f"🔗 Initialized shared Pinecone connection to {settings.PINECONE_INDEX_NAME}")
    
    return _pinecone_client, _pinecone_index


class VectorStore:
    """Handles vector storage and retrieval using Pinecone."""
    
    def __init__(self):
        # Use shared client for connection reuse
        self.pc, self.index = get_pinecone_client()
        self.index_name = settings.PINECONE_INDEX_NAME
        self.vector_size = 1536  # OpenAI text-embedding-3-small dimension
        
        print(f"Vector store initialized with shared connection")
    
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
        """Store chunks with their embeddings in Pinecone WITH full text in metadata."""
        # Group chunks by author for namespace storage
        chunks_by_author = {}
        embeddings_by_author = {}
        all_chunk_ids = []
        
        for chunk, embedding in zip(chunks, embeddings):
            author_id = chunk.metadata["author_id"]
            if author_id not in chunks_by_author:
                chunks_by_author[author_id] = []
                embeddings_by_author[author_id] = []
            
            chunks_by_author[author_id].append(chunk)
            embeddings_by_author[author_id].append(embedding)
        
        # Store each author's chunks in their namespace
        for author_id, author_chunks in chunks_by_author.items():
            namespace = f"author_{author_id}"
            author_embeddings = embeddings_by_author[author_id]
            
            print(f"Storing {len(author_chunks)} chunks for author {author_id} in namespace {namespace}")
            
            vectors_to_upsert = []
            
            for chunk, embedding in zip(author_chunks, author_embeddings):
                vector_id = str(uuid.uuid4())
                all_chunk_ids.append(vector_id)
                
                # CRITICAL FIX: Keep full text in metadata for RAG
                metadata = {
                    "author_id": chunk.metadata["author_id"],
                    "book_id": chunk.metadata["book_id"],
                    "section_title": chunk.metadata["section_title"][:100],  # Truncate long titles
                    "chunk_index": chunk.metadata["chunk_index"],
                    "chunk_type": chunk.chunk_type.value,
                    "token_count": chunk.token_count,
                    "page_number": chunk.metadata.get("page_number", 1),
                    "text": chunk.text[:8000],  # Store full text (up to 8000 chars for Pinecone limits)
                    "chunk_id": vector_id  # Store ID to fetch from DB if needed
                }
                
                vectors_to_upsert.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Batch upsert with optimized batch size
            batch_size = 100  # Reduced batch size due to larger metadata
            
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                try:
                    self.index.upsert(vectors=batch, namespace=namespace)
                    print(f"Upserted batch {i//batch_size + 1}/{(len(vectors_to_upsert) + batch_size - 1)//batch_size} to {namespace}")
                except Exception as e:
                    print(f"Error upserting batch to {namespace}: {str(e)}")
                    raise e
        
        return all_chunk_ids  # Return the generated IDs
    
    def search(
        self, 
        query_vector: List[float], 
        author_ids: List[int], 
        limit: int = 20,
        score_threshold: float = 0.4
    ) -> List[Dict[str, Any]]:
        """CRITICAL FIX: Parallel namespace queries instead of serial."""
        
        search_start = time.time()
        print(f"🚀 PARALLEL Pinecone Search: {len(author_ids)} authors, limit={limit}")
        
        # CRITICAL FIX #1: Parallel execution for multiple namespaces
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def query_namespace(author_id: int):
            """Query a single author namespace."""
            namespace = f"author_{author_id}"
            ns_start = time.time()
            
            try:
                search_results = self.index.query(
                    vector=query_vector,
                    namespace=namespace,
                    top_k=limit,  # No over-fetching
                    include_metadata=True,
                    include_values=False
                )
                
                ns_time = time.time() - ns_start
                print(f"📊 Author {author_id} namespace: {ns_time:.3f}s - {len(search_results.matches)} matches")
                
                # Process results for this namespace
                results = []
                for match in search_results.matches:
                    if match.score >= score_threshold:
                        result = {
                            "id": match.id,
                            "score": match.score,
                            "author_id": match.metadata.get("author_id"),
                            "book_id": match.metadata.get("book_id"),
                            "section_title": match.metadata.get("section_title", ""),
                            "chunk_type": match.metadata.get("chunk_type", ""),
                            "token_count": match.metadata.get("token_count", 0),
                            "page_number": match.metadata.get("page_number", 1),
                            "chunk_id": match.metadata.get("chunk_id", match.id),
                            "text": match.metadata.get("text", "")  # Get full text from Pinecone metadata
                        }
                        results.append(result)
                
                return results, ns_time
                
            except Exception as e:
                print(f"⚠️ Error in namespace author_{author_id}: {e}")
                return [], 0.0
        
        # PARALLEL EXECUTION - This is the key fix!
        all_results = []
        namespace_times = []
        
        with ThreadPoolExecutor(max_workers=min(len(author_ids), 4)) as executor:
            # Submit all namespace queries simultaneously
            future_to_author = {
                executor.submit(query_namespace, author_id): author_id 
                for author_id in author_ids
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_author):
                author_id = future_to_author[future]
                try:
                    results, ns_time = future.result()
                    all_results.extend(results)
                    namespace_times.append(ns_time)
                except Exception as e:
                    print(f"❌ Failed to query author {author_id}: {e}")
        
        # Sort by score and limit results
        all_results.sort(key=lambda x: x["score"], reverse=True)
        final_results = all_results[:limit]
        
        total_time = time.time() - search_start
        max_ns_time = max(namespace_times) if namespace_times else 0
        
        print(f"⚡ PARALLEL Search Complete: {total_time:.3f}s - {len(final_results)} results")
        print(f"   - Max namespace time: {max_ns_time:.3f}s")
        print(f"   - Parallel efficiency: {(max_ns_time/total_time)*100:.1f}%")
        
        if final_results:
            scores = [r["score"] for r in final_results]
            print(f"📊 Score range: {min(scores):.3f} - {max(scores):.3f}")
        
        return final_results
    
    def _search_single_namespace_with_filter(
        self, 
        query_vector: List[float], 
        author_ids: List[int], 
        limit: int, 
        score_threshold: float
    ) -> List[Dict[str, Any]]:
        """OPTIMIZATION: Single query with filter for small datasets."""
        
        print(f"🎯 Single namespace search with filter (small dataset optimization)")
        
        # Use filter instead of multiple namespaces for small datasets
        filter_dict = {
            "author_id": {"$in": author_ids}
        }
        
        try:
            query_start = time.time()
            search_results = self.index.query(
                vector=query_vector,
                filter=filter_dict,
                top_k=limit * 2,  # Slight over-fetch for filtering
                include_metadata=True,
                include_values=False,
                namespace=""  # Use default namespace
            )
            query_time = time.time() - query_start
            
            print(f"📊 Filtered search: {query_time:.3f}s - {len(search_results.matches)} matches")
            
            # Process results
            results = []
            for match in search_results.matches:
                if match.score >= score_threshold:
                    result = {
                        "id": match.id,
                        "score": match.score,
                        "author_id": match.metadata.get("author_id"),
                        "book_id": match.metadata.get("book_id"),
                        "section_title": match.metadata.get("section_title", ""),
                        "chunk_type": match.metadata.get("chunk_type", ""),
                        "token_count": match.metadata.get("token_count", 0),
                        "page_number": match.metadata.get("page_number", 1),
                        "chunk_id": match.metadata.get("chunk_id", match.id),
                        "text": match.metadata.get("text", "")  # Get full text from Pinecone metadata
                    }
                    results.append(result)
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            print(f"❌ Error in filtered search: {e}")
            return []
    
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