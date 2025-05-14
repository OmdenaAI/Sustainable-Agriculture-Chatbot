import os
import json
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
import os
import json
import argparse
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def generate_question_and_answer(client, text):
    prompt = (
        "Given the following paragraph, generate a question that can be answered using the paragraph, "
        "and then provide the answer. Try to come up with a question that a farmer would ask, less scholarly, more practical. "
        "No questions about number of pages, names of researchers. If it's not possible, return an empty string.\n\n"
        f"Paragraph:\n{text.strip()}\n\n"
        "Format your response like this:\nQuestion: <your question>\nAnswer: <your answer>"
    )

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=256,
    )

    output = response.choices[0].message.content.strip()
    question, answer = None, None
    for line in output.split("\n"):
        if line.lower().startswith("question:"):
            question = line.partition(":")[2].strip()
        elif line.lower().startswith("answer:"):
            answer = line.partition(":")[2].strip()

    if not question or not answer:
        raise ValueError("Failed to parse question/answer:\n" + output)

    return question, answer

def main(root_dir, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )

    for folder_name in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder_name)
        chunk_file = os.path.join(folder_path, "chunks.json")
        if not os.path.exists(chunk_file):
            continue

        with open(chunk_file, "r") as f:
            try:
                chunks = json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading JSON in {chunk_file}")
                continue

        for chunk in tqdm(chunks, desc=f"Processing {folder_name}"):
            text = chunk.get("text", "").strip()
            if not text:
                continue

            try:
                question, answer = generate_question_and_answer(client, text)
                if question and answer:
                    entry = {
                        "chunk_id": chunk.get("chunk_id"),
                        "doc_id": chunk.get("doc_id"),
                        "source": chunk.get("source_url"),
                        "question": question,
                        "answer": answer,
                        "context": text
                    }

                    with open(output_path, "a") as out_file:
                        out_file.write(json.dumps(entry) + "\n")
            except Exception as e:
                print(f"Failed to generate QA for chunk {chunk.get('chunk_id')}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate farmer-style QA pairs from paragraph chunks.")
    parser.add_argument(
        "--root",
        type=str,
        default="tools/evaluate_retrieval/output_20250502/chunked",
        help="Root directory containing folders of chunks.json files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="tools/insert_db/data/generated_questions_farmer_persona_chunk_ids_fixed.jsonl",
        help="Path to output .jsonl file"
    )
    args = parser.parse_args()
    main(args.root, args.output)


