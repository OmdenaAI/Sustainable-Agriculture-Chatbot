from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import os
load_dotenv()

# Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Load The APi keys
QDRANT_URL=os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') # Embeddings


# Retrival
qdrant = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    collection_name="my_documents", # Collection name
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)