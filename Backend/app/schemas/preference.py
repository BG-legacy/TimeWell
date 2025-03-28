from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class CoachVoice(str, Enum):
    MOTIVATIONAL = "motivational"
    SUPPORTIVE = "supportive"
    DIRECT = "direct"
    ANALYTICAL = "analytical"
    FRIENDLY = "friendly"

class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

class Preferences(BaseModel):
    coach_voice: Optional[CoachVoice] = CoachVoice.SUPPORTIVE
    theme: Optional[Theme] = Theme.SYSTEM
    notifications_enabled: Optional[bool] = True
    daily_reminder_time: Optional[str] = "09:00" # Format: "HH:MM"
    weekly_summary_day: Optional[int] = 0 # 0 = Sunday, 1 = Monday, etc.
    
    class Config:
        populate_by_name = True 