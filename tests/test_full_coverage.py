# tests/test_full_coverage.py

import pytest
import json
from fastapi.testclient import TestClient
from pr_guardian.main import app
from pr_guardian.graph import review_node, get_model

client = TestClient(app)

def test_api_health_check_fix():
    """Fixes the KeyError: 'message' failure."""
    response = client.get("/")
    assert response.status_code == 200
    assert "online" in response.json()["message"] #

def test_ollama_latest_tag_fix():
    """Verifies local models automatically get :latest tag."""
    model = get_model("local/llama3.2")
    assert model.model == "llama3.2:latest" #

@pytest.mark.asyncio
async def test_sequential_false_positive_prompt():
    """Verifies state sharing logic in the graph."""
    state = {
        "code": "eval(x)",
        "reviews": {"gpt-4o": "Found injection."},
        "messages": []
    }
    config = {"configurable": {"model_name": "groq"}}
    # Node should execute without error while seeing existing reviews
    result = await review_node(state, config)
    assert "groq" in result["reviews"]

def test_sequential_payload_acceptance():
    """Verifies API accepts the new toggle."""
    payload = {
        "code": "pass",
        "model_names": ["gpt-4o"],
        "thread_id": "test",
        "sequential": True
    }
    response = client.post("/review", json=payload)
    assert response.status_code == 200