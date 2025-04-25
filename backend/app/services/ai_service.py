import logging
from typing import List, Dict
import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.services.rag import RAGService
import os

# Setup logging
logger = logging.getLogger(__name__)

GROQ_MODEL = "llama3-70b-8192" 
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
K_RETRIEVED = 10
TEMPERATURE = 0.7
MAX_TOKENS = 1024
TIMEOUT = 30.0

class AIService:
    """
    Service for interacting with AI models, integrated with RAGService for context retrieval
    """
    def __init__(self, rag_service: RAGService = None):
        self.api_key = settings.GROQ_API_KEY
        self.api_url = GROQ_URL
        self.model = GROQ_MODEL  

        # Initialize RAGService
        if rag_service is None:
            self.rag_service = RAGService()
        else:
            self.rag_service = rag_service

    async def initialize(self):
        """
        Initialize the AI service and its dependencies asynchronously.
        """
        # Ensure the RAGService is initialized
        await self.rag_service.initialize()


    def load_system_prompt(self) -> str:
        """
        Load the system message prompt from a text file.
        """
        prompt_file_path = os.path.join("app/prompts", "basic_prompt.txt")
        
        try:
            with open(prompt_file_path, "r") as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"Prompt file {prompt_file_path} not found.")
            raise AIServiceError(f"Prompt file {prompt_file_path} not found.")
        except Exception as e:
            logger.error(f"Error loading prompt: {str(e)}")
            raise AIServiceError(f"Error loading prompt: {str(e)}")
    

    async def generate_response(
        self,
        message: str,
        history: List[Dict[str, str]],
        user_id: str,
        limit: int = K_RETRIEVED
    ) -> str:
        """
        Generate a response using the AI model, first retrieving context from RAGService
        """
        try:
            # Retrieve context from RAG service
            rag_result = await self.rag_service.retrieve(query=message, limit=limit)
            context = rag_result.get("answer", "")

            # Create system message with agriculture focus and context
            system_prompt = self.load_system_prompt() 

            system_message = {
                "role": "system",
                "content": system_prompt.format(context=context) 
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
                        "temperature": TEMPERATURE,
                        "max_tokens": MAX_TOKENS
                    },
                    timeout=TIMEOUT
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
