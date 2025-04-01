from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.suggestion import Suggestion
from app.services.suggestion_service import SuggestionService
from bson.errors import InvalidId

router = APIRouter(
    prefix="/suggestions",
    tags=["suggestions"]
)

suggestion_service = SuggestionService()

# Mock authentication function for testing
async def get_current_user():
    # In a real app, this would validate the token
    # and return the user information
    return {"id": "test_user_id"}

@router.get("/{user_id}", response_model=List[Suggestion])
async def get_user_suggestions(user_id: str, current_user=Depends(get_current_user)):
    """
    Get all suggestions for a specific user.
    
    Args:
        user_id (str): The ID of the user
        
    Returns:
        List[Suggestion]: List of suggestions for the user
        
    Raises:
        HTTPException: If user_id is invalid or if there's an error fetching suggestions
    """
    try:
        suggestions = await suggestion_service.get_user_suggestions(user_id)
        return suggestions
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user ID format: {user_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching suggestions: {str(e)}"
        ) 