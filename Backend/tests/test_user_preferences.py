import pytest
import uuid
from app.core.database import get_database
from app.schemas.user import UserCreate
from app.schemas.preference import Preferences, CoachVoice, Theme
from app.services.user import create_user, update_user_preferences

@pytest.mark.asyncio
async def test_user_preferences():
    """Test user preferences functionality."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # 1. Create a test user with default preferences
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Verify default preferences are set
        assert "preferences" in test_user
        assert test_user["preferences"]["coach_voice"] == CoachVoice.SUPPORTIVE
        assert test_user["preferences"]["theme"] == Theme.SYSTEM
        assert test_user["preferences"]["notifications_enabled"] == True
        
        # 3. Update preferences
        new_preferences = {
            "coach_voice": CoachVoice.MOTIVATIONAL,
            "theme": Theme.DARK,
            "notifications_enabled": False
        }
        
        updated_user = await update_user_preferences(user_id, new_preferences)
        
        # 4. Verify preferences were updated
        assert updated_user["preferences"]["coach_voice"] == CoachVoice.MOTIVATIONAL
        assert updated_user["preferences"]["theme"] == Theme.DARK
        assert updated_user["preferences"]["notifications_enabled"] == False
        
        # 5. Partial update of preferences
        coach_voice_update = {"coach_voice": CoachVoice.DIRECT}
        updated_user = await update_user_preferences(user_id, coach_voice_update)
        
        # 6. Verify only coach_voice was updated, other settings preserved
        assert updated_user["preferences"]["coach_voice"] == CoachVoice.DIRECT
        assert updated_user["preferences"]["theme"] == Theme.DARK
        assert updated_user["preferences"]["notifications_enabled"] == False
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
        db.close_database_connection() 