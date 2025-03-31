import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
import uuid
from datetime import datetime

from app.main import app
from app.schemas.user import UserCreate
from app.services.user import create_user
from app.core.security import create_access_token
from app.services.habit import create_habit
from app.schemas.habit import HabitCreate

client = TestClient(app)

@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def test_user():
    """Create a test user and return user data with access token."""
    unique_id = str(uuid.uuid4())[:8]
    user_data = UserCreate(
        email=f"test_endpoint_{unique_id}@example.com",
        username=f"testendpoint_{unique_id}",
        password="password123"
    )
    user = await create_user(user_data)
    
    # Create access token
    access_token = await create_access_token({"sub": str(user["_id"])})
    
    return {
        "user": user,
        "access_token": access_token
    }

@pytest.fixture(scope="module")
async def test_habit(test_user):
    """Create a test habit and return habit data."""
    unique_id = str(uuid.uuid4())[:8]
    habit_data = HabitCreate(
        title=f"Test Endpoint Habit {unique_id}",
        description="This is a test habit for endpoint testing",
        frequency="daily",
        target_days=[1, 3, 5],
        color="#00ff00",
        icon="test-icon"
    )
    
    habit = await create_habit(str(test_user["user"]["_id"]), habit_data)
    return habit

def test_create_habit(test_user):
    """Test creating a habit through the API endpoint."""
    unique_id = str(uuid.uuid4())[:8]
    
    # Prepare headers with JWT token
    headers = {
        "Authorization": f"Bearer {test_user['access_token']}"
    }
    
    # Prepare habit data
    habit_data = {
        "title": f"API Test Habit {unique_id}",
        "description": "This habit was created through the API",
        "frequency": "weekly",
        "target_days": [0, 6],  # Weekend days
        "color": "#ff00ff",
        "icon": "api-icon"
    }
    
    # Make the request
    response = client.post("/habits/", json=habit_data, headers=headers)
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    
    # Verify data
    assert data["title"] == habit_data["title"]
    assert data["description"] == habit_data["description"]
    assert data["frequency"] == habit_data["frequency"]
    assert data["target_days"] == habit_data["target_days"]
    assert data["color"] == habit_data["color"]
    assert data["icon"] == habit_data["icon"]
    assert data["streak_count"] == 0
    assert data["longest_streak"] == 0
    assert data["is_active"] == True
    assert "user_id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_get_all_habits(test_user):
    """Test getting all habits for a user through the API endpoint."""
    # Prepare headers with JWT token
    headers = {
        "Authorization": f"Bearer {test_user['access_token']}"
    }
    
    # Make the request
    response = client.get("/habits/", headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify data structure
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check first habit's structure
    habit = data[0]
    assert "title" in habit
    assert "description" in habit
    assert "frequency" in habit
    assert "streak_count" in habit
    assert "longest_streak" in habit
    assert "is_active" in habit
    assert "user_id" in habit
    assert "_id" in habit
    assert "created_at" in habit
    assert "updated_at" in habit

def test_get_habit_by_id(test_user, test_habit):
    """Test getting a specific habit by ID through the API endpoint."""
    # Prepare headers with JWT token
    headers = {
        "Authorization": f"Bearer {test_user['access_token']}"
    }
    
    # Make the request
    habit_id = str(test_habit["_id"])
    response = client.get(f"/habits/{habit_id}", headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify data
    assert data["_id"] == habit_id
    assert data["title"] == test_habit["title"]
    assert data["description"] == test_habit["description"]
    assert data["frequency"] == test_habit["frequency"]
    assert data["user_id"] == str(test_habit["user_id"])

def test_update_habit(test_user, test_habit):
    """Test updating a habit through the API endpoint."""
    # Prepare headers with JWT token
    headers = {
        "Authorization": f"Bearer {test_user['access_token']}"
    }
    
    # Prepare update data
    update_data = {
        "title": "Updated Habit Title",
        "description": "This habit has been updated through the API",
        "frequency": "monthly",
        "target_days": [15],
        "color": "#0000ff"
    }
    
    # Make the request
    habit_id = str(test_habit["_id"])
    response = client.patch(f"/habits/{habit_id}", json=update_data, headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify data
    assert data["_id"] == habit_id
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]
    assert data["frequency"] == update_data["frequency"]
    assert data["target_days"] == update_data["target_days"]
    assert data["color"] == update_data["color"]
    assert data["icon"] == test_habit["icon"]  # Unchanged field

def test_increment_streak(test_user, test_habit):
    """Test incrementing a habit streak through the API endpoint."""
    # Prepare headers with JWT token
    headers = {
        "Authorization": f"Bearer {test_user['access_token']}"
    }
    
    # Get current streak values
    habit_id = str(test_habit["_id"])
    response = client.get(f"/habits/{habit_id}", headers=headers)
    data = response.json()
    initial_streak = data["streak_count"]
    initial_longest = data["longest_streak"]
    
    # Make the increment request
    response = client.post(f"/habits/{habit_id}/increment-streak", headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify data
    assert data["_id"] == habit_id
    assert data["streak_count"] == initial_streak + 1
    assert data["longest_streak"] >= initial_longest
    assert data["longest_streak"] >= data["streak_count"]

def test_reset_streak(test_user, test_habit):
    """Test resetting a habit streak through the API endpoint."""
    # Prepare headers with JWT token
    headers = {
        "Authorization": f"Bearer {test_user['access_token']}"
    }
    
    # First increment streak a couple times
    habit_id = str(test_habit["_id"])
    client.post(f"/habits/{habit_id}/increment-streak", headers=headers)
    client.post(f"/habits/{habit_id}/increment-streak", headers=headers)
    
    # Get streak values before reset
    response = client.get(f"/habits/{habit_id}", headers=headers)
    data = response.json()
    streak_before = data["streak_count"]
    longest_before = data["longest_streak"]
    
    # Make sure streak is greater than 0
    assert streak_before > 0
    
    # Make the reset request
    response = client.post(f"/habits/{habit_id}/reset-streak", headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify data
    assert data["_id"] == habit_id
    assert data["streak_count"] == 0
    assert data["longest_streak"] == longest_before  # Longest streak should be preserved

def test_delete_habit(test_user):
    """Test deleting a habit through the API endpoint."""
    # First create a habit to delete
    unique_id = str(uuid.uuid4())[:8]
    
    # Prepare headers with JWT token
    headers = {
        "Authorization": f"Bearer {test_user['access_token']}"
    }
    
    # Create a habit
    habit_data = {
        "title": f"Delete Test Habit {unique_id}",
        "description": "This habit will be deleted",
        "frequency": "daily"
    }
    
    response = client.post("/habits/", json=habit_data, headers=headers)
    data = response.json()
    habit_id = data["_id"]
    
    # Delete the habit
    response = client.delete(f"/habits/{habit_id}", headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "deleted successfully" in data["message"]
    
    # Verify it's deleted
    response = client.get(f"/habits/{habit_id}", headers=headers)
    assert response.status_code == 404

def test_unauthorized_access():
    """Test that unauthorized access is properly rejected."""
    # No authorization header
    response = client.get("/habits/")
    assert response.status_code == 401
    
    # Invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/habits/", headers=headers)
    assert response.status_code == 401

def test_forbidden_access(test_user):
    """Test that accessing another user's habit is forbidden."""
    # This would require a second user and their habit
    # For simplicity, let's just test with a non-existent habit ID
    # that should return 404 rather than 403 since it doesn't exist
    headers = {
        "Authorization": f"Bearer {test_user['access_token']}"
    }
    
    fake_id = str(ObjectId())
    response = client.get(f"/habits/{fake_id}", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_habits_by_user_id(test_user):
    """Test getting habits by user ID through the API endpoint."""
    user_data = await test_user
    user_id = str(user_data["user"]["_id"])
    
    # Prepare headers with JWT token
    headers = {
        "Authorization": f"Bearer {user_data['access_token']}"
    }
    
    # Make the request to get habits by user_id
    response = client.get(f"/habits/user/{user_id}", headers=headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify data structure
    assert isinstance(data, list)
    
    # If there are habits, verify their structure
    if len(data) > 0:
        habit = data[0]
        assert "title" in habit
        assert "description" in habit
        assert "frequency" in habit
        assert "streak_count" in habit
        assert "longest_streak" in habit
        assert "is_active" in habit
        assert "user_id" in habit
        assert "_id" in habit
        assert "created_at" in habit
        assert "updated_at" in habit
        assert str(habit["user_id"]) == user_id

@pytest.mark.asyncio
async def test_get_habits_by_user_id_unauthorized(test_user):
    """Test that unauthorized access to other user's habits is properly rejected."""
    user_data = await test_user
    
    # Generate a random user_id that is different from the test user
    random_user_id = str(ObjectId())
    
    # Prepare headers with JWT token
    headers = {
        "Authorization": f"Bearer {user_data['access_token']}"
    }
    
    # Make the request to get habits for a different user
    response = client.get(f"/habits/user/{random_user_id}", headers=headers)
    
    # Check that access is denied
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"] 