import pytest
from fastapi.testclient import TestClient
import uuid
import json
from datetime import datetime, timedelta
from app.main import app
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.event import EventCreate, EventUpdate
from app.services.user import create_user
from app.services.event import create_event
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_create_event_endpoint():
    """Test the POST /events endpoint."""
    # Setup
    db = get_database()
    db.connect_to_database()
    client = TestClient(app)
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
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
            "title": f"Test Event {unique_id}",
            "description": "Test event description",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "is_completed": False
        }
        
        # 4. Make the API call
        response = client.post(
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
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_get_events_endpoint():
    """Test the GET /events endpoint."""
    # Setup
    db = get_database()
    db.connect_to_database()
    client = TestClient(app)
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create some events for the user
        event_ids = []
        for i in range(3):
            start_time = datetime.utcnow() + timedelta(days=i)
            end_time = start_time + timedelta(hours=2)
            event_data = EventCreate(
                title=f"Test Event {i} {unique_id}",
                description=f"Test event description {i}",
                start_time=start_time,
                end_time=end_time,
                is_completed=False
            )
            event = await create_event(user_id, event_data)
            event_ids.append(str(event["_id"]))
        
        # 3. Create a JWT token for the user
        access_token = create_access_token(
            data={"sub": test_user["email"], "user_id": user_id}
        )
        
        # 4. Make the API call
        response = client.get(
            "/events",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # 5. Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        
        # Verify our events are in the response
        response_event_ids = [event["id"] for event in data]
        for event_id in event_ids:
            assert event_id in response_event_ids
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_update_event_endpoint():
    """Test the PATCH /events/{event_id} endpoint."""
    # Setup
    db = get_database()
    db.connect_to_database()
    client = TestClient(app)
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create an event to update
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = EventCreate(
            title=f"Test Event to Update {unique_id}",
            description="This event will be updated",
            start_time=start_time,
            end_time=end_time,
            is_completed=False
        )
        event = await create_event(user_id, event_data)
        event_id = str(event["_id"])
        
        # 3. Create a JWT token for the user
        access_token = create_access_token(
            data={"sub": test_user["email"], "user_id": user_id}
        )
        
        # 4. Prepare update data
        update_data = {
            "title": "Updated Event Title",
            "is_completed": True
        }
        
        # 5. Make the API call
        response = client.patch(
            f"/events/{event_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=update_data
        )
        
        # 6. Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["is_completed"] == update_data["is_completed"]
        assert data["description"] == event_data.description  # Should be unchanged
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_delete_event_endpoint():
    """Test the DELETE /events/{event_id} endpoint."""
    # Setup
    db = get_database()
    db.connect_to_database()
    client = TestClient(app)
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create an event to delete
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = EventCreate(
            title=f"Test Event to Delete {unique_id}",
            description="This event will be deleted",
            start_time=start_time,
            end_time=end_time,
            is_completed=False
        )
        event = await create_event(user_id, event_data)
        event_id = str(event["_id"])
        
        # 3. Create a JWT token for the user
        access_token = create_access_token(
            data={"sub": test_user["email"], "user_id": user_id}
        )
        
        # 4. Make the API call
        response = client.delete(
            f"/events/{event_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # 5. Check the response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]
        
        # 6. Verify the event is deleted by trying to get it
        get_response = client.get(
            f"/events/{event_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert get_response.status_code == 404
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})
        db.close_database_connection() 