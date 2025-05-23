from deepeval.models import DeepEvalBaseLLM
import requests
from app.core.config import settings
from deepeval.metrics.answer_relevancy.answer_relevancy import Statements


class GroqLLM(DeepEvalBaseLLM):
    def __init__(self, model_name: str = "llama3-70b-8192"):
        self.model_name = model_name
        self.api_key = settings.OPENAI_API_KEY

    def load_model(self):
        return None 

    def generate(self, prompt: str) -> str:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
        )
        return response.json()["choices"][0]["message"]["content"]

    async def a_generate(self, prompt: str, **kwargs) -> str:
        output_text = self.generate(prompt)
        # Wrap the raw string output in Statements object
        return Statements(statements=[output_text])

    def get_model_name(self):
        return f"Groq-{self.model_name}"
