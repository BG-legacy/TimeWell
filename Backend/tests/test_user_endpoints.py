import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
from app.core.database import get_database
from app.schemas.user import UserCreate
from bson import ObjectId

# Create a test client
client = TestClient(app)

@pytest.fixture
def mock_db():
    """Mock the database connection."""
    with patch('app.services.user.get_database') as mock_get_db:
        # Mock the database client
        mock_client = MagicMock()
        mock_db_instance = MagicMock()
        mock_db_instance.client = mock_client
        mock_get_db.return_value = mock_db_instance

        # Setup mock collection and methods
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        # Default user
        test_user = {
            "_id": ObjectId(),
            "email": "testendpoint@example.com",
            "username": "testendpoint",
            "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password123"
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Setup find_one to return the test user or None
        def mock_find_one(query):
            if query.get("email") == "testendpoint@example.com":
                return test_user
            return None
        
        mock_collection.find_one.side_effect = mock_find_one
        
        # Setup insert_one to return an object with an inserted_id property
        def mock_insert_one(data):
            inserted_id = ObjectId()
            mock_result = MagicMock()
            mock_result.inserted_id = inserted_id
            return mock_result
        
        mock_collection.insert_one.side_effect = mock_insert_one
        
        yield mock_collection

def test_signup(mock_db):
    """Test user signup endpoint."""
    # Test signup
    response = client.post(
        "/auth/signup",
        json={
            "email": "testendpoint2@example.com",
            "username": "testendpoint2",
            "password": "password123"
        }
    )
    
    assert response.status_code == 201
    assert "email" in response.json()
    assert "username" in response.json()
    assert "_id" in response.json()

def test_login(mock_db):
    """Test user login endpoint."""
    # Setup the mock to return a test user for login
    mock_db.find_one.return_value = {
        "_id": ObjectId(),
        "email": "testendpoint@example.com",
        "username": "testendpoint",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password123"
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Test login
    response = client.post(
        "/auth/login",
        data={
            "username": "testendpoint@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(mock_db):
    """Test login with invalid credentials."""
    # Setup the mock to return None for the given email
    mock_db.find_one.return_value = None
    
    response = client.post(
        "/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401

def test_get_current_user_invalid_token():
    """Test getting current user with invalid token."""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    
    assert response.status_code == 401 