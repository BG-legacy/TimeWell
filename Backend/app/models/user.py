from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
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

class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    email: str = Field(...)
    username: str = Field(...)
    hashed_password: str = Field(...)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True,
            }
        } 