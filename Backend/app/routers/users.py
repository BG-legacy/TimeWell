from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from app.core.security import get_current_active_user
from app.schemas.user import UserResponse

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