import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_post_habit_unauthorized():
    """Test that unauthorized access is rejected when creating a habit."""
    response = client.post(
        "/habits/",
        json={
            "title": "Unauthorized Habit",
            "frequency": "daily"
        }
    )
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Not authenticated" in response.json()["detail"] 