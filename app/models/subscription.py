from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    author = relationship("Author", back_populates="subscriptions")

    # Ensure unique user-author pairs
    __table_args__ = (UniqueConstraint('user_id', 'author_id', name='unique_user_author'),)