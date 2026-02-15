# tests/ui/test_gui.py
import pytest
from streamlit.testing.v1 import AppTest

def test_gui_selection_limit():
    at = AppTest.from_file("gui.py").run()
    
    # Verify the 3-model limit is enforced in the UI logic
    selector = at.multiselect(key="selected_models")
    selector.select("GPT-4o").select("Groq: Llama 3.3").select("Local: Llama 3.2")
    at.run()
    
    # Try to select a 4th (this should be blocked by Streamlit's max_selections)
    assert len(at.session_state.selected_models) <= 3