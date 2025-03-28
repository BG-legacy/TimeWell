from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from bson.errors import InvalidId
from app.core.database import get_database
from app.schemas.analysis import SuggestionCreate

# Define database constants
DATABASE_NAME = "timewell"
COLLECTION = "suggestions"

async def create_suggestion(suggestion: SuggestionCreate) -> Dict[str, Any]:
    """
    Create a new suggestion in the database.
    
    Args:
        suggestion: The suggestion data
        
    Returns:
        The created suggestion document
    """
    db = get_database().client
    
    # Convert user_id and event_id to ObjectId if they're not already
    suggestion_data = suggestion.model_dump()
    
    if isinstance(suggestion_data["user_id"], str):
        suggestion_data["user_id"] = ObjectId(suggestion_data["user_id"])
    
    if isinstance(suggestion_data["event_id"], str):
        suggestion_data["event_id"] = ObjectId(suggestion_data["event_id"])
    
    # Convert aligned_goals to ObjectIds if they are valid ObjectId strings
    # If not, keep them as strings (for the case of LangChain analysis where they might not be ObjectIds)
    aligned_goals = []
    for goal_id in suggestion_data["aligned_goals"]:
        if isinstance(goal_id, str):
            try:
                aligned_goals.append(ObjectId(goal_id))
            except InvalidId:
                # If it's not a valid ObjectId, just keep it as a string
                aligned_goals.append(goal_id)
        else:
            aligned_goals.append(goal_id)
    
    suggestion_data["aligned_goals"] = aligned_goals
    
    # Add timestamps
    suggestion_data["created_at"] = datetime.utcnow()
    
    # Insert into database
    result = await db[DATABASE_NAME][COLLECTION].insert_one(suggestion_data)
    
    # Get the created suggestion
    suggestion_data["_id"] = result.inserted_id
    
    return suggestion_data

async def get_suggestions_by_user_id(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all suggestions for a specific user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        A list of suggestion documents
    """
    db = get_database().client
    
    # Convert user_id to ObjectId if it's not already
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    cursor = db[DATABASE_NAME][COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
    suggestions = await cursor.to_list(length=None)
    
    return suggestions

async def get_suggestions_by_event_id(event_id: str) -> List[Dict[str, Any]]:
    """
    Get all suggestions for a specific event.
    
    Args:
        event_id: The ID of the event
        
    Returns:
        A list of suggestion documents
    """
    db = get_database().client
    
    # Convert event_id to ObjectId if it's not already
    if isinstance(event_id, str):
        event_id = ObjectId(event_id)
    
    cursor = db[DATABASE_NAME][COLLECTION].find({"event_id": event_id}).sort("created_at", -1)
    suggestions = await cursor.to_list(length=None)
    
    return suggestions

async def get_suggestion_by_id(suggestion_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a suggestion by its ID.
    
    Args:
        suggestion_id: The ID of the suggestion
        
    Returns:
        The suggestion document if found, otherwise None
    """
    db = get_database().client
    
    # Convert suggestion_id to ObjectId if it's not already
    if isinstance(suggestion_id, str):
        suggestion_id = ObjectId(suggestion_id)
    
    suggestion = await db[DATABASE_NAME][COLLECTION].find_one({"_id": suggestion_id})
    
    return suggestion

async def mark_suggestion_applied(suggestion_id: str, is_applied: bool = True) -> Optional[Dict[str, Any]]:
    """
    Mark a suggestion as applied or not applied.
    
    Args:
        suggestion_id: The ID of the suggestion
        is_applied: Whether the suggestion has been applied
        
    Returns:
        The updated suggestion document if found, otherwise None
    """
    db = get_database().client
    
    # Convert suggestion_id to ObjectId if it's not already
    if isinstance(suggestion_id, str):
        suggestion_id = ObjectId(suggestion_id)
    
    result = await db[DATABASE_NAME][COLLECTION].update_one(
        {"_id": suggestion_id},
        {"$set": {"is_applied": is_applied, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        return None
    
    return await get_suggestion_by_id(str(suggestion_id)) 