from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.subscription import Subscription
from app.models.author import Author
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse

router = APIRouter()


@router.post("/", response_model=SubscriptionResponse)
def subscribe_to_author(
    subscription: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subscribe to an author."""
    
    # Check if author exists
    author = db.query(Author).filter(Author.id == subscription.author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Check if already subscribed
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.author_id == subscription.author_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already subscribed to this author")
    
    # Create subscription
    db_subscription = Subscription(
        user_id=current_user.id,
        author_id=subscription.author_id
    )
    
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    
    return SubscriptionResponse(
        id=db_subscription.id,
        author_id=db_subscription.author_id,
        author_name=author.name,
        created_at=db_subscription.created_at
    )


@router.delete("/{author_id}")
def unsubscribe_from_author(
    author_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unsubscribe from an author."""
    
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.author_id == author_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    db.delete(subscription)
    db.commit()
    
    return {"message": "Successfully unsubscribed"}


@router.get("/", response_model=List[SubscriptionResponse])
def get_my_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscriptions."""
    
    subscriptions = db.query(Subscription).join(Author).filter(
        Subscription.user_id == current_user.id
    ).all()
    
    return [
        SubscriptionResponse(
            id=sub.id,
            author_id=sub.author_id,
            author_name=sub.author.name,
            author_bio=sub.author.bio,
            book_count=len(sub.author.books),
            created_at=sub.created_at
        )
        for sub in subscriptions
    ]


@router.get("/authors")
def list_available_authors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available authors for subscription."""
    
    authors = db.query(Author).offset(skip).limit(limit).all()
    
    # Get user's current subscriptions
    user_subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).all()
    subscribed_author_ids = {sub.author_id for sub in user_subscriptions}
    
    return [
        {
            "id": author.id,
            "name": author.name,
            "bio": author.bio,
            "is_subscribed": author.id in subscribed_author_ids,
            "book_count": len(author.books)
        }
        for author in authors
    ]