from dotenv import load_dotenv
import os
load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

from langchain_groq import ChatGroq

llm = ChatGroq(model="llama-3.3-70b-versatile",temperature=0.3,api_key=GROQ_API_KEY)