from pr_guardian.graph import get_model

def test_factory_all_providers():
    assert "ChatAnthropic" in str(type(get_model("claude")))
    assert "ChatTogether" in str(type(get_model("together")))
    assert "ChatGroq" in str(type(get_model("groq")))
    # Hugging Face returns a ChatHuggingFace wrapper
    assert "ChatHuggingFace" in str(type(get_model("hf/gpt2")))