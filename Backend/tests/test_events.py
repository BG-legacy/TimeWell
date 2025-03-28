import pytest
import uuid
from bson import ObjectId
from datetime import datetime, timedelta
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.event import EventCreate, EventUpdate
from app.services.user import create_user
from app.services.event import create_event, get_events_by_user_id, get_event_by_id, update_event, delete_event

@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Initialize database connection for all tests."""
    db = get_database()
    db.connect_to_database()
    yield
    db.close_database_connection()

@pytest.fixture(scope="module")
async def test_db():
    """Connect to database and clean up test data."""
    db = get_database()
    # Make sure we're connected
    if db.client is None:
        db.connect_to_database()
    
    # Clean up any test data first
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
    await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})
    
    yield db
    
    # Clean up after tests
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
    await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})

@pytest.fixture(scope="function")
async def test_user(test_db):
    """Create a test user for each test."""
    unique_id = str(uuid.uuid4())[:8]
    user_data = UserCreate(
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        password="password123"
    )
    user = await create_user(user_data)
    return user

@pytest.mark.asyncio
async def test_create_event():
    """Test creating a new event."""
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
        
        # Create an event
        event_unique_id = str(uuid.uuid4())[:8]
        event_data = EventCreate(
            title=f"Test Event {event_unique_id}",
            description="Test event description",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=2),
            is_completed=False
        )
        
        event = await create_event(str(test_user["_id"]), event_data)
        
        # Check the returned event data
        assert event["title"] == event_data.title
        assert event["description"] == event_data.description
        assert "start_time" in event
        assert "end_time" in event
        assert event["is_completed"] == event_data.is_completed
        assert isinstance(event["_id"], ObjectId)
        assert str(event["user_id"]) == str(test_user["_id"])
        assert isinstance(event["created_at"], datetime)
        assert isinstance(event["updated_at"], datetime)
    
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_get_events_by_user_id():
    """Test retrieving events by user ID."""
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
        
        # Create multiple events for the user
        for i in range(3):
            event_unique_id = str(uuid.uuid4())[:8]
            event_data = EventCreate(
                title=f"Test Event {event_unique_id}",
                description=f"Test event description {i}",
                start_time=datetime.utcnow() + timedelta(days=i),
                end_time=datetime.utcnow() + timedelta(days=i, hours=2),
                is_completed=False
            )
            await create_event(str(test_user["_id"]), event_data)
        
        # Get the user's events
        events = await get_events_by_user_id(str(test_user["_id"]))
        
        # Check that we got at least 3 events
        assert len(events) >= 3
        
        # Check the structure of the returned events
        for event in events:
            assert "title" in event
            assert "description" in event
            assert "start_time" in event
            assert "is_completed" in event
            assert "_id" in event
            assert "user_id" in event
            assert str(event["user_id"]) == str(test_user["_id"])
            assert "created_at" in event
            assert "updated_at" in event
    
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_update_event():
    """Test updating an event."""
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
        
        # First create an event to update
        event_unique_id = str(uuid.uuid4())[:8]
        event_data = EventCreate(
            title=f"Test Event to Update {event_unique_id}",
            description="This event will be updated",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=2),
            is_completed=False
        )
        event = await create_event(str(test_user["_id"]), event_data)
        event_id = str(event["_id"])
        
        # Update data
        update_data = EventUpdate(
            title="Updated Test Event",
            is_completed=True
        )
        
        # Update the event
        updated_event = await update_event(event_id, update_data)
        
        # Check the updated event
        assert updated_event["title"] == "Updated Test Event"
        assert updated_event["is_completed"] == True
        assert updated_event["description"] == event["description"]  # Should remain unchanged
    
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_delete_event():
    """Test deleting an event."""
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
        
        # Create a new event to delete
        event_unique_id = str(uuid.uuid4())[:8]
        event_data = EventCreate(
            title=f"Test Event to Delete {event_unique_id}",
            description="This event will be deleted",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=2),
            is_completed=False
        )
        
        event = await create_event(str(test_user["_id"]), event_data)
        event_id = str(event["_id"])
        
        # Delete the event
        result = await delete_event(event_id)
        
        # Check the result
        assert "message" in result
        assert "deleted successfully" in result["message"]
        
        # Verify the event is deleted
        deleted_event = await get_event_by_id(event_id)
        assert deleted_event is None
    
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["events"].delete_many({"title": {"$regex": r"^Test Event"}})
        db.close_database_connection() 