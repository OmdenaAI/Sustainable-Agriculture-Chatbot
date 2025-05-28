import json
import logging
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric
from models.custom_groq import GroqLLM
from templates.custom_template import CustomAnswerRelevancyTemplate
import os


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)


input_folder = "simulated_conversations_results/"
output_folder = "evaluation_score_results/"

model = GroqLLM()
metric = AnswerRelevancyMetric(model=model, evaluation_template=CustomAnswerRelevancyTemplate)


for file in os.listdir(input_folder):
    if file.endswith(".json"):
        logging.info(f"Processing file: {file}")
        input_file = f"{input_folder}/{file}"
        output_file = f"{output_folder}scores_{file}"

        with open(input_file) as f:
            data = json.load(f)

        tests = data["tests"]

        scores = []
        
        for test in tests:
            try:
                test_case = LLMTestCase(
                    input=test["input"],
                    actual_output=test["model_response"],
                    expected_output=test["expected_output"],
                    retrieval_context=[test["kickoff_context"]],
                )

                metric.measure(test_case)
                scores.append({"question": test["input"], "score": metric.score})

            except Exception as e:
                logging.error(f"Error processing test case: {e}")
                continue
            
        with open(output_file, "w") as f:
            json.dump(scores, f, indent=4)