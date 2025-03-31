import pytest
import asyncio
from app.core.database import get_database
from app.schemas.habit import HabitCreate, HabitUpdate, HabitResponse
from app.models.habit import Habit
from datetime import datetime
from bson import ObjectId

@pytest.mark.asyncio
async def test_database_connection():
    """Test the MongoDB database connection."""
    db = get_database()
    db.connect_to_database()
    
    # Verify connection works by accessing MongoDB server info
    client = db.client
    server_info = await client.server_info()
    
    assert "version" in server_info
    assert server_info["ok"] == 1.0
    
    db.close_database_connection()

def test_habit_models_exist():
    """Test that the habit models exist."""
    assert HabitCreate
    assert HabitUpdate
    assert HabitResponse
    assert Habit

def test_habit_create_model():
    """Test the HabitCreate model"""
    habit_data = {
        "title": "Morning Meditation",
        "description": "10 minutes of mindfulness meditation",
        "frequency": "daily",
        "target_days": [0, 1, 2, 3, 4],
        "color": "#4287f5",
        "icon": "meditation"
    }
    habit = HabitCreate(**habit_data)
    assert habit.title == habit_data["title"]
    assert habit.description == habit_data["description"]
    assert habit.frequency == habit_data["frequency"]
    assert habit.target_days == habit_data["target_days"]
    assert habit.color == habit_data["color"]
    assert habit.icon == habit_data["icon"]

def test_habit_update_model():
    """Test the HabitUpdate model"""
    habit_data = {
        "title": "Updated Meditation",
        "frequency": "weekly", 
        "target_days": [0, 6],
        "color": "#ff0000"
    }
    habit = HabitUpdate(**habit_data)
    assert habit.title == habit_data["title"]
    assert habit.frequency == habit_data["frequency"]
    assert habit.target_days == habit_data["target_days"]
    assert habit.color == habit_data["color"]
    assert habit.description is None  # Default for optional fields

def test_habit_response_model():
    """Test the HabitResponse model"""
    now = datetime.utcnow()
    object_id = ObjectId()
    habit_data = {
        "_id": object_id,
        "user_id": ObjectId(),
        "title": "Response Meditation",
        "description": "Response description",
        "frequency": "daily",
        "streak_count": 5,
        "longest_streak": 10,
        "created_at": now,
        "updated_at": now,
        "color": "#4287f5",
        "icon": "meditation",
        "is_active": True
    }
    
    # PyObjectId will convert string to ObjectId automatically
    habit = HabitResponse(**habit_data)
    assert habit.title == habit_data["title"]
    assert habit.description == habit_data["description"]
    assert habit.frequency == habit_data["frequency"]
    assert habit.streak_count == habit_data["streak_count"]
    assert habit.longest_streak == habit_data["longest_streak"]
    assert habit.color == habit_data["color"]
    assert habit.icon == habit_data["icon"]
    assert habit.is_active == habit_data["is_active"]

def test_habit_router_imported():
    """Test that the habits router is properly imported in main.py"""
    from app.main import app
    router_names = [router.tags[0] for router in app.routes if hasattr(router, 'tags') and router.tags]
    assert "habits" in router_names 