from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.author import Author
from app.models.book import Book
from app.models.subscription import Subscription
from app.api.deps import get_current_user
from app.schemas.auth import User as UserSchema

from app.models.settings import SystemSetting
from app.models.usage import UsageLog
from app.services.token_tracker import token_tracker

router = APIRouter()

def check_superadmin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return current_user

@router.get("/users", response_model=List[UserSchema])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Get all users (Superadmin only)."""
    return db.query(User).all()

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Update user role (Superadmin only)."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.role = role
    db.commit()
    db.refresh(db_user)
    return {"message": f"User {db_user.username} role updated to {role}"}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Delete a user (Superadmin only)."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.get("/authors", response_model=List[UserSchema])
def get_all_authors(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Get all authors (Superadmin only)."""
    return db.query(User).filter(User.role == UserRole.AUTHOR).all()

@router.get("/authors/{user_id}/books")
def get_author_books(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Get all books for a specific author (Superadmin only)."""
    author = db.query(Author).filter(Author.user_id == user_id).first()
    if not author:
        return []
    return db.query(Book).filter(Book.author_id == author.id).all()

@router.get("/stats/global")
def get_global_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Get global system statistics (Superadmin only)."""
    total_users = db.query(User).count()
    total_authors = db.query(User).filter(User.role == UserRole.AUTHOR).count()
    total_books = db.query(Book).count()
    
    return {
        "total_users": total_users,
        "total_authors": total_authors,
        "total_books": total_books
    }

@router.get("/books/all")
def get_all_books(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Get all books in the system with author names (Superadmin only)."""
    books = db.query(Book).all()
    result = []
    for book in books:
        author = db.query(Author).filter(Author.id == book.author_id).first()
        author_user = db.query(User).filter(User.id == author.user_id).first() if author else None
        result.append({
            "id": book.id,
            "title": book.title,
            "author_name": author_user.username if author_user else "Unknown",
            "processing_status": book.processing_status,
            "created_at": book.created_at
        })
    return result

@router.get("/settings")
def get_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Get all system settings (Superadmin only)."""
    settings = db.query(SystemSetting).all()
    return {s.key: s.value for s in settings}

@router.get("/readers", response_model=List[UserSchema])
def get_all_readers(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Get all readers (Superadmin only)."""
    return db.query(User).filter(User.role == UserRole.USER).all()

@router.get("/readers/{user_id}/details")
def get_reader_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Get detailed stats and subscriptions for a reader (Superadmin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get subscriptions
    subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
    sub_list = []
    for sub in subscriptions:
        author = db.query(Author).filter(Author.id == sub.author_id).first()
        author_user = db.query(User).filter(User.id == author.user_id).first() if author else None
        sub_list.append({
            "author_id": sub.author_id,
            "author_name": author_user.username if author_user else "Unknown",
            "subscribed_at": sub.created_at
        })
    
    # Get usage stats for this user
    stats = token_tracker.get_usage_stats(user_id=user_id, days=30)
    
    return {
        "user": user,
        "subscriptions": sub_list,
        "usage_stats": stats
    }

@router.get("/usage/logs")
def get_usage_logs(
    user_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    days: int = 7,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Get usage logs with advanced filtering (Superadmin only)."""
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    query = db.query(UsageLog).filter(UsageLog.timestamp >= cutoff_date)
    
    if user_id:
        query = query.filter(UsageLog.user_id == user_id)
    if operation_type:
        query = query.filter(UsageLog.operation_type == operation_type)
        
    logs = query.order_by(UsageLog.timestamp.desc()).limit(limit).all()
    
    return logs

@router.post("/settings")
def update_system_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_superadmin)
):
    """Update system settings (Superadmin only)."""
    for key, value in settings.items():
        db_setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if db_setting:
            db_setting.value = str(value)
        else:
            db_setting = SystemSetting(key=key, value=str(value))
            db.add(db_setting)
    db.commit()
    return {"message": "Settings updated successfully"}
