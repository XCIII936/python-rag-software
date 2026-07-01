"""Auth-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserRegister(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    email: Optional[str] = None
    role: str = Field(default="student", pattern="^(student|teacher)$")


class UserCreate(BaseModel):
    username: str
    password_hash: str
    email: Optional[str] = None
    role: str = "student"


class UserUpdate(BaseModel):
    email: Optional[str] = None
    avatar: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)
