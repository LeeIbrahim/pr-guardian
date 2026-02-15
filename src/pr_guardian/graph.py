# src/pr_guardian/graph.py

from __future__ import annotations
import os
from typing import Dict, TypedDict, Annotated

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_ollama import OllamaLLM
from huggingface_hub import AsyncInferenceClient

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    code: str
    reviews: Annotated[dict, merge_reviews]
    final_report: str

# Merge function to safely update the state dictionary
def merge_reviews(existing: dict, new: dict) -> dict:
    updated = existing.copy()
    updated.update(new)
    return updated

class AgentState(TypedDict):
    code: str
    reviews: Annotated[dict, merge_reviews]
    final_report: str

def get_model(model_name: str):
    m_name = model_name.lower()

    # Local Llama via Ollama (No API Key needed)
    if m_name.startswith("local/"):
        local_model = m_name.split("/", 1)[1]

        if ":" not in local_model:
            local_model = f"{local_model}:latest"

        return OllamaLLM(
            model=local_model,
            base_url="http://127.0.0.1:11434",
            timeout=120
        )

    # Hugging Face via the 2026 Router
    if m_name.startswith("hf/"):
        repo_id = model_name.split("/", 1)[1]
        hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        return AsyncInferenceClient(
            model=repo_id,
            token=hf_key,
            provider="auto" # Router finds the model across all providers to avoid 404s
        )

    # Groq Llama 3.3 integration
    if m_name == "groq":
        return ChatGroq(
            model_name="llama-3.3-70b-versatile", 
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

    return ChatOpenAI(
        model="gpt-4o", 
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

async def review_node(state: AgentState, config: RunnableConfig) -> Dict:
    model_name = config.get("configurable", {}).get("model_name", "gpt-4o")
    
    try:
        llm = get_model(model_name)
        prompt = f"Audit this code for security and performance vulnerabilities:\n\n{state['code']}"
        
        if model_name.startswith("hf/"):
            resp = await llm.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.1
            )
            content = resp.choices[0].message.content
        else:
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            
    except Exception as e:
        # Surface errors directly to the UI for easier debugging
        content = f"DEBUG ERROR: {type(e).__name__} - {str(e)}"
        
    return {"reviews": {model_name: content}}

async def final_node(state: AgentState) -> Dict:
    reviews = state.get("reviews", {})
    report_parts = [f"### Review from {m}\n{c}" for m, c in reviews.items()]
    return {"final_report": "\n\n".join(report_parts)}

def _build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("reviewer", review_node)
    workflow.add_node("final", final_node)

    workflow.set_entry_point("reviewer")
    workflow.add_edge("reviewer", "final")
    workflow.add_edge("final", END)

    # Return the UNCOMPILED workflow so main.py can add a checkpointer
    return workflow

app_graph = _build_graph().compile()