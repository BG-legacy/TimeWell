import pytest
import pytest_asyncio
import uuid
from bson import ObjectId
from datetime import datetime, timedelta
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.habit import HabitCreate, HabitUpdate
from app.services.user import create_user
from app.services.habit import (
    create_habit, 
    get_habits_by_user_id, 
    get_habit_by_id, 
    update_habit, 
    delete_habit,
    increment_streak,
    reset_streak
)

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

@pytest.mark.asyncio
async def test_create_habit(test_user):
    """Test creating a new habit."""
    unique_id = str(uuid.uuid4())[:8]
    habit_data = HabitCreate(
        title=f"Test Habit {unique_id}",
        description="Test habit description",
        frequency="daily",
        target_days=[0, 1, 2, 3, 4],  # Monday to Friday
        color="#4287f5",
        icon="meditation"
    )
    
    habit = await create_habit(str(test_user["_id"]), habit_data)
    
    # Check the returned habit data
    assert habit["title"] == habit_data.title
    assert habit["description"] == habit_data.description
    assert habit["frequency"] == habit_data.frequency
    assert habit["target_days"] == habit_data.target_days
    assert habit["color"] == habit_data.color
    assert habit["icon"] == habit_data.icon
    assert habit["streak_count"] == 0
    assert habit["longest_streak"] == 0
    assert habit["is_active"] == True
    assert isinstance(habit["_id"], ObjectId)
    assert str(habit["user_id"]) == str(test_user["_id"])
    assert isinstance(habit["created_at"], datetime)
    assert isinstance(habit["updated_at"], datetime)

@pytest.mark.asyncio
async def test_get_habits_by_user_id(test_user):
    """Test retrieving habits by user ID."""
    # Create multiple habits for the user
    for i in range(3):
        unique_id = str(uuid.uuid4())[:8]
        habit_data = HabitCreate(
            title=f"Test Habit {unique_id}",
            description=f"Test habit description {i}",
            frequency=["daily", "weekly", "monthly"][i % 3],
            target_days=[i, i+1, i+2] if i < 7 else None
        )
        await create_habit(str(test_user["_id"]), habit_data)
    
    # Get the user's habits
    habits = await get_habits_by_user_id(str(test_user["_id"]))
    
    # Check that we got at least 3 habits
    assert len(habits) >= 3
    
    # Check the structure of the returned habits
    for habit in habits:
        assert "title" in habit
        assert "description" in habit
        assert "frequency" in habit
        assert "streak_count" in habit
        assert "longest_streak" in habit
        assert "is_active" in habit
        assert "_id" in habit
        assert "user_id" in habit
        assert str(habit["user_id"]) == str(test_user["_id"])
        assert "created_at" in habit
        assert "updated_at" in habit

@pytest.mark.asyncio
async def test_get_habit_by_id(test_user):
    """Test retrieving a habit by ID."""
    # First create a habit
    unique_id = str(uuid.uuid4())[:8]
    habit_data = HabitCreate(
        title=f"Test Habit {unique_id}",
        description="Test retrieving by ID",
        frequency="daily"
    )
    created_habit = await create_habit(str(test_user["_id"]), habit_data)
    
    # Get the habit by ID
    habit_id = str(created_habit["_id"])
    retrieved_habit = await get_habit_by_id(habit_id)
    
    # Check the retrieved habit
    assert retrieved_habit is not None
    assert str(retrieved_habit["_id"]) == habit_id
    assert retrieved_habit["title"] == habit_data.title
    assert retrieved_habit["description"] == habit_data.description
    assert str(retrieved_habit["user_id"]) == str(test_user["_id"])

@pytest.mark.asyncio
async def test_update_habit(test_user):
    """Test updating a habit."""
    # First create a habit to update
    unique_id = str(uuid.uuid4())[:8]
    habit_data = HabitCreate(
        title=f"Test Habit to Update {unique_id}",
        description="This habit will be updated",
        frequency="daily",
        target_days=[1, 3, 5]
    )
    habit = await create_habit(str(test_user["_id"]), habit_data)
    habit_id = str(habit["_id"])
    
    # Update data
    update_data = HabitUpdate(
        title="Updated Test Habit",
        frequency="weekly",
        target_days=[0, 6],  # Sunday and Saturday
        color="#ff0000"
    )
    
    # Update the habit
    updated_habit = await update_habit(habit_id, str(test_user["_id"]), update_data)
    
    # Check the updated habit
    assert updated_habit["title"] == "Updated Test Habit"
    assert updated_habit["frequency"] == "weekly"
    assert updated_habit["target_days"] == [0, 6]
    assert updated_habit["color"] == "#ff0000"
    assert updated_habit["description"] == habit["description"]  # Should remain unchanged

@pytest.mark.asyncio
async def test_delete_habit(test_user):
    """Test deleting a habit."""
    # Create a new habit to delete
    unique_id = str(uuid.uuid4())[:8]
    habit_data = HabitCreate(
        title=f"Test Habit to Delete {unique_id}",
        description="This habit will be deleted",
        frequency="monthly",
        target_days=[15]  # Middle of the month
    )
    
    habit = await create_habit(str(test_user["_id"]), habit_data)
    habit_id = str(habit["_id"])
    
    # Delete the habit
    result = await delete_habit(habit_id, str(test_user["_id"]))
    
    # Check the result
    assert result["status"] == "success"
    assert "deleted successfully" in result["message"]
    
    # Verify the habit is deleted
    deleted_habit = await get_habit_by_id(habit_id)
    assert deleted_habit is None

@pytest.mark.asyncio
async def test_increment_streak(test_user):
    """Test incrementing a habit streak."""
    # First create a habit
    unique_id = str(uuid.uuid4())[:8]
    habit_data = HabitCreate(
        title=f"Test Habit for Streak {unique_id}",
        description="This habit will have its streak incremented",
        frequency="daily"
    )
    
    habit = await create_habit(str(test_user["_id"]), habit_data)
    habit_id = str(habit["_id"])
    
    # Initial check
    assert habit["streak_count"] == 0
    assert habit["longest_streak"] == 0
    
    # Increment streak
    updated_habit = await increment_streak(habit_id, str(test_user["_id"]))
    
    # Check streak was incremented
    assert updated_habit["streak_count"] == 1
    assert updated_habit["longest_streak"] == 1
    
    # Increment again
    updated_habit = await increment_streak(habit_id, str(test_user["_id"]))
    
    # Check streak was incremented again
    assert updated_habit["streak_count"] == 2
    assert updated_habit["longest_streak"] == 2

@pytest.mark.asyncio
async def test_reset_streak(test_user):
    """Test resetting a habit streak."""
    # First create a habit
    unique_id = str(uuid.uuid4())[:8]
    habit_data = HabitCreate(
        title=f"Test Habit for Reset {unique_id}",
        description="This habit will have its streak reset",
        frequency="daily"
    )
    
    habit = await create_habit(str(test_user["_id"]), habit_data)
    habit_id = str(habit["_id"])
    
    # Increment streak a few times
    await increment_streak(habit_id, str(test_user["_id"]))
    await increment_streak(habit_id, str(test_user["_id"]))
    updated_habit = await increment_streak(habit_id, str(test_user["_id"]))
    
    # Check streak before reset
    assert updated_habit["streak_count"] == 3
    assert updated_habit["longest_streak"] == 3
    
    # Reset streak
    reset_habit = await reset_streak(habit_id, str(test_user["_id"]))
    
    # Check streak was reset but longest_streak remains
    assert reset_habit["streak_count"] == 0
    assert reset_habit["longest_streak"] == 3

@pytest.mark.asyncio
async def test_longest_streak_preserved(test_user):
    """Test that longest streak is preserved when current streak is reset."""
    # First create a habit
    unique_id = str(uuid.uuid4())[:8]
    habit_data = HabitCreate(
        title=f"Test Habit for Longest Streak {unique_id}",
        description="This habit will test longest streak preservation",
        frequency="daily"
    )
    
    habit = await create_habit(str(test_user["_id"]), habit_data)
    habit_id = str(habit["_id"])
    
    # Build up a streak of 5
    for _ in range(5):
        await increment_streak(habit_id, str(test_user["_id"]))
    
    # Reset the streak
    await reset_streak(habit_id, str(test_user["_id"]))
    
    # Build a smaller streak of 3
    for _ in range(3):
        updated_habit = await increment_streak(habit_id, str(test_user["_id"]))
    
    # Check that longest streak is still 5
    assert updated_habit["streak_count"] == 3
    assert updated_habit["longest_streak"] == 5 