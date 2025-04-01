from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import List, Optional, Dict, Any
from app.schemas.coach import ReflectionRequest, ReflectionResponse
from app.core.database import get_database
from datetime import datetime, timedelta
from app.schemas.preference import CoachVoice
from app.core.security import get_current_active_user
import uuid
import os
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

# Get database name from environment
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "timewell")

router = APIRouter(
    prefix="/coach",
    tags=["coach"],
    responses={404: {"description": "Not found"}},
)


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