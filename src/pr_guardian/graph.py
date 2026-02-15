# src/pr_guardian/graph.py

from __future__ import annotations
import os
from typing import Dict, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_ollama import OllamaLLM
from huggingface_hub import AsyncInferenceClient

# Helper function to merge reviews into state
def merge_reviews(existing: dict, new: dict) -> dict:
    updated = existing.copy()
    updated.update(new)
    return updated

# Define the state shape
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    code: str
    reviews: Annotated[dict, merge_reviews]
    final_report: str

# Logic to route and initialize specific LLM instances
def get_model(model_name: str):
    m_name = model_name.lower()
    
    # Handle local models via Ollama
    if m_name.startswith("local/"):
        local_model = m_name.split("/", 1)[1]
        if ":" not in local_model:
            local_model = f"{local_model}:latest"
        return OllamaLLM(model=local_model, base_url="http://127.0.0.1:11434")
    
    # Handle Groq Llama models
    if m_name == "groq":
        return ChatGroq(model_name="llama-3.3-70b-versatile")
    
    # Handle Hugging Face inference models
    if m_name.startswith("hf/"):
        repo_id = model_name.split("/", 1)[1]
        return AsyncInferenceClient(model=repo_id, token=os.getenv("HUGGINGFACE_API_KEY"))

    # Default to OpenAI models
    return ChatOpenAI(model=m_name, temperature=0.1)

# Primary node for performing code reviews
async def review_node(state: AgentState, config: RunnableConfig) -> Dict:
    model_name = config.get("configurable", {}).get("model_name", "gpt-4o")
    existing_reviews = state.get("reviews", {})
    
    prompt = f"Audit this code for security vulnerabilities:\n\n{state['code']}"
    
    # Check for previous reviews to support sequential chaining
    if existing_reviews:
        context = "\n".join([f"- {m}: {c[:300]}..." for m, c in existing_reviews.items()])
        prompt = (
            f"Code:\n{state['code']}\n\n"
            f"Previous findings:\n{context}\n\n"
            f"Identify any FALSE POSITIVES from previous models and add new insights."
        )

    try:
        llm = get_model(model_name)
        if model_name.startswith("hf/"):
            resp = await llm.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024
            )
            content = resp.choices[0].message.content
        else:
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        content = f"ERROR: {str(e)}"
        
    return {"reviews": {model_name: content}}

# Graph construction
def _build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("reviewer", review_node)
    workflow.set_entry_point("reviewer")
    workflow.add_edge("reviewer", END)
    return workflow