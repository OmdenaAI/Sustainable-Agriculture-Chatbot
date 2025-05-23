import json
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from models.custom_groq import GroqLLM

# Load your JSON file
with open("tools/chatbot_evaluation/results_user_personas_A/chatbot_test_results.json") as f:
    data = json.load(f)

tests = data["tests"]

model = GroqLLM()
metric = AnswerRelevancyMetric(model=model)

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

