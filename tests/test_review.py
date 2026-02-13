import pytest
from fastapi.testclient import TestClient
from pr_guardian.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "online" in response.json()["message"]

@pytest.mark.asyncio
async def test_review_endpoint_logic():
    # The payload now represents the multi-model intent
    test_payload = {
        "code": "def example(): pass",
        "models": ["gpt-4o", "claude"] # Assuming main.py was updated for list
    }
    
    response = client.post("/review", json=test_payload)
    
    assert response.status_code == 200
    report = response.json()["report"]
    # Verify it is a dictionary containing at least one model's feedback
    assert isinstance(report, dict)