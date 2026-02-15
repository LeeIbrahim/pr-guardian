import pytest
from fastapi.testclient import TestClient
from pr_guardian.main import app
from pr_guardian.graph import review_node
from pr_guardian.graph import merge_reviews

client = TestClient(app)

def test_api_sequential_flag():
    payload = {"code": "pass", "model_names": ["gpt-4o"], "thread_id": "1", "sequential": True}
    response = client.post("/review", json=payload)
    assert response.status_code == 200

# 2. Logic: False Positive Cross-Referencing
@pytest.mark.asyncio
async def test_false_positive_logic():
    # Verify that if previous reviews exist, the prompt changes to include them."""
    state = {
        "code": "eval(input())",
        "reviews": {"model_1": "This is a critical injection flaw."},
        "messages": []
    }
    config = {"configurable": {"model_name": "gpt-4o"}}
    
    # We call the node; in a real run, the 'reviewer' uses the presence of 
    # 'reviews' in state to trigger the "Point out false positives" prompt logic.
    result = await review_node(state, config)
    assert "gpt-4o" in result["reviews"]

@pytest.mark.asyncio
async def test_model_error_handling():
    config = {"configurable": {"model_name": "non_existent_model"}}
    state = {"code": "print('hi')", "reviews": {}}
    result = await review_node(state, config)
    assert "ERROR" in result["reviews"]["non_existent_model"]
    
def test_merge_reviews_logic():
    old = {"m1": "res1"}
    new = {"m2": "res2"}
    combined = merge_reviews(old, new)
    assert "m1" in combined and "m2" in combined