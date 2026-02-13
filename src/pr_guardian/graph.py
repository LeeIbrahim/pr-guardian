# src/pr_guardian/graph.py

from __future__ import annotations
import os
from typing import Dict, TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEndpoint

def get_model(model_name: str):
    # Return a concrete LangChain chat model based on a short identifier.
    # Raises RuntimeError with a clean message if any required key is missing.
    m_name = model_name.lower()

    # HuggingFace inference API (hf/<repo_id>)
    if m_name.startswith("hf/"):
        repo_id = model_name.split("/", 1)[1]
        hf_key = os.getenv("HUGGINGFACE_API_KEY")
        if not hf_key:
            raise RuntimeError(
                "HuggingFace API key missing. Set HUGGINGFACE_API_KEY in .env."
            )
        # Bypassing ChatHuggingFace wrapper to fix StopIteration errors and improve stability
        return HuggingFaceEndpoint(
            repo_id=repo_id,
            task="text-generation",
            huggingfacehub_api_token=hf_key,
            timeout=300,
            max_new_tokens=1024,
            temperature=0.1
        )

    # Anthropic Claude
    if "claude" in m_name:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise RuntimeError(
                "Anthropic API key missing. Set ANTHROPIC_API_KEY in .env."
            )
        return ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0)

    # Together.ai
    if "together" in m_name:
        together_key = os.getenv("TOGETHER_API_KEY")
        if not together_key:
            raise RuntimeError(
                "Together.ai API key missing. Set TOGETHER_API_KEY in .env."
            )
        return ChatOpenAI(
            model="meta-llama/Llama-3.3-70b-instruct-turbo",
            base_url="https://api.together.xyz/v1",
            api_key=together_key,
        )

    # Groq
    if "groq" in m_name:
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise RuntimeError(
                "Groq API key missing. Set GROQ_API_KEY in .env."
            )
        return ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    # Local Ollama (OpenAI-compatible)
    if "local" in m_name:
        return ChatOpenAI(
            model="llama3.1",
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )

    # Default OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError(
            "OpenAI API key missing. Set OPENAI_API_KEY in .env."
        )
    return ChatOpenAI(model=model_name, temperature=0)

class AgentState(TypedDict):
    code: str
    reviews: Dict[str, str]
    final_report: str | None

async def review_node(state: AgentState, config: RunnableConfig) -> AgentState:
    # Calls the selected LLM and stores its answer under state["reviews"].
    # Gracefully catches errors and stores them instead of crashing.
    model_name = config.get("configurable", {}).get("model_name", "gpt-4o")
    reviews = state.setdefault("reviews", {})

    try:
        llm = get_model(model_name)

        # Standardizing prompt for both Chat models and Endpoints
        prompt = f"System: You are a Senior Developer. Human: Audit the code for security and style: {state['code']}"

        response = await llm.ainvoke(prompt, config=config)
        
        # Handle response content variations between different LangChain model types
        if hasattr(response, "content"):
            content = response.content
        else:
            content = str(response)

    except Exception as e:
        content = f"ERROR: {str(e)}"

    reviews[model_name] = content
    state["reviews"] = reviews
    return state

def final_node(state: AgentState, config: RunnableConfig) -> AgentState:
    # Collates all individual reviews into a single markdown report.
    if not state.get("reviews"):
        state["final_report"] = "No reviews were generated."
        return state

    report_parts = [
        f"## Review from **{model}**\n{txt}" for model, txt in state["reviews"].items()
    ]
    state["final_report"] = "\n\n".join(report_parts)
    return state

def _build_graph() -> StateGraph:
    # Compiles the LangGraph workflow.
    graph = StateGraph(AgentState)

    graph.add_node("reviewer", review_node)
    graph.add_node("final", final_node)

    graph.set_entry_point("reviewer")
    graph.add_edge("reviewer", "final")
    graph.add_edge("final", END)

    return graph.compile()

app_graph = _build_graph()