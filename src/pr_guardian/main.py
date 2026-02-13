# src/pr_guardian/main.py

from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from .graph import app_graph
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os

# Load environment variables from the root .env file
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="PR Guardian API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReviewRequest(BaseModel):
    code: str
    thread_id: str
    model_names: list[str] = ["gpt-4o"]

@app.get("/")
def read_root():
    return {"message": "PR Guardian API is online"}

def check_model_keys(model_name: str):
    # Check if the required API key for a model is present.
    # Standardized to HUGGINGFACE_API_KEY to resolve the mismatch.
    if model_name.startswith("hf/") and not os.getenv("HUGGINGFACE_API_KEY"):
        return False, "Missing HUGGINGFACE_API_KEY"
    if model_name == "together" and not os.getenv("TOGETHER_API_KEY"):
        return False, "Missing TOGETHER_API_KEY"
    if "claude" in model_name and not os.getenv("ANTHROPIC_API_KEY"):
        return False, "Missing ANTHROPIC_API_KEY"
    if model_name == "groq" and not os.getenv("GROQ_API_KEY"):
        return False, "Missing GROQ_API_KEY"
    if model_name == "gpt-4o" and not os.getenv("OPENAI_API_KEY"):
        return False, "Missing OPENAI_API_KEY"
    return True, None

async def run_model(code: str, model_name: str, thread_id: str):
    # Runs a single model and returns (model_name, review or error).
    has_key, key_error = check_model_keys(model_name)
    if not has_key:
        return model_name, f"ERROR: {key_error}"

    config = {
        "configurable": {
            "thread_id": thread_id,
            "model_name": model_name
        }
    }

    initial_state = {"code": code, "reviews": {}}

    try:
        result = await app_graph.ainvoke(initial_state, config=config)
        reviews = result.get("reviews", {})
        content = reviews.get(model_name, "No output returned.")
    except Exception as e:
        content = f"ERROR: {str(e)}"

    return model_name, content

@app.post("/review")
async def review_code(request: ReviewRequest):
    thread_id = request.thread_id.strip() or "default_session"

    if not request.model_names:
        raise HTTPException(status_code=400, detail="No models selected.")

    tasks = [run_model(request.code, model_name, thread_id) for model_name in request.model_names]
    results = await asyncio.gather(*tasks)

    reviews_dict = {model_name: content for model_name, content in results}

    # Final report collation
    final_report = "\n\n".join(
        f"## Review from **{model}**\n{txt}" for model, txt in reviews_dict.items()
    )

    return {"report": final_report, "reviews": reviews_dict}