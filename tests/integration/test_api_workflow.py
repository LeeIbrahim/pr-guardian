# tests/integration/test_api_workflow.py

import json
from fastapi.testclient import TestClient
from pr_guardian.main import app

client = TestClient(app)

def test_full_review_flow_integration():
    payload = {
        "code": "def insecure(): pass",
        "thread_id": "test_integration",
        "model_names": ["gpt-4o"]
    }
    
    response = client.post("/review", json=payload)
    
    assert response.status_code == 200
    
    found_data = False
    for line in response.iter_lines():
        if line:
            # Handle both bytes (real server) and str (TestClient)
            # If it has the 'decode' attribute, it's bytes; otherwise, use it as is.
            decoded_line = line.decode('utf-8') if hasattr(line, 'decode') else line
            
            if decoded_line.startswith("data:"):
                json_str = decoded_line.replace("data: ", "").strip()
                data = json.loads(json_str)
                
                assert "model" in data
                assert "review" in data
                found_data = True
                break
    
    assert found_data, "The stream did not return any valid data packets."