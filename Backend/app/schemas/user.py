from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, Dict, Any
from app.schemas.preference import Preferences, CoachVoice, Theme

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    preferences: Optional[Preferences] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[Preferences] = None

class UserInDB(UserBase):
    id: Optional[str] = Field(alias="_id")
    hashed_password: str
    is_active: bool = True
    preferences: Optional[Preferences] = None
    created_at: datetime
    updated_at: datetime

class UserResponse(UserBase):
    id: str = Field(alias="_id")
    is_active: bool
    preferences: Optional[Preferences] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None 