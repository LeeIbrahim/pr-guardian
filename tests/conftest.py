# tests/conftest.py
import pytest
import os
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def sample_code():
    return "def insecure_function(): os.system('rm -rf /')"

@pytest.fixture
def sample_state(sample_code):
    return {
        "code": sample_code,
        "reviews": {},
        "final_report": ""
    }

@pytest.fixture
def mock_llm_response():
    # Helper to create a fake AIMessage response compatible with LangChain
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=MagicMock(content="✅ Test audit passed."))
    return mock