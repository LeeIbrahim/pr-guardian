# tests/integration/test_api.py
import pytest
import json
from fastapi.testclient import TestClient
from pr_guardian.main import app

client = TestClient(app)

def test_api_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert "online" in response.json()["message"]

def test_review_endpoint_streaming():
    # Tests the full cycle from API call to SSE stream
    payload = {
        "code": "print('hello')",
        "thread_id": "test_id",
        "model_names": ["gpt-4o"]
    }
    
    # We use a POST request and iterate through the stream
    with client.stream("POST", "/review", json=payload) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("data: "):
                data = json.loads(line.replace("data: ", ""))
                assert "model" in data
                assert "review" in data
                break