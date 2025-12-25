from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String, unique=True, index=True)  # UUID from Pinecone
    text = Column(Text, nullable=False)
    section_title = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_type = Column(String, nullable=False)
    token_count = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1)
    
    # Foreign keys
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    book = relationship("Book", back_populates="chunks")
    author = relationship("Author", back_populates="chunks")