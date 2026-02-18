# tests/integration/test_gui.py  (add this function)

import io
from streamlit.testing.v1 import AppTest


def test_run_button_triggers_something():
    """
    Minimal check: clicking 'Run Parallel Audit' causes script re-run
    and shows either error message or live review container when input exists.
    """
    at = AppTest.from_file("gui.py").run()

    # Provide minimal input so button is "active" (no warning)
    at.text_area[0].input("print('test')")          # or use file uploader if you prefer
    at.run()

    # Make sure we have at least one model selected (default should help)
    assert len(at.multiselect(key="model_selector").value) >= 1

    # Find the primary Run button
    run_buttons = [b for b in at.button if b.label and "Run Parallel Audit" in b.label]
    assert len(run_buttons) > 0, "Run button should be visible"

    run_button = run_buttons[0]

    # Before click: expect no "Live Review Stream" yet or no success message
    initial_markdown = [m.value for m in at.markdown if m.value]
    assert not any("Audit complete" in text for text in initial_markdown)

    # Click → triggers rerun
    run_button.click()
    at.run()   # important: simulate the script re-execution after button click

    # After click: we should see either
    #   a) an error (backend not running → good for local test)
    #   b) "Live Review Stream" header
    #   c) some markdown from the streaming response
    updated_markdown = [m.value for m in at.markdown if m.value]
    updated_errors   = [e for e in at.error if e.value]

    assert (
        "Live Review Stream" in str(at) or
        len(updated_markdown) > len(initial_markdown) or
        "Streaming Error" in str(at) or
        len(updated_errors) > 0
    ), "Clicking Run should cause visible change (new content, error, etc.)"