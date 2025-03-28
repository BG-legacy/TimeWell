import pytest
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture(autouse=True)
def env_setup():
    """Ensure environment variables are loaded for all tests"""
    assert os.getenv("MONGODB_URL") is not None, "MONGODB_URL environment variable is not set"
    assert os.getenv("MONGODB_DATABASE_NAME") is not None, "MONGODB_DATABASE_NAME environment variable is not set" 