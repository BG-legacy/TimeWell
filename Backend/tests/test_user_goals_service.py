import pytest
import uuid
from bson import ObjectId
from datetime import datetime, timedelta
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.goal import GoalCreate
from app.services.user import create_user
from app.services.goal import create_goal, get_goals_by_user_id

@pytest.mark.asyncio
async def test_get_user_goals():
    """Test getting a user's goals."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
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
        
        # 2. Create some goals for the user
        goal_ids = []
        for i in range(3):
            goal_data = GoalCreate(
                title=f"Test Goal {i} {unique_id}",
                description=f"Test goal description {i}",
                target_date=datetime.utcnow() + timedelta(days=i+1),
                is_completed=False
            )
            goal = await create_goal(user_id, goal_data)
            goal_ids.append(str(goal["_id"]))
        
        # 3. Get the user's goals using the service function
        goals = await get_goals_by_user_id(user_id)
        
        # 4. Check the results
        assert len(goals) >= 3
        
        # Verify our goals are in the response
        response_goal_ids = [str(goal["_id"]) for goal in goals]
        for goal_id in goal_ids:
            assert goal_id in response_goal_ids, f"Goal {goal_id} not found in response"
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["goals"].delete_many({"title": {"$regex": r"^Test Goal"}})
        db.close_database_connection()

@pytest.mark.asyncio
async def test_create_user_goal():
    """Test creating a goal for a user."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
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
        
        # 2. Create a goal for the user
        goal_data = GoalCreate(
            title=f"Test Goal {unique_id}",
            description="Test goal description",
            target_date=datetime.utcnow() + timedelta(days=7),
            is_completed=False
        )
        
        new_goal = await create_goal(user_id, goal_data)
        
        # 3. Verify the goal was created correctly
        assert new_goal["title"] == goal_data.title
        assert new_goal["description"] == goal_data.description
        assert "target_date" in new_goal
        assert new_goal["is_completed"] == goal_data.is_completed
        assert isinstance(new_goal["_id"], ObjectId)
        assert str(new_goal["user_id"]) == user_id
        assert isinstance(new_goal["created_at"], datetime)
        assert isinstance(new_goal["updated_at"], datetime)
        
        # 4. Verify the goal appears in the user's goals
        goals = await get_goals_by_user_id(user_id)
        goal_ids = [str(goal["_id"]) for goal in goals]
        assert str(new_goal["_id"]) in goal_ids
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["goals"].delete_many({"title": {"$regex": r"^Test Goal"}})
        db.close_database_connection() 