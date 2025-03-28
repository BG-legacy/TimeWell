from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: Optional[str] = Field(alias="_id")
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class UserResponse(UserBase):
    id: str = Field(alias="_id")
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None 