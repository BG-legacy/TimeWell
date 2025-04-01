from typing import List
from bson import ObjectId
from app.models.suggestion import Suggestion
from app.core.database import get_database, db
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class SuggestionService:
    def __init__(self):
        # Ensure database is connected
        if db.client is None:
            db.connect_to_database()
            
        self.db = db
        self.db_name = os.getenv("MONGODB_DATABASE_NAME", "timewell")
        self.collection = self.db.client[self.db_name]["suggestions"]
        
        # Indexes will be created asynchronously when needed
    
    async def _ensure_indexes(self):
        """Create indexes for faster querying"""
        try:
            # Create indexes in the background
            await self.collection.create_index("user_id", background=True)
            await self.collection.create_index("event_id", background=True)
            await self.collection.create_index([("user_id", 1), ("is_active", 1)], background=True)
        except Exception as e:
            logging.warning(f"Failed to create indexes: {e}")

    async def get_user_suggestions(self, user_id: str) -> List[Suggestion]:
        """
        Fetch all suggestions for a specific user.
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            List[Suggestion]: List of suggestions for the user
        """
        try:
            query = {
                "user_id": ObjectId(user_id),
                "is_active": True
            }
            # Find all matching documents and sort them
            cursor = self.collection.find(query).sort("created_at", -1)
            
            suggestions = []
            async for document in cursor:
                suggestions.append(Suggestion(**document))
            return suggestions
        except Exception as e:
            logging.error(f"Error fetching suggestions: {e}")
            # Return empty list rather than raising exception
            return [] 