import json
import requests
import os


API_URL = "http://localhost:8000/chat/"
input_folder = "user_personas_and_qs/"         
output_folder= "simulated_conversations_results/"

def load_data(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def query_chatbot(prompt):
    response = requests.post(API_URL, json={
        "prompt": prompt,
    })

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"[Error {response.status_code}]"

def run_evaluation(data):
    topic = data.get("topic", "")
    profile = data.get("profile", "")
    if isinstance(profile, dict):
        user_profile = ", ".join(f"{key}: {value}" for key, value in profile.items())
    else:
        user_profile = str(profile)
    kickoff = data.get("conversation", {}).get("kickoff", "")
    follow_ups = data.get("conversation", {}).get("follow_up", [])
    results = []

    for item in follow_ups:
        question = item["question"]
        expected = item["answer"]
        prompt = f"Use the user profile: {user_profile} and the Topic: {topic} to answer the question {question}. Please provide anwsers up 300 characters."
        actual = query_chatbot(prompt)

        results.append({
            "input": question,
            "expected_output": expected,
            "model_response": actual,
            "topic": topic,
            "kickoff_context": kickoff
        })

    return results

if __name__ == "__main__":

    for file in os.listdir(input_folder):
        if file.endswith(".json"):
            input_file = f"{input_folder}/{file}"
            output_file = f"{output_folder}simulation_{file}"
            input_data = load_data(input_file)
            evaluation_results = run_evaluation(input_data)
            
            with open(output_file, "w") as f:
                json.dump({"tests": evaluation_results}, f, indent=2)

            print(f"✅ Done. Results saved to: {output_file}")
