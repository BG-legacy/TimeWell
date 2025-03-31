from datetime import datetime
from app.core.database import get_database
from app.schemas.habit import HabitCreate, HabitUpdate
from fastapi import HTTPException, status
from bson import ObjectId
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

COLLECTION = "habits"
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "timewell")

async def get_habit_by_id(habit_id: str):
    """Get a habit by ID."""
    db = get_database().client
    habit = await db[DATABASE_NAME][COLLECTION].find_one({"_id": ObjectId(habit_id)})
    return habit

async def get_habits_by_user_id(user_id: str, skip: int = 0, limit: int = 100):
    """Get habits by user ID."""
    db = get_database().client
    habits = await db[DATABASE_NAME][COLLECTION].find(
        {"user_id": ObjectId(user_id)}
    ).skip(skip).limit(limit).to_list(length=limit)
    return habits

async def create_habit(user_id: str, habit: HabitCreate):
    """Create a new habit."""
    db = get_database().client
    
    # Create new habit
    now = datetime.utcnow()
    habit_data = habit.dict()
    habit_data.update({
        "user_id": ObjectId(user_id),
        "streak_count": 0,
        "longest_streak": 0,
        "last_completed": None,
        "created_at": now,
        "updated_at": now
    })
    
    result = await db[DATABASE_NAME][COLLECTION].insert_one(habit_data)
    habit_data["_id"] = result.inserted_id
    return habit_data

async def update_habit(habit_id: str, user_id: str, update_data: HabitUpdate):
    """Update a habit."""
    db = get_database().client
    
    # Make sure the habit exists and belongs to the user
    habit = await get_habit_by_id(habit_id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )
    
    if str(habit["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this habit"
        )
    
    # Ensure _id is not updated
    update_dict = update_data.dict(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    # Add updated_at timestamp
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await db[DATABASE_NAME][COLLECTION].update_one(
        {"_id": ObjectId(habit_id)},
        {"$set": update_dict}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found or no changes made"
        )
    
    return await get_habit_by_id(habit_id)

async def delete_habit(habit_id: str, user_id: str):
    """Delete a habit."""
    db = get_database().client
    
    # Make sure the habit exists and belongs to the user
    habit = await get_habit_by_id(habit_id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )
    
    if str(habit["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this habit"
        )
    
    result = await db[DATABASE_NAME][COLLECTION].delete_one({"_id": ObjectId(habit_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )
    
    return {"status": "success", "message": "Habit deleted successfully"}

async def increment_streak(habit_id: str, user_id: str):
    """Increment the streak count for a habit."""
    db = get_database().client
    
    # Make sure the habit exists and belongs to the user
    habit = await get_habit_by_id(habit_id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )
    
    if str(habit["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this habit"
        )
    
    # Increment streak count
    new_streak = habit["streak_count"] + 1
    longest_streak = max(new_streak, habit["longest_streak"])
    
    result = await db[DATABASE_NAME][COLLECTION].update_one(
        {"_id": ObjectId(habit_id)},
        {"$set": {
            "streak_count": new_streak, 
            "longest_streak": longest_streak,
            "updated_at": datetime.utcnow()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found or no changes made"
        )
    
    return await get_habit_by_id(habit_id)

async def reset_streak(habit_id: str, user_id: str):
    """Reset the streak count for a habit."""
    db = get_database().client
    
    # Make sure the habit exists and belongs to the user
    habit = await get_habit_by_id(habit_id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )
    
    if str(habit["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this habit"
        )
    
    result = await db[DATABASE_NAME][COLLECTION].update_one(
        {"_id": ObjectId(habit_id)},
        {"$set": {
            "streak_count": 0,
            "updated_at": datetime.utcnow()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found or no changes made"
        )
    
    return await get_habit_by_id(habit_id)

async def mark_habit_complete(habit_id: str, user_id: str):
    """Mark a habit as complete, increment streak, and update last_completed timestamp."""
    db = get_database().client
    
    # Make sure the habit exists and belongs to the user
    habit = await get_habit_by_id(habit_id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )
    
    if str(habit["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this habit"
        )
    
    # Get current time
    now = datetime.utcnow()
    
    # Increment streak count
    new_streak = habit["streak_count"] + 1
    longest_streak = max(new_streak, habit.get("longest_streak", 0))
    
    # Update the habit
    result = await db[DATABASE_NAME][COLLECTION].update_one(
        {"_id": ObjectId(habit_id)},
        {"$set": {
            "streak_count": new_streak, 
            "longest_streak": longest_streak,
            "last_completed": now,
            "updated_at": now
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found or no changes made"
        )
    
    return await get_habit_by_id(habit_id) 