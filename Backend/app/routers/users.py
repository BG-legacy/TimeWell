from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Any, List, Dict

from app.core.security import get_current_active_user
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.schemas.goal import GoalResponse, GoalCreate
from app.schemas.preference import Preferences, CoachVoice
from app.services.user import create_user, get_users, get_user_by_id, update_user, delete_user, update_user_preferences
from app.services.goal import get_goals_by_user_id, create_goal

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={401: {"description": "Unauthorized"}},
)

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    """
    Get current user.
    """
    return current_user

@router.get("/", response_model=List[UserResponse])
async def read_users(skip: int = 0, limit: int = 100, current_user: dict = Depends(get_current_active_user)):
    """
    Retrieve users.
    """
    users = await get_users(skip=skip, limit=limit)
    return users

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(user: UserCreate):
    """
    Create new user.
    """
    new_user = await create_user(user)
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(user_id: str, current_user: dict = Depends(get_current_active_user)):
    """
    Get a specific user by id.
    """
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/{user_id}/goals", response_model=List[GoalResponse])
async def read_user_goals(
    user_id: str, 
    skip: int = 0, 
    limit: int = 100, 
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get goals for a specific user.
    """
    # Check if user exists
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only allow users to see their own goals or admin users
    if str(current_user["_id"]) != user_id and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    goals = await get_goals_by_user_id(user_id, skip=skip, limit=limit)
    return goals

@router.post("/{user_id}/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_user_goal(
    user_id: str,
    goal: GoalCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a goal for a specific user.
    """
    # Check if user exists
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only allow users to create goals for themselves or admin users
    if str(current_user["_id"]) != user_id and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create goals for this user"
        )
    
    # Create the goal
    new_goal = await create_goal(user_id, goal)
    return new_goal

@router.get("/{user_id}/preferences", response_model=Preferences)
async def get_user_preferences(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get a user's preferences.
    """
    # Only allow users to see their own preferences or admin users
    if str(current_user["_id"]) != user_id and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get user
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return preferences or default ones if not set
    preferences = user.get("preferences", {})
    if not preferences:
        preferences = Preferences().dict()
    
    return preferences

@router.patch("/{user_id}/preferences", response_model=UserResponse)
async def update_preferences(
    user_id: str,
    preferences: Preferences,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update a user's preferences.
    """
    # Only allow users to update their own preferences or admin users
    if str(current_user["_id"]) != user_id and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update the preferences
    updated_user = await update_user_preferences(user_id, preferences.dict(exclude_unset=True))
    return updated_user

@router.patch("/{user_id}/preferences/coach-voice", response_model=UserResponse)
async def update_coach_voice(
    user_id: str,
    coach_voice: CoachVoice,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update a user's coach voice preference.
    """
    # Only allow users to update their own preferences or admin users
    if str(current_user["_id"]) != user_id and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update just the coach_voice preference
    updated_user = await update_user_preferences(user_id, {"coach_voice": coach_voice})
    return updated_user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: str, 
    update_data: UserUpdate, 
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update a user.
    """
    if str(current_user["_id"]) != user_id and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Convert Pydantic model to dict, excluding None values
    update_dict = update_data.dict(exclude_unset=True)
    
    # Only proceed if there are fields to update
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    updated_user = await update_user(user_id, update_dict)
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user_by_id(
    user_id: str, 
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete a user.
    """
    if str(current_user["_id"]) != user_id and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    result = await delete_user(user_id)
    return result 