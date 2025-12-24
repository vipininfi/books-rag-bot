from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    total_pages = Column(Integer)
    total_chunks = Column(Integer)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    author = relationship("Author", back_populates="books")