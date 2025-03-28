from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Any, List

from app.core.security import get_current_active_user
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse
from app.services.goal import create_goal, get_goal_by_id, update_goal, delete_goal

router = APIRouter(
    prefix="/goals",
    tags=["goals"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_new_goal(
    goal: GoalCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new goal for the current user.
    """
    user_id = str(current_user["_id"])
    new_goal = await create_goal(user_id, goal)
    return new_goal

@router.get("/{goal_id}", response_model=GoalResponse)
async def read_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get a specific goal by id.
    """
    goal = await get_goal_by_id(goal_id)
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Check if the goal belongs to the current user or if user is admin
    if str(goal["user_id"]) != str(current_user["_id"]) and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return goal

@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal_info(
    goal_id: str,
    update_data: GoalUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update a goal.
    """
    user_id = str(current_user["_id"])
    updated_goal = await update_goal(goal_id, user_id, update_data)
    return updated_goal

@router.delete("/{goal_id}", status_code=status.HTTP_200_OK)
async def delete_goal_by_id(
    goal_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete a goal.
    """
    user_id = str(current_user["_id"])
    result = await delete_goal(goal_id, user_id)
    return result 