import pytest
from fastapi.testclient import TestClient
from pr_guardian.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_review_thread_isolation():
    """Verify that different threads do not bleed review data."""
    payload1 = {"code": "x=1", "thread_id": "session_1", "models": ["gpt-4o"]}
    payload2 = {"code": "y=2", "thread_id": "session_2", "models": ["claude"]}
    
    resp1 = client.post("/review", json=payload1)
    resp2 = client.post("/review", json=payload2)
    
    # Ensure reports reflect the specific models requested in those threads
    assert "gpt-4o" in resp1.json()["report"]
    assert "claude" in resp2.json()["report"]
    assert "claude" not in resp1.json()["report"]

@pytest.mark.asyncio
async def test_empty_thread_id_fallback():
    payload = {"code": "print('hello')", "thread_id": ""}
    response = client.post("/review", json=payload)
    assert response.status_code == 200