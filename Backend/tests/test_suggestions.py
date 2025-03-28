import pytest
import asyncio
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.event import EventCreate
from app.schemas.analysis import SuggestionCreate
from app.services.user import create_user
from app.services.event import create_event
from app.services.suggestion import (
    create_suggestion, 
    get_suggestions_by_user_id, 
    get_suggestion_by_id, 
    mark_suggestion_applied,
    get_suggestions_by_event_id
)
from app.services.ai_analysis import analyze_event_goal_alignment

@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_suggestions_crud():
    """Test CRUD operations for suggestions."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_suggestion_{unique_id}@example.com",
            username=f"testuser_suggestion_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create an event
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = EventCreate(
            title=f"Test Suggestion Event {unique_id}",
            description="Test event for suggestion",
            start_time=start_time,
            end_time=end_time,
            is_completed=False
        )
        event = await create_event(user_id, event_data)
        event_id = str(event["_id"])
        
        # Create some dummy goal IDs - using valid ObjectId strings
        goal_id1 = str(ObjectId())
        goal_id2 = str(ObjectId())
        
        # 3. Create a suggestion
        suggestion_data = SuggestionCreate(
            user_id=user_id,
            event_id=event_id,
            score=7,
            aligned_goals=[goal_id1, goal_id2],
            analysis="This event aligns well with your productivity goals.",
            suggestion="Consider adding specific milestones to track progress.",
            new_goal_suggestion=None
        )
        
        # Create the suggestion
        suggestion = await create_suggestion(suggestion_data)
        suggestion_id = str(suggestion["_id"])
        
        # 4. Verify the suggestion was created correctly
        assert suggestion["user_id"] == ObjectId(user_id)
        assert suggestion["event_id"] == ObjectId(event_id)
        assert suggestion["score"] == 7
        assert len(suggestion["aligned_goals"]) == 2
        assert suggestion["analysis"] == "This event aligns well with your productivity goals."
        assert suggestion["suggestion"] == "Consider adding specific milestones to track progress."
        assert suggestion["new_goal_suggestion"] is None
        assert suggestion["is_applied"] is False
        
        # 5. Get suggestions by user ID
        user_suggestions = await get_suggestions_by_user_id(user_id)
        assert len(user_suggestions) >= 1
        
        # Find our test suggestion
        found_suggestion = None
        for s in user_suggestions:
            if str(s["_id"]) == suggestion_id:
                found_suggestion = s
                break
        
        assert found_suggestion is not None
        assert str(found_suggestion["user_id"]) == user_id
        
        # 6. Get suggestion by ID
        retrieved_suggestion = await get_suggestion_by_id(suggestion_id)
        assert retrieved_suggestion is not None
        assert str(retrieved_suggestion["_id"]) == suggestion_id
        assert str(retrieved_suggestion["user_id"]) == user_id
        assert str(retrieved_suggestion["event_id"]) == event_id
        
        # 7. Mark suggestion as applied
        updated_suggestion = await mark_suggestion_applied(suggestion_id, True)
        assert updated_suggestion is not None
        assert updated_suggestion["is_applied"] is True
        
        # 8. Mark suggestion as not applied
        updated_suggestion = await mark_suggestion_applied(suggestion_id, False)
        assert updated_suggestion is not None
        assert updated_suggestion["is_applied"] is False
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({
            "email": {"$regex": r"^test_suggestion.*@example\.com$"}
        })
        await db.client["timewell"]["events"].delete_many({
            "title": {"$regex": r"^Test Suggestion Event"}
        })
        await db.client["timewell"]["suggestions"].delete_many({
            "analysis": "This event aligns well with your productivity goals."
        })
        db.close_database_connection()

@pytest.mark.asyncio
async def test_suggestion_saved_from_event_analysis():
    """Test that suggestions are saved when analyzing an event."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    # Create a module-level mock function that will replace the chain.ainvoke
    from app.services import ai_analysis
    original_chain = ai_analysis.chain
    
    # Mock analysis result that the LangChain would return
    mock_analysis_result = {
        "score": 8,
        "aligned_goals": ["goal-123", "goal-456"],
        "analysis": "This is a test analysis from the integration test.",
        "suggestion": "This is a test suggestion from the integration test.",
        "new_goal_suggestion": "This is a test new goal suggestion."
    }
    
    # Create a mock chain object with an ainvoke method
    class MockChain:
        async def ainvoke(self, *args, **kwargs):
            return {"text": json.dumps(mock_analysis_result)}
    
    # Replace the chain with our mock
    ai_analysis.chain = MockChain()
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_analysis_{unique_id}@example.com",
            username=f"testuser_analysis_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create an event to analyze
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = EventCreate(
            title=f"Test Analysis Event {unique_id}",
            description="Test event for analysis integration test",
            start_time=start_time,
            end_time=end_time,
            is_completed=False
        )
        event = await create_event(user_id, event_data)
        event_id = str(event["_id"])
        
        # 3. Call the analysis service
        result = await analyze_event_goal_alignment(user_id, event_id)
        
        # 4. Verify the analysis was successful
        assert result["error"] is False
        assert result["event_id"] == event_id
        assert "analysis" in result
        
        # 5. Get suggestions for the event to verify one was created
        suggestions = await get_suggestions_by_event_id(event_id)
        
        # 6. Verify a suggestion was created
        assert len(suggestions) == 1
        suggestion = suggestions[0]
        
        # 7. Verify the suggestion has the correct data
        assert str(suggestion["user_id"]) == user_id
        assert str(suggestion["event_id"]) == event_id
        assert suggestion["score"] == mock_analysis_result["score"]
        assert suggestion["analysis"] == mock_analysis_result["analysis"]
        assert suggestion["suggestion"] == mock_analysis_result["suggestion"]
        assert suggestion["new_goal_suggestion"] == mock_analysis_result["new_goal_suggestion"]
        
        # 8. Verify the suggestion has non-ObjectId goals (since our mock returns string goals)
        assert len(suggestion["aligned_goals"]) == 2
        aligned_goals = [goal for goal in suggestion["aligned_goals"]]
        assert "goal-123" in aligned_goals
        assert "goal-456" in aligned_goals
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({
            "email": {"$regex": r"^test_analysis.*@example\.com$"}
        })
        await db.client["timewell"]["events"].delete_many({
            "title": {"$regex": r"^Test Analysis Event"}
        })
        await db.client["timewell"]["suggestions"].delete_many({
            "analysis": "This is a test analysis from the integration test."
        })
        
        # Restore the original chain
        ai_analysis.chain = original_chain
        
        db.close_database_connection() 