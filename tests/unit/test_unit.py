# tests/test_unit.py
import pytest
from pr_guardian.main import is_allowed_local, ReviewRequest

def test_model_filtering_logic():
    # Only allowed models pass the filter
    assert is_allowed_local("llama3.2") is True
    assert is_allowed_local("deepseek-r1:1.5b") is True
    assert is_allowed_local("mistral") is False # Mistral is restricted

def test_review_request_validation():
    # Test that 3 models are now accepted
    req = ReviewRequest(
        code="print('hello')",
        model_names=["gpt-4o", "local/llama3.2", "gpt-4o-mini"]
    )
    assert len(req.model_names) == 3

    # Test that 4 models are rejected by Pydantic
    with pytest.raises(ValueError):
        ReviewRequest(
            code="print('hello')",
            model_names=["gpt-4o", "local/llama3.2", "gpt-4o-mini", "groq"]
        )