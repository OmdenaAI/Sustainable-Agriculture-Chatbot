from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_similarity,
)
from ragas.evaluation import evaluate
from datasets import Dataset
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()

llm = ChatOpenAI(
    model="llama3-70b-8192", 
    temperature=0
)

with open('tools/insert_db/data/eval.jsonl') as f:
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
            print(e)
