import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from pr_guardian.graph import create_graph

app = FastAPI(title="PR Guardian API")

class ReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50000)
    model_names: List[str] = Field(..., min_length=1, max_length=3)
    user_message: Optional[str] = Field(None, max_length=1000)

    @field_validator("model_names")
    @classmethod
    def validate_models(cls, v: List[str]) -> List[str]:
        # Constraint: No mistral references
        for model in v:
            if "mistral" in model.lower():
                raise ValueError("Mistral models are restricted.")
        return v

@app.get("/models")
async def get_available_models():
    return {
        "GPT-4o": "gpt-4o",
        "Groq: Llama 3.3": "groq",
        "Local: DeepSeek R1": "local/deepseek-r1:1.5b",
        "Local: Llama 3.2": "local/llama3.2",
    }

@app.post("/review")
async def run_review(request: ReviewRequest):
    graph = create_graph()

    async def event_generator():
        initial_state = {
            "code": request.code,
            "user_message": request.user_message or "",
            "reviews": {}, 
            "final_report": "",
        }

        async for event in graph.astream(initial_state):
            for _, output in event.items():
                if "reviews" in output and output["reviews"]:
                    reviews = output["reviews"]
                    
                    if isinstance(reviews, dict):
                        # Stream each model's review as a separate SSE message
                        for model_id, review_text in reviews.items():
                            # Only stream if the model was actually requested
                            if model_id in request.model_names:
                                chunk = {"model": model_id, "review": review_text}
                                yield f"data: {json.dumps(chunk)}\n\n"
                    
                    elif isinstance(reviews, list):
                        chunk = {"model": request.model_names[0], "review": reviews[-1]}
                        yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")