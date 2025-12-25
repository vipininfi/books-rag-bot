"""
Query Intent Router - Routes queries to appropriate search method.
CRITICAL OPTIMIZATION: Avoid vector search for fact-based queries.
"""

import re
from typing import List, Dict, Any, Tuple
from enum import Enum

class QueryType(Enum):
    FACT_LOOKUP = "fact_lookup"      # who/what/when/where questions
    SEMANTIC_SEARCH = "semantic"     # conceptual/thematic queries
    HYBRID = "hybrid"                # needs both approaches

class QueryRouter:
    """Routes queries to the most efficient search method."""
    
    def __init__(self):
        # Fact-based query patterns (should NOT use vector search)
        self.fact_patterns = [
            # Who questions
            r'^who\s+(is|was|are|were)\s+',
            r'^who\s+(created|wrote|invented|founded|discovered)',
            r'^who\s+(lives|lived|works|worked)',
            
            # What questions (specific facts)
            r'^what\s+(is|was|are|were)\s+the\s+(name|title|capital|population)',
            r'^what\s+(year|date|time|day)',
            r'^what\s+(happened|occurs|occurred)',
            
            # When questions
            r'^when\s+(did|was|were|is|are)',
            r'^when\s+(happened|occurs|occurred)',
            
            # Where questions
            r'^where\s+(is|was|are|were|did|does)',
            r'^where\s+(lives|lived|works|worked)',
            
            # How many/much (quantitative)
            r'^how\s+(many|much|long|old|tall|big|small)',
            
            # Simple definitions
            r'^define\s+',
            r'^definition\s+of\s+',
            r'^meaning\s+of\s+',
        ]
        
        # Semantic search patterns (should use vector search)
        self.semantic_patterns = [
            # How-to questions
            r'^how\s+(to|can|do|does)\s+',
            r'^how\s+(should|would|could)\s+',
            
            # Why questions (explanatory)
            r'^why\s+(is|are|do|does|did|should|would)',
            
            # Conceptual queries
            r'^explain\s+',
            r'^describe\s+',
            r'^tell\s+me\s+about\s+',
            r'^what\s+(are\s+the\s+)?(benefits|advantages|disadvantages|steps|ways|methods)',
            
            # Comparative
            r'^compare\s+',
            r'^difference\s+between\s+',
            r'^similarities\s+',
            
            # Advice/guidance
            r'^advice\s+',
            r'^tips\s+',
            r'^best\s+practices\s+',
            r'^recommendations\s+',
        ]
        
        # Character/entity names that suggest fact lookup
        self.entity_indicators = [
            'doctor dolittle', 'dr dolittle', 'dolittle',
            'john dolittle', 'dr. dolittle',
            # Add more character names as needed
        ]
    
    def classify_query(self, query: str) -> Tuple[QueryType, float]:
        """
        Classify query type and return confidence score.
        
        Returns:
            (QueryType, confidence_score)
        """
        
        query_lower = query.lower().strip()
        
        # Check for fact patterns
        fact_score = 0.0
        for pattern in self.fact_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                fact_score += 0.8
                break
        
        # Check for entity indicators
        for entity in self.entity_indicators:
            if entity.lower() in query_lower:
                fact_score += 0.6
                break
        
        # Check for semantic patterns
        semantic_score = 0.0
        for pattern in self.semantic_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                semantic_score += 0.8
                break
        
        # Additional scoring based on query characteristics
        if len(query.split()) <= 4:  # Short queries often factual
            fact_score += 0.2
        
        if any(word in query_lower for word in ['how', 'why', 'explain', 'describe']):
            semantic_score += 0.3
        
        # Determine query type
        if fact_score > semantic_score and fact_score > 0.5:
            return QueryType.FACT_LOOKUP, fact_score
        elif semantic_score > fact_score and semantic_score > 0.5:
            return QueryType.SEMANTIC_SEARCH, semantic_score
        else:
            return QueryType.HYBRID, max(fact_score, semantic_score)
    
    def should_use_vector_search(self, query: str) -> bool:
        """
        Determine if query should use vector search.
        CRITICAL: This prevents unnecessary Pinecone calls.
        """
        
        query_type, confidence = self.classify_query(query)
        
        # Only use vector search for semantic queries or low-confidence cases
        return query_type in [QueryType.SEMANTIC_SEARCH, QueryType.HYBRID]
    
    def get_routing_decision(self, query: str) -> Dict[str, Any]:
        """Get detailed routing decision for debugging."""
        
        query_type, confidence = self.classify_query(query)
        use_vector = self.should_use_vector_search(query)
        
        return {
            "query": query,
            "query_type": query_type.value,
            "confidence": confidence,
            "use_vector_search": use_vector,
            "recommended_approach": self._get_approach_recommendation(query_type)
        }
    
    def _get_approach_recommendation(self, query_type: QueryType) -> str:
        """Get recommended search approach."""
        
        if query_type == QueryType.FACT_LOOKUP:
            return "Use keyword/SQL search, avoid vector search"
        elif query_type == QueryType.SEMANTIC_SEARCH:
            return "Use vector search for semantic matching"
        else:
            return "Use hybrid approach: keyword + vector search"

# Global router instance
query_router = QueryRouter()