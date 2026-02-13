import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch, MagicMock

def test_gui_multiselect_and_audit():
    # Load the app from your gui.py file
    at = AppTest.from_file("src/pr_guardian/gui.py").run()
    
    # Simulate selecting multiple models in the UI
    # Indices correspond to the options list in your gui.py
    at.multiselect(key="model_select").select("gpt-4o").select("claude").run()
    
    # Simulate entering code into the text area
    at.text_area(key="code_input").input("def test(): pass").run()
    
    # Mock the backend API call to avoid real network traffic
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "report": "Mocked aggregate report"
        }
        
        # Click the 'Audit' button
        at.button(key="audit_button").click().run()
        
        # Assert that the GUI is displaying the success/report area
        assert not at.exception
        assert mock_post.called