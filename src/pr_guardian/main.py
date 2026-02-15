# src/pr_guardian/main.py

import json
import asyncio
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from .graph import _build_graph #
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import MemorySaver

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="PR Guardian API")
memory = MemorySaver()

# FIX: Compile using the builder function to define app_graph
app_graph = _build_graph().compile(checkpointer=memory)

class ReviewRequest(BaseModel):
    code: str
    thread_id: str
    model_names: list[str] = ["gpt-4o"]
    sequential: bool = False #

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    # FIX: Ensure the key matches the test expectation ("message")
    return {"message": "PR Guardian API is online"}

async def run_model(code: str, model_name: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id, "model_name": model_name}}
    # We pass the same thread_id so models share memory in sequential mode
    initial_state = {"code": code, "reviews": {}, "messages": []}

    try:
        result = await app_graph.ainvoke(initial_state, config=config)
        if result is None:
            return model_name, "ERROR: Graph returned None."
        reviews = result.get("reviews", {})
        content = reviews.get(model_name, "No output returned.")
    except Exception as e:
        content = f"ERROR: {str(e)}"
    return model_name, content

async def stream_reviews_generator(request: ReviewRequest):
    if request.sequential:
        # Sequential: Models run one after another
        for m_name in request.model_names:
            model_name, content = await run_model(request.code, m_name, request.thread_id)
            yield f"data: {json.dumps({'model': model_name, 'review': content})}\n\n"
    else:
        # Parallel: Models run concurrently
        tasks = [run_model(request.code, m, request.thread_id) for m in request.model_names]
        for future in asyncio.as_completed(tasks):
            model_name, content = await future
            yield f"data: {json.dumps({'model': model_name, 'review': content})}\n\n"

@app.post("/review")
async def review_code(request: ReviewRequest):
    if not request.model_names:
        raise HTTPException(status_code=400, detail="No models selected.")
    return StreamingResponse(
        stream_reviews_generator(request),
        media_type="text/event-stream"
    )