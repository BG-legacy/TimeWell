from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Annotated, Literal
from bson import ObjectId
import re

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

class HabitBase(BaseModel):
    """
    Base model for habits with common fields.
    
    Attributes:
        title: The name of the habit
        description: Optional detailed description
        frequency: How often the habit should be completed (daily, weekly, monthly)
        target_days: Days when the habit should be completed (depending on frequency)
        color: Hex color code for UI display
        icon: Icon name for UI display
        is_active: Whether the habit is currently active
    """
    title: str
    description: Optional[str] = None
    frequency: Literal["daily", "weekly", "monthly"]
    target_days: Optional[List[int]] = None  # days of week (0-6) or month (1-31)
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = True

    @field_validator('target_days')
    @classmethod
    def validate_target_days(cls, v, info):
        if v is None:
            return v
        
        values = info.data
        if 'frequency' not in values:
            return v
            
        frequency = values['frequency']
        
        if frequency == 'daily':
            # For daily habits, target_days should be null or empty
            if v and len(v) > 0:
                raise ValueError("Daily habits should not have target days specified")
        elif frequency == 'weekly':
            # For weekly habits, target_days should contain days of week (0-6)
            if not all(0 <= day <= 6 for day in v):
                raise ValueError("Weekly habits' target days must be between 0 (Monday) and 6 (Sunday)")
        elif frequency == 'monthly':
            # For monthly habits, target_days should contain days of month (1-31)
            if not all(1 <= day <= 31 for day in v):
                raise ValueError("Monthly habits' target days must be between 1 and 31")
        
        return v

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        if v is None:
            return v
            
        # Check if it's a valid hex color (with or without # prefix)
        if not re.match(r'^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', v):
            raise ValueError("Color must be a valid hex color code (e.g., '#4287f5' or '4287f5')")
            
        # Ensure it has the # prefix
        if not v.startswith('#'):
            v = f'#{v}'
            
        return v

class HabitCreate(HabitBase):
    """Model for creating a new habit."""
    pass

class HabitUpdate(BaseModel):
    """
    Model for updating an existing habit.
    
    All fields are optional, allowing partial updates to the habit.
    Only the fields that are set will be updated.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    target_days: Optional[List[int]] = None
    streak_count: Optional[int] = None
    longest_streak: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None

class HabitResponse(HabitBase):
    """
    Model for the habit response returned by the API.
    
    Includes all base fields plus:
    - id: The habit's unique identifier
    - user_id: The ID of the user who owns the habit
    - streak_count: Current streak for the habit
    - longest_streak: Longest streak achieved for the habit
    - last_completed: Timestamp when the habit was last completed
    - created_at: Timestamp when the habit was created
    - updated_at: Timestamp when the habit was last updated
    """
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    streak_count: int
    longest_streak: int
    last_completed: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "_id": "5f9f1b9b9d9d6b8c8c8c8c8c",
                "user_id": "5f9f1b9b9d9d6b8c8c8c8c8c",
                "title": "Morning Meditation",
                "description": "10 minutes of mindfulness meditation",
                "frequency": "daily",
                "streak_count": 5,
                "longest_streak": 10,
                "last_completed": "2023-01-01T10:00:00",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T10:00:00",
                "color": "#4287f5",
                "icon": "meditation",
                "is_active": True
            }
        }
    ) 