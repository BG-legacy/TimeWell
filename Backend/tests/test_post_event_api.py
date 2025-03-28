import pytest
import asyncio
import uuid
import json
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.main import app
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.services.user import create_user
from app.core.security import create_access_token

@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_post_event_api():
    """Test the POST /events API endpoint using AsyncClient."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_api_{unique_id}@example.com",
            username=f"testuser_api_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create a JWT token for the user
        access_token = create_access_token(
            data={"sub": test_user["email"], "user_id": user_id}
        )
        
        # 3. Prepare event data
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = {
            "title": f"Test API Event {unique_id}",
            "description": "Test event description for API test",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "is_completed": False
        }
        
        # 4. Make the API call using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/events",
                headers={"Authorization": f"Bearer {access_token}"},
                json=event_data
            )
        
        # 5. Check the response
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == event_data["title"]
        assert data["description"] == event_data["description"]
        assert data["is_completed"] == event_data["is_completed"]
        assert "id" in data
        assert "user_id" in data
        assert data["user_id"] == user_id
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test_api.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test API Event"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_post_event_api_validation():
    """Test validation for the POST /events API endpoint."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_api_{unique_id}@example.com",
            username=f"testuser_api_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create a JWT token for the user
        access_token = create_access_token(
            data={"sub": test_user["email"], "user_id": user_id}
        )
        
        # 3. Prepare invalid event data (missing required start_time)
        invalid_event_data = {
            "title": f"Test API Event Invalid {unique_id}",
            "description": "This event is missing required fields",
            "is_completed": False
        }
        
        # 4. Make the API call with invalid data
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/events",
                headers={"Authorization": f"Bearer {access_token}"},
                json=invalid_event_data
            )
        
        # 5. Check that validation fails appropriately
        assert response.status_code == 422  # Unprocessable Entity for validation errors
        error_data = response.json()
        assert "detail" in error_data
        
        # 6. Now try with no authentication
        valid_event_data = {
            "title": f"Test API Event No Auth {unique_id}",
            "description": "This event has valid data but no auth",
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "is_completed": False
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/events",
                json=valid_event_data
            )
        
        # 7. Check that unauthorized request is rejected
        assert response.status_code == 401  # Unauthorized
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test_api.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test API Event"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_post_event_with_goal_api():
    """Test creating an event with a goal ID via the API."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_api_{unique_id}@example.com",
            username=f"testuser_api_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create a JWT token for the user
        access_token = create_access_token(
            data={"sub": test_user["email"], "user_id": user_id}
        )
        
        # 3. Prepare event data with a valid MongoDB ObjectId for goal_id 
        # Use a valid 24-character hex string format for ObjectId
        mock_goal_id = "507f1f77bcf86cd799439011"
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = {
            "title": f"Test API Event with Goal {unique_id}",
            "description": "Test event with goal ID via API",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "goal_id": mock_goal_id,
            "is_completed": False
        }
        
        # 4. Make the API call
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/events",
                headers={"Authorization": f"Bearer {access_token}"},
                json=event_data
            )
        
        # 5. Check the response
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == event_data["title"]
        assert "goal_id" in data
        assert data["goal_id"] == mock_goal_id
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test_api.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test API Event"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_get_events_by_user_id_api():
    """Test the GET /events/user/{user_id} API endpoint."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_api_{unique_id}@example.com",
            username=f"testuser_api_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create a JWT token for the user
        access_token = create_access_token(
            data={"sub": test_user["email"], "user_id": user_id}
        )
        
        # 3. Create multiple events for the user
        for i in range(3):
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(hours=2)
            event_data = {
                "title": f"Test API Event {i} {unique_id}",
                "description": f"Event {i} for GET by user_id test",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "is_completed": False
            }
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                await client.post(
                    "/events",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json=event_data
                )
        
        # 4. Make the API call to get events by user_id
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/events/user/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        
        # 5. Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3  # We created 3 events
        
        # Check that each event has the correct fields
        for event in data:
            assert "id" in event
            assert "title" in event
            assert "description" in event
            assert "user_id" in event
            assert event["user_id"] == user_id
        
        # 6. Test unauthorized access by creating another user and trying to access the first user's events
        other_unique_id = str(uuid.uuid4())[:8]
        other_user_data = UserCreate(
            email=f"test_api_other_{other_unique_id}@example.com",
            username=f"testuser_api_other_{other_unique_id}",
            password="password123"
        )
        other_user = await create_user(other_user_data)
        other_token = create_access_token(
            data={"sub": other_user["email"], "user_id": str(other_user["_id"])}
        )
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/events/user/{user_id}",
                headers={"Authorization": f"Bearer {other_token}"}
            )
        
        # Should be forbidden
        assert response.status_code == 403
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test_api.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test API Event"}})
        db.close_database_connection() 