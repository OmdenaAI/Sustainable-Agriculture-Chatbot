from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
import numpy as np
import logging
import uuid
import os

from app.core.config import settings
from app.core.exceptions import DatabaseError

# Setup logging
logger = logging.getLogger(__name__)

# Singleton pattern for Qdrant client
_qdrant_client = None

async def get_qdrant_client() -> QdrantClient:
    """
    Returns a singleton instance of the Qdrant client
    """
    global _qdrant_client
    
    if _qdrant_client is None:
        try:
            # Initialize client
            logger.info(f"Initializing Qdrant client with URL: {settings.QDRANT_URL}")
            
            _qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
            
            # Create collection if it doesn't exist
            collections = _qdrant_client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if settings.QDRANT_COLLECTION not in collection_names:
                logger.info(f"Creating Qdrant collection: {settings.QDRANT_COLLECTION}")
                
                _qdrant_client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=models.VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=models.Distance.COSINE,
                    )
                )
                logger.info(f"Created collection: {settings.QDRANT_COLLECTION}")
        except Exception as e:
            logger.error(f"Error initializing Qdrant client: {str(e)}")
            raise DatabaseError(f"Failed to initialize Qdrant client: {str(e)}")
    
    return _qdrant_client

class QdrantRepository:
    """
    Repository for interacting with Qdrant vector database
    """
    def __init__(self):
        self.client = None
        self.collection_name = settings.QDRANT_COLLECTION
    
    async def initialize(self):
        """
        Initialize the Qdrant client
        """
        self.client = await get_qdrant_client()
        if not self.client:
            logger.warning("Qdrant client not initialized")
    
    async def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        """
        Add documents with their embeddings to the vector database
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Qdrant client")
                raise DatabaseError("Failed to initialize Qdrant client")
        
        try:
            points = []
            
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                # Generate a unique ID for each document
                doc_id = str(uuid.uuid4())
                
                points.append(
                    models.PointStruct(
                        id=doc_id,
                        vector=embedding,
                        payload={
                            "text": doc.get("text", ""),
                            "metadata": doc.get("metadata", {}),
                            "doc_id": doc_id
                        }
                    )
                )
            
            # Upsert points to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} documents to Qdrant")
            return len(points)
            
        except Exception as e:
            logger.error(f"Error adding documents to Qdrant: {str(e)}")
            raise DatabaseError(f"Failed to add documents to Qdrant: {str(e)}")
    
    async def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents based on embedding
        """
        if not self.client:
            await self.initialize()
            if not self.client:
                logger.error("Failed to initialize Qdrant client")
                raise DatabaseError("Failed to initialize Qdrant client")
        
        try:
            # Search for similar documents
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Format results
            results = []
            for result in search_result:
                results.append({
                    "text": result.payload.get("text", ""),
                    "metadata": result.payload.get("metadata", {}),
                    "score": result.score,
                    "doc_id": result.payload.get("doc_id", "")
                })
            
            logger.info(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for similar documents: {str(e)}")
            raise DatabaseError(f"Failed to search for similar documents: {str(e)}")