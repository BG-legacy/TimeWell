from datetime import datetime
from app.core.database import get_database
from app.schemas.goal import GoalCreate, GoalUpdate
from fastapi import HTTPException, status
from bson import ObjectId
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

COLLECTION = "goals"
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "timewell")

async def get_goal_by_id(goal_id: str):
    """Get a goal by ID."""
    db = get_database().client
    goal = await db[DATABASE_NAME][COLLECTION].find_one({"_id": ObjectId(goal_id)})
    return goal

async def get_goals_by_user_id(user_id: str, skip: int = 0, limit: int = 100):
    """Get goals by user ID."""
    db = get_database().client
    goals = await db[DATABASE_NAME][COLLECTION].find(
        {"user_id": ObjectId(user_id)}
    ).skip(skip).limit(limit).to_list(length=limit)
    return goals

async def create_goal(user_id: str, goal: GoalCreate):
    """Create a new goal."""
    db = get_database().client
    
    # Create new goal
    now = datetime.utcnow()
    goal_data = goal.dict()
    goal_data.update({
        "user_id": ObjectId(user_id),
        "created_at": now,
        "updated_at": now
    })
    
    result = await db[DATABASE_NAME][COLLECTION].insert_one(goal_data)
    goal_data["_id"] = result.inserted_id
    return goal_data

async def update_goal(goal_id: str, user_id: str, update_data: GoalUpdate):
    """Update a goal."""
    db = get_database().client
    
    # Make sure the goal exists and belongs to the user
    goal = await get_goal_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    if str(goal["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this goal"
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
        {"_id": ObjectId(goal_id)},
        {"$set": update_dict}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found or no changes made"
        )
    
    return await get_goal_by_id(goal_id)

async def delete_goal(goal_id: str, user_id: str):
    """Delete a goal."""
    db = get_database().client
    
    # Make sure the goal exists and belongs to the user
    goal = await get_goal_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    if str(goal["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this goal"
        )
    
    result = await db[DATABASE_NAME][COLLECTION].delete_one({"_id": ObjectId(goal_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return {"status": "success", "message": "Goal deleted successfully"} 