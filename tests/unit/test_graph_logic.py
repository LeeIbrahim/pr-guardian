# tests/unit/test_graph_logic.py
import pytest
from pr_guardian.graph import get_model, merge_reviews

def test_merge_reviews_logic():
    # Test that the Annotated merge function correctly handles state updates
    existing = {"gpt-4o": "Review A"}
    new = {"local/llama3.2:latest": "Review B"}
    result = merge_reviews(existing, new)
    assert len(result) == 2
    assert result["gpt-4o"] == "Review A"

def test_ollama_routing_logic():
    # Verifies that 'local/llama3.2' is transformed correctly
    model = get_model("local/llama3.2")
    assert model.model == "llama3.2:latest"
    assert "11434" in model.base_url

def test_hf_router_initialization():
    # Verifies that HF models return the AsyncInferenceClient
    from huggingface_hub import AsyncInferenceClient
    model = get_model("hf/Qwen/Qwen2.5-Coder-7B-Instruct")
    assert isinstance(model, AsyncInferenceClient)