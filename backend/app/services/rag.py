import logging
from typing import List, Dict, Any
import os

from app.core.config import settings
from app.db.qdrant import QdrantRepository
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.initialized = False
        self.qdrant_repo = QdrantRepository()
        # Check if we should use the mock implementation
        self.use_mock = os.getenv("USE_MOCK_RAG", "true").lower() == "true"
        if self.use_mock:
            logger.warning("Using mock RAG implementation - no real document retrieval will be used")
        self._documents = []  # In-memory storage for mock implementation
    
    async def initialize(self):
        """Initialize the RAG service"""
        logger.info("Initializing RAG service")
        
        if not self.use_mock:
            try:
                await self.qdrant_repo.initialize()
                logger.info("Qdrant repository initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant repository: {str(e)}")
                logger.warning("Falling back to mock RAG implementation")
                self.use_mock = True
        
        self.initialized = True
        logger.info("RAG service initialized")

    async def generate_embedding(self, text):
        """
        Generate an embedding for the given text
        
        Args:
            text: The text to embed
            
        Returns:
            list: The embedding vector
        """
        try:
            if self.use_mock:
                # Mock implementation
                import hashlib
                
                # Create a deterministic "embedding" based on the hash of the text
                hash_obj = hashlib.md5(text.encode())
                hash_bytes = hash_obj.digest()
                
                # Convert hash bytes to a list of floats between -1 and 1
                mock_embedding = [((b / 255) * 2 - 1) for b in hash_bytes]
                
                # Pad or truncate to get a fixed size
                embedding_size = settings.EMBEDDING_DIMENSION
                if len(mock_embedding) < embedding_size:
                    mock_embedding.extend([0] * (embedding_size - len(mock_embedding)))
                else:
                    mock_embedding = mock_embedding[:embedding_size]
                
                return mock_embedding
            else:
                # Real implementation using OpenAI
                try:
                    from openai import OpenAI
                    
                    client = OpenAI(api_key=settings.OPENAI_API_KEY)
                    response = client.embeddings.create(
                        model="text-embedding-3-small",
                        input=text
                    )
                    
                    return response.data[0].embedding
                except ImportError:
                    logger.error("OpenAI package not installed, falling back to mock")
                    self.use_mock = True
                    return await self.generate_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    async def add_documents(self, documents):
        """
        Add documents to the vector database
        
        Args:
            documents: List of document chunks with content and metadata
            
        Returns:
            int: Number of documents added
        """
        try:
            logger.info(f"Adding {len(documents)} documents to vector database")
            
            if self.use_mock:
                # Mock implementation
                for doc in documents:
                    content = doc.get("content", "")
                    metadata = doc.get("metadata", {})
                    
                    # Generate embedding for the content
                    embedding = await self.generate_embedding(content)
                    
                    # Store in mock database
                    await self.store_document(content, embedding, metadata)
                
                return len(documents)
            else:
                # Real implementation
                embeddings = []
                for doc in documents:
                    embedding = await self.generate_embedding(doc.get("content", ""))
                    embeddings.append(embedding)
                
                return await self.qdrant_repo.add_documents(documents, embeddings)
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    async def store_document(self, content, embedding, metadata):
        """
        Store a document and its embedding in the vector database
        
        Args:
            content: The document content
            embedding: The embedding vector
            metadata: Additional metadata
            
        Returns:
            str: The document ID
        """
        try:
            import uuid
            doc_id = str(uuid.uuid4())
            
            if self.use_mock:
                # Mock implementation
                logger.info(f"Stored document {doc_id} in mock vector database")
                
                self._documents.append({
                    "id": doc_id,
                    "content": content,
                    "embedding": embedding,
                    "metadata": metadata
                })
            else:
                # Real implementation
                documents = [{
                    "text": content,
                    "metadata": metadata
                }]
                embeddings = [embedding]
                await self.qdrant_repo.add_documents(documents, embeddings)
                logger.info(f"Stored document {doc_id} in Qdrant")
            
            return doc_id
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            raise

    async def retrieve(self, query, limit=10):
        """
        Retrieve relevant documents for a query
        
        Args:
            query: The query text
            limit: Maximum number of results to return
            
        Returns:
            list: Relevant documents
        """
        logger.info(f"RAG retrieve called with query: {query[:50]}...")
        
        try:
            if self.use_mock:
                # For development/testing, return empty or mock results
                if not self._documents:
                    return []
                
                # Generate embedding for the query
                query_embedding = await self.generate_embedding(query)
                
                # Calculate similarity scores (simplified)
                import random
                results = []
                for doc in self._documents:
                    # In a real implementation, you would use cosine similarity
                    # For now, we'll just return all documents with a random score
                    score = random.uniform(0.5, 0.9)
                    
                    results.append({
                        "doc_id": doc["id"],
                        "text": doc["content"],
                        "metadata": doc["metadata"],
                        "score": score
                    })
                
                # Sort by score and limit results
                results.sort(key=lambda x: x["score"], reverse=True)
                return results[:limit]
            else:
                # Real implementation using Qdrant
                query_embedding = await self.generate_embedding(query)
                return await self.qdrant_repo.search_similar(query_embedding, limit)
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            # If there's an error, return an empty list to avoid breaking the chat flow
            return []
