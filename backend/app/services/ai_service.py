import logging
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceError

# Setup logging
logger = logging.getLogger(__name__)

class AIService:
    """
    Service for interacting with AI models
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-70b-8192"  # Groq's LLaMA 3 model
    
    async def generate_response(
        self,
        message: str,
        context: List[Dict[str, Any]],
        history: List[Dict[str, str]],
        user_id: str
    ) -> str:
        """
        Generate a response using the AI model
        """
        try:
            # Format context for the prompt
            context_text = ""
            if context:
                context_text = "\n\n".join([doc["text"] for doc in context])
            
            # Create system message with agriculture focus and context
            system_message = {
                "role": "system",
                "content": f"""You are an agriculture expert assistant. 
Your goal is to provide helpful, accurate information about farming, crops, livestock, and agricultural practices.
Always base your answers on the provided context when available.

When you don't know the answer or don't have enough context, admit it and suggest what information might help.
Keep responses concise, practical, and focused on helping farmers and agricultural professionals.

Context information:
{context_text}"""
            }
            
            # Format conversation history
            messages = [system_message]
            
            # Add history messages
            for msg in history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make API request to AI provider
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1024
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                # Extract the generated text
                generated_text = response_data["choices"][0]["message"]["content"]
                
                return generated_text
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise AIServiceError(f"AI API error: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise AIServiceError(f"AI request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise AIServiceError(f"Error generating response: {str(e)}")