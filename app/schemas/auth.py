from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_role: str
    user_id: int


class User(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    
    class Config:
        from_attributes = True