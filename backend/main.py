# main.py
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from dotenv import load_dotenv
from graph import create_graph

load_dotenv()

app = FastAPI(title="PR Guardian Backend")

# Restricted origins for CORS implementation 
origins = [
    "https://localhost:5173",
    "https://127.0.0.1:5173",

    "http://localhost:5173",
    "http://127.0.0.1:5173",
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

AVAILABLE_MODELS = {
    "GPT-4o": "gpt-4o-latest",
    "Grok 3": "grok-3",
    "DeepSeek R1 (Local)": "local/deepseek-r1:1.5b",
    "Llama 3.2 (Local)": "local/llama3.2"
}

@app.get("/models")
async def get_models():
    return [
        {"label": name, "value": model_id} 
        for name, model_id in AVAILABLE_MODELS.items()
    ]

@app.post("/review")
async def review_code(request: AuditRequest):
    if not request.code:
        raise HTTPException(status_code=400, detail="No code provided")

    workflow = create_graph()

    async def generate():
        inputs = {"code": request.code, "user_message": request.user_message}
        result = await workflow.ainvoke(inputs)
        
        # Stream the individual model reviews back to the GUI 
        for model_id, review_text in result["reviews"].items():
            yield f"data: {json.dumps({'model': model_id, 'review': review_text})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        ssl_keyfile="./key.pem", 
        ssl_certfile="./cert.pem"
    )