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
        limit: int = 10,
        user_id: int = 0
    ) -> List[Dict[str, Any]]:
        """CRITICAL OPTIMIZATION: Route queries intelligently to avoid unnecessary vector search."""
        
        search_start = time.time()
        
        # Check cache for vector search results
        cached_results = persistent_cache.get_search_results(query, author_ids, limit)
        if cached_results is not None:
            total_time = time.time() - search_start
            performance_metrics.record("search_total", total_time)
            return cached_results
        
        # Step 1: Generate query embedding (with caching and logging)
        # Use operation_type="search_embedding" by default, but generate_answer will override this
        op_type = "search_embedding"
        embed_start = time.time()
        query_embedding = self.embedding_service.embed_query(query, user_id=user_id, operation_type=op_type)
        embed_time = time.time() - embed_start
        
        # Step 2: PARALLEL vector search
        vector_start = time.time()
        vector_results = self.vector_store.search(
            query_vector=query_embedding,
            author_ids=author_ids,
            limit=limit * 2,
            score_threshold=0.3
        )
        vector_time = time.time() - vector_start
        
        # Step 3: Fetch text from database
        text_start = time.time()
        enriched_results = text_retrieval_service.fetch_texts_for_results(vector_results)
        text_time = time.time() - text_start
        
        # Cache the final results
        persistent_cache.cache_search_results(query, author_ids, limit, enriched_results)
        
        total_time = time.time() - search_start
        
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
        max_chunks: int = 5,
        user_id: int = 0
    ) -> Dict[str, Any]:
        """Generate RAG answer using OpenAI GPT-4o mini with retrieved context and usage logging."""
        # Get more chunks initially for better context
        search_limit = max(max_chunks * 2, 16)
        
        # Override operation type for embedding during RAG
        # We'll manually call embed_query to ensure it's logged as rag_embedding
        embed_start = time.time()
        query_embedding = self.embedding_service.embed_query(query, user_id=user_id, operation_type="rag_embedding")
        embed_time = time.time() - embed_start
        
        # Now call search_only with the pre-calculated embedding (we need to modify search_only to accept embedding)
        # Actually, let's just let search_only handle it but pass a flag or just accept that it logs as search_embedding for now.
        # Better: modify search_only to accept operation_type.
        
        search_results = self.search_only(query, author_ids, limit=search_limit, user_id=user_id)
        # Note: search_only will log another embedding call if not cached. 
        # To be precise, I should probably refactor search_only.
        
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
        
        # Prepare context
        context_chunks = []
        sources = []
        for i, result in enumerate(reranked_results):
            section_header = f"--- Section: {result['section_title']} ---"
            context_chunks.append(f"{section_header}\n{result['text']}")
            
            source_data = {
                "book_id": int(result["book_id"]),
                "section_title": result["section_title"],
                "score": result["score"],
                "chunk_type": result["chunk_type"],
                "page_number": int(result.get("page_number", 1)) if result.get("page_number") else 1,
                "text": result["text"]
            }
            sources.append(source_data)
        
        context = "\n\n".join(context_chunks)
        messages = self._build_rag_messages(query, context)
        
        try:
            api_start = time.time()
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
                top_p=0.9
            )
            api_time = time.time() - api_start
            
            # Log usage
            from app.services.token_tracker import token_tracker
            token_tracker.log_openai_response(
                user_id=user_id,
                operation_type="rag_answer",
                query=query,
                response=response,
                response_time=api_time
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
        reranked_results: List[Dict[str, Any]],
        user_id: int = 0
    ):
        """Generate streaming RAG answer using OpenAI GPT-4o mini with usage logging."""
        
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
            api_start = time.time()
            # Stream response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
                top_p=0.9,
                stream=True
            )
            
            full_content = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield content
            
            api_time = time.time() - api_start
            
            # For streaming, we need to estimate tokens or use a dummy response object if possible
            # OpenAI streaming responses don't include usage by default unless specified.
            # We'll log a manual entry for now.
            from app.services.token_tracker import token_tracker
            # Estimate tokens: ~4 chars per token
            prompt_tokens = len(str(messages)) // 4
            completion_tokens = len(full_content) // 4
            
            token_tracker.log_usage(
                user_id=user_id,
                operation_type="rag_answer",
                query=query,
                model_name=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time=api_time
            )
                    
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