import pytest
from app.core.database import Database, get_database
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def database():
    db = Database()
    yield db
    db.close_database_connection()

def test_database_connection(database):
    """Test that we can connect to the database"""
    database.connect_to_database()
    assert database.client is not None

def test_database_connection_with_custom_url(database):
    """Test that we can connect to the database with a custom URL"""
    test_url = "mongodb://localhost:27017"
    database.connect_to_database(test_url)
    assert database.client is not None

def test_database_connection_from_env(database):
    """Test that we can connect to the database using environment variables"""
    database.connect_to_database()
    assert database.client is not None
    assert os.getenv("MONGODB_URL") is not None

def test_get_database():
    """Test that get_database returns a Database instance"""
    db = get_database()
    assert isinstance(db, Database) 