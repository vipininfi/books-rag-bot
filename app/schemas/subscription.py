from pydantic import BaseModel
from datetime import datetime


class SubscriptionCreate(BaseModel):
    author_id: int


class SubscriptionResponse(BaseModel):
    id: int
    author_id: int
    author_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True