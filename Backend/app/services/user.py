from datetime import datetime
from app.core.database import get_database
from app.schemas.user import UserCreate, UserResponse
from app.schemas.preference import Preferences
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException, status
from bson import ObjectId
import os
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any

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

async def get_users(skip: int = 0, limit: int = 100):
    """Get a list of users."""
    db = get_database().client
    users = await db[DATABASE_NAME][COLLECTION].find().skip(skip).limit(limit).to_list(length=limit)
    return users

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
    
    # Add preferences if provided
    if user.preferences:
        user_data["preferences"] = user.preferences.dict()
    else:
        # Set default preferences
        user_data["preferences"] = Preferences().dict()
    
    result = await db[DATABASE_NAME][COLLECTION].insert_one(user_data)
    user_data["_id"] = result.inserted_id
    return user_data

async def update_user(user_id: str, update_data: dict):
    """Update a user."""
    db = get_database().client
    
    # Ensure _id is not updated
    if "_id" in update_data:
        del update_data["_id"]
    
    # Handle nested preferences update
    if "preferences" in update_data and isinstance(update_data["preferences"], dict):
        # Get current user to merge preferences
        current_user = await get_user_by_id(user_id)
        if current_user and "preferences" in current_user:
            # Merge existing preferences with updates
            current_prefs = current_user.get("preferences", {})
            current_prefs.update(update_data["preferences"])
            update_data["preferences"] = current_prefs
    
    # Add updated_at timestamp
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db[DATABASE_NAME][COLLECTION].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or no changes made"
        )
    
    return await get_user_by_id(user_id)

async def update_user_preferences(user_id: str, preferences: Dict[str, Any]):
    """Update only a user's preferences."""
    db = get_database().client
    
    # Get current user to merge preferences
    current_user = await get_user_by_id(user_id)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Merge existing preferences with updates
    current_prefs = current_user.get("preferences", {})
    current_prefs.update(preferences)
    
    # Add updated_at timestamp
    update_data = {
        "preferences": current_prefs,
        "updated_at": datetime.utcnow()
    }
    
    result = await db[DATABASE_NAME][COLLECTION].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or no changes made"
        )
    
    return await get_user_by_id(user_id)

async def delete_user(user_id: str):
    """Delete a user."""
    db = get_database().client
    result = await db[DATABASE_NAME][COLLECTION].delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"status": "success", "message": "User deleted successfully"}

async def authenticate_user(email: str, password: str):
    """Authenticate a user by email and password."""
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user 