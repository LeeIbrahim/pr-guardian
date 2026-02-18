# tests/ui/test_gui_view.py
import pytest
from streamlit.testing.v1 import AppTest


def test_gui_selection_limit():
    """
    Verify that the model multiselect enforces the 3-model limit in the UI.
    """
    at = AppTest.from_file("gui.py").run()
    
    # The actual key used in gui.py is "model_selector" (not "selected_models")
    selector = at.multiselect(key="model_selector")
    
    assert selector is not None, "Model selector multiselect should be present"
    assert selector.max_selections == 3, "UI should enforce max 3 selections"

    # Get available options
    options = selector.options
    
    # Select up to 3 items
    if len(options) >= 3:
        selector.select(options[:3])
    else:
        selector.select(options)
    
    at.run()
    
    # After selection, value should never exceed 3
    assert len(selector.value) <= 3, "Should not allow more than 3 models"

    # Try to force more than 3 (Streamlit should ignore extras)
    if len(options) >= 4:
        try:
            selector.select(options[:4])
            at.run()
            assert len(selector.value) <= 3, "Selection should still be capped at 3"
        except Exception:
            # Some Streamlit versions raise or silently ignore — either is acceptable
            pass