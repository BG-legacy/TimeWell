import os
import json
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from app.services.goal import get_goals_by_user_id
from app.services.event import get_event_by_id
from app.services.suggestion import create_suggestion
from app.schemas.analysis import SuggestionCreate
from app.services.prompt_templates import VoiceStyle
from app.services.chain_factory import chain_factory
from app.services.fallback_messages import fallback_service
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define response schemas for structured output
response_schemas = [
    ResponseSchema(
        name="score",
        description="Alignment score from 1-10 (10 being perfectly aligned).",
        type="number"
    ),
    ResponseSchema(
        name="aligned_goals",
        description="List of goal IDs this event contributes to.",
        type="list[string]"
    ),
    ResponseSchema(
        name="analysis",
        description="Brief analysis of the alignment (2-3 sentences).",
        type="string"
    ),
    ResponseSchema(
        name="suggestion",
        description="One suggestion to improve alignment with goals.",
        type="string"
    ),
    ResponseSchema(
        name="new_goal_suggestion",
        description="Suggested new goal if the event doesn't align with any existing goals (or null if not applicable).",
        type="string"
    )
]

# Create the human message template
human_template = """
Please analyze this event:

EVENT:
Title: {title}
Description: {description}
Start Time: {start_time}
End Time: {end_time}
Completed: {is_completed}

USER'S GOALS:
{goals_data}

Analyze how well this event aligns with the user's goals.
Provide:
1. An alignment score (1-10)
2. Which goals (if any) this event contributes to
3. A brief analysis (2-3 sentences)
4. One suggestion to improve alignment
5. If the event doesn't align with any goals, suggest a new potential goal it might support
"""

async def analyze_event_goal_alignment(
    user_id: str, 
    event_id: str, 
    voice_style: str = VoiceStyle.COOL_COUSIN.value,
    model_name: str = "gpt-4",
    use_fallback_on_error: bool = True
) -> Dict[str, Any]:
    """
    Analyze an event's alignment with the user's goals using LangChain and GPT-4.
    
    Args:
        user_id: The ID of the user
        event_id: The ID of the event to analyze
        voice_style: The voice style to use for the analysis (default: cool_cousin)
        model_name: The LLM model to use (default: gpt-4)
        use_fallback_on_error: Whether to use fallback messages if AI fails (default: True)
        
    Returns:
        A dictionary containing the analysis results
    """
    # Get the event details
    event = await get_event_by_id(event_id)
    if not event:
        return {
            "error": True,
            "message": f"Event with ID {event_id} not found"
        }
    
    # Check if the event belongs to the user
    if str(event["user_id"]) != user_id:
        return {
            "error": True,
            "message": "Not authorized to analyze this event"
        }
    
    # Get the user's goals
    goals = await get_goals_by_user_id(user_id)
    
    # Prepare data for GPT-4 analysis
    event_data = {
        "title": event.get("title", ""),
        "description": event.get("description", ""),
        "start_time": event.get("start_time", ""),
        "end_time": event.get("end_time", ""),
        "is_completed": event.get("is_completed", False)
    }
    
    # Convert goal ObjectIds to strings for JSON serialization
    goals_data = []
    for goal in goals:
        goals_data.append({
            "id": str(goal["_id"]),
            "title": goal.get("title", ""),
            "description": goal.get("description", ""),
            "target_date": goal.get("target_date", ""),
            "is_completed": goal.get("is_completed", False)
        })
    
    try:
        # Create the chain with parser using the chain factory
        chain_config = chain_factory.create_parser_chain(
            human_template=human_template,
            response_schemas=response_schemas,
            voice_style=voice_style,
            model_name=model_name
        )
        
        chain = chain_config["chain"]
        parser = chain_config["parser"]
        
        # Run the LangChain
        response = await chain.ainvoke({
            "title": event_data["title"],
            "description": event_data["description"],
            "start_time": event_data["start_time"],
            "end_time": event_data["end_time"],
            "is_completed": event_data["is_completed"],
            "goals_data": json.dumps(goals_data) if goals_data else "No goals found for this user."
        })
        
        # Get the text and parse it with the output parser
        text_response = response["text"]
        analysis_result = parser.parse(text_response)
        
        # Save the analysis result to the suggestions collection
        suggestion_data = SuggestionCreate(
            user_id=user_id,
            event_id=event_id,
            score=analysis_result["score"],
            aligned_goals=analysis_result["aligned_goals"],
            analysis=analysis_result["analysis"],
            suggestion=analysis_result["suggestion"],
            new_goal_suggestion=analysis_result["new_goal_suggestion"],
            voice_style=voice_style  # Store the voice style used
        )
        
        # Create the suggestion in the database
        await create_suggestion(suggestion_data)
        
        # Converting to JSON string to match the original API format
        json_result = json.dumps(analysis_result)
        
        return {
            "error": False,
            "event_id": str(event["_id"]),
            "analysis": json_result,
            "voice_style": voice_style,
            "model_used": model_name
        }
    
    except Exception as e:
        logger.error(f"Error in AI analysis: {str(e)}")
        
        if not use_fallback_on_error:
            return {
                "error": True,
                "message": f"Error performing analysis: {str(e)}"
            }
        
        # Use fallback messages
        logger.info(f"Using fallback messages for event {event_id} with voice style {voice_style}")
        
        # Get a fallback analysis
        fallback_response = fallback_service.get_fallback_analysis(
            voice_style=voice_style,
            event_data=event
        )
        
        try:
            # Still try to create a suggestion with the fallback content
            suggestion_data = SuggestionCreate(
                user_id=user_id,
                event_id=event_id,
                score=5,  # Neutral score for fallback
                aligned_goals=[],
                analysis=fallback_response["analysis"]["analysis"],
                suggestion=fallback_response["analysis"]["suggestion"],
                new_goal_suggestion=None,
                voice_style=voice_style
            )
            
            # Save the fallback suggestion
            await create_suggestion(suggestion_data)
            
        except Exception as inner_e:
            # If we can't save the suggestion, just log it and continue
            logger.error(f"Could not save fallback suggestion: {str(inner_e)}")
        
        # Format the response like a normal analysis
        json_result = json.dumps(fallback_response["analysis"])
        fallback_response["analysis"] = json_result
        
        return fallback_response 