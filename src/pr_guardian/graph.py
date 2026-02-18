import os
import asyncio
import httpx
from typing import TypedDict, Dict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the provided code and give a thorough PR review covering:
- Bugs and correctness issues
- Security vulnerabilities
- Performance concerns
- Code quality and readability
- Suggestions for improvement

Format your response in clear markdown with sections."""


class AgentState(TypedDict):
    code: str
    reviews: Dict[str, str]
    user_message: str


async def call_openai(code: str, user_message: str) -> str:
    prompt = f"{code}\n\n{user_message}" if user_message else code
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def call_groq(code: str, user_message: str) -> str:
    prompt = f"{code}\n\n{user_message}" if user_message else code
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def call_ollama(model: str, code: str, user_message: str) -> str:
    prompt = f"{code}\n\n{user_message}" if user_message else code
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


async def run_all_reviews(code: str, user_message: str) -> Dict[str, str]:
    """Run all four model calls concurrently."""
    results = await asyncio.gather(
        call_openai(code, user_message),
        call_groq(code, user_message),
        call_ollama("deepseek-r1:1.5b", code, user_message),
        call_ollama("llama3.2", code, user_message),
        return_exceptions=True,
    )

    model_ids = ["gpt-4o", "groq", "local/deepseek-r1:1.5b", "local/llama3.2"]
    reviews = {}
    for model_id, result in zip(model_ids, results):
        if isinstance(result, Exception):
            reviews[model_id] = f"Error calling model: {type(result).__name__}: {result}"
        else:
            reviews[model_id] = result

    return reviews


async def code_reviewer(state: AgentState) -> dict:
    reviews = await run_all_reviews(state["code"], state.get("user_message", ""))
    return {"reviews": reviews}


def create_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("reviewer", code_reviewer)
    workflow.set_entry_point("reviewer")
    workflow.add_edge("reviewer", END)
    return workflow.compile()