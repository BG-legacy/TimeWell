import os
import json
from dotenv import load_dotenv
from typing import List, Dict, Any
from app.services.goal import get_goals_by_user_id
from app.services.event import get_event_by_id
from app.services.suggestion import create_suggestion
from app.schemas.analysis import SuggestionCreate
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.chains import LLMChain

load_dotenv()

# Initialize OpenAI client through LangChain
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4",
    temperature=0.7
)

# Define response schemas for structured output
response_schemas = [
    ResponseSchema(
        name="score",
        description="Alignment score from 1-10 (10 being perfectly aligned).",
        type="integer"
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

# Create the output parser
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

# Create the system and human message templates
system_template = """
You are an AI assistant specialized in analyzing time management and goal alignment.
Your task is to analyze how well an event aligns with a user's goals and provide meaningful insights.
Provide a concise analysis, a score from 1-10 (10 being perfectly aligned), and suggestions for improvement.

{format_instructions}
"""

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

# Create the prompt template
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

# Create the chain
chain = LLMChain(llm=llm, prompt=chat_prompt)

async def analyze_event_goal_alignment(user_id: str, event_id: str) -> Dict[str, Any]:
    """
    Analyze an event's alignment with the user's goals using LangChain and GPT-4.
    
    Args:
        user_id: The ID of the user
        event_id: The ID of the event to analyze
        
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
        # Run the LangChain
        response = await chain.ainvoke({
            "format_instructions": format_instructions,
            "title": event_data["title"],
            "description": event_data["description"],
            "start_time": event_data["start_time"],
            "end_time": event_data["end_time"],
            "is_completed": event_data["is_completed"],
            "goals_data": json.dumps(goals_data) if goals_data else "No goals found for this user."
        })
        
        # Get the text and parse it with the output parser
        text_response = response["text"]
        analysis_result = output_parser.parse(text_response)
        
        # Save the analysis result to the suggestions collection
        suggestion_data = SuggestionCreate(
            user_id=user_id,
            event_id=event_id,
            score=analysis_result["score"],
            aligned_goals=analysis_result["aligned_goals"],
            analysis=analysis_result["analysis"],
            suggestion=analysis_result["suggestion"],
            new_goal_suggestion=analysis_result["new_goal_suggestion"]
        )
        
        # Create the suggestion in the database
        await create_suggestion(suggestion_data)
        
        # Converting to JSON string to match the original API format
        json_result = json.dumps(analysis_result)
        
        return {
            "error": False,
            "event_id": str(event["_id"]),
            "analysis": json_result
        }
    
    except Exception as e:
        return {
            "error": True,
            "message": f"Error performing analysis: {str(e)}"
        } 