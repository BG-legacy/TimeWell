import pytest
import pytest_asyncio
import uuid
from fastapi.testclient import TestClient
from bson import ObjectId
from datetime import datetime

from app.main import app
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.services.user import create_user
from app.core.security import create_access_token
from app.schemas.habit import HabitCreate
from app.services.habit import create_habit

client = TestClient(app)

@pytest_asyncio.fixture(scope="module")
async def db():
    """Connect to database and clean up test data."""
    db = get_database()
    db.connect_to_database()
    
    # Clean up any test data first
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test_habit_user.*@example\.com$"}})
    await db.client["timewell"]["habits"].delete_many({"title": {"$regex": r"^Test User Habit"}})
    
    yield db
    
    # Clean up after tests
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test_habit_user.*@example\.com$"}})
    await db.client["timewell"]["habits"].delete_many({"title": {"$regex": r"^Test User Habit"}})
    db.close_database_connection()

@pytest_asyncio.fixture(scope="module")
async def test_users(db):
    """Create multiple test users for testing."""
    users = []
    
    # Create 2 users
    for i in range(2):
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_habit_user_{unique_id}@example.com",
            username=f"test_habit_user_{unique_id}",
            password="password123"
        )
        user = await create_user(user_data)
        
        # Create access token
        access_token = await create_access_token({"sub": str(user["_id"])})
        
        users.append({
            "user": user,
            "access_token": access_token
        })
    
    return users

@pytest_asyncio.fixture(scope="module")
async def user_habits(test_users, db):
    """Create habits for each test user."""
    habits = []
    
    # Create 2 habits for each user
    for i, user_data in enumerate(test_users):
        user_id = str(user_data["user"]["_id"])
        
        for j in range(2):
            unique_id = str(uuid.uuid4())[:8]
            habit_data = HabitCreate(
                title=f"Test User Habit {i}_{j}_{unique_id}",
                description=f"Habit {j} for user {i}",
                frequency="daily",
                target_days=None,
                color="#FF5733",
                icon=f"test-icon-{j}"
            )
            
            habit = await create_habit(user_id, habit_data)
            habits.append(habit)
    
    return habits

@pytest.mark.asyncio
async def test_get_own_habits_by_user_id(test_users, user_habits):
    """Test that a user can get their own habits."""
    for i, user_data in enumerate(test_users):
        user_id = str(user_data["user"]["_id"])
        
        # Prepare headers with JWT token
        headers = {
            "Authorization": f"Bearer {user_data['access_token']}"
        }
        
        # Make the request to get habits by user_id
        response = await client.get(f"/habits/user/{user_id}", headers=headers)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Verify data structure
        assert isinstance(data, list)
        assert len(data) >= 2  # At least 2 habits per user
        
        # Verify all habits belong to the requesting user
        for habit in data:
            assert str(habit["user_id"]) == user_id

@pytest.mark.asyncio
async def test_get_other_user_habits_unauthorized(test_users):
    """Test that a user cannot get another user's habits."""
    # User 1 tries to get User 2's habits
    user1 = test_users[0]
    user2_id = str(test_users[1]["user"]["_id"])
    
    # Prepare headers with JWT token for User 1
    headers = {
        "Authorization": f"Bearer {user1['access_token']}"
    }
    
    # Make the request to get User 2's habits
    response = await client.get(f"/habits/user/{user2_id}", headers=headers)
    
    # Check that access is denied
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_habits_without_auth():
    """Test that unauthenticated requests are rejected."""
    user_id = str(ObjectId())  # Random user ID
    
    # Make the request without authentication
    response = await client.get(f"/habits/user/{user_id}")
    
    # Check that authentication is required
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"] 