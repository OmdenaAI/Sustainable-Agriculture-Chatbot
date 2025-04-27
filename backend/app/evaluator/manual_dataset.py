from datasets import Dataset

data = [
    {
        "question": "How can I increase tomato yield?",
        "ground_truth": "You can increase tomato yield by using high-quality seeds, proper irrigation, and fertilizers.",
        "contexts": [
            "Using drip irrigation helps increase tomato yield.",
            "Proper fertilizer usage is crucial for healthy tomato plants."
        ],
        "answer": "Use drip irrigation and good fertilizer to improve your tomato yield."
    },
    # Add more QA examples here
]

dataset = Dataset.from_list(data)
