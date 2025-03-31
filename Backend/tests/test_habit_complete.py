import pytest
import pytest_asyncio
import uuid
from fastapi.testclient import TestClient
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time

from app.main import app
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.services.user import create_user
from app.core.security import create_access_token

client = TestClient(app)

@pytest_asyncio.fixture(scope="module")
async def db():
    """Connect to database and clean up test data."""
    db = get_database()
    db.connect_to_database()
    
    # Clean up any test data first
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
    await db.client["timewell"]["habits"].delete_many({"title": {"$regex": r"^Test Habit"}})
    
    yield db
    
    # Clean up after tests
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
    await db.client["timewell"]["habits"].delete_many({"title": {"$regex": r"^Test Habit"}})
    db.close_database_connection()

@pytest_asyncio.fixture(scope="module")
async def test_user(db):
    """Create a test user."""
    unique_id = str(uuid.uuid4())[:8]
    user_data = UserCreate(
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        password="password123"
    )
    user = await create_user(user_data)
    return user

@pytest_asyncio.fixture(scope="module")
async def authenticated_user(test_user):
    """Create an authenticated user with token."""
    # Create access token
    access_token = await create_access_token({"sub": str(test_user["_id"])})
    
    return {
        "_id": str(test_user["_id"]),
        "email": test_user["email"],
        "username": test_user["username"],
        "token": access_token
    }

@pytest.mark.asyncio
async def test_put_habit_complete_unauthorized(client):
    """Test that unauthorized access to complete a habit is properly rejected."""
    habit_id = str(ObjectId())
    response = await client.put(f"/habits/{habit_id}/complete")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_put_habit_complete_success(client, authenticated_user, db):
    """Test successful completion of a habit."""
    # Create a test habit for the authenticated user
    user_id = authenticated_user["_id"]
    current_time = datetime.utcnow()
    
    habit_data = {
        "_id": ObjectId(),
        "user_id": ObjectId(user_id),
        "title": "Test Habit",
        "description": "A test habit",
        "frequency": "daily",
        "target_days": [0, 1, 2, 3, 4, 5, 6],
        "streak_count": 0,
        "longest_streak": 0,
        "last_completed": None,
        "color": "#FF5733",
        "icon": "test-icon",
        "is_active": True,
        "created_at": current_time,
        "updated_at": current_time
    }
    
    await db.habits.insert_one(habit_data)
    habit_id = str(habit_data["_id"])
    
    # Test completing the habit
    with freeze_time(current_time):
        response = await client.put(
            f"/habits/{habit_id}/complete",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["streak_count"] == 1
        assert response_data["longest_streak"] == 1
        assert "last_completed" in response_data
        
        # Verify the habit was updated in the database
        updated_habit = await db.habits.find_one({"_id": ObjectId(habit_id)})
        assert updated_habit["streak_count"] == 1
        assert updated_habit["longest_streak"] == 1
        assert updated_habit["last_completed"] is not None

@pytest.mark.asyncio
async def test_put_habit_complete_streak_maintenance(client, authenticated_user, db):
    """Test that completing a habit multiple days in a row increases the streak."""
    # Create a test habit for the authenticated user
    user_id = authenticated_user["_id"]
    start_time = datetime.utcnow()
    
    habit_data = {
        "_id": ObjectId(),
        "user_id": ObjectId(user_id),
        "title": "Daily Streak Habit",
        "description": "A habit to test streaks",
        "frequency": "daily",
        "target_days": [0, 1, 2, 3, 4, 5, 6],
        "streak_count": 0,
        "longest_streak": 0,
        "last_completed": None,
        "color": "#FF5733",
        "icon": "test-icon",
        "is_active": True,
        "created_at": start_time,
        "updated_at": start_time
    }
    
    await db.habits.insert_one(habit_data)
    habit_id = str(habit_data["_id"])
    
    # Complete the habit on day 1
    with freeze_time(start_time):
        response = await client.put(
            f"/habits/{habit_id}/complete",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 200
        assert response.json()["streak_count"] == 1
    
    # Complete the habit on day 2
    with freeze_time(start_time + timedelta(days=1)):
        response = await client.put(
            f"/habits/{habit_id}/complete",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 200
        assert response.json()["streak_count"] == 2
        assert response.json()["longest_streak"] == 2
    
    # Skip a day and break the streak
    with freeze_time(start_time + timedelta(days=3)):
        response = await client.put(
            f"/habits/{habit_id}/complete",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 200
        assert response.json()["streak_count"] == 1  # Streak resets to 1
        assert response.json()["longest_streak"] == 2  # Longest streak remains 2 