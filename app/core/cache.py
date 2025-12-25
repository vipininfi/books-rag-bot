"""
Persistent caching system for embeddings and search results.
"""

import json
import os
import hashlib
import time
from typing import List, Dict, Any, Optional
import pickle

class PersistentCache:
    """File-based persistent cache for embeddings."""
    
    def __init__(self, cache_dir: str = "./cache", max_age_hours: int = 24):
        self.cache_dir = cache_dir
        self.max_age_seconds = max_age_hours * 3600
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache files
        self.embeddings_file = os.path.join(cache_dir, "embeddings.pkl")
        self.search_results_file = os.path.join(cache_dir, "search_results.pkl")
        
        # Load existing caches
        self.embeddings_cache = self._load_cache(self.embeddings_file)
        self.search_cache = self._load_cache(self.search_results_file)
        
        print(f"📁 Persistent cache initialized: {len(self.embeddings_cache)} embeddings, {len(self.search_cache)} searches")
    
    def _load_cache(self, filename: str) -> dict:
        """Load cache from file."""
        try:
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    cache = pickle.load(f)
                
                # Clean expired entries
                current_time = time.time()
                cleaned_cache = {}
                
                for key, (data, timestamp) in cache.items():
                    if current_time - timestamp < self.max_age_seconds:
                        cleaned_cache[key] = (data, timestamp)
                
                print(f"📁 Loaded {len(cleaned_cache)} valid entries from {filename}")
                return cleaned_cache
            
        except Exception as e:
            print(f"⚠️ Error loading cache {filename}: {e}")
        
        return {}
    
    def _save_cache(self, cache: dict, filename: str):
        """Save cache to file."""
        try:
            with open(filename, 'wb') as f:
                pickle.dump(cache, f)
        except Exception as e:
            print(f"⚠️ Error saving cache {filename}: {e}")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        normalized_text = text.strip().lower()
        return hashlib.md5(normalized_text.encode()).hexdigest()
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding."""
        key = self._get_cache_key(text)
        
        if key in self.embeddings_cache:
            embedding, timestamp = self.embeddings_cache[key]
            
            # Check if not expired
            if time.time() - timestamp < self.max_age_seconds:
                return embedding
            else:
                # Remove expired entry
                del self.embeddings_cache[key]
        
        return None
    
    def cache_embedding(self, text: str, embedding: List[float]):
        """Cache an embedding."""
        key = self._get_cache_key(text)
        self.embeddings_cache[key] = (embedding, time.time())
        
        # Save to disk periodically (every 10 entries)
        if len(self.embeddings_cache) % 10 == 0:
            self._save_cache(self.embeddings_cache, self.embeddings_file)
    
    def get_search_results(self, query: str, author_ids: List[int], limit: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results."""
        # Create cache key from query + author_ids + limit
        cache_data = {
            "query": query.strip().lower(),
            "author_ids": sorted(author_ids),
            "limit": limit
        }
        key = hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
        
        if key in self.search_cache:
            results, timestamp = self.search_cache[key]
            
            # Check if not expired (shorter expiry for search results)
            if time.time() - timestamp < 3600:  # 1 hour for search results
                return results
            else:
                del self.search_cache[key]
        
        return None
    
    def cache_search_results(self, query: str, author_ids: List[int], limit: int, results: List[Dict[str, Any]]):
        """Cache search results."""
        cache_data = {
            "query": query.strip().lower(),
            "author_ids": sorted(author_ids),
            "limit": limit
        }
        key = hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
        
        self.search_cache[key] = (results, time.time())
        
        # Save to disk periodically
        if len(self.search_cache) % 5 == 0:
            self._save_cache(self.search_cache, self.search_results_file)
    
    def save_all(self):
        """Save all caches to disk."""
        self._save_cache(self.embeddings_cache, self.embeddings_file)
        self._save_cache(self.search_cache, self.search_results_file)
        print(f"💾 Saved caches: {len(self.embeddings_cache)} embeddings, {len(self.search_cache)} searches")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "embeddings_count": len(self.embeddings_cache),
            "search_results_count": len(self.search_cache),
            "cache_dir": self.cache_dir
        }

# Global cache instance
persistent_cache = PersistentCache()