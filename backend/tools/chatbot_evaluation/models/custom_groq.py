from deepeval.models import DeepEvalBaseLLM
import requests
from app.core.config import Settings
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
            print("Model rate limit exceeded. Waiting...")
            sleep(5)
            return self.generate(prompt)

        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

    def parse_to_schema(self, output_text: str, schema: str, try_number=0, max_tries=5):
        if schema == str:
            return output_text
        else:
            try:
                return schema.model_validate_json(output_text)
            except Exception as e:
                print(f"Error parsing JSON, try {try_number + 1}")
                if try_number < max_tries:
                    prompt = f"""Make the following a valid JSON, only return a valid JSON.
                    Wrong JSON:
                    {output_text}
                    Fixed JSON:
                    """
                    output_text = self.generate(prompt)
                    return self.parse_to_schema(output_text, schema, try_number + 1, max_tries)
                else:
                    raise TypeError(f"Json is not in the expected format")
                


    async def a_generate(self, prompt: str, schema = str, **kwargs):
        output_text = self.generate(prompt)
        response = self.parse_to_schema(output_text, schema)
        return response

    def get_model_name(self):
        return f"Groq-{self.model_name}"
