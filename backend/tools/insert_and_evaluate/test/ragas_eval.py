from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_similarity,
)

import os
import json
import argparse
from dotenv import load_dotenv
from ragas import evaluate
from ragas.metrics import faithfulness, context_precision, context_recall
from datasets import Dataset
from langchain_openai import ChatOpenAI

def main(jsonl_path):
    load_dotenv()

    llm = ChatOpenAI(
        model="llama3-70b-8192", 
        temperature=0
    )

    with open(jsonl_path, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                ragas_input = [{
                    "question": data.get("question"),
                    "ground_truth": data.get("larger_context"),
                    "contexts": data.get("candidates") if isinstance(data.get("candidates"), list) else [data.get("candidates")],
                    "answer": data.get("answer")
                }]

                dataset = Dataset.from_list(ragas_input)

                result = evaluate(
                    dataset,
                    metrics=[
                        faithfulness,
                        context_precision,
                        context_recall,
                    ],
                    llm=llm
                )

                print(result)
            except Exception as e:
                print(f"Error processing line: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate RAGAS metrics on a JSONL dataset.")
    parser.add_argument(
        "--jsonl_path",
        type=str,
        default="tools/insert_db/data/eval.jsonl",
        help="Path to the .jsonl file to evaluate"
    )
    args = parser.parse_args()
    main(args.jsonl_path)

