import pytest
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

@pytest.fixture(autouse=True)
def env_setup():
    """Ensure environment variables are loaded for all tests"""
    assert os.getenv("MONGODB_URL") is not None, "MONGODB_URL environment variable is not set"
    assert os.getenv("MONGODB_DATABASE_NAME") is not None, "MONGODB_DATABASE_NAME environment variable is not set"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close() 