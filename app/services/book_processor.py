from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.book import Book, ProcessingStatus
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
            
            # Step 4: Generate embeddings
            print("Step 4: Generating embeddings...")
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_service.embed_batch(chunk_texts)
            
            # Step 5: Store in vector database
            print("Step 5: Storing in vector database...")
            self.vector_store.store_chunks(chunks, embeddings)
            
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
    
    def reprocess_book(self, book_id: int):
        """Reprocess a book (useful for updates or fixes)."""
        # Delete existing chunks
        self.vector_store.delete_book_chunks(book_id)
        
        # Process again
        self.process_book(book_id)