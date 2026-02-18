# tests/test_integration.py
import json
import pytest
from fastapi.testclient import TestClient
from pr_guardian.main import app

client = TestClient(app)

def test_streaming_review_limit_3():
    # Verify the backend accepts a 3-model payload
    payload = {
        "code": "print('test')",
        "model_names": ["gpt-4o-mini", "gpt-4o", "local/llama3.2"],
        "user_message": "Testing 3 models"
    }
    with client.stream("POST", "/review", json=payload) as response:
        assert response.status_code == 200

def test_streaming_review_over_limit():
    # Verify the backend rejects 4 models with 422 Unprocessable Entity
    payload = {
        "code": "print('test')",
        "model_names": ["gpt-4o-mini", "gpt-4o", "local/llama3.2", "groq"]
    }
    response = client.post("/review", json=payload)
    assert response.status_code == 422