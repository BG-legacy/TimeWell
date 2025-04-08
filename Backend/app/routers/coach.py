from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import List, Optional, Dict, Any
from app.schemas.coach import ReflectionRequest, ReflectionResponse
from app.core.database import get_database
from datetime import datetime, timedelta
from app.schemas.preference import CoachVoice
from app.core.security import get_current_active_user
import uuid
import os
import logging
from dotenv import load_dotenv
from bson import ObjectId
from app.core.auth import get_current_user
from app.services.coach_service import coach_service
from app.services.event import get_events_by_user_id
from app.services.goal import get_goals_by_user_id
from app.services.prompt_templates import VoiceStyle
from app.schemas.analysis import AnalysisResponse
from pydantic import BaseModel, Field

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database name from environment
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "timewell")

router = APIRouter(
    prefix="/coach",
    tags=["coach"],
    responses={404: {"description": "Not found"}},
)

class CoachingRequest(BaseModel):
    prompt: str = Field(..., description="The user's prompt or question")
    voice_style: Optional[str] = Field(default="cool_cousin", description="The voice style to use for the response")
    model: Optional[str] = Field(default="gpt-4", description="The model to use")

class CoachingResponse(BaseModel):
    text: str = Field(..., description="The coaching response text")
    voice_style: str = Field(..., description="The voice style used")
    model: str = Field(..., description="The model used")
    token_usage: Optional[int] = Field(None, description="Token usage for the request")
    error: Optional[bool] = Field(None, description="Whether there was an error")
    message: Optional[str] = Field(None, description="Error message if applicable")

class ActionPlan(BaseModel):
    actions: List[str] = Field(..., description="List of recommended actions")
    priorities: List[str] = Field(..., description="List of priority areas to focus on")
    insights: List[str] = Field(..., description="List of insights from the user's data")

class ActionPlanRequest(BaseModel):
    timeframe: str = Field(default="week", description="Timeframe for the action plan (day, week, month)")
    voice_style: Optional[str] = Field(default="motivator", description="The voice style to use for the response")


def generate_voice_specific_content(coach_voice: CoachVoice, content_type: str, data: Dict[str, Any]) -> str:
    """
    Generate content based on the user's preferred coach voice.
    
    This function provides different phrasings for the same content based on the coach voice preference.
    
    Args:
        coach_voice: The user's preferred coaching style
        content_type: Type of content to generate (reflection, encouragement, feedback)
        data: Dictionary with relevant data for the content generation
        
    Returns:
        String with the voice-specific content
    """
    # Simplified version - in production this would integrate with a GPT API
    if content_type == "encouragement":
        achievement = data.get("achievement", "your progress")
        
        if coach_voice == CoachVoice.MOTIVATIONAL:
            return f"Amazing job with {achievement}! You're crushing it! Keep that momentum going!"
        
        elif coach_voice == CoachVoice.SUPPORTIVE:
            return f"I'm really proud of your work on {achievement}. You're doing great and making steady progress."
        
        elif coach_voice == CoachVoice.DIRECT:
            return f"Good work on {achievement}. You've achieved your target. Now focus on the next goal."
        
        elif coach_voice == CoachVoice.ANALYTICAL:
            return f"The data shows excellent completion of {achievement}. This puts you ahead of schedule for your long-term objectives."
        
        elif coach_voice == CoachVoice.FRIENDLY:
            return f"Hey there! Just wanted to say you're doing awesome with {achievement}! It's really great to see!"
    
    elif content_type == "feedback":
        area = data.get("area", "your routine")
        suggestion = data.get("suggestion", "make some adjustments")
        
        if coach_voice == CoachVoice.MOTIVATIONAL:
            return f"Let's take {area} to the next level! I know you can {suggestion} and achieve even more!"
        
        elif coach_voice == CoachVoice.SUPPORTIVE:
            return f"I've noticed something about {area}. Would you consider trying to {suggestion}? I think it might help you."
        
        elif coach_voice == CoachVoice.DIRECT:
            return f"{area} needs improvement. You should {suggestion} to see better results."
        
        elif coach_voice == CoachVoice.ANALYTICAL:
            return f"Analysis of {area} indicates suboptimal performance. Implementing '{suggestion}' would likely yield a 20% improvement."
        
        elif coach_voice == CoachVoice.FRIENDLY:
            return f"Hey! I was thinking about {area} - maybe we could try to {suggestion}? Just a thought! :-)"
    
    # Default case
    return f"Here's a note about {data.get('topic', 'your progress')}"


@router.post("/feedback", status_code=status.HTTP_200_OK)
async def generate_feedback(
    feedback_data: dict = Body(..., description="Feedback data with 'area' and 'suggestion' fields"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Generate personalized feedback using the user's preferred coach voice.
    
    This endpoint generates feedback on a specific area with a suggestion for improvement,
    using the user's preferred coaching style.
    
    - **feedback_data**: JSON object with 'area' and 'suggestion' fields (e.g., {"area": "morning routine", "suggestion": "start with a workout"})
    """
    # Extract data from request body
    area = feedback_data.get("area", "your routine")
    suggestion = feedback_data.get("suggestion", "make some adjustments")
    
    # Get user's preferred coach voice
    preferences = current_user.get("preferences", {})
    coach_voice = preferences.get("coach_voice", CoachVoice.SUPPORTIVE)
    
    # Generate feedback using the preferred coach voice
    feedback = generate_voice_specific_content(
        coach_voice=coach_voice,
        content_type="feedback",
        data={"area": area, "suggestion": suggestion}
    )
    
    return {
        "user_id": str(current_user["_id"]),
        "coach_voice": coach_voice,
        "feedback": feedback
    }


@router.post("/encourage", status_code=status.HTTP_200_OK)
async def generate_encouragement(
    achievement_data: dict = Body(..., description="Achievement data with 'achievement' field"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Generate personalized encouragement using the user's preferred coach voice.
    
    This endpoint generates encouraging messages based on a specific achievement,
    using the user's preferred coaching style.
    
    - **achievement_data**: JSON object with 'achievement' field (e.g., {"achievement": "completing all tasks"})
    """
    # Extract achievement from request body
    achievement = achievement_data.get("achievement", "your progress")
    
    # Get user's preferred coach voice
    preferences = current_user.get("preferences", {})
    coach_voice = preferences.get("coach_voice", CoachVoice.SUPPORTIVE)
    
    # Generate encouragement using the preferred coach voice
    encouragement = generate_voice_specific_content(
        coach_voice=coach_voice,
        content_type="encouragement",
        data={"achievement": achievement}
    )
    
    return {
        "user_id": str(current_user["_id"]),
        "coach_voice": coach_voice,
        "encouragement": encouragement
    }


@router.post("/reflect", response_model=ReflectionResponse, status_code=status.HTTP_201_CREATED)
async def create_reflection(
    reflection_request: ReflectionRequest, 
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a personalized reflection for a user based on their data and specified time period.
    
    The reflection analyzes user activities, habits, and goals to provide insights and suggestions.
    
    - **user_id**: ID of the user requesting reflection
    - **reflection_type**: Type of reflection ("weekly", "monthly", "status")
    - **time_period**: Optional specific time period (defaults to current week/month)
    - **focus_areas**: Optional specific areas to focus reflection on
    """
    # Use authenticated user's ID if not specifically overridden by an admin
    user_id = reflection_request.user_id
    
    # Get database connection
    db = get_database().client
    
    # Verify user exists
    user = await db[DATABASE_NAME]["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get user's preferred coach voice
    preferences = user.get("preferences", {})
    coach_voice = preferences.get("coach_voice", CoachVoice.SUPPORTIVE)
    
    # Determine time period if not specified
    time_period = reflection_request.time_period
    if not time_period:
        now = datetime.utcnow()
        if reflection_request.reflection_type == "weekly":
            # Calculate start of current week (Monday)
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            time_period = f"{start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d, %Y')}"
        elif reflection_request.reflection_type == "monthly":
            # Current month
            time_period = now.strftime("%B %Y")
        else:  # status
            time_period = "current"

    # In a production app, this would integrate with the GPT API
    # Here we'll simulate different outputs based on the coach voice
    
    # Base reflection data that would be personalized with user data in production
    base_data = {
        "reflection_type": reflection_request.reflection_type,
        "time_period": time_period,
        "focus_areas": reflection_request.focus_areas,
    }
    
    # Generate reflection content based on coach voice
    reflection_text = ""
    highlights = []
    suggestions = []
    
    if reflection_request.reflection_type == "weekly":
        # Different intro based on coach voice
        if coach_voice == CoachVoice.MOTIVATIONAL:
            reflection_text = f"Incredible week, champion! Looking at {time_period}, you've shown amazing dedication to your goals!"
            highlights = ["Crushed your daily targets 5 days in a row!", "Smashed that big project deadline - outstanding!"]
            suggestions = ["Let's challenge ourselves even more next week!", "How about adding one more workout to take it to the next level?"]
        
        elif coach_voice == CoachVoice.SUPPORTIVE:
            reflection_text = f"It's been a good week for you during {time_period}. I've noticed some really positive patterns in your habits."
            highlights = ["You've been consistent with your morning routine", "You made good progress on your main project"]
            suggestions = ["Consider taking a bit more time for self-care next week", "Maybe we could work on spacing out your tasks more evenly"]
        
        elif coach_voice == CoachVoice.DIRECT:
            reflection_text = f"Week of {time_period} analysis: Overall good performance with room for improvement."
            highlights = ["Met daily habit targets", "Project deadlines achieved"]
            suggestions = ["Increase focus time by 20%", "Reduce procrastination on start-of-day tasks"]
        
        elif coach_voice == CoachVoice.ANALYTICAL:
            reflection_text = f"Analysis of week {time_period}: Productivity metrics show 72% overall efficiency with variable performance across domains."
            highlights = ["Task completion rate: 85% (↑6% from previous week)", "Focus time: 24.3 hours (within optimal range)"]
            suggestions = ["Recommend redistributing deep work sessions to morning hours for 12% projected efficiency gain", "Task batching opportunities identified in email processing workflow"]
        
        elif coach_voice == CoachVoice.FRIENDLY:
            reflection_text = f"Hey there! We've made it through another week ({time_period})! Let's chat about how things went!"
            highlights = ["You did great keeping up with your daily check-ins!", "Loved seeing you make time for that hobby you enjoy!"]
            suggestions = ["Maybe we could try squeezing in a little more sleep next week?", "How about we plan something fun as a reward for your hard work?"]
    
    elif reflection_request.reflection_type == "status":
        # Status update with coach voice variations
        if coach_voice == CoachVoice.MOTIVATIONAL:
            reflection_text = "You're absolutely crushing it right now! Your current momentum is fantastic!"
        elif coach_voice == CoachVoice.SUPPORTIVE:
            reflection_text = "Things are going well for you right now. I can see you're putting in consistent effort."
        elif coach_voice == CoachVoice.DIRECT:
            reflection_text = "Current status: On track. Continue current performance levels to meet objectives."
        elif coach_voice == CoachVoice.ANALYTICAL:
            reflection_text = "Present status analysis: Metrics indicate satisfactory progress with 68% task efficiency."
        elif coach_voice == CoachVoice.FRIENDLY:
            reflection_text = "Hey! Just checking in on how you're doing - seems like things are going pretty well!"
        
        # Generic highlights and suggestions that would be personalized in production
        highlights = ["Current habits are being maintained", "Making progress toward primary goals"]
        suggestions = ["Consider focusing more on your top priority today", "Take short breaks to maintain energy"]
    
    # Add focus area specific content if provided
    if reflection_request.focus_areas:
        areas = ", ".join(reflection_request.focus_areas)
        
        if coach_voice == CoachVoice.MOTIVATIONAL:
            reflection_text += f" You asked about {areas} - you're making incredible strides in these areas!"
        elif coach_voice == CoachVoice.SUPPORTIVE:
            reflection_text += f" Regarding your focus areas ({areas}), I've noticed some positive trends."
        elif coach_voice == CoachVoice.DIRECT:
            reflection_text += f" Focus areas {areas}: Satisfactory progress. Specific metrics below."
        elif coach_voice == CoachVoice.ANALYTICAL:
            reflection_text += f" Analysis of focus domains ({areas}) indicates variable performance metrics across specified areas."
        elif coach_voice == CoachVoice.FRIENDLY:
            reflection_text += f" About those areas you mentioned ({areas}) - there's some cool progress happening there!"
    
    # Create the reflection document
    reflection = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "reflection_type": reflection_request.reflection_type,
        "time_period": time_period,
        "coach_voice": coach_voice,
        "reflection_text": reflection_text,
        "highlights": highlights,
        "suggestions": suggestions,
        "created_at": datetime.utcnow(),
    }
    
    # Store the reflection in the database
    result = await db[DATABASE_NAME]["reflections"].insert_one(reflection)
    
    # Return the created reflection
    return ReflectionResponse(
        user_id=reflection["user_id"],
        reflection_text=reflection["reflection_text"],
        highlights=reflection["highlights"],
        suggestions=reflection["suggestions"],
        created_at=reflection["created_at"]
    )

@router.post("/ask", response_model=CoachingResponse)
async def ask_coach(
    request: CoachingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ask the TimeWell coach a question and get a response.
    
    This endpoint uses direct OpenAI API calls to provide coaching advice
    using the specified voice style.
    
    The system will provide a fallback response if the AI service is unavailable.
    """
    response = await coach_service.get_coaching_message(
        user_prompt=request.prompt,
        voice_style=request.voice_style,
        model=request.model,
        use_fallback_on_error=True  # Always use fallback if AI fails
    )
    
    if "error" in response and response["error"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response["message"]
        )
    
    # Check if this is a fallback response and add a header if it is
    if "fallback" in response and response["fallback"]:
        # In a real FastAPI response, we'd set a header here
        # This is handled on the frontend
        pass
        
    return response

@router.get("/weekly-review", response_model=CoachingResponse)
async def get_weekly_review(
    voice_style: Optional[str] = "wise_elder",
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a weekly review of the user's progress.
    
    This endpoint gathers the user's events and goals from the past week
    and provides a personalized review and recommendations.
    
    The system will provide a fallback response if the AI service is unavailable.
    """
    try:
        # Calculate the date range for the past week
        today = datetime.utcnow()
        week_ago = today - timedelta(days=7)
        
        # Get the user's events from the past week
        events = await get_events_by_user_id(str(current_user["_id"]))
        recent_events = [e for e in events if e.get("start_time") and e.get("start_time") >= week_ago]
        
        # Get the user's active goals
        goals = await get_goals_by_user_id(str(current_user["_id"]))
        active_goals = [g for g in goals if not g.get("is_completed", False)]
        
        # Prepare the user data
        user_data = {
            "events": recent_events,
            "goals": active_goals,
            "user_name": current_user.get("username", "User")
        }
        
        # Generate the weekly review
        response = await coach_service.weekly_review(
            user_data=user_data,
            voice_style=voice_style,
            use_fallback_on_error=True  # Always use fallback if AI fails
        )
        
        if "error" in response and response["error"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response["message"]
            )
        
        # Check if this is a fallback response and add a header if it is
        if "fallback" in response and response["fallback"]:
            # In a real FastAPI response, we'd set a header here
            # This is handled on the frontend
            pass
            
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating weekly review: {str(e)}"
        )

@router.post("/action-plan", response_model=ActionPlan)
async def get_action_plan(
    request: ActionPlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate an action plan for the user based on their goals and events.
    
    This endpoint uses the structured JSON response format from OpenAI
    to create a well-structured action plan.
    
    The system will provide a fallback response if the AI service is unavailable.
    """
    try:
        # Define the timeframe based on the request
        if request.timeframe == "day":
            days_ago = 1
        elif request.timeframe == "month":
            days_ago = 30
        else:  # default to week
            days_ago = 7
            
        # Calculate the date range
        today = datetime.utcnow()
        start_date = today - timedelta(days=days_ago)
        
        # Get the user's events
        events = await get_events_by_user_id(str(current_user["_id"]))
        recent_events = [e for e in events if e.get("start_time") and e.get("start_time") >= start_date]
        
        # Get the user's goals
        goals = await get_goals_by_user_id(str(current_user["_id"]))
        
        # Prepare events and goals summaries
        events_summary = "\n".join([f"- {e['title']}: {e['description']}" for e in recent_events])
        goals_summary = "\n".join([f"- {g['title']}: {g['description']}" for g in goals])
        
        # Create the prompt
        prompt = f"""
        Please analyze this user's recent activities and goals, and create an action plan.
        
        RECENT EVENTS ({request.timeframe}):
        {events_summary if events_summary else "No events recorded recently."}
        
        GOALS:
        {goals_summary if goals_summary else "No goals defined."}
        
        Based on this information, provide:
        1. A list of recommended actions to take
        2. Priority areas to focus on
        3. Insights from the data
        """
        
        # Define the response schema for structured output
        response_schema = {
            "type": "object",
            "properties": {
                "actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 3-5 recommended actions based on goals and activities"
                },
                "priorities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 2-3 priority areas to focus on"
                },
                "insights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 2-3 insights from the data"
                }
            },
            "required": ["actions", "priorities", "insights"]
        }
        
        # Use the structured coach context manager
        async with coach_service.structured_coach(
            voice_style=request.voice_style,
            use_fallback_on_error=True  # Always use fallback if AI fails
        ) as coach:
            result = await coach(prompt, response_schema)
            
            if "error" in result and result["error"]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["message"]
                )
            
            # Check if this is a fallback response and add a header if it is
            if "fallback" in result and result["fallback"]:
                # In a real FastAPI response, we'd set a header here
                # This is handled on the frontend
                pass
                
            return result["data"]
            
    except Exception as e:
        # If all else fails (including fallback mechanism), return a simple fallback
        from app.services.fallback_messages import fallback_service
        
        # Log the error
        logger.error(f"Critical error generating action plan, using emergency fallback: {str(e)}")
        
        # Return emergency fallback
        return fallback_service.get_fallback_action_plan(request.voice_style) 