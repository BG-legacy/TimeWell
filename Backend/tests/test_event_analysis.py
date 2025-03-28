import pytest
import asyncio
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from app.main import app
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.event import EventCreate
from app.services.user import create_user
from app.services.event import create_event
from app.core.security import create_access_token

@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_analyze_event_endpoint(monkeypatch):
    """Test the POST /events/analyze endpoint."""
    # Create a mock analysis result
    mock_analysis_result = {
        "score": 7,
        "aligned_goals": ["goal1", "goal2"],
        "analysis": "This event aligns well with your productivity goals.",
        "suggestion": "Consider adding specific milestones to track progress.",
        "new_goal_suggestion": None
    }
    
    # Create a module-level mock function that will replace the chain.ainvoke
    # This avoids trying to set attributes directly on the chain object
    original_chain = None
    
    # Save the original module
    from app.services import ai_analysis
    original_chain = ai_analysis.chain
    
    # Create a mock chain object with an ainvoke method
    class MockChain:
        async def ainvoke(self, *args, **kwargs):
            return {"text": json.dumps(mock_analysis_result)}
    
    # Replace the chain with our mock
    ai_analysis.chain = MockChain()
    
    # Setup
    db = get_database()
    db.connect_to_database()
    
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
        
        # 2. Create a JWT token for the user
        access_token = create_access_token(
            data={"sub": test_user["email"], "user_id": user_id}
        )
        
        # 3. Create an event to analyze
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = EventCreate(
            title=f"Test Analysis Event {unique_id}",
            description="Test event for analysis",
            start_time=start_time,
            end_time=end_time,
            is_completed=False
        )
        event = await create_event(user_id, event_data)
        event_id = str(event["_id"])
        
        # 4. Make the API call to analyze the event
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/events/analyze",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"event_id": event_id}
            )
        
        # 5. Check the response
        assert response.status_code == 200
        data = response.json()
        assert not data["error"]
        assert data["event_id"] == event_id
        assert "analysis" in data
        
        # 6. Test unauthorized access - create another user
        other_unique_id = str(uuid.uuid4())[:8]
        other_user_data = UserCreate(
            email=f"test_analysis_other_{other_unique_id}@example.com",
            username=f"testuser_analysis_other_{other_unique_id}",
            password="password123"
        )
        other_user = await create_user(other_user_data)
        other_token = create_access_token(
            data={"sub": other_user["email"], "user_id": str(other_user["_id"])}
        )
        
        # 7. Try to analyze an event that belongs to the first user
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/events/analyze",
                headers={"Authorization": f"Bearer {other_token}"},
                json={"event_id": event_id}
            )
        
        # Should be forbidden
        assert response.status_code == 403
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({
            "email": {"$regex": r"^test_analysis.*@example\.com$"}
        })
        await db.client["timewell"]["events"].delete_many({
            "title": {"$regex": r"^Test Analysis Event"}
        })
        db.close_database_connection()
        
        # Restore the original chain
        if original_chain is not None:
            ai_analysis.chain = original_chain 