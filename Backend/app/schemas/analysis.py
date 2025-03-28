from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AlignmentRequest(BaseModel):
    event_id: str = Field(..., description="The ID of the event to analyze")

class AlignedGoal(BaseModel):
    id: str = Field(..., description="The ID of the aligned goal")
    title: str = Field(..., description="The title of the aligned goal")
    contribution_level: str = Field(..., description="How the event contributes to this goal")

class GoalAlignmentAnalysis(BaseModel):
    score: int = Field(..., description="Alignment score from 1-10", ge=1, le=10)
    aligned_goals: List[str] = Field(default=[], description="IDs of goals this event aligns with")
    analysis: str = Field(..., description="Brief analysis of the alignment")
    suggestion: str = Field(..., description="Suggestion to improve alignment")
    new_goal_suggestion: Optional[str] = Field(None, description="Suggestion for a new goal if no alignment found")

class AnalysisResponse(BaseModel):
    error: bool = Field(..., description="Whether there was an error in the analysis")
    event_id: Optional[str] = Field(None, description="The ID of the analyzed event")
    analysis: Optional[str] = Field(None, description="The analysis result in JSON format")
    message: Optional[str] = Field(None, description="Error message if applicable")

class SuggestionCreate(BaseModel):
    user_id: str = Field(..., description="The ID of the user who owns this suggestion")
    event_id: str = Field(..., description="The ID of the event this suggestion is for")
    score: int = Field(..., description="Alignment score from 1-10", ge=1, le=10)
    aligned_goals: List[str] = Field(default=[], description="IDs of goals this event aligns with")
    analysis: str = Field(..., description="Brief analysis of the alignment")
    suggestion: str = Field(..., description="Suggestion to improve alignment")
    new_goal_suggestion: Optional[str] = Field(None, description="Suggestion for a new goal if no alignment found")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this suggestion was created")
    is_applied: bool = Field(default=False, description="Whether this suggestion has been applied by the user") 