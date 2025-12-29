from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SubscriptionCreate(BaseModel):
    author_id: int


class SubscriptionResponse(BaseModel):
    id: int
    author_id: int
    author_name: str
    author_bio: Optional[str] = None
    book_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True