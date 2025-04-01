import pytest
from httpx import AsyncClient
from app.main import app
from app.schemas.preference import CoachVoice
from app.core.security import get_current_active_user

# Test user ID to use for testing
TEST_USER_ID = "60d5e74dc2dfc33c4c7c0e9a"

# Mock user with preferences
TEST_USER = {
    "_id": TEST_USER_ID,
    "email": "test@example.com",
    "username": "testuser",
    "preferences": {
        "coach_voice": CoachVoice.MOTIVATIONAL
    }
}

# Mock for the current user dependency
async def override_get_current_active_user():
    return TEST_USER


@pytest.mark.asyncio
async def test_generate_encouragement():
    """Test generating encouragement with the user's coach voice"""
    # Setup dependency overrides
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    # Create a test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        achievement = "completing your daily goal streak"
        
        # Make the request using JSON format
        response = await client.post(
            "/coach/encourage", 
            json={"achievement": achievement}
        )
        
        # Print response details for debugging
        print("\nResponse status:", response.status_code)
        print("Response content:", response.content.decode())
        
        # Assert the response
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == TEST_USER_ID
        assert data["coach_voice"] == CoachVoice.MOTIVATIONAL
        assert "encouragement" in data
        assert achievement in data["encouragement"]
        # Check for motivational style phrases
        assert "crushing it" in data["encouragement"].lower() or "amazing" in data["encouragement"].lower()
    
    # Clean up
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_generate_feedback():
    """Test generating feedback with the user's coach voice"""
    # Setup dependency overrides
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    # Create a test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        area = "morning routine"
        suggestion = "start with a quick workout"
        
        # Make the request using JSON format
        response = await client.post(
            "/coach/feedback", 
            json={
                "area": area,
                "suggestion": suggestion
            }
        )
        
        # Assert the response
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == TEST_USER_ID
        assert data["coach_voice"] == CoachVoice.MOTIVATIONAL
        assert "feedback" in data
        assert area in data["feedback"]
        assert suggestion in data["feedback"]
        # Check for motivational style phrases
        assert "next level" in data["feedback"].lower() or "achieve" in data["feedback"].lower()
    
    # Clean up
    app.dependency_overrides = {} 