import pytest
from httpx import AsyncClient
from app.main import app
from app.schemas.coach import ReflectionRequest
from app.schemas.preference import CoachVoice
from unittest.mock import patch, MagicMock, AsyncMock
from app.core.security import get_current_active_user
from app.core.database import get_database, db
import os
from datetime import datetime

# Test user ID to use for testing
TEST_USER_ID = "60d5e74dc2dfc33c4c7c0e9a"

# Mock database name from env
DATABASE_NAME = "timewell"

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


# Mock database collections
class AsyncMockCollection:
    async def find_one(self, query):
        if query.get("_id") == "invalid_user_id":
            return None
        return TEST_USER
        
    async def insert_one(self, document):
        return MagicMock(inserted_id="mocked_reflection_id")

    async def to_list(self, length):
        return []


# Set up mock database for testing
@pytest.fixture(autouse=True)
def mock_db():
    # Create a mock MongoDB client
    mock_db = MagicMock()
    mock_mongo_client = MagicMock()
    
    # Create mock collections
    mock_db.users = AsyncMockCollection()
    mock_db.reflections = AsyncMockCollection()
    
    # Configure the mock MongoDB client
    mock_mongo_client.__getitem__.return_value = mock_db
    
    # Patch the database client
    with patch.object(db, 'client', mock_mongo_client):
        yield


@pytest.mark.asyncio
async def test_create_weekly_reflection():
    """Test creating a weekly reflection"""
    # Setup dependency overrides
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    # Create a test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Prepare the request data
        reflection_request = {
            "user_id": TEST_USER_ID,
            "reflection_type": "weekly",
            "focus_areas": ["fitness", "productivity"]
        }
        
        # Make the request
        response = await client.post("/coach/reflect", json=reflection_request)
        
        # Assert the response
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == TEST_USER_ID
        assert "reflection_text" in data
        assert "highlights" in data
        assert "suggestions" in data
        assert "created_at" in data
    
    # Clean up
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_create_status_reflection():
    """Test creating a status reflection"""
    # Setup dependency overrides
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    # Create a test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Prepare the request data
        reflection_request = {
            "user_id": TEST_USER_ID,
            "reflection_type": "status",
            "time_period": "current"
        }
        
        # Make the request
        response = await client.post("/coach/reflect", json=reflection_request)
        
        # Assert the response
        assert response.status_code == 201
        data = response.json()
        assert "reflection_text" in data
        # The content depends on the coach voice, so check if it's created but don't check exact content
        assert data["reflection_text"] != ""
    
    # Clean up
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_generate_encouragement():
    """Test generating encouragement with the user's coach voice"""
    # Setup dependency overrides
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    # Create a test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with form data 
        achievement = "completing your daily goal streak"
        response = await client.post(
            "/coach/encourage", 
            json={"achievement": achievement}  # Use json for the Body parameter
        )
        
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
        # Test with json data
        area = "morning routine"
        suggestion = "start with a quick workout"
        
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


@pytest.mark.asyncio
async def test_create_reflection_invalid_user():
    """Test creating a coach reflection with an invalid user ID"""
    # Setup dependency overrides
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    # Create a test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Prepare the request data with an invalid user ID
        reflection_request = {
            "user_id": "invalid_user_id",
            "reflection_type": "weekly"
        }
        
        # Make the request
        response = await client.post("/coach/reflect", json=reflection_request)
        
        # Assert the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    # Clean up
    app.dependency_overrides = {} 