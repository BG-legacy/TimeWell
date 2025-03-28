from datetime import datetime
from app.core.database import get_database
from app.schemas.event import EventCreate, EventUpdate
from fastapi import HTTPException, status
from bson import ObjectId
import os
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

COLLECTION = "events"
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "timewell")

async def get_event_by_id(event_id: str):
    """Get an event by ID."""
    db = get_database().client
    event = await db[DATABASE_NAME][COLLECTION].find_one({"_id": ObjectId(event_id)})
    return event

async def get_events_by_user_id(user_id: str):
    """Get all events for a user."""
    db = get_database().client
    events_cursor = db[DATABASE_NAME][COLLECTION].find({"user_id": ObjectId(user_id)})
    events = await events_cursor.to_list(length=100)
    return events

async def create_event(user_id: str, event: EventCreate):
    """Create a new event."""
    db = get_database().client
    
    # Create new event
    now = datetime.utcnow()
    event_data = event.dict()
    
    # Convert goal_id to ObjectId if present
    if event_data.get("goal_id"):
        event_data["goal_id"] = ObjectId(event_data["goal_id"])
    
    event_data.update({
        "user_id": ObjectId(user_id),
        "created_at": now,
        "updated_at": now
    })
    
    result = await db[DATABASE_NAME][COLLECTION].insert_one(event_data)
    event_data["_id"] = result.inserted_id
    return event_data

async def update_event(event_id: str, event_update: EventUpdate):
    """Update an event."""
    db = get_database().client
    
    # Find the event
    event = await get_event_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found"
        )
    
    # Prepare update data
    update_data = {k: v for k, v in event_update.dict(exclude_unset=True).items() if v is not None}
    
    # Convert goal_id to ObjectId if present
    if update_data.get("goal_id"):
        update_data["goal_id"] = ObjectId(update_data["goal_id"])
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update the event
    await db[DATABASE_NAME][COLLECTION].update_one(
        {"_id": ObjectId(event_id)},
        {"$set": update_data}
    )
    
    # Return the updated event
    return await get_event_by_id(event_id)

async def delete_event(event_id: str):
    """Delete an event."""
    db = get_database().client
    
    # Find the event
    event = await get_event_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found"
        )
    
    # Delete the event
    await db[DATABASE_NAME][COLLECTION].delete_one({"_id": ObjectId(event_id)})
    return {"message": "Event deleted successfully"} 