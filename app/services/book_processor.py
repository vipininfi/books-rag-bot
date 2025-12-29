from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.core.config import settings
from app.models.book import Book, ProcessingStatus
from app.models.chunk import Chunk
from app.services.pdf_processor import PDFProcessor
from app.services.chunking_engine import ChunkingEngine
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


class BookProcessor:
    """Orchestrates the complete book processing pipeline."""
    
    def __init__(self):
        # Create database session
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()
        
        # Initialize services
        self.pdf_processor = PDFProcessor()
        self.chunking_engine = ChunkingEngine()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
    
    def process_book(self, book_id: int):
        """Complete processing pipeline for a book."""
        try:
            # Get book record
            book = self.db.query(Book).filter(Book.id == book_id).first()
            if not book:
                raise Exception(f"Book {book_id} not found")
            
            # Update status
            book.processing_status = ProcessingStatus.PROCESSING
            self.db.commit()
            
            print(f"Processing book: {book.title}")
            
            # Step 1: Extract text with layout
            print("Step 1: Extracting text from PDF...")
            lines = self.pdf_processor.extract_text_with_layout(book.file_path)
            
            # Step 2: Detect sections
            print("Step 2: Detecting document structure...")
            sections = self.pdf_processor.detect_sections(lines)
            
            # Step 3: Chunk sections
            print("Step 3: Chunking content...")
            chunks = self.chunking_engine.chunk_sections(
                sections=sections,
                author_id=book.author_id,
                book_id=book.id
            )
            
            print(f"Generated {len(chunks)} chunks")
            
            # Step 4: Generate embeddings with usage logging
            print("Step 4: Generating embeddings...")
            
            # Get user_id for token tracking
            from app.models.author import Author
            author = self.db.query(Author).filter(Author.id == book.author_id).first()
            user_id = author.user_id if author else 0
            
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_service.embed_batch(
                chunk_texts, 
                user_id=user_id, 
                operation_type="book_batch_embedding"
            )
            
            # Step 5: Store in vector database AND database
            print("Step 5: Storing in vector database...")
            chunk_ids = self.vector_store.store_chunks(chunks, embeddings)
            
            # Step 6: Store chunks in database for text retrieval
            print("Step 6: Storing chunks in database...")
            self._store_chunks_in_database(chunks, chunk_ids)
            
            # Update book record
            book.processing_status = ProcessingStatus.COMPLETED
            book.total_chunks = len(chunks)
            book.total_pages = max([line.page for line in lines]) if lines else 0
            self.db.commit()
            
            print(f"Successfully processed book: {book.title}")
            
        except Exception as e:
            print(f"Error processing book {book_id}: {str(e)}")
            
            # Update status to failed
            book = self.db.query(Book).filter(Book.id == book_id).first()
            if book:
                book.processing_status = ProcessingStatus.FAILED
                self.db.commit()
            
            raise e
        
        finally:
            self.db.close()
    
    def _store_chunks_in_database(self, chunks, chunk_ids):
        """Store chunks in database for text retrieval using the same IDs as Pinecone."""
        try:
            for chunk, chunk_id in zip(chunks, chunk_ids):
                # Create database chunk record with same ID as Pinecone
                db_chunk = Chunk(
                    chunk_id=chunk_id,  # Use same UUID as Pinecone
                    text=chunk.text,  # Store full text
                    section_title=chunk.metadata["section_title"],
                    chunk_index=chunk.metadata["chunk_index"],
                    chunk_type=chunk.chunk_type.value,
                    token_count=chunk.token_count,
                    page_number=chunk.metadata.get("page_number", 1),
                    book_id=chunk.metadata["book_id"],
                    author_id=chunk.metadata["author_id"]
                )
                
                self.db.add(db_chunk)
            
            self.db.commit()
            print(f"Stored {len(chunks)} chunks in database with matching Pinecone IDs")
            
        except Exception as e:
            print(f"Error storing chunks in database: {e}")
            self.db.rollback()
            raise e
    
    def reprocess_book(self, book_id: int):
        """Reprocess a book (useful for updates or fixes)."""
        # Delete existing chunks from vector store
        self.vector_store.delete_book_chunks(book_id)
        
        # Delete existing chunks from database
        self.db.query(Chunk).filter(Chunk.book_id == book_id).delete()
        self.db.commit()
        
        # Process again
        self.process_book(book_id)