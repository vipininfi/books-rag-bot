from openai import OpenAI
from typing import List
import numpy as np
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import threading

from app.core.config import settings
from app.core.cache import persistent_cache

# Global client instance for connection reuse
_openai_client = None
_client_lock = threading.Lock()

def get_openai_client():
    """Get a shared OpenAI client instance for connection reuse."""
    global _openai_client
    if _openai_client is None:
        with _client_lock:
            if _openai_client is None:
                _openai_client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=8.0,  # Reduced timeout for faster failures
                    max_retries=1   # Reduced retries for speed
                )
    return _openai_client


class EmbeddingService:
    """Handles text embedding generation using OpenAI's text-embedding-3-small model."""
    
    def __init__(self):
        # Use shared client for connection reuse
        self.client = get_openai_client()
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.dimension = 1536  # text-embedding-3-small dimension
        
        # In-memory cache for session
        self._session_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        print(f"Initialized OpenAI embedding service with model: {self.model_name}")
        print(f"Embedding dimension: {self.dimension}")
    
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        persistent_stats = persistent_cache.get_stats()
        
        return {
            "session_cache_size": len(self._session_cache),
            "session_cache_hits": self._cache_hits,
            "session_cache_misses": self._cache_misses,
            "session_hit_rate_percent": round(hit_rate, 1),
            "persistent_embeddings": persistent_stats["embeddings_count"],
            "persistent_searches": persistent_stats["search_results_count"]
        }
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text with aggressive caching."""
        try:
            embed_start = time.time()
            
            # Check session cache first (fastest)
            cache_key = hashlib.md5(text.strip().lower().encode()).hexdigest()
            if cache_key in self._session_cache:
                self._cache_hits += 1
                embed_time = time.time() - embed_start
                print(f"⚡ SESSION CACHED: {embed_time:.3f}s for '{text[:30]}...'")
                return self._session_cache[cache_key]
            
            # Check persistent cache (fast)
            cached_embedding = persistent_cache.get_embedding(text)
            if cached_embedding is not None:
                self._cache_hits += 1
                # Also store in session cache
                self._session_cache[cache_key] = cached_embedding
                embed_time = time.time() - embed_start
                print(f"💾 PERSISTENT CACHED: {embed_time:.3f}s for '{text[:30]}...'")
                return cached_embedding
            
            # Cache miss - need to call API
            self._cache_misses += 1
            
            # Clean and prepare text
            text = text.strip()
            if not text:
                raise ValueError("Empty text provided for embedding")
            
            # Truncate if too long (OpenAI has token limits)
            if len(text) > 8000:  # Conservative limit
                text = text[:8000]
            
            # Make API call
            api_start = time.time()
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text,
                encoding_format="float"
            )
            api_time = time.time() - api_start
            
            embedding = response.data[0].embedding
            
            # Cache in both session and persistent cache
            self._session_cache[cache_key] = embedding
            persistent_cache.cache_embedding(text, embedding)
            
            embed_time = time.time() - embed_start
            print(f"🤖 NEW API CALL: {embed_time:.3f}s (API: {api_time:.3f}s) for '{text[:30]}...'")
            
            return embedding
            
        except Exception as e:
            print(f"❌ Error generating embedding: {str(e)}")
            raise e
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query with caching."""
        try:
            query_start = time.time()
            
            # Use the cached embed_text method
            result = self.embed_text(query)
            
            query_time = time.time() - query_start
            
            # Show cache stats every 3 requests
            if (self._cache_hits + self._cache_misses) % 3 == 0:
                stats = self.get_cache_stats()
                print(f"📊 Cache: {stats['session_hit_rate_percent']}% hit rate | Session: {stats['session_cache_size']} | Persistent: {stats['persistent_embeddings']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error generating query embedding: {str(e)}")
            raise e
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            # Clean and prepare texts
            processed_texts = []
            for text in texts:
                text = text.strip()
                if not text:
                    text = "Empty content"  # Fallback for empty texts
                
                # Truncate if too long
                if len(text) > 8000:
                    text = text[:8000]
                
                processed_texts.append(text)
            
            # OpenAI allows batch processing up to 2048 inputs
            batch_size = 100  # Conservative batch size for reliability
            all_embeddings = []
            
            for i in range(0, len(processed_texts), batch_size):
                batch = processed_texts[i:i + batch_size]
                
                print(f"Processing embedding batch {i//batch_size + 1}/{(len(processed_texts) + batch_size - 1)//batch_size}")
                
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch,
                    encoding_format="float"
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Add small delay to respect rate limits
                if i + batch_size < len(processed_texts):
                    time.sleep(0.1)
            
            return all_embeddings
            
        except Exception as e:
            print(f"Error generating batch embeddings: {str(e)}")
            raise e
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "provider": "OpenAI",
            "max_tokens": 8191  # OpenAI's token limit for embeddings
        }