import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pr_guardian.graph import get_model, review_node

# Testing the routing logic
def test_get_model_routing():
    # Test local routing
    local_model = get_model("local")
    assert local_model.openai_api_base == "http://localhost:11434/v1"
    
    # Test Anthropic routing
    claude_model = get_model("claude")
    from langchain_anthropic import ChatAnthropic
    assert isinstance(claude_model, ChatAnthropic)

# Testing the review node with AsyncMock
@pytest.mark.asyncio
async def test_review_node_async(sample_state):
    with patch("pr_guardian.graph.get_model") as mock_factory:
        # Implementing AsyncMock for the awaitable ainvoke call
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Audit Complete"))
        mock_factory.return_value = mock_llm
        
        config = {"configurable": {"model_id": "gpt-4o"}}
        result = await review_node(sample_state, config)
        
        # Verify the new dictionary structure
        assert "gpt-4o" in result["reviews"]
        assert result["reviews"]["gpt-4o"] == "Audit Complete"

@pytest.mark.asyncio
async def test_parallel_accumulation_logic():
    from pr_guardian.graph import review_node
    
    # Initial state
    state = {"code": "x = 1", "reviews": {}}
    
    with patch("pr_guardian.graph.get_model") as mock_factory:
        mock_llm = MagicMock()
        mock_factory.return_value = mock_llm
        
        # First "Parallel" Task: Model A
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Report A"))
        res1 = await review_node(state, {"configurable": {"model_id": "model_a"}})
        state["reviews"].update(res1["reviews"])
        
        # Second "Parallel" Task: Model B
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Report B"))
        res2 = await review_node(state, {"configurable": {"model_id": "model_b"}})
        state["reviews"].update(res2["reviews"])
        
        # Assert accumulation happened
        assert len(state["reviews"]) == 2
        assert state["reviews"]["model_a"] == "Report A"
        assert state["reviews"]["model_b"] == "Report B"

@pytest.mark.asyncio
async def test_parallel_accumulation_logic():
    from pr_guardian.graph import review_node
    
    # Initial state
    state = {"code": "x = 1", "reviews": {}}
    
    with patch("pr_guardian.graph.get_model") as mock_factory:
        mock_llm = MagicMock()
        mock_factory.return_value = mock_llm
        
        # First "Parallel" Task: Model A
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Report A"))
        res1 = await review_node(state, {"configurable": {"model_id": "model_a"}})
        state["reviews"].update(res1["reviews"])
        
        # Second "Parallel" Task: Model B
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Report B"))
        res2 = await review_node(state, {"configurable": {"model_id": "model_b"}})
        state["reviews"].update(res2["reviews"])
        
        # Assert accumulation happened
        assert len(state["reviews"]) == 2
        assert state["reviews"]["model_a"] == "Report A"
        assert state["reviews"]["model_b"] == "Report B"