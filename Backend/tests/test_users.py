import pytest
import asyncio
import uuid
from bson import ObjectId
from datetime import datetime
from app.core.database import Database, get_database
from app.schemas.user import UserCreate
from app.services.user import create_user, get_user_by_email, authenticate_user
from app.core.security import verify_password, get_password_hash

@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Initialize database connection for all tests."""
    db = get_database()
    db.connect_to_database()
    yield
    db.close_database_connection()

@pytest.fixture(scope="module")
async def test_db():
    """Get database instance for tests."""
    db = get_database()
    # Make sure we're connected
    if db.client is None:
        db.connect_to_database()
    
    # Clean up any test users first
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})
    yield db
    await db.client["timewell"]["users"].delete_many({"email": {"$regex": r"^test.*@example\.com$"}})

@pytest.fixture
def unique_test_user_data():
    """Generate a unique test user data to avoid conflicts."""
    unique_id = str(uuid.uuid4())[:8]
    return UserCreate(
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        password="password123"
    )

@pytest.fixture(scope="module")
def test_user_data():
    """Fixed test user data for authentication tests."""
    return UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

@pytest.mark.asyncio
async def test_create_user(test_db, unique_test_user_data):
    """Test creating a new user."""
    # Create a new user
    user = await create_user(unique_test_user_data)
    
    # Check the returned user data
    assert user["email"] == unique_test_user_data.email
    assert user["username"] == unique_test_user_data.username
    assert "hashed_password" in user
    assert verify_password(unique_test_user_data.password, user["hashed_password"])
    assert user["is_active"] is True
    assert isinstance(user["_id"], ObjectId)
    assert isinstance(user["created_at"], datetime)
    assert isinstance(user["updated_at"], datetime)

@pytest.mark.asyncio
async def test_get_user_by_email(test_db, test_user_data):
    """Test retrieving a user by email."""
    # First make sure we have a user to retrieve
    try:
        await create_user(test_user_data)
    except:
        # User might already exist
        pass
        
    user = await get_user_by_email(test_user_data.email)
    assert user is not None
    assert user["email"] == test_user_data.email
    assert user["username"] == test_user_data.username

@pytest.mark.asyncio
async def test_authenticate_user(test_db, test_user_data):
    """Test user authentication."""
    # Test valid credentials
    user = await authenticate_user(test_user_data.email, test_user_data.password)
    assert user is not None
    assert user["email"] == test_user_data.email
    
    # Test invalid password
    user = await authenticate_user(test_user_data.email, "wrongpassword")
    assert user is False
    
    # Test non-existent user
    user = await authenticate_user("nonexistent@example.com", "password123")
    assert user is False

@pytest.mark.asyncio
async def test_create_duplicate_user(test_db, test_user_data):
    """Test creating a user with an email that already exists."""
    from fastapi import HTTPException
    
    # Try to create a duplicate user
    with pytest.raises(HTTPException) as excinfo:
        await create_user(test_user_data)
    
    # Check that we got the right error
    assert excinfo.value.status_code == 400
    assert "already exists" in excinfo.value.detail 