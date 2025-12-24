import google.generativeai as genai
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.services.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService


class RAGService:
    """Handles Retrieval-Augmented Generation using Gemini 2.0 Flash."""
    
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash"  # Exact model as requested
        self.model = genai.GenerativeModel(self.model_name)
        
        # Initialize services
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
    
    def search_only(
        self, 
        query: str, 
        author_ids: List[int], 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform semantic search without RAG generation."""
        # Generate query embedding using BGE
        query_embedding = self.embedding_service.embed_query(query)
        
        # Search vector store
        results = self.vector_store.search(
            query_vector=query_embedding,
            author_ids=author_ids,
            limit=limit
        )
        
        return results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_answer(
        self, 
        query: str, 
        author_ids: List[int], 
        max_chunks: int = 8
    ) -> Dict[str, Any]:
        """Generate RAG answer using Gemini 2.0 Flash with retrieved context."""
        # Get more chunks initially for better context
        search_limit = max(max_chunks * 2, 16)  # Get more chunks to choose from
        search_results = self.search_only(query, author_ids, limit=search_limit)
        
        if not search_results:
            return {
                "answer": "No relevant information found in your subscribed authors' books.",
                "sources": [],
                "total_chunks": 0,
                "model_used": self.model_name
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
        
        # Generate answer using Gemini with improved settings
        prompt = self._build_rag_prompt(query, context)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Slightly higher for more creative synthesis
                    max_output_tokens=1500,  # More space for comprehensive answers
                    top_p=0.9,
                    top_k=40
                )
            )
            
            answer = response.text
            
        except Exception as e:
            print(f"Error generating answer with Gemini: {str(e)}")
            answer = "I apologize, but I encountered an error while generating the answer. Please try again."
        
        return {
            "answer": answer,
            "sources": sources,
            "total_chunks": len(reranked_results),
            "query": query,
            "model_used": self.model_name
        }
    
    def _build_rag_prompt(self, query: str, context: str) -> str:
        """Build the RAG prompt for Gemini."""
        return f"""You are a knowledgeable assistant that helps users understand and apply insights from books. Your task is to answer questions using the provided context from the user's subscribed books.

INSTRUCTIONS:
1. **Primary Goal**: Provide helpful, actionable answers based on the context provided
2. **Use the Context**: Extract insights, concepts, and guidance from the provided text
3. **Synthesize Information**: Combine related ideas from different parts of the context to create comprehensive answers
4. **Be Practical**: Focus on actionable advice and clear explanations
5. **Stay Grounded**: Base your answer on the provided context, but feel free to connect ideas and draw reasonable conclusions
6. **Acknowledge Limitations**: If the context only partially addresses the question, mention what is covered and what might need additional information

CRITICAL FORMATTING REQUIREMENTS:
- Use **bold text** for key concepts and section headings (surround with **)
- Use numbered lists (1., 2., 3.) for step-by-step instructions - each step should be on a new line
- Use bullet points (•) for related items or examples
- Add proper spacing: Always put a space after periods, colons, and other punctuation
- Break content into clear paragraphs with double line breaks between major sections
- Start each numbered step with the number, period, space, then a clear heading
- Ensure proper sentence spacing throughout

EXAMPLE FORMAT:
**Main Heading**

Introductory paragraph with proper spacing. Each sentence should flow naturally with correct punctuation spacing.

1. **First Step Title**
Clear explanation of the first step. Make sure there are spaces after periods and proper formatting.

2. **Second Step Title** 
Detailed explanation with examples:
• First example point
• Second example point
• Third example point

**Next Section Heading**

Additional information and guidance with proper paragraph breaks.

CONTEXT FROM BOOKS:
{context}

USER QUESTION: {query}

Please provide a well-formatted, comprehensive answer that draws from the available context. Pay special attention to proper spacing, punctuation, and formatting to ensure excellent readability."""
    
    
    
    
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
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the models being used."""
        return {
            "llm_model": self.model_name,
            "embedding_model": self.embedding_service.get_model_info(),
            "vector_store": "Pinecone"
        }