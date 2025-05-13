## Current Implementation Overview

chatbot should be tested with real Qdrant Integration
It uses a **mock implementation** of the RAG (Retrieval-Augmented Generation) system. This document explains how the current implementation works and provides a detailed guide for connecting to a real Qdrant vector database.

## How the Current Mock Implementation Works

The current `RAGService` class in `app/services/rag.py` implements a simplified in-memory version of a vector database:

1. **Document Storage**: Documents are stored in an in-memory Python list (`self._documents`)
2. **Mock Embeddings**: Instead of using a real embedding API, it generates "fake" embeddings using MD5 hashes
3. **Simplified Retrieval**: Document retrieval uses random similarity scores instead of actual vector similarity

This approach allows for development and testing without requiring an actual vector database, but has several limitations:
- Documents are lost when the server restarts
- Similarity search is not accurate (uses random scores)
- Won't scale to large document collections (all in memory)
- No persistence or backup capabilities

## Connecting to Qdrant

[Qdrant](https://qdrant.tech/) is a vector database designed for production-ready similarity search. To implement a proper Qdrant connection, follow these steps:

### 1. Prerequisites

1. **Qdrant Instance**: Either:
   - Set up a local Qdrant instance using Docker:
     \`\`\`bash
     docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
     \`\`\`
   - Create a cloud instance at [Qdrant Cloud](https://cloud.qdrant.io/)

2. **Environment Variables**: Ensure these are set in your `.env` file:
   \`\`\`
   QDRANT_URL=http://localhost:6333  # or your cloud URL
   QDRANT_API_KEY=your_api_key_here  # if using Qdrant Cloud
   QDRANT_COLLECTION=agriculture_documents
   \`\`\`

3. **Dependencies**: Install the Qdrant client:
   \`\`\`bash
   poetry add qdrant-client
   \`\`\`

### 2. Implementing the Qdrant Connection

Replace the current mock implementation in `app/services/rag.py` with a real Qdrant connection:

```python
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        """Initialize the RAG service with Qdrant connection"""
        try:
            # Connect to Qdrant
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            # Create collection if it doesn't exist
            if settings.QDRANT_COLLECTION not in collection_names:
                self.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=models.VectorParams(
                        size=settings.EMBEDDING_DIMENSION,  # 1536 for OpenAI embeddings
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION}")
            
            logger.info("Connected to Qdrant successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise

    async def generate_embedding(self, text):
        """
        Generate an embedding for the given text using OpenAI API
        
        Args:
            text: The text to embed
            
        Returns:
            list: The embedding vector
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    async def add_documents(self, documents):
        """
        Add documents to Qdrant
        
        Args:
            documents: List of document chunks with content and metadata
            
        Returns:
            int: Number of documents added
        """
        try:
            # Log the operation
            logger.info(f"Adding {len(documents)} documents to Qdrant")
            
            points = []
            for doc in documents:
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
                
                # Generate embedding for the content
                embedding = await self.generate_embedding(content)
                
                # Create a point for Qdrant
                import uuid
                doc_id = str(uuid.uuid4())
                
                points.append(models.PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "content": content,
                        "metadata": metadata
                    }
                ))
            
            # Batch insert into Qdrant
            self.client.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=points
            )
            
            return len(documents)
        except Exception as e:
            logger.error(f"Error adding documents to Qdrant: {str(e)}")
            raise

    async def store_document(self, content, embedding, metadata):
        """
        Store a single document and its embedding in Qdrant
        
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
            
            self.client.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=[models.PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "content": content,
                        "metadata": metadata
                    }
                )]
            )
            
            logger.info(f"Stored document {doc_id} in Qdrant")
            return doc_id
        except Exception as e:
            logger.error(f"Error storing document in Qdrant: {str(e)}")
            raise

    async def retrieve(self, query, limit=10):
        """
        Retrieve relevant documents for a query from Qdrant
        
        Args:
            query: The query text
            limit: Maximum number of results to return
            
        Returns:
            list: Relevant documents
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.generate_embedding(query)
            
            # Search Qdrant
            search_result = self.client.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                results.append({
                    "doc_id": str(scored_point.id),
                    "text": scored_point.payload.get("content", ""),
                    "metadata": scored_point.payload.get("metadata", {}),
                    "score": scored_point.score
                })
            
            return results
        except Exception as e:
            logger.error(f"Error retrieving documents from Qdrant: {str(e)}")
            raise

    if not self.use_mock:
        try:
            await self.qdrant_repo.initialize()
            logger.info("Qdrant repository initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant repository: {str(e)}")
            logger.warning("Falling back to mock RAG implementation")
            self.use_mock = True
