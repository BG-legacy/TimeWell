from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.with_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, value, info):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

    def __repr__(self):
        return f"PyObjectId({super().__repr__()})"

class Suggestion(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    category: str = Field(...)  # e.g., "productivity", "health", "learning"
    priority: int = Field(default=1)  # 1-5, where 5 is highest priority
    status: str = Field(default="pending")  # pending, accepted, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: Optional[List[str]] = None
    is_active: bool = Field(default=True)
    
    # New fields for AI and event tracking
    ai_prompt: Optional[str] = None  # The prompt used to generate this suggestion
    ai_response: Optional[str] = None  # The full AI response that generated this suggestion
    event_id: Optional[PyObjectId] = None  # Reference to the event that triggered this suggestion
    was_accepted: bool = Field(default=False)  # Whether the user accepted this suggestion

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "title": "Start a Daily Reading Habit",
                "description": "Read for 20 minutes every morning to improve knowledge and focus",
                "category": "learning",
                "priority": 4,
                "status": "pending",
                "tags": ["reading", "morning-routine", "learning"],
                "is_active": True,
                "ai_prompt": "Generate a suggestion for improving morning productivity",
                "ai_response": "Based on the user's schedule and goals, I suggest implementing a daily reading habit...",
                "event_id": "507f1f77bcf86cd799439011",
                "was_accepted": False
            }
        }
    ) 