# backend/app/services/rag.py
import logging
from typing import Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

import os
from dotenv import load_dotenv

from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)
load_dotenv()

MODEL = "models/text-embedding-004"
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "my_documents"
K_RETRIEVED = 10
SEARCH_TYPE = "similarity"

class RAGService:
    """
    Service for Retrieval-Augmented Generation, but simplified to just retrieve from Qdrant
    """
    def __init__(self):
        self.initialized = False
        self.retriever = None

    async def initialize(self):
        """
        Initialize the Qdrant retriever
        """
        try:
            logger.info("Initializing Qdrant retriever")

            QDRANT_URL = QDRANT_URL
            QDRANT_API_KEY = QDRANT_API_KEY

            embeddings = GoogleGenerativeAIEmbeddings(model=MODEL)

            qdrant = QdrantVectorStore.from_existing_collection(
                embedding=embeddings,
                collection_name=COLLECTION_NAME,
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
            )

            self.retriever = qdrant.as_retriever(search_type=SEARCH_TYPE, search_kwargs={"k": K_RETRIEVED})

            self.initialized = True
            logger.info("Qdrant retriever initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing Qdrant retriever: {str(e)}")
            self.initialized = False

    async def retrieve(self, query: str, limit: int = K_RETRIEVED) -> Dict[str, Any]:
        """
        Retrieve relevant information for a user query directly from Qdrant
        """
        if not self.initialized:
            logger.warning("Qdrant retriever not initialized")
            return {"answer": "Qdrant retriever not initialized."}

        try:
            logger.info(f"Processing query: {query[:50]}...")
            results = self.retriever.retrieve(query, k=limit)

            if not results:
                return {"answer": "No relevant documents found."}

            answer = "\n".join([result["text"] for result in results])
            return {"answer": answer}
        
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return {"answer": "An error occurred while processing the query."}


    
    #def _mock_results(self) -> List[Dict[str, Any]]:
    #    """
    #    Return mock results for development
    #    """
    #    return [
    #        {
    #            "text": "Sustainable farming practices include crop rotation, which helps maintain soil health and reduce pest problems.",
    #            "metadata": {
    #                "source": "Sustainable Farming Guide",
    #                "relevance": 0.92
    #            },
    #            "score": 0.92,
    #            "doc_id": "doc1"
    #        },
    #        {
    #            "text": "Integrated Pest Management (IPM) is an ecosystem-based strategy that focuses on long-term prevention of pests.",
    #            "metadata": {
    #                "source": "IPM Handbook",
    #                "relevance": 0.85
    #            },
    #            "score": 0.85,
    #            "doc_id": "doc2"
    #        },
    #        {
    #            "text": "Conservation tillage practices can significantly reduce soil erosion and improve soil health.",
    #            "metadata": {
    #                "source": "Soil Conservation Manual",
    #                "relevance": 0.78
    #            },
    #            "score": 0.78,
    #            "doc_id": "doc3"
    #        }
    #    ]