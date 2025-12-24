#!/usr/bin/env python3

from app.services.vector_store import VectorStore
from app.db.database import SessionLocal
from app.models.book import Book
import sys

def clear_vector_database():
    """Clear all vectors from the Pinecone database and reset book processing status."""
    
    print("🧹 Clearing Vector Database...")
    print("=" * 50)
    
    try:
        # Initialize vector store
        vector_store = VectorStore()
        
        # Get current stats
        print("📊 Current database stats:")
        stats = vector_store.get_collection_info()
        print(f"   Total vectors: {stats['total_points']}")
        print(f"   Vector dimension: {stats['vector_size']}")
        
        if stats['total_points'] == 0:
            print("✅ Vector database is already empty!")
            return
        
        # Confirm deletion
        confirm = input(f"\n⚠️  This will delete ALL {stats['total_points']} vectors. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Operation cancelled.")
            return
        
        # Delete all vectors
        print("\n🗑️  Deleting all vectors...")
        
        # Pinecone delete all vectors (delete without filter deletes everything)
        vector_store.index.delete(delete_all=True)
        
        print("✅ All vectors deleted from Pinecone!")
        
        # Reset book processing status in database
        print("\n🔄 Resetting book processing status...")
        db = SessionLocal()
        try:
            books = db.query(Book).all()
            for book in books:
                book.processing_status = "pending"
                book.total_chunks = None
            
            db.commit()
            print(f"✅ Reset processing status for {len(books)} books")
            
        except Exception as e:
            print(f"❌ Error resetting book status: {e}")
            db.rollback()
        finally:
            db.close()
        
        # Verify deletion
        print("\n🔍 Verifying deletion...")
        final_stats = vector_store.get_collection_info()
        print(f"   Remaining vectors: {final_stats['total_points']}")
        
        if final_stats['total_points'] == 0:
            print("✅ Vector database successfully cleared!")
        else:
            print(f"⚠️  Warning: {final_stats['total_points']} vectors still remain")
        
        print("\n🎉 Database cleared! You can now upload new books for testing.")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        import traceback
        traceback.print_exc()

def clear_specific_book(book_id: int):
    """Clear vectors for a specific book."""
    
    print(f"🧹 Clearing vectors for book ID: {book_id}")
    
    try:
        vector_store = VectorStore()
        
        # Delete book chunks
        vector_store.delete_book_chunks(book_id)
        
        # Reset book status
        db = SessionLocal()
        try:
            book = db.query(Book).filter(Book.id == book_id).first()
            if book:
                book.processing_status = "pending"
                book.total_chunks = None
                db.commit()
                print(f"✅ Cleared vectors and reset status for book: {book.title}")
            else:
                print(f"❌ Book with ID {book_id} not found")
        except Exception as e:
            print(f"❌ Error resetting book status: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error clearing book vectors: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            book_id = int(sys.argv[1])
            clear_specific_book(book_id)
        except ValueError:
            print("❌ Invalid book ID. Please provide a valid integer.")
    else:
        clear_vector_database()