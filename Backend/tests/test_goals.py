import pytest
import uuid
from bson import ObjectId
from datetime import datetime, timedelta
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.goal import GoalCreate, GoalUpdate
from app.services.user import create_user
from app.services.goal import create_goal, get_goals_by_user_id, get_goal_by_id, update_goal, delete_goal

@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def db():
    """Connect to database and clean up test data."""
    db = get_database()
    db.connect_to_database()
    
    # Clean up any test data first
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
    await db.client["timewell"]["goals"].delete_many({"title": {"$regex": r"^Test Goal"}})
    
    yield db
    
    # Clean up after tests
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
    await db.client["timewell"]["goals"].delete_many({"title": {"$regex": r"^Test Goal"}})
    db.close_database_connection()

@pytest.fixture(scope="module")
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
async def test_create_goal(test_user):
    """Test creating a new goal."""
    unique_id = str(uuid.uuid4())[:8]
    goal_data = GoalCreate(
        title=f"Test Goal {unique_id}",
        description="Test goal description",
        target_date=datetime.utcnow() + timedelta(days=7),
        is_completed=False
    )
    
    goal = await create_goal(str(test_user["_id"]), goal_data)
    
    # Check the returned goal data
    assert goal["title"] == goal_data.title
    assert goal["description"] == goal_data.description
    assert "target_date" in goal
    assert goal["is_completed"] == goal_data.is_completed
    assert isinstance(goal["_id"], ObjectId)
    assert str(goal["user_id"]) == str(test_user["_id"])
    assert isinstance(goal["created_at"], datetime)
    assert isinstance(goal["updated_at"], datetime)

@pytest.mark.asyncio
async def test_get_goals_by_user_id(test_user):
    """Test retrieving goals by user ID."""
    # Create multiple goals for the user
    for i in range(3):
        unique_id = str(uuid.uuid4())[:8]
        goal_data = GoalCreate(
            title=f"Test Goal {unique_id}",
            description=f"Test goal description {i}",
            target_date=datetime.utcnow() + timedelta(days=i+1),
            is_completed=False
        )
        await create_goal(str(test_user["_id"]), goal_data)
    
    # Get the user's goals
    goals = await get_goals_by_user_id(str(test_user["_id"]))
    
    # Check that we got at least 3 goals
    assert len(goals) >= 3
    
    # Check the structure of the returned goals
    for goal in goals:
        assert "title" in goal
        assert "description" in goal
        assert "is_completed" in goal
        assert "_id" in goal
        assert "user_id" in goal
        assert str(goal["user_id"]) == str(test_user["_id"])
        assert "created_at" in goal
        assert "updated_at" in goal

@pytest.mark.asyncio
async def test_update_goal(test_user):
    """Test updating a goal."""
    # First create a goal to update
    unique_id = str(uuid.uuid4())[:8]
    goal_data = GoalCreate(
        title=f"Test Goal to Update {unique_id}",
        description="This goal will be updated",
        is_completed=False
    )
    goal = await create_goal(str(test_user["_id"]), goal_data)
    goal_id = str(goal["_id"])
    
    # Update data
    update_data = GoalUpdate(
        title="Updated Test Goal",
        is_completed=True
    )
    
    # Update the goal
    updated_goal = await update_goal(goal_id, str(test_user["_id"]), update_data)
    
    # Check the updated goal
    assert updated_goal["title"] == "Updated Test Goal"
    assert updated_goal["is_completed"] == True
    assert updated_goal["description"] == goal["description"]  # Should remain unchanged

@pytest.mark.asyncio
async def test_delete_goal(test_user):
    """Test deleting a goal."""
    # Create a new goal to delete
    unique_id = str(uuid.uuid4())[:8]
    goal_data = GoalCreate(
        title=f"Test Goal to Delete {unique_id}",
        description="This goal will be deleted",
        is_completed=False
    )
    
    goal = await create_goal(str(test_user["_id"]), goal_data)
    goal_id = str(goal["_id"])
    
    # Delete the goal
    result = await delete_goal(goal_id, str(test_user["_id"]))
    
    # Check the result
    assert result["status"] == "success"
    assert "deleted successfully" in result["message"]
    
    # Verify the goal is deleted
    deleted_goal = await get_goal_by_id(goal_id)
    assert deleted_goal is None 