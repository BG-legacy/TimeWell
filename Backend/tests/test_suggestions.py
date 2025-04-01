import pytest
import asyncio
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId
from fastapi.testclient import TestClient
from app.core.database import get_database, db
from app.schemas.user import UserCreate
from app.schemas.event import EventCreate
from app.schemas.analysis import SuggestionCreate
from app.services.user import create_user
from app.services.event import create_event
from app.services.suggestion import (
    create_suggestion, 
    get_suggestions_by_user_id, 
    get_suggestion_by_id, 
    mark_suggestion_applied,
    get_suggestions_by_event_id
)
from app.services.ai_analysis import analyze_event_goal_alignment
from app.models.suggestion import Suggestion
from app.services.suggestion_service import SuggestionService
from app.main import app
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="module")
def event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_database():
    # Connect to the database
    if db.client is None:
        db.connect_to_database()
    
    # Get database name from environment
    db_name = os.getenv("MONGODB_DATABASE_NAME", "timewell")
    
    # Ensure suggestions collection exists
    try:
        await db.client[db_name].create_collection("suggestions")
    except:
        # Collection might already exist
        pass
    
    yield
    
    # Clean up
    # Don't close connection, as it may be needed by other tests
    # db.close_database_connection()

@pytest.fixture
def suggestion_service():
    # Ensure database is connected before creating service
    if db.client is None:
        db.connect_to_database()
    
    return SuggestionService()

@pytest.fixture
def sample_user_id():
    return str(ObjectId())

@pytest.fixture
def sample_event_id():
    return str(ObjectId())

@pytest.fixture
def sample_suggestion_data(sample_user_id, sample_event_id):
    return {
        "user_id": sample_user_id,
        "title": "Test Suggestion",
        "description": "This is a test suggestion",
        "category": "productivity",
        "priority": 3,
        "status": "pending",
        "tags": ["test", "productivity"],
        "is_active": True,
        "ai_prompt": "Generate a productivity suggestion",
        "ai_response": "Based on analysis, here's a productivity suggestion...",
        "event_id": sample_event_id,
        "was_accepted": False
    }

@pytest.fixture
def sample_suggestion(sample_suggestion_data):
    return Suggestion(**sample_suggestion_data)

@pytest.fixture
def auth_client():
    # Create a TestClient with a mock authentication token
    client = TestClient(app)
    # Mock authentication by adding the Bearer token or bypass auth
    client.headers["Authorization"] = "Bearer test_token"
    return client

@pytest.mark.asyncio
async def test_suggestions_crud():
    """Test CRUD operations for suggestions."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_suggestion_{unique_id}@example.com",
            username=f"testuser_suggestion_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create an event
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = EventCreate(
            title=f"Test Suggestion Event {unique_id}",
            description="Test event for suggestion",
            start_time=start_time,
            end_time=end_time,
            is_completed=False
        )
        event = await create_event(user_id, event_data)
        event_id = str(event["_id"])
        
        # Create some dummy goal IDs - using valid ObjectId strings
        goal_id1 = str(ObjectId())
        goal_id2 = str(ObjectId())
        
        # 3. Create a suggestion
        suggestion_data = SuggestionCreate(
            user_id=user_id,
            event_id=event_id,
            score=7,
            aligned_goals=[goal_id1, goal_id2],
            analysis="This event aligns well with your productivity goals.",
            suggestion="Consider adding specific milestones to track progress.",
            new_goal_suggestion=None
        )
        
        # Create the suggestion
        suggestion = await create_suggestion(suggestion_data)
        suggestion_id = str(suggestion["_id"])
        
        # 4. Verify the suggestion was created correctly
        assert suggestion["user_id"] == ObjectId(user_id)
        assert suggestion["event_id"] == ObjectId(event_id)
        assert suggestion["score"] == 7
        assert len(suggestion["aligned_goals"]) == 2
        assert suggestion["analysis"] == "This event aligns well with your productivity goals."
        assert suggestion["suggestion"] == "Consider adding specific milestones to track progress."
        assert suggestion["new_goal_suggestion"] is None
        assert suggestion["is_applied"] is False
        
        # 5. Get suggestions by user ID
        user_suggestions = await get_suggestions_by_user_id(user_id)
        assert len(user_suggestions) >= 1
        
        # Find our test suggestion
        found_suggestion = None
        for s in user_suggestions:
            if str(s["_id"]) == suggestion_id:
                found_suggestion = s
                break
        
        assert found_suggestion is not None
        assert str(found_suggestion["user_id"]) == user_id
        
        # 6. Get suggestion by ID
        retrieved_suggestion = await get_suggestion_by_id(suggestion_id)
        assert retrieved_suggestion is not None
        assert str(retrieved_suggestion["_id"]) == suggestion_id
        assert str(retrieved_suggestion["user_id"]) == user_id
        assert str(retrieved_suggestion["event_id"]) == event_id
        
        # 7. Mark suggestion as applied
        updated_suggestion = await mark_suggestion_applied(suggestion_id, True)
        assert updated_suggestion is not None
        assert updated_suggestion["is_applied"] is True
        
        # 8. Mark suggestion as not applied
        updated_suggestion = await mark_suggestion_applied(suggestion_id, False)
        assert updated_suggestion is not None
        assert updated_suggestion["is_applied"] is False
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({
            "email": {"$regex": r"^test_suggestion.*@example\.com$"}
        })
        await db.client["timewell"]["events"].delete_many({
            "title": {"$regex": r"^Test Suggestion Event"}
        })
        await db.client["timewell"]["suggestions"].delete_many({
            "analysis": "This event aligns well with your productivity goals."
        })
        db.close_database_connection()

@pytest.mark.asyncio
async def test_suggestion_saved_from_event_analysis():
    """Test that suggestions are saved when analyzing an event."""
    # Setup
    db = get_database()
    db.connect_to_database()
    
    # Create a module-level mock function that will replace the chain.ainvoke
    from app.services import ai_analysis
    original_chain = ai_analysis.chain
    
    # Mock analysis result that the LangChain would return
    mock_analysis_result = {
        "score": 8,
        "aligned_goals": ["goal-123", "goal-456"],
        "analysis": "This is a test analysis from the integration test.",
        "suggestion": "This is a test suggestion from the integration test.",
        "new_goal_suggestion": "This is a test new goal suggestion."
    }
    
    # Create a mock chain object with an ainvoke method
    class MockChain:
        async def ainvoke(self, *args, **kwargs):
            return {"text": json.dumps(mock_analysis_result)}
    
    # Replace the chain with our mock
    ai_analysis.chain = MockChain()
    
    try:
        # 1. Create a test user
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test_analysis_{unique_id}@example.com",
            username=f"testuser_analysis_{unique_id}",
            password="password123"
        )
        test_user = await create_user(user_data)
        user_id = str(test_user["_id"])
        
        # 2. Create an event to analyze
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        event_data = EventCreate(
            title=f"Test Analysis Event {unique_id}",
            description="Test event for analysis integration test",
            start_time=start_time,
            end_time=end_time,
            is_completed=False
        )
        event = await create_event(user_id, event_data)
        event_id = str(event["_id"])
        
        # 3. Call the analysis service
        result = await analyze_event_goal_alignment(user_id, event_id)
        
        # 4. Verify the analysis was successful
        assert result["error"] is False
        assert result["event_id"] == event_id
        assert "analysis" in result
        
        # 5. Get suggestions for the event to verify one was created
        suggestions = await get_suggestions_by_event_id(event_id)
        
        # 6. Verify a suggestion was created
        assert len(suggestions) == 1
        suggestion = suggestions[0]
        
        # 7. Verify the suggestion has the correct data
        assert str(suggestion["user_id"]) == user_id
        assert str(suggestion["event_id"]) == event_id
        assert suggestion["score"] == mock_analysis_result["score"]
        assert suggestion["analysis"] == mock_analysis_result["analysis"]
        assert suggestion["suggestion"] == mock_analysis_result["suggestion"]
        assert suggestion["new_goal_suggestion"] == mock_analysis_result["new_goal_suggestion"]
        
        # 8. Verify the suggestion has non-ObjectId goals (since our mock returns string goals)
        assert len(suggestion["aligned_goals"]) == 2
        aligned_goals = [goal for goal in suggestion["aligned_goals"]]
        assert "goal-123" in aligned_goals
        assert "goal-456" in aligned_goals
        
    finally:
        # Clean up
        await db.client["timewell"]["users"].delete_many({
            "email": {"$regex": r"^test_analysis.*@example\.com$"}
        })
        await db.client["timewell"]["events"].delete_many({
            "title": {"$regex": r"^Test Analysis Event"}
        })
        await db.client["timewell"]["suggestions"].delete_many({
            "analysis": "This is a test analysis from the integration test."
        })
        
        # Restore the original chain
        ai_analysis.chain = original_chain
        
        db.close_database_connection()

class TestSuggestionModel:
    def test_suggestion_creation(self, sample_suggestion_data):
        suggestion = Suggestion(**sample_suggestion_data)
        assert suggestion.title == "Test Suggestion"
        assert suggestion.description == "This is a test suggestion"
        assert suggestion.category == "productivity"
        assert suggestion.priority == 3
        assert suggestion.status == "pending"
        assert suggestion.tags == ["test", "productivity"]
        assert suggestion.is_active is True
        assert suggestion.ai_prompt == "Generate a productivity suggestion"
        assert suggestion.ai_response == "Based on analysis, here's a productivity suggestion..."
        assert suggestion.was_accepted is False
        assert isinstance(suggestion.created_at, datetime)
        assert isinstance(suggestion.updated_at, datetime)

    def test_suggestion_defaults(self):
        minimal_data = {
            "user_id": str(ObjectId()),
            "title": "Minimal Suggestion",
            "description": "Minimal test",
            "category": "test"
        }
        suggestion = Suggestion(**minimal_data)
        assert suggestion.priority == 1
        assert suggestion.status == "pending"
        assert suggestion.tags is None
        assert suggestion.is_active is True
        assert suggestion.ai_prompt is None
        assert suggestion.ai_response is None
        assert suggestion.event_id is None
        assert suggestion.was_accepted is False

    def test_suggestion_validation(self):
        with pytest.raises(ValueError):
            Suggestion(
                user_id="invalid_id",  # Invalid ObjectId
                title="Test",
                description="Test",
                category="test"
            )

class TestSuggestionService:
    @pytest.mark.asyncio
    @patch('app.services.suggestion_service.db')
    async def test_get_user_suggestions(self, mock_db, sample_suggestion_data):
        # Create mock cursor with sort method
        mock_cursor = AsyncMock()
        mock_cursor.sort.return_value = mock_cursor  # Make sort return the cursor for chaining
        
        # Set up sample document to return
        sample_suggestion = Suggestion(**sample_suggestion_data)
        mock_cursor.__aiter__.return_value = [sample_suggestion.model_dump(by_alias=True)]
        
        # Create mock collection
        mock_collection = AsyncMock()
        mock_collection.find.return_value = mock_cursor
        
        # Set up mock database
        mock_db_instance = MagicMock()
        mock_db_instance.__getitem__.return_value = mock_collection
        
        # Configure db mock
        mock_db.client = MagicMock()
        mock_db.client.__getitem__.return_value = mock_db_instance
        
        # Create service and replace collection
        service = SuggestionService()
        
        # Call method
        suggestions = await service.get_user_suggestions(sample_suggestion_data["user_id"])
        
        # Verify results
        assert len(suggestions) == 1
        assert suggestions[0].title == sample_suggestion_data["title"]
        assert suggestions[0].description == sample_suggestion_data["description"]
        
        # Verify correct methods were called
        mock_collection.find.assert_called_once()
        mock_cursor.sort.assert_called_once_with("created_at", -1)

    @pytest.mark.asyncio
    @patch('app.services.suggestion_service.db')
    async def test_get_user_suggestions_empty(self, mock_db, sample_user_id):
        # Create mock cursor with sort method
        mock_cursor = AsyncMock()
        mock_cursor.sort.return_value = mock_cursor  # Make sort return the cursor for chaining
        
        # Set up empty results
        mock_cursor.__aiter__.return_value = []
        
        # Create mock collection
        mock_collection = AsyncMock()
        mock_collection.find.return_value = mock_cursor
        
        # Set up mock database
        mock_db_instance = MagicMock()
        mock_db_instance.__getitem__.return_value = mock_collection
        
        # Configure db mock
        mock_db.client = MagicMock()
        mock_db.client.__getitem__.return_value = mock_db_instance
        
        # Create service
        service = SuggestionService()
        
        # Call method
        suggestions = await service.get_user_suggestions(sample_user_id)
        
        # Verify results
        assert len(suggestions) == 0
        
        # Verify correct methods were called
        mock_collection.find.assert_called_once()
        mock_cursor.sort.assert_called_once_with("created_at", -1)

    @pytest.mark.asyncio
    @patch('app.services.suggestion_service.db')
    async def test_get_user_suggestions_inactive(self, mock_db, sample_suggestion_data):
        # Create mock cursor with sort method
        mock_cursor = AsyncMock()
        mock_cursor.sort.return_value = mock_cursor  # Make sort return the cursor for chaining
        
        # Set up empty results (inactive suggestion will be filtered out)
        mock_cursor.__aiter__.return_value = []
        
        # Create mock collection
        mock_collection = AsyncMock()
        mock_collection.find.return_value = mock_cursor
        
        # Set up mock database
        mock_db_instance = MagicMock()
        mock_db_instance.__getitem__.return_value = mock_collection
        
        # Configure db mock
        mock_db.client = MagicMock()
        mock_db.client.__getitem__.return_value = mock_db_instance
        
        # Create service
        service = SuggestionService()
        
        # Mark sample data as inactive
        sample_suggestion_data["is_active"] = False
        
        # Call method
        suggestions = await service.get_user_suggestions(sample_suggestion_data["user_id"])
        
        # Verify results
        assert len(suggestions) == 0
        
        # Verify correct query was used (filter includes is_active=True)
        mock_collection.find.assert_called_once()
        query_arg = mock_collection.find.call_args[0][0]
        assert query_arg["is_active"] is True
        mock_cursor.sort.assert_called_once_with("created_at", -1)

class TestSuggestionRouter:
    @pytest.mark.asyncio
    async def test_get_user_suggestions_endpoint(self, auth_client, sample_suggestion_data, suggestion_service):
        # Insert a test suggestion
        suggestion = Suggestion(**sample_suggestion_data)
        await suggestion_service.collection.insert_one(suggestion.model_dump(by_alias=True))
        
        # Make request to endpoint
        response = auth_client.get(f"/suggestions/{sample_suggestion_data['user_id']}")
        
        # Verify response
        assert response.status_code == 200
        suggestions = response.json()
        assert len(suggestions) > 0
        assert suggestions[0]["title"] == sample_suggestion_data["title"]
        
        # Clean up
        await suggestion_service.collection.delete_many({"user_id": ObjectId(sample_suggestion_data["user_id"])})

    @pytest.mark.asyncio
    async def test_get_user_suggestions_empty_endpoint(self, auth_client, sample_user_id, suggestion_service):
        # Delete any existing suggestions
        await suggestion_service.collection.delete_many({"user_id": ObjectId(sample_user_id)})
        
        # Make request to endpoint with no suggestions
        response = auth_client.get(f"/suggestions/{sample_user_id}")
        
        # Verify response
        assert response.status_code == 200
        suggestions = response.json()
        assert len(suggestions) == 0

    @pytest.mark.asyncio
    async def test_get_user_suggestions_invalid_id(self, auth_client):
        # Make request with invalid user ID
        with patch("app.routers.suggestion_router.suggestion_service.get_user_suggestions", 
                  side_effect=Exception("Invalid ObjectId")):
            response = auth_client.get("/suggestions/invalid_id")
            
            # Verify response
            assert response.status_code == 500
            assert "Error fetching suggestions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_suggestions_inactive_filter(self, auth_client, sample_suggestion_data, suggestion_service):
        # Insert an inactive suggestion
        sample_suggestion_data["is_active"] = False
        suggestion = Suggestion(**sample_suggestion_data)
        await suggestion_service.collection.insert_one(suggestion.model_dump(by_alias=True))
        
        # Make request to endpoint
        response = auth_client.get(f"/suggestions/{sample_suggestion_data['user_id']}")
        
        # Verify response
        assert response.status_code == 200
        suggestions = response.json()
        assert len(suggestions) == 0  # Inactive suggestions should not be returned
        
        # Clean up
        await suggestion_service.collection.delete_many({"user_id": ObjectId(sample_suggestion_data["user_id"])}) 