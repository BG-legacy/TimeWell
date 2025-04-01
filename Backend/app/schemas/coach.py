from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class ReflectionRequest(BaseModel):
    """
    Schema for requesting a reflection from the coach
    """
    user_id: str = Field(..., description="ID of the user requesting reflection")
    reflection_type: Literal["weekly", "monthly", "status"] = Field(..., description="Type of reflection requested")
    time_period: Optional[str] = Field(None, description="Specific time period to reflect on (e.g., 'Apr 1-7', '2023-04-01 to 2023-04-07')")
    focus_areas: Optional[List[str]] = Field(None, description="Optional specific areas to focus reflection on")


class ReflectionResponse(BaseModel):
    """
    Schema for coach reflection response
    """
    user_id: str = Field(..., description="ID of the user the reflection is for")
    reflection_text: str = Field(..., description="The coach's reflection text")
    highlights: Optional[List[str]] = Field(None, description="Key highlights or achievements")
    suggestions: Optional[List[str]] = Field(None, description="Suggestions for improvement")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the reflection was created")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "60d5e74dc2dfc33c4c7c0e9a",
                "reflection_text": "You've made great progress this week on your fitness goals...",
                "highlights": ["Completed all workouts", "Improved sleep schedule"],
                "suggestions": ["Consider adding more variety to your workouts", "Try to reduce screen time before bed"],
                "created_at": "2023-04-15T14:30:00"
            }
        } 