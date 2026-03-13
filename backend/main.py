# main.py
import asyncio
import json
import os
import uvicorn
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from graph import create_graph

load_dotenv()

app = FastAPI(title="PR Guardian Backend")

# Restricted origins for CORS implementation
origins = [
    "https://pr-guardian-ui.onrender.com"
]

# Dev routes to make it easier to work in the dev environments and sometimes not use ssl.
environment = os.getenv("ENVIRONMENT")
if environment == "development":
    origins.extend([
        "https://localhost:3000",
        "http://localhost:3000",

        "https://127.0.0.1:3000",
        "http://127.0.0.1:3000",
        
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

class AuditRequest(BaseModel):
    code: str
    model_names: List[str]
    user_message: Optional[str] = ""

# This effectively works as a health check.
@app.get("/models")
async def get_models():
    return [
        {"label": name, "value": model_id} 
        for name, model_id in os.getenv("VITE_AVAILABLE_MODELS").items()
    ]

@app.post("/review")
async def review_code(request: AuditRequest):
    if not request.code:
        raise HTTPException(status_code=400, detail="No code provided")

    workflow = create_graph()

    async def generate():
        inputs = {
            "code": request.code,
            "user_message": request.user_message,
            "models": request.model_names
        }
        result = await workflow.ainvoke(inputs)
        
        # Stream the individual model reviews back to the GUI 
        for model_id, review_text in result["reviews"].items():
            yield f"data: {json.dumps({'model': model_id, 'review': review_text})}\n\n"
            # Yield control to ensure the chunk is sent
            await asyncio.sleep(0)

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=os.getenv("VITE_BACKEND_URL"), 
        port=8000, 
        ssl_keyfile="./key.pem", 
        ssl_certfile="./cert.pem"
    )