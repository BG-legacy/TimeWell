import pytest
import asyncio
from app.core.database import get_database

@pytest.mark.asyncio
async def test_database_connection():
    """Test the MongoDB database connection."""
    db = get_database()
    db.connect_to_database()
    
    # Verify connection works by accessing MongoDB server info
    client = db.client
    server_info = await client.server_info()
    
    assert "version" in server_info
    assert server_info["ok"] == 1.0
    
    db.close_database_connection() 