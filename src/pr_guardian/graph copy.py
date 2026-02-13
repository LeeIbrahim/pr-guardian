import os
from typing import Annotated, TypedDict, Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_together import ChatTogether
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

def get_model(model_name: str):
    m_name = model_name.lower()
    
    # Hugging Face Inference API
    if "hf/" in m_name:
        # Expected format: "hf/meta-llama/Llama-3.2-3B-Instruct"
        repo_id = model_name.replace("hf/", "")
        llm = HuggingFaceEndpoint(
            repo_id=repo_id,
            task="text-generation",
            huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_KEY")
        )
        return ChatHuggingFace(llm=llm)
    
    if "claude" in m_name:
        return ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0)
    
    elif "together" in m_name:
        return ChatTogether(model="meta-llama/Llama-3.3-70b-instruct-turbo")
    
    elif "groq" in m_name:
        return ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    elif "local" in m_name:
        return ChatOpenAI(model="llama3.1", base_url="http://localhost:11434/v1", api_key="ollama")
    
    else:
        return ChatOpenAI(model=model_name, temperature=0)

# State Definition for Comparison
class AgentState(TypedDict):
    # The state object passed between nodes in the graph.
    code: str
    reviews: Dict[str, str]

async def review_node(state: AgentState, config: RunnableConfig):
    model_id = config["configurable"].get("model_id", "gpt-4o")
    llm = get_model(model_id)
    
    prompt = [
        SystemMessage(content="You are a Senior Developer. Audit the code for security and style."),
        HumanMessage(content=state["code"])
    ]
    response = await llm.ainvoke(prompt)
    
    # Returns the result in a dictionary keyed by the model name
    return {"reviews": {model_id: response.content}}

workflow = StateGraph(AgentState)
workflow.add_node("reviewer", review_node)

workflow.set_entry_point("reviewer")
workflow.add_edge("reviewer", END)

app_graph = workflow.compile()