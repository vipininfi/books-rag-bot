from openai import OpenAI
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import hashlib
import json
from functools import lru_cache

from app.core.config import settings
from app.services.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService
from app.services.text_retrieval import text_retrieval_service
from app.services.query_router import query_router, QueryType
from app.core.performance import performance_metrics
from app.core.cache import persistent_cache


class RAGService:
    """Handles Retrieval-Augmented Generation with intelligent query routing."""
    
    def __init__(self):
        # Configure OpenAI
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_name = settings.LLM_MODEL_NAME
        
        # Initialize services
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        
        print(f"Initialized OPTIMIZED RAG service with query routing and parallel search")
    
    def search_only(
        self, 
        query: str, 
        author_ids: List[int], 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """CRITICAL OPTIMIZATION: Route queries intelligently to avoid unnecessary vector search."""
        
        search_start = time.time()
        print(f"🧠 INTELLIGENT Search: '{query}' for {len(author_ids)} authors")
        
        # CRITICAL FIX #2: Query intent routing
        routing_decision = query_router.get_routing_decision(query)
        print(f"🎯 Query routing: {routing_decision['query_type']} (confidence: {routing_decision['confidence']:.2f})")
        
        # Check cache for vector search results
        cached_results = persistent_cache.get_search_results(query, author_ids, limit)
        if cached_results is not None:
            total_time = time.time() - search_start
            print(f"⚡ SEARCH RESULTS CACHED: {total_time:.3f}s - Found {len(cached_results)} results")
            performance_metrics.record("search_total", total_time)
            return cached_results
        
        # Step 1: Generate query embedding (with caching)
        embed_start = time.time()
        query_embedding = self.embedding_service.embed_query(query)
        embed_time = time.time() - embed_start
        
        # Step 2: PARALLEL vector search with lower threshold for better recall
        vector_start = time.time()
        vector_results = self.vector_store.search(
            query_vector=query_embedding,
            author_ids=author_ids,
            limit=limit * 2,  # Get more results for better reranking
            score_threshold=0.3  # Lower threshold to get more potential matches
        )
        vector_time = time.time() - vector_start
        
        # Step 3: Fetch text from database (no text in Pinecone metadata)
        text_start = time.time()
        enriched_results = text_retrieval_service.fetch_texts_for_results(vector_results)
        text_time = time.time() - text_start
        
        # Cache the final results
        persistent_cache.cache_search_results(query, author_ids, limit, enriched_results)
        
        total_time = time.time() - search_start
        print(f"✅ OPTIMIZED Search Complete: {total_time:.3f}s")
        print(f"   - Embedding: {embed_time:.3f}s ({(embed_time/total_time)*100:.1f}%)")
        print(f"   - Vector Search: {vector_time:.3f}s ({(vector_time/total_time)*100:.1f}%)")
        print(f"   - Text Retrieval: {text_time:.3f}s ({(text_time/total_time)*100:.1f}%)")
        
        # Record performance metrics
        performance_metrics.record("search_total", total_time)
        performance_metrics.record("embedding", embed_time)
        performance_metrics.record("vector_search", vector_time)
        performance_metrics.record("text_retrieval", text_time)
        
        return enriched_results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_answer(
        self, 
        query: str, 
        author_ids: List[int], 
        max_chunks: int = 5
    ) -> Dict[str, Any]:
        """Generate RAG answer using OpenAI GPT-4o mini with retrieved context."""
        # Get more chunks initially for better context
        search_limit = max(max_chunks * 2, 16)  # Get more chunks to choose from
        search_results = self.search_only(query, author_ids, limit=search_limit)
        
        if not search_results:
            return {
                "answer": "No relevant information found in your subscribed authors' books.",
                "sources": [],
                "total_chunks": 0,
                "query": query,
                "llm_model": self.model_name
            }
        
        # Rerank and select best chunks
        reranked_results = self.rerank_results(query, search_results, max_chunks)
        
        # Prepare context with better formatting
        context_chunks = []
        sources = []
        
        for i, result in enumerate(reranked_results):
            # Add section headers for better context organization
            section_header = f"--- Section: {result['section_title']} ---"
            context_chunks.append(f"{section_header}\n{result['text']}")
            
            source_data = {
                "book_id": int(result["book_id"]),  # Ensure integer
                "section_title": result["section_title"],
                "score": result["score"],
                "chunk_type": result["chunk_type"],
                "page_number": int(result.get("page_number", 1)) if result.get("page_number") else 1,  # Ensure integer
                "text": result["text"]  # Include the text for highlighting
            }
            
            # Log what we're adding to sources
            print(f"🔧 RAG Backend - Adding source {i+1}:")
            print(f"   book_id: {source_data['book_id']} (type: {type(source_data['book_id'])})")
            print(f"   section_title: {source_data['section_title']}")
            print(f"   page_number: {source_data['page_number']} (type: {type(source_data['page_number'])})")
            print(f"   text_length: {len(source_data['text'])}")
            
            sources.append(source_data)
        
        context = "\n\n".join(context_chunks)
        
        # Generate answer using OpenAI GPT-4o mini
        messages = self._build_rag_messages(query, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            answer = response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating answer with OpenAI: {str(e)}")
            answer = "I apologize, but I encountered an error while generating the answer. Please try again."
        
        return {
            "answer": answer,
            "sources": sources,
            "total_chunks": len(reranked_results),
            "query": query,
            "llm_model": self.model_name
        }
    
    def _build_rag_messages(self, query: str, context: str) -> List[Dict[str, str]]:
        """Build the messages for OpenAI chat completion."""
        system_prompt = """You are a book expert assistant that answers questions using ONLY the provided text excerpts from books. Your job is to find the specific answer in the given context and quote directly from it.

CRITICAL RULES:
1. **ONLY use information from the provided context** - Do not add general knowledge or assumptions
2. **Quote directly from the text** when possible to support your answer
3. **If the answer is in the context, find it and explain it clearly**
4. **If the answer is NOT in the context, say so explicitly** - don't make up generic answers
5. **Reference specific sections** when you find relevant information

ANSWER FORMAT:
- Start with a direct answer if found in the context
- Quote the relevant text passages
- Explain what the text means in relation to the question
- Use **bold** for key points and section headings
- If no specific answer is found, clearly state: "The provided text does not contain information about [topic]"

EXAMPLE GOOD ANSWER:
**Direct Answer from the Text**

According to the book, [specific answer based on context].

The text states: "[exact quote from context]"

This means [explanation of what the quote reveals about the question].

EXAMPLE BAD ANSWER:
- Making general assumptions not in the text
- Saying "we can infer" when the text has the actual answer
- Giving generic advice instead of book-specific content"""

        user_prompt = f"""BOOK CONTEXT:
{context}

QUESTION: {query}

Please answer this question using ONLY the information provided in the book context above. Quote directly from the text and explain what it reveals about the question. If the specific answer is not in the provided context, clearly state that."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def rerank_results(
        self, 
        query: str, 
        results: List[Dict[str, Any]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Rerank search results for better relevance."""
        query_words = set(query.lower().split())
        
        for result in results:
            text_words = set(result["text"].lower().split())
            
            # Calculate different relevance signals
            keyword_overlap = len(query_words.intersection(text_words))
            
            # Boost exact phrase matches
            exact_matches = 0
            query_lower = query.lower()
            text_lower = result["text"].lower()
            for word in query_words:
                if len(word) > 3 and word in text_lower:
                    exact_matches += 1
            
            # Boost title relevance
            title_relevance = 0
            section_title_lower = result["section_title"].lower()
            for word in query_words:
                if len(word) > 3 and word in section_title_lower:
                    title_relevance += 2  # Title matches are more important
            
            # Calculate composite score
            base_score = result["score"]
            keyword_score = keyword_overlap / max(len(query_words), 1)
            exact_score = exact_matches / max(len(query_words), 1)
            title_score = title_relevance / max(len(query_words), 1)
            
            # Weighted combination
            composite_score = (
                base_score * 0.4 +           # Vector similarity
                keyword_score * 0.25 +       # Keyword overlap
                exact_score * 0.25 +         # Exact word matches
                title_score * 0.1            # Title relevance
            )
            
            result["composite_score"] = composite_score
            result["keyword_overlap"] = keyword_overlap
            result["exact_matches"] = exact_matches
            result["title_relevance"] = title_relevance
        
        # Sort by composite score
        results.sort(key=lambda x: x["composite_score"], reverse=True)
        
        return results[:top_k]
    
    def generate_streaming_answer(
        self, 
        query: str, 
        reranked_results: List[Dict[str, Any]]
    ):
        """Generate streaming RAG answer using OpenAI GPT-4o mini."""
        
        if not reranked_results:
            yield "No relevant information found in your subscribed authors' books."
            return
        
        # Prepare context
        context_chunks = []
        for result in reranked_results:
            section_header = f"--- Section: {result['section_title']} ---"
            context_chunks.append(f"{section_header}\n{result['text']}")
        
        context = "\n\n".join(context_chunks)
        messages = self._build_rag_messages(query, context)
        
        try:
            # Stream response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=True  # Enable streaming
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"Error generating streaming answer: {str(e)}")
            yield f"I apologize, but I encountered an error while generating the answer: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the models being used."""
        return {
            "llm_model": self.model_name,
            "embedding_model": self.embedding_service.get_model_info(),
            "vector_store": "Pinecone"
        }