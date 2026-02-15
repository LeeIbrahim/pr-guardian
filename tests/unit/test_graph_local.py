import pytest
from pr_guardian.graph import merge_reviews, get_model
from langchain_ollama import OllamaLLM

def test_merge_reviews_logic():
    # Ensures that multi-model results don't overwrite each other
    existing = {"gpt-4o": "Security look good."}
    new = {"local/llama3.1:latest": "Add input validation."}
    result = merge_reviews(existing, new)
    
    assert len(result) == 2
    assert "gpt-4o" in result
    assert "local/llama3.1:latest" in result

def test_ollama_routing_syntax():
    # Test that 'local/llama3.1' correctly maps to OllamaLLM with :latest
    model = get_model("local/llama3.1")
    assert isinstance(model, OllamaLLM)
    assert model.model == "llama3.1:latest"
    assert model.base_url == "http://127.0.0.1:11434"