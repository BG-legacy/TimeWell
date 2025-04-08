import asyncio
import sys
import os
import json
from datetime import datetime

# Add the parent directory to the Python path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.prompt_templates import VoiceStyle
from app.services.coach_service import coach_service
from app.services.ai_analysis import analyze_event_goal_alignment
from app.services.event import create_event, get_event_by_id
from app.services.user import create_user, get_user_by_id
from app.core.database import get_database
from app.schemas.event import EventCreate
from app.schemas.user import UserCreate
from bson import ObjectId

async def setup_database():
    """Initialize the database connection"""
    db = get_database()
    db.connect_to_database()
    return db

async def create_test_user():
    """Create a test user for the interactive session"""
    user_data = UserCreate(
        username="test_interactive_user",
        email="test_interactive@example.com",
        password="password123"
    )
    
    # Check if user already exists by email instead of ID
    db = get_database().client
    existing_user = await db["timewell"]["users"].find_one({"email": user_data.email})
    if existing_user:
        print(f"Found existing test user with ID: {existing_user['_id']}")
        return existing_user
    
    # Create new user
    try:
        user = await create_user(user_data)
        print(f"Created test user with ID: {user['_id']}")
        return user
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        # Try to find by email as fallback
        db = get_database().client
        user = await db["timewell"]["users"].find_one({"email": user_data.email})
        if user:
            print(f"Found existing user with ID: {user['_id']}")
            return user
        raise

async def create_test_event(user_id, title, description):
    """Create a test event for analysis"""
    now = datetime.utcnow()
    event_data = EventCreate(
        title=title,
        description=description,
        start_time=now,
        end_time=now,
        is_completed=False
    )
    
    # Create the event
    event = await create_event(user_id, event_data)
    print(f"Created test event with ID: {event['_id']}")
    return event

async def test_coaching_interaction():
    """Test the coaching interaction with real AI responses"""
    print("\n===== TESTING AI VOICE STYLES - COACHING =====")
    
    # Create test user
    user = await create_test_user()
    
    # Get available voice styles
    voice_styles = [
        VoiceStyle.COOL_COUSIN.value,
        VoiceStyle.OG_BIG_BRO.value,
        VoiceStyle.ORACLE.value,
        VoiceStyle.MOTIVATOR.value,
        VoiceStyle.WISE_ELDER.value
    ]
    
    # Let user select voice style
    print("\nAvailable voice styles:")
    for i, style in enumerate(voice_styles):
        print(f"{i+1}. {style}")
    
    choice = int(input("\nSelect a voice style (1-5): ")) - 1
    voice_style = voice_styles[choice]
    
    # Get user input for the coaching prompt
    user_prompt = input("\nEnter your coaching prompt (e.g., 'How can I manage my time better?'): ")
    
    # Call the coaching service with actual AI
    print(f"\nGetting response from {voice_style} voice style...")
    result = await coach_service.get_coaching_message(
        user_prompt,
        voice_style=voice_style,
        model="gpt-3.5-turbo",
        use_fallback_on_error=True
    )
    
    # Print the response
    print("\n===== AI RESPONSE =====")
    print(f"Voice Style: {result['voice_style']}")
    if "fallback" in result and result["fallback"]:
        print("(FALLBACK RESPONSE - AI service unavailable)")
    
    print("\nResponse:")
    print(result["text"])
    
    if "token_usage" in result:
        print(f"\nToken usage: {result['token_usage']}")
    
    return result

async def test_event_analysis():
    """Test the event analysis with real AI responses"""
    print("\n===== TESTING AI VOICE STYLES - EVENT ANALYSIS =====")
    
    # Create test user
    user = await create_test_user()
    
    # Get available voice styles
    voice_styles = [
        VoiceStyle.COOL_COUSIN.value,
        VoiceStyle.OG_BIG_BRO.value,
        VoiceStyle.ORACLE.value,
        VoiceStyle.MOTIVATOR.value,
        VoiceStyle.WISE_ELDER.value
    ]
    
    # Let user select voice style
    print("\nAvailable voice styles:")
    for i, style in enumerate(voice_styles):
        print(f"{i+1}. {style}")
    
    choice = int(input("\nSelect a voice style (1-5): ")) - 1
    voice_style = voice_styles[choice]
    
    # Get user input for the event details
    event_title = input("\nEnter an event title: ")
    event_description = input("Enter an event description: ")
    
    # Create a test event
    event = await create_test_event(str(user["_id"]), event_title, event_description)
    
    # Call the event analysis service with actual AI
    print(f"\nAnalyzing event with {voice_style} voice style...")
    result = await analyze_event_goal_alignment(
        str(user["_id"]),
        str(event["_id"]),
        voice_style=voice_style,
        model_name="gpt-3.5-turbo",
        use_fallback_on_error=True
    )
    
    # Print the response
    print("\n===== AI RESPONSE =====")
    print(f"Voice Style: {result['voice_style']}")
    if "fallback" in result and result["fallback"]:
        print("(FALLBACK RESPONSE - AI service unavailable)")
    
    analysis = result["analysis"]
    if isinstance(analysis, str):
        analysis = json.loads(analysis)
    
    print("\nAnalysis:")
    print(analysis["analysis"])
    
    print("\nSuggestion:")
    print(analysis["suggestion"])
    
    if "score" in analysis:
        print(f"\nAlignment Score: {analysis['score']}/10")
    
    return result

async def main():
    """Main function to run the interactive test"""
    # Setup database connection
    await setup_database()
    
    while True:
        print("\n===== INTERACTIVE AI VOICE STYLE TEST =====")
        print("1. Test Coaching Interaction")
        print("2. Test Event Analysis")
        print("3. Exit")
        
        choice = input("\nSelect an option (1-3): ")
        
        if choice == "1":
            await test_coaching_interaction()
        elif choice == "2":
            await test_event_analysis()
        elif choice == "3":
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main()) 