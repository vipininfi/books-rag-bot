from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path

from app.db.database import get_db
from app.models.book import Book, ProcessingStatus
from app.models.author import Author
from app.api.deps import get_current_user
from app.models.user import User
from app.core.config import settings
from app.services.book_processor import BookProcessor

router = APIRouter()


@router.post("/upload")
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = None,
    description: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a PDF book for processing."""
    
    # Check if user is an author
    if current_user.role != "author":
        raise HTTPException(status_code=403, detail="Only authors can upload books")
    
    # Find the author record for this user
    author = db.query(Author).filter(Author.user_id == current_user.id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author profile not found")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Check file size (default to 100MB if not set)
    max_size = getattr(settings, 'MAX_FILE_SIZE', 100 * 1024 * 1024)
    if file.size and file.size > max_size:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Create upload directory
    upload_dir = Path(getattr(settings, 'UPLOAD_DIR', 'uploads'))
    upload_dir.mkdir(exist_ok=True)
    
    # Save file
    file_path = upload_dir / f"{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create book record
    book = Book(
        title=title or file.filename,
        description=description,
        file_path=str(file_path),
        file_size=file.size or 0,
        author_id=author.id,
        processing_status=ProcessingStatus.PENDING
    )
    
    db.add(book)
    db.commit()
    db.refresh(book)
    
    # Queue background processing
    background_tasks.add_task(process_book_background, book.id)
    
    return {
        "book_id": book.id,
        "message": "Book uploaded successfully. Processing started.",
        "status": "pending"
    }


@router.get("/{book_id}/pdf")
def get_book_pdf(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Serve the PDF file for a book."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if user has access to this book (subscribed to author)
    from app.models.subscription import Subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.author_id == book.author_id
    ).first()
    
    if not subscription and current_user.role not in ["author", "superadmin"]:
        raise HTTPException(status_code=403, detail="Access denied. Subscribe to this author to view their books.")
    
    # Check if file exists
    if not os.path.exists(book.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        path=book.file_path,
        media_type="application/pdf",
        filename=f"{book.title}.pdf"
    )


@router.get("/my")
def list_my_books(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List books belonging to the current author."""
    if current_user.role != "author":
        raise HTTPException(status_code=403, detail="Only authors can access this endpoint")
    
    author = db.query(Author).filter(Author.user_id == current_user.id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author profile not found")
    
    books = db.query(Book).filter(Book.author_id == author.id).all()
    return books


@router.get("/subscribed")
def list_subscribed_books(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List books from authors the current user is subscribed to."""
    from app.models.subscription import Subscription
    
    # Get all author IDs the user is subscribed to
    subscriptions = db.query(Subscription).filter(Subscription.user_id == current_user.id).all()
    author_ids = [sub.author_id for sub in subscriptions]
    
    if not author_ids:
        return []
    
    books = db.query(Book).filter(Book.author_id.in_(author_ids)).all()
    return books


@router.get("/{book_id}")
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get book details."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {
        "id": book.id,
        "title": book.title,
        "description": book.description,
        "author_id": book.author_id,
        "processing_status": book.processing_status,
        "total_pages": book.total_pages,
        "total_chunks": book.total_chunks,
        "created_at": book.created_at
    }


@router.get("/")
def list_books(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all books."""
    books = db.query(Book).offset(skip).limit(limit).all()
    return books


@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a book and all its associated data."""
    # Find book
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if user is the author
    author = db.query(Author).filter(Author.user_id == current_user.id).first()
    if not author or book.author_id != author.id:
        raise HTTPException(status_code=403, detail="Only the author can delete this book")
    
    try:
        # 1. Delete from Pinecone
        from app.services.vector_store import VectorStore
        vector_store = VectorStore()
        vector_store.delete_book_chunks(book_id, author_id=book.author_id)
        
        # 2. Delete chunks from DB
        from app.models.chunk import Chunk
        db.query(Chunk).filter(Chunk.book_id == book_id).delete()
        
        # 3. Delete physical file
        if os.path.exists(book.file_path):
            try:
                os.remove(book.file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {book.file_path}: {e}")
            
        # 4. Delete book record
        db.delete(book)
        db.commit()
        
        return {"message": "Book and all associated data deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting book: {str(e)}")


def process_book_background(book_id: int):
    """Background task to process uploaded book."""
    # This would be implemented in a separate service
    # For now, just a placeholder
    processor = BookProcessor()
    processor.process_book(book_id)