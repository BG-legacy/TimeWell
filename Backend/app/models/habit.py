from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Annotated
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

class Habit(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    title: str = Field(...)
    description: Optional[str] = None
    frequency: str = Field(...)  # daily, weekly, monthly
    target_days: Optional[List[int]] = None  # days of week (0-6) or month (1-31)
    streak_count: int = Field(default=0)
    longest_streak: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = Field(default=True)

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "title": "Morning Meditation",
                "description": "10 minutes of mindfulness meditation",
                "frequency": "daily",
                "streak_count": 5,
                "longest_streak": 10,
                "color": "#4287f5",
                "icon": "meditation",
                "is_active": True
            }
        }
    ) 