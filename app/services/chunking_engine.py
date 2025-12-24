import tiktoken
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.services.pdf_processor import Section
from app.core.config import settings


class ChunkType(str, Enum):
    FIXED = "fixed"
    SEMANTIC = "semantic"


@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any]
    chunk_type: ChunkType
    token_count: int


class ChunkingEngine:
    """Handles hybrid chunking: structural + selective semantic."""
    
    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = settings.DEFAULT_CHUNK_SIZE
        self.overlap = settings.CHUNK_OVERLAP
        self.max_semantic_calls = settings.MAX_SEMANTIC_CALLS_PER_BOOK
        self.semantic_calls_used = 0
    
    def chunk_sections(
        self, 
        sections: List[Section], 
        author_id: int, 
        book_id: int
    ) -> List[Chunk]:
        """Main chunking pipeline: fixed + selective semantic."""
        all_chunks = []
        self.semantic_calls_used = 0
        
        for section in sections:
            section_text = " ".join(section.paragraphs)
            token_count = self._count_tokens(section_text)
            
            # Decide chunking strategy
            if self._should_use_semantic_chunking(section, token_count):
                chunks = self._semantic_chunk_section(section, author_id, book_id)
            else:
                chunks = self._fixed_chunk_section(section, author_id, book_id)
            
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _should_use_semantic_chunking(self, section: Section, token_count: int) -> bool:
        """Determine if section needs semantic chunking."""
        # Check limits
        if self.semantic_calls_used >= self.max_semantic_calls:
            return False
        
        # Must be large enough
        if token_count < 1200:
            return False
        
        # Must have abstract title
        abstract_titles = [
            "introduction", "overview", "discussion", "theory", 
            "foundations", "concepts", "background", "methodology"
        ]
        
        title_lower = section.title.lower()
        is_abstract = any(keyword in title_lower for keyword in abstract_titles)
        
        return is_abstract
    
    def _semantic_chunk_section(
        self, 
        section: Section, 
        author_id: int, 
        book_id: int
    ) -> List[Chunk]:
        """Apply semantic chunking to a section."""
        self.semantic_calls_used += 1
        
        # For now, implement a simple semantic split
        # In production, this would call an LLM
        split_points = self._mock_semantic_split(section.paragraphs)
        
        chunks = []
        for i, (start, end) in enumerate(split_points):
            chunk_paragraphs = section.paragraphs[start:end]
            chunk_text = " ".join(chunk_paragraphs)
            
            # Apply fixed chunking to each semantic chunk if still too large
            if self._count_tokens(chunk_text) > self.chunk_size:
                sub_chunks = self._fixed_chunk_text(
                    chunk_text, author_id, book_id, section.title, ChunkType.SEMANTIC, section.start_page
                )
                chunks.extend(sub_chunks)
            else:
                chunks.append(Chunk(
                    text=chunk_text,
                    metadata={
                        "author_id": author_id,
                        "book_id": book_id,
                        "section_title": section.title,
                        "chunk_index": i,
                        "start_page": section.start_page,
                        "end_page": section.end_page,
                        "page_number": section.start_page  # Use start page as primary page
                    },
                    chunk_type=ChunkType.SEMANTIC,
                    token_count=self._count_tokens(chunk_text)
                ))
        
        return chunks
    
    def _fixed_chunk_section(
        self, 
        section: Section, 
        author_id: int, 
        book_id: int
    ) -> List[Chunk]:
        """Apply fixed chunking to a section."""
        section_text = " ".join(section.paragraphs)
        return self._fixed_chunk_text(
            section_text, author_id, book_id, section.title, ChunkType.FIXED, section.start_page
        )
    
    def _fixed_chunk_text(
        self, 
        text: str, 
        author_id: int, 
        book_id: int, 
        section_title: str,
        chunk_type: ChunkType,
        page_number: int = 1
    ) -> List[Chunk]:
        """Core fixed chunking algorithm."""
        chunks = []
        sentences = self._split_into_sentences(text)
        
        buffer = []
        buffer_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            
            # Check if adding this sentence exceeds chunk size
            if buffer_tokens + sentence_tokens > self.chunk_size and buffer:
                # Create chunk
                chunk_text = " ".join(buffer)
                chunks.append(Chunk(
                    text=chunk_text,
                    metadata={
                        "author_id": author_id,
                        "book_id": book_id,
                        "section_title": section_title,
                        "chunk_index": chunk_index,
                        "page_number": page_number
                    },
                    chunk_type=chunk_type,
                    token_count=buffer_tokens
                ))
                
                # Start new buffer with overlap
                overlap_text = self._get_overlap_text(buffer)
                buffer = [overlap_text, sentence] if overlap_text else [sentence]
                buffer_tokens = self._count_tokens(" ".join(buffer))
                chunk_index += 1
            else:
                buffer.append(sentence)
                buffer_tokens += sentence_tokens
        
        # Add final chunk
        if buffer:
            chunk_text = " ".join(buffer)
            chunks.append(Chunk(
                text=chunk_text,
                metadata={
                    "author_id": author_id,
                    "book_id": book_id,
                    "section_title": section_title,
                    "chunk_index": chunk_index,
                    "page_number": page_number
                },
                chunk_type=chunk_type,
                token_count=buffer_tokens
            ))
        
        return chunks
    
    def _mock_semantic_split(self, paragraphs: List[str]) -> List[tuple]:
        """Mock semantic splitting. In production, use LLM."""
        # Simple heuristic: split every 3-4 paragraphs
        splits = []
        start = 0
        
        while start < len(paragraphs):
            end = min(start + 3, len(paragraphs))
            splits.append((start, end))
            start = end
        
        return splits
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, buffer: List[str]) -> Optional[str]:
        """Get overlap text from buffer."""
        if not buffer:
            return None
        
        overlap_text = " ".join(buffer[-2:])  # Last 2 sentences
        if self._count_tokens(overlap_text) <= self.overlap:
            return overlap_text
        
        return buffer[-1] if buffer else None
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))