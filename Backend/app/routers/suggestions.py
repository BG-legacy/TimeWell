from fastapi import APIRouter, Depends, HTTPException, status
from app.services import suggestion as suggestion_service
from app.core.auth import get_current_user
from typing import List, Dict, Any
from bson import ObjectId

router = APIRouter(
    prefix="/suggestions",
    tags=["suggestions"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=List[Dict[str, Any]])
async def get_user_suggestions(
    current_user: dict = Depends(get_current_user)
):
    """Get all suggestions for the current user."""
    suggestions = await suggestion_service.get_suggestions_by_user_id(str(current_user["_id"]))
    
    # Convert ObjectId fields to strings for all suggestions in the response
    response_data = []
    for suggestion in suggestions:
        suggestion_data = {
            **suggestion,
            "id": str(suggestion["_id"]),
            "user_id": str(suggestion["user_id"]),
            "event_id": str(suggestion["event_id"])
        }
        
        # Convert aligned_goals to strings if they are ObjectIds
        aligned_goals = []
        for goal_id in suggestion["aligned_goals"]:
            if isinstance(goal_id, ObjectId):
                aligned_goals.append(str(goal_id))
            else:
                aligned_goals.append(goal_id)
        
        suggestion_data["aligned_goals"] = aligned_goals
        response_data.append(suggestion_data)
        
    return response_data

@router.get("/event/{event_id}", response_model=List[Dict[str, Any]])
async def get_event_suggestions(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all suggestions for a specific event."""
    suggestions = await suggestion_service.get_suggestions_by_event_id(event_id)
    
    # Check if the suggestions belong to the current user
    filtered_suggestions = []
    for suggestion in suggestions:
        if str(suggestion["user_id"]) == str(current_user["_id"]):
            filtered_suggestions.append(suggestion)
    
    # Convert ObjectId fields to strings for all suggestions in the response
    response_data = []
    for suggestion in filtered_suggestions:
        suggestion_data = {
            **suggestion,
            "id": str(suggestion["_id"]),
            "user_id": str(suggestion["user_id"]),
            "event_id": str(suggestion["event_id"])
        }
        
        # Convert aligned_goals to strings if they are ObjectIds
        aligned_goals = []
        for goal_id in suggestion["aligned_goals"]:
            if isinstance(goal_id, ObjectId):
                aligned_goals.append(str(goal_id))
            else:
                aligned_goals.append(goal_id)
        
        suggestion_data["aligned_goals"] = aligned_goals
        response_data.append(suggestion_data)
        
    return response_data

@router.get("/{suggestion_id}", response_model=Dict[str, Any])
async def get_suggestion(
    suggestion_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a suggestion by ID."""
    suggestion = await suggestion_service.get_suggestion_by_id(suggestion_id)
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion with ID {suggestion_id} not found"
        )
    
    # Check if the suggestion belongs to the current user
    if str(suggestion["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this suggestion"
        )
    
    # Convert ObjectId fields to strings for the response
    response_data = {
        **suggestion,
        "id": str(suggestion["_id"]),
        "user_id": str(suggestion["user_id"]),
        "event_id": str(suggestion["event_id"])
    }
    
    # Convert aligned_goals to strings if they are ObjectIds
    aligned_goals = []
    for goal_id in suggestion["aligned_goals"]:
        if isinstance(goal_id, ObjectId):
            aligned_goals.append(str(goal_id))
        else:
            aligned_goals.append(goal_id)
    
    response_data["aligned_goals"] = aligned_goals
    
    return response_data

@router.patch("/{suggestion_id}/apply", response_model=Dict[str, Any])
async def apply_suggestion(
    suggestion_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a suggestion as applied."""
    # Check if the suggestion exists and belongs to the current user
    suggestion = await suggestion_service.get_suggestion_by_id(suggestion_id)
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion with ID {suggestion_id} not found"
        )
    
    if str(suggestion["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to apply this suggestion"
        )
    
    # Mark the suggestion as applied
    updated_suggestion = await suggestion_service.mark_suggestion_applied(suggestion_id, True)
    
    if not updated_suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to update suggestion with ID {suggestion_id}"
        )
    
    # Convert ObjectId fields to strings for the response
    response_data = {
        **updated_suggestion,
        "id": str(updated_suggestion["_id"]),
        "user_id": str(updated_suggestion["user_id"]),
        "event_id": str(updated_suggestion["event_id"])
    }
    
    # Convert aligned_goals to strings if they are ObjectIds
    aligned_goals = []
    for goal_id in updated_suggestion["aligned_goals"]:
        if isinstance(goal_id, ObjectId):
            aligned_goals.append(str(goal_id))
        else:
            aligned_goals.append(goal_id)
    
    response_data["aligned_goals"] = aligned_goals
    
    return response_data

@router.patch("/{suggestion_id}/unapply", response_model=Dict[str, Any])
async def unapply_suggestion(
    suggestion_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a suggestion as not applied."""
    # Check if the suggestion exists and belongs to the current user
    suggestion = await suggestion_service.get_suggestion_by_id(suggestion_id)
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion with ID {suggestion_id} not found"
        )
    
    if str(suggestion["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to apply this suggestion"
        )
    
    # Mark the suggestion as not applied
    updated_suggestion = await suggestion_service.mark_suggestion_applied(suggestion_id, False)
    
    if not updated_suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to update suggestion with ID {suggestion_id}"
        )
    
    # Convert ObjectId fields to strings for the response
    response_data = {
        **updated_suggestion,
        "id": str(updated_suggestion["_id"]),
        "user_id": str(updated_suggestion["user_id"]),
        "event_id": str(updated_suggestion["event_id"])
    }
    
    # Convert aligned_goals to strings if they are ObjectIds
    aligned_goals = []
    for goal_id in updated_suggestion["aligned_goals"]:
        if isinstance(goal_id, ObjectId):
            aligned_goals.append(str(goal_id))
        else:
            aligned_goals.append(goal_id)
    
    response_data["aligned_goals"] = aligned_goals
    
    return response_data 