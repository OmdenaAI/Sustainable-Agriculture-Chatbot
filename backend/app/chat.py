import os
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel
import httpx

router = APIRouter()
load_dotenv(".env.development")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class PromptRequest(BaseModel):
    prompt: str

@router.post("/")
async def chat(request: PromptRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ API Key not configured")
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt
                }
            ],
            "temperature": 0.5
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"GROQ API error: {response.text}"
                )
                
            return response.json()
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
