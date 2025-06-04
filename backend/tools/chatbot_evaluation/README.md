# Chatbot Evaluation Toolkit

This folder contains tools and scripts for evaluating chatbot performance using simulated user personas and conversations. The workflow is designed to help you create, simulate, and score chatbot interactions for research and development purposes.

## Folder Structure

- `chatbot_eval.py`: Evaluates chatbot responses using the `deepeval` library and custom metrics. Processes simulated conversation results and outputs evaluation scores. Logging is set up to display progress and errors in the console.
- `conversation_simulation.py`: Simulates conversations with the chatbot API using user personas and question sets. Supports different persona formats and conversation strategies.
- `user_personas_and_qs/`: Contains user persona JSON files, each with a profile, topic, kickoff question, and follow-up questions (with answers). Personas include user characteristics for more realistic simulations (profiles).
- `simulated_conversations_results/`: Stores the results of simulated conversations in JSON format, ready for evaluation.
- `evaluation_score_results/`: Stores the output of chatbot evaluation runs, with scores for each question.
- `models/`: Custom model integrations (e.g., GroqLLM) for use with evaluation scripts.
- `templates/`: Custom evaluation templates of metrics for answer relevancy.

## Workflow

1. **Create User Personas**: Define user profiles, topics, kickoff questions, and follow-up questions in `user_personas_and_qs/`.
2. **Simulate Conversations**: Run `conversation_simulation.py` to generate simulated conversations between personas and the chatbot. Results are saved in `simulated_conversations_results/`.
3. **Evaluate Responses**: Run `chatbot_eval.py` to score chatbot responses using custom or standard metrics. Scores are saved in `evaluation_score_results/`.
4. **Assess Scores**: Evaluate scores saved in `evaluation_score_results/`.

## Notes

- The evaluation uses the `deepeval` package. If you do not have an OpenAI API key, you can use or extend the custom Groq integration in `models/custom_groq`.


## Future tasks
- Develop and refine evaluation metrics for consistent and meaningful chatbot assessment.
- Expand persona and question sets for broader coverage.
- Improve model integration and simulations.
- Improve prompts in `templates/custom_template`, but avoid over customization.
