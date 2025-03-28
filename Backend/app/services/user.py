from datetime import datetime
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException, status
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

COLLECTION = "users"
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "timewell")

async def get_user_by_email(email: str):
    """Get a user by email."""
    db = get_database().client
    user = await db[DATABASE_NAME][COLLECTION].find_one({"email": email})
    return user

async def get_user_by_id(user_id: str):
    """Get a user by ID."""
    db = get_database().client
    user = await db[DATABASE_NAME][COLLECTION].find_one({"_id": ObjectId(user_id)})
    return user

async def create_user(user: UserCreate):
    """Create a new user."""
    db = get_database().client
    
    # Check if user already exists
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    now = datetime.utcnow()
    user_data = {
        "email": user.email,
        "username": user.username,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db[DATABASE_NAME][COLLECTION].insert_one(user_data)
    user_data["_id"] = result.inserted_id
    return user_data

async def authenticate_user(email: str, password: str):
    """Authenticate a user by email and password."""
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user 