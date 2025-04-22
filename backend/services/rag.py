# Setting the path 

import sys
import os

# Add the parent folder of 'services' (i.e., 'backend') to the module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# import from the db and llm packages
from db.qdrant import qdrant  # Ensure qdrant.py 
from llm import llm  # Ensure llm.py 

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

system_prompt = (
    "You are a highly capable assistant tasked with answering questions based on provided context. "
    "Refer to the following context when formulating your answer. If the answer isn't clear, "
    "politely state that you don't know. Keep your response concise and informative. "
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

retriever = qdrant.as_retriever(search_type="similarity", search_kwargs={"k": 10})  # For showing 10 results
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

response = rag_chain.invoke({"input": "What does sustainable agriculture mean?"})
print(response["answer"])
