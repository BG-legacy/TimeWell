from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    goal_id: Optional[str] = None
    is_completed: Optional[bool] = False

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    goal_id: Optional[str] = None
    is_completed: Optional[bool] = None

class EventResponse(EventBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 