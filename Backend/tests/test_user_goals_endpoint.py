import pytest
from fastapi.testclient import TestClient
import uuid
import json
from datetime import datetime, timedelta
from app.main import app
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.goal import GoalCreate
from app.services.user import create_user
from app.services.goal import create_goal
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_get_user_goals_endpoint():
    """Test the GET /users/{user_id}/goals endpoint."""
    # Setup
    db = get_database()
    db.connect_to_database()
    client = TestClient(app)
    
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
        
        # 3. Create a JWT token for the user
        access_token = create_access_token(
            data={"sub": test_user["email"], "user_id": user_id}
        )
        
        # 4. Make the API call
        response = client.get(
            f"/users/{user_id}/goals",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # 5. Check the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        
        # Verify our goals are in the response
        response_goal_ids = [goal["_id"] for goal in data]
        for goal_id in goal_ids:
            assert goal_id in response_goal_ids
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        await db.client["timewell"]["goals"].delete_many({"title": {"$regex": r"^Test Goal"}})
        db.close_database_connection() 