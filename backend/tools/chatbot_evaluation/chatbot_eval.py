import json
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric
from models.custom_groq import GroqLLM
from templates.custom_template import CustomAnswerRelevancyTemplate
# Load your JSON file
with open("results_user_personas_A/chatbot_test_results.json") as f:
    data = json.load(f)

tests = data["tests"]

model = GroqLLM()
metric = AnswerRelevancyMetric(model=model, evaluation_template=CustomAnswerRelevancyTemplate)
for test in tests:
    test_case = LLMTestCase(
        input=test["input"],
        actual_output=test["model_response"],
        expected_output=test["expected_output"],
        retrieval_context=[test["kickoff_context"]]
    )

    metric.measure(test_case)
    print(f"Question: {test['input']}")
    print(f"Relevance Score: {metric.score}")
    print("----")

