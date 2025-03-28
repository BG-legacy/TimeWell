import pytest
import uuid
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.event import EventCreate
from app.services.user import create_user
from app.services.event import create_event, get_event_by_id

@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_post_event_direct():
    """Test creating an event using the service directly."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # Prepare event data
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = EventCreate(
            title=f"Test Event POST {unique_id}",
            description="Test event description for POST test",
            start_time=start_time,
            end_time=end_time,
            is_completed=False
        )
        
        # Create the event using the service
        event = await create_event(user_id, event_data)
        
        # Verify the event was created correctly
        assert event is not None
        assert event["title"] == event_data.title
        assert event["description"] == event_data.description
        assert isinstance(event["_id"], ObjectId)
        assert str(event["user_id"]) == user_id
        assert "start_time" in event
        assert "end_time" in event
        assert event["is_completed"] == event_data.is_completed
        assert isinstance(event["created_at"], datetime)
        assert isinstance(event["updated_at"], datetime)
        
        # Verify the event can be retrieved
        retrieved_event = await get_event_by_id(str(event["_id"]))
        assert retrieved_event is not None
        assert str(retrieved_event["_id"]) == str(event["_id"])
        assert retrieved_event["title"] == event_data.title
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event POST"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_post_event_with_goal():
    """Test creating an event linked to a goal."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # Create a mock goal ID
        mock_goal_id = str(ObjectId())
        
        # Prepare event data with goal_id
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = EventCreate(
            title=f"Test Event with Goal {unique_id}",
            description="Test event linked to a goal",
            start_time=start_time,
            end_time=end_time,
            goal_id=mock_goal_id,
            is_completed=False
        )
        
        # Create the event using the service
        event = await create_event(user_id, event_data)
        
        # Verify the event was created correctly with goal_id
        assert event is not None
        assert event["title"] == event_data.title
        assert str(event["user_id"]) == user_id
        assert "goal_id" in event
        assert str(event["goal_id"]) == mock_goal_id
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event with Goal"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_post_multiple_events():
    """Test creating multiple events for a user."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # Create multiple events
        event_ids = []
        for i in range(5):
            start_time = datetime.utcnow() + timedelta(days=i)
            end_time = start_time + timedelta(hours=2)
            event_data = EventCreate(
                title=f"Test Multiple Events {i} {unique_id}",
                description=f"Test multiple events creation {i}",
                start_time=start_time,
                end_time=end_time,
                is_completed=False
            )
            event = await create_event(user_id, event_data)
            event_ids.append(str(event["_id"]))
        
        # Verify we created 5 events
        assert len(event_ids) == 5
        
        # Verify each event exists in the database
        for event_id in event_ids:
            retrieved_event = await get_event_by_id(event_id)
            assert retrieved_event is not None
            assert str(retrieved_event["_id"]) == event_id
            assert str(retrieved_event["user_id"]) == user_id
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Multiple Events"}})
        db.close_database_connection() 