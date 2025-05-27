from deepeval.models import DeepEvalBaseLLM
import requests
from app.core.config import Settings
from deepeval.metrics.answer_relevancy.answer_relevancy import Statements
from deepeval.metrics.answer_relevancy.schema import Verdicts,AnswerRelevancyVerdict, Reason
from dotenv import load_dotenv
from time import sleep

load_dotenv()
settings = Settings()

class GroqLLM(DeepEvalBaseLLM):
    def __init__(self, model_name: str = "llama3-70b-8192"):
        self.model_name = model_name
        self.api_key = settings.GROQ_API_KEY
         

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
                "temperature": 0,
            }
        )
        if response.status_code == 429:
            print("Rate limit exceeded. Waiting...")
            sleep(5)
            return self.generate(prompt)

        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

    async def a_generate(self, prompt: str, schema = str, **kwargs):
        output_text = self.generate(prompt)
        if schema == str:
            response = output_text
        else:
            try:
                response = schema.model_validate_json(output_text)
            except:
                raise TypeError("Json is not in the expected format")
        return response

    def get_model_name(self):
        return f"Groq-{self.model_name}"
