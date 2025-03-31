from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Any, List

from app.core.security import get_current_active_user
from app.schemas.habit import HabitCreate, HabitUpdate, HabitResponse
from app.services.habit import (
    create_habit, 
    get_habit_by_id, 
    get_habits_by_user_id,
    update_habit, 
    delete_habit,
    increment_streak,
    reset_streak,
    mark_habit_complete
)

router = APIRouter(
    prefix="/habits",
    tags=["habits"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_new_habit(
    habit: HabitCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new habit for the current user.
    
    The habit must include:
    - title: The name of the habit
    - frequency: One of "daily", "weekly", or "monthly"
    
    Optional fields:
    - description: A detailed description of the habit
    - target_days: 
        - For daily habits: Should be null or empty
        - For weekly habits: Days of week (0-6, where 0 is Monday)
        - For monthly habits: Days of month (1-31)
    - color: Hex color code for UI display
    - icon: Icon name for UI display
    - is_active: Whether the habit is active (default: true)
    
    The response includes:
    - All input fields
    - streak_count: Current streak (starts at 0)
    - longest_streak: Longest streak achieved (starts at 0)
    - created_at and updated_at timestamps
    """
    user_id = str(current_user["_id"])
    new_habit = await create_habit(user_id, habit)
    return new_habit

@router.get("/", response_model=List[HabitResponse])
async def read_habits(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get all habits for the current user.
    """
    user_id = str(current_user["_id"])
    habits = await get_habits_by_user_id(user_id, skip, limit)
    return habits

@router.get("/{habit_id}", response_model=HabitResponse)
async def read_habit(
    habit_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get a specific habit by id.
    """
    habit = await get_habit_by_id(habit_id)
    
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found"
        )
    
    # Check if the habit belongs to the current user
    if str(habit["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return habit

@router.patch("/{habit_id}", response_model=HabitResponse)
async def update_habit_info(
    habit_id: str,
    update_data: HabitUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update a habit.
    """
    user_id = str(current_user["_id"])
    updated_habit = await update_habit(habit_id, user_id, update_data)
    return updated_habit

@router.delete("/{habit_id}", status_code=status.HTTP_200_OK)
async def delete_habit_by_id(
    habit_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete a habit.
    """
    user_id = str(current_user["_id"])
    result = await delete_habit(habit_id, user_id)
    return result

@router.post("/{habit_id}/increment-streak", response_model=HabitResponse)
async def increment_habit_streak(
    habit_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Increment the streak count for a habit.
    """
    user_id = str(current_user["_id"])
    updated_habit = await increment_streak(habit_id, user_id)
    return updated_habit

@router.post("/{habit_id}/reset-streak", response_model=HabitResponse)
async def reset_habit_streak(
    habit_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Reset the streak count for a habit.
    """
    user_id = str(current_user["_id"])
    updated_habit = await reset_streak(habit_id, user_id)
    return updated_habit

@router.get("/user/{user_id}", response_model=List[HabitResponse])
async def read_habits_by_user_id(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get all habits for a specific user by user_id.
    
    This endpoint is primarily for admin or authorized users to view
    habits of other users. Regular users can only view their own habits.
    
    If the requesting user is not an admin or the owner of the habits,
    permission will be denied.
    """
    # Check if the user is requesting their own habits or if they're an admin
    is_own_habits = str(current_user["_id"]) == user_id
    is_admin = current_user.get("is_admin", False)
    
    if not (is_own_habits or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view other users' habits"
        )
    
    habits = await get_habits_by_user_id(user_id, skip, limit)
    return habits

@router.put("/{habit_id}/complete", response_model=HabitResponse)
async def complete_habit(
    habit_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Mark a habit as complete.
    
    This endpoint:
    1. Increments the habit's streak count
    2. Updates the longest streak if needed
    3. Sets the last_completed timestamp to the current time
    
    Returns the updated habit with the new streak information.
    """
    user_id = str(current_user["_id"])
    updated_habit = await mark_habit_complete(habit_id, user_id)
    return updated_habit 