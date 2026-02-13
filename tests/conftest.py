import pytest
from unittest.mock import MagicMock
from pr_guardian.graph import app_graph

@pytest.fixture
def mock_llm_response():
    # Helper to create a fake AIMessage response
    mock = MagicMock()
    mock.ainvoke.return_value = MagicMock(content="✅ Test audit passed.")
    return mock

@pytest.fixture
def sample_state():
    return {
        "code": "def hello(): print('world')",
        "reviews": {}
    }