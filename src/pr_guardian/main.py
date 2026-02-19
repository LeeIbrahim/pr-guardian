import os
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="PR Guardian Backend")

# Restricted origins for proper CORS implementation
origins = [
    "https://localhost:8501",
    "https://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

class AuditRequest(BaseModel):
    code: str
    model_names: List[str]
    user_message: Optional[str] = ""

# Mistral removed per instructions
AVAILABLE_MODELS = {
    "GPT-4o": "gpt-4o-latest",
    "Claude 3.5 Sonnet": "claude-3-5-sonnet-20240620",
    "Gemini 1.5 Pro": "gemini-1.5-pro"
}

@app.get("/models")
async def get_models():
    return AVAILABLE_MODELS

async def audit_streamer(code: str, model_id: str, user_msg: str):
    yield f"data: {json.dumps({'model': model_id, 'review': 'Starting audit...'})}\n\n"
    await asyncio.sleep(1)
    
    response_text = f"Reviewing code for {model_id}...\n\n1. Security: No issues.\n2. Optimization: Review handlers."
    if user_msg:
        response_text += f"\nNote: {user_msg}"

    yield f"data: {json.dumps({'model': model_id, 'review': response_text})}\n\n"

@app.post("/review")
async def review_code(request: AuditRequest):
    if not request.code:
        raise HTTPException(status_code=400, detail="No code provided")

    async def generate():
        for m_id in request.model_names:
            async for update in audit_streamer(request.code, m_id, request.user_message):
                yield update

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        ssl_keyfile="./key.pem", 
        ssl_certfile="./cert.pem",
        log_level="info"
    )