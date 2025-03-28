from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class Event(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    goal_id: Optional[PyObjectId] = None
    title: str = Field(...)
    description: Optional[str] = None
    start_time: datetime = Field(...)
    end_time: Optional[datetime] = None
    is_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "user_id": "5f9f1b9b0b1b9c0c0c8c1c1c",
                "goal_id": "5f9f1b9b0b1b9c0c0c8c1c1c",
                "title": "Coding Session",
                "description": "Work on TimeWell project",
                "start_time": "2023-12-31T14:00:00",
                "end_time": "2023-12-31T16:00:00",
                "is_completed": False
            }
        } 