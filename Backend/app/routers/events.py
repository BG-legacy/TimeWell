from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.event import EventCreate, EventUpdate, EventResponse
from app.schemas.analysis import AlignmentRequest, AnalysisResponse
from app.services import event as event_service
from app.services import user as user_service
from app.services.ai_analysis import analyze_event_goal_alignment
from app.core.auth import get_current_user
from typing import List
from bson import ObjectId
from datetime import datetime

router = APIRouter(
    prefix="/events",
    tags=["events"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new event for the current user."""
    event = await event_service.create_event(str(current_user["_id"]), event_data)
    
    # Convert ObjectId fields to strings for the response
    response_data = {
        **event,
        "id": str(event["_id"]), 
        "user_id": str(event["user_id"])
    }
    
    # Convert goal_id to string if it exists and is an ObjectId
    if "goal_id" in event and event["goal_id"]:
        response_data["goal_id"] = str(event["goal_id"])
        
    return response_data

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_event(
    request: AlignmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze an event's alignment with the user's goals using GPT-4.
    
    This endpoint uses AI to analyze how well an event aligns with the user's goals
    and provides suggestions for improvement.
    """
    # Get the event details to verify ownership
    event = await event_service.get_event_by_id(request.event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {request.event_id} not found"
        )
    
    # Check if the event belongs to the current user
    if str(event["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to analyze this event"
        )
    
    # Perform the analysis
    analysis_result = await analyze_event_goal_alignment(
        str(current_user["_id"]), 
        request.event_id
    )
    
    return analysis_result

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get an event by ID."""
    event = await event_service.get_event_by_id(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found"
        )
    
    # Check if the event belongs to the current user
    if str(event["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this event"
        )
    
    # Convert ObjectId fields to strings for the response
    response_data = {
        **event,
        "id": str(event["_id"]), 
        "user_id": str(event["user_id"])
    }
    
    # Convert goal_id to string if it exists and is an ObjectId
    if "goal_id" in event and event["goal_id"]:
        response_data["goal_id"] = str(event["goal_id"])
        
    return response_data

@router.get("", response_model=List[EventResponse])
async def get_user_events(
    current_user: dict = Depends(get_current_user)
):
    """Get all events for the current user."""
    events = await event_service.get_events_by_user_id(str(current_user["_id"]))
    
    # Convert ObjectId fields to strings for all events in the response
    response_data = []
    for event in events:
        event_data = {
            **event,
            "id": str(event["_id"]),
            "user_id": str(event["user_id"])
        }
        
        # Convert goal_id to string if it exists and is an ObjectId
        if "goal_id" in event and event["goal_id"]:
            event_data["goal_id"] = str(event["goal_id"])
            
        response_data.append(event_data)
        
    return response_data

@router.get("/user/{user_id}", response_model=List[EventResponse])
async def get_events_by_user_id(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all events for a specific user."""
    # Check if the requested user_id exists
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check authorization - only allow users to see their own events unless admin
    # Future enhancement: Add admin role check
    if str(current_user["_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access events for this user"
        )
    
    # Get the events
    events = await event_service.get_events_by_user_id(user_id)
    
    # Convert ObjectId fields to strings for all events in the response
    response_data = []
    for event in events:
        event_data = {
            **event,
            "id": str(event["_id"]),
            "user_id": str(event["user_id"])
        }
        
        # Convert goal_id to string if it exists and is an ObjectId
        if "goal_id" in event and event["goal_id"]:
            event_data["goal_id"] = str(event["goal_id"])
            
        response_data.append(event_data)
        
    return response_data

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event_endpoint(
    event_id: str,
    event_update: EventUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an event."""
    # Check if the event exists and belongs to the user
    existing_event = await event_service.get_event_by_id(event_id)
    
    if not existing_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found"
        )
    
    if str(existing_event["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this event"
        )
    
    # Update the event
    updated_event = await event_service.update_event(event_id, event_update)
    
    # Convert ObjectId fields to strings for the response
    response_data = {
        **updated_event,
        "id": str(updated_event["_id"]), 
        "user_id": str(updated_event["user_id"])
    }
    
    # Convert goal_id to string if it exists and is an ObjectId
    if "goal_id" in updated_event and updated_event["goal_id"]:
        response_data["goal_id"] = str(updated_event["goal_id"])
        
    return response_data

@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
async def delete_event_endpoint(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an event."""
    # Check if the event exists and belongs to the user
    existing_event = await event_service.get_event_by_id(event_id)
    
    if not existing_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found"
        )
    
    if str(existing_event["user_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this event"
        )
    
    # Delete the event
    return await event_service.delete_event(event_id) 