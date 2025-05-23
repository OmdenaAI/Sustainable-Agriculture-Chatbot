Here the goal is to create user personas and simulate conversations with the chatbot via the API and the save them to a format that is further usable for chatbot evaluation. 

conversation_simulation.py is using user_personas_and_qs_A, i.e. users created by Adelia, however, Catalina's approach is more thorough as it also gives users characteristics. 

for chatbot evaluation we need:
- user persona
- a specific topic
- kickoff question
- subsequent questions -- either hard-coded or let the llm ask more questions depending on the first answer
- actual factual answers from our sources to be able to compare the output against them

chatbot_eval.py uses deepeval, however, i don't have an openai api key for which under models i tried to write a custom groq integration that is not working for the moment. 

here the task is to develop metrics that we can all use. 