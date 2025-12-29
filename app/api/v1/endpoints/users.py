from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.db.database import get_db
from app.models.user import User
from app.models.author import Author
from app.api.deps import get_current_user
from app.api.v1.endpoints.auth import get_password_hash, verify_password

router = APIRouter()


class UserProfileResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    author_bio: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile information."""
    
    profile_data = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "author_bio": None
    }
    
    # If user is an author, get their bio
    if current_user.role == "author":
        author = db.query(Author).filter(Author.user_id == current_user.id).first()
        if author:
            profile_data["author_bio"] = author.bio
    
    return profile_data


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information."""
    
    # Verify current password if new password is provided
    if profile_update.new_password:
        if not profile_update.current_password:
            raise HTTPException(
                status_code=400,
                detail="Current password is required to set a new password"
            )
        
        if not verify_password(profile_update.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect"
            )
    
    # Update user fields
    if profile_update.username:
        # Check if username is already taken
        existing_user = db.query(User).filter(
            User.username == profile_update.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username is already taken"
            )
        current_user.username = profile_update.username
    
    if profile_update.email:
        # Check if email is already taken
        existing_user = db.query(User).filter(
            User.email == profile_update.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email is already registered"
            )
        current_user.email = profile_update.email
    
    if profile_update.new_password:
        current_user.hashed_password = get_password_hash(profile_update.new_password)
    
    # Update author bio if user is an author
    if current_user.role == "author" and profile_update.bio is not None:
        author = db.query(Author).filter(Author.user_id == current_user.id).first()
        if author:
            author.bio = profile_update.bio
        else:
            # Create author record if it doesn't exist
            author = Author(
                name=current_user.username,
                bio=profile_update.bio,
                user_id=current_user.id
            )
            db.add(author)
    
    db.commit()
    db.refresh(current_user)
    
    # Return updated profile
    profile_data = {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "author_bio": None
    }
    
    if current_user.role == "author":
        author = db.query(Author).filter(Author.user_id == current_user.id).first()
        if author:
            profile_data["author_bio"] = author.bio
    
    return profile_data