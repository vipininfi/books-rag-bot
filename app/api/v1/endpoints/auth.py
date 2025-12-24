from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
import hashlib

from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserLogin, Token
from app.core.config import settings

router = APIRouter()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Simple SHA256 hash for demo purposes
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    # Simple SHA256 hash for demo purposes
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # If user is an author, create author record
    if user.role == UserRole.AUTHOR:
        from app.models.author import Author
        author = Author(
            name=user.username,
            bio=f"Author profile for {user.username}",
            user_id=db_user.id
        )
        db.add(author)
        db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_role": db_user.role,
        "user_id": db_user.id
    }


@router.post("/login", response_model=Token)
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login user with form data."""
    try:
        # Find user
        db_user = db.query(User).filter(User.email == username).first()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check password
        if not verify_password(password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": str(db_user.id)})
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user_role": db_user.role,
            "user_id": db_user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error for debugging
        print(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )