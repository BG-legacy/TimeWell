import pytest
import uuid
from bson import ObjectId
from datetime import datetime, timedelta
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.goal import GoalCreate, GoalUpdate
from app.services.user import create_user
from app.services.goal import create_goal, get_goals_by_user_id, get_goal_by_id, update_goal, delete_goal

@pytest.mark.asyncio
async def test_goal_crud_operations():
    """Test the full CRUD lifecycle of a goal."""
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
        
        # 2. Create a goal
        goal_data = GoalCreate(
            title=f"Test Goal {unique_id}",
            description="Test goal description",
            target_date=datetime.utcnow() + timedelta(days=7),
            is_completed=False
        )
        
        goal = await create_goal(user_id, goal_data)
        goal_id = str(goal["_id"])
        
        # Check the goal was created correctly
        assert goal["title"] == goal_data.title
        assert goal["description"] == goal_data.description
        assert goal["is_completed"] == goal_data.is_completed
        assert isinstance(goal["_id"], ObjectId)
        assert str(goal["user_id"]) == user_id
        
        # 3. Get the user's goals
        goals = await get_goals_by_user_id(user_id)
        assert len(goals) >= 1
        
        found_goal = False
        for g in goals:
            if str(g["_id"]) == goal_id:
                found_goal = True
                break
        
        assert found_goal, "Created goal wasn't found in the user's goals"
        
        # 4. Update the goal
        update_data = GoalUpdate(
            title="Updated Test Goal",
            is_completed=True
        )
        
        updated_goal = await update_goal(goal_id, user_id, update_data)
        
        # Check the update worked
        assert updated_goal["title"] == "Updated Test Goal"
        assert updated_goal["is_completed"] == True
        assert updated_goal["description"] == goal["description"]  # Should remain unchanged
        
        # 5. Delete the goal
        result = await delete_goal(goal_id, user_id)
        assert result["status"] == "success"
        
        # Verify the goal is deleted
        deleted_goal = await get_goal_by_id(goal_id)
        assert deleted_goal is None
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["goals"].delete_many({"title": {"$regex": r"^Test Goal"}})
        db.close_database_connection() 