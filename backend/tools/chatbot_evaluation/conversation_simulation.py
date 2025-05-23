import json
import requests

API_URL = "http://localhost:8000/api/chat"
INPUT_JSON = "tools/chatbot_evaluation/user_personas_and_qs_A/topic_001.json"         
OUTPUT_JSON = "tools/chatbot_evaluation/results_user_personas_A/chatbot_test_results.json"

def load_data(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def query_chatbot(question):
    response = requests.post(API_URL, json={
        "message": question,
        "history": []
    })

    if response.status_code == 200:
        return response.json().get("response", "").strip()
    else:
        return f"[Error {response.status_code}]"

def run_evaluation(data):
    topic = data.get("topic", "")
    kickoff = data.get("conversation", {}).get("kickoff", "")
    follow_ups = data.get("conversation", {}).get("follow_up", [])

    results = []

    for item in follow_ups:
        question = item["question"]
        expected = item["answer"]
        actual = query_chatbot(question)

        results.append({
            "input": question,
            "expected_output": expected,
            "model_response": actual,
            "topic": topic,
            "kickoff_context": kickoff
        })

    return results

if __name__ == "__main__":
    input_data = load_data(INPUT_JSON)
    evaluation_results = run_evaluation(input_data)

    with open(OUTPUT_JSON, "w") as f:
        json.dump({"tests": evaluation_results}, f, indent=2)

    print(f"✅ Done. Results saved to: {OUTPUT_JSON}")
